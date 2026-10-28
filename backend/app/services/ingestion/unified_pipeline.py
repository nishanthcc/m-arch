import time
import hashlib
import logging
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.models import Project, Source, SourceSnapshot, ProjectImportJob, Chunk
from app.services.ingestion.validator import validate_and_extract_archive, ALLOWED_EXTENSIONS, DISALLOWED_BINARIES, is_safe_path
from app.services.ingestion.extractor import extract_file_content, detect_file_type
from app.services.ingestion.chunker import chunk_text
from app.services.profiling.profiler import project_profiler
from app.services.embeddings.local_embeddings import embedding_service
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.fts_index import index_chunk_fts, delete_project_fts

logger = logging.getLogger("m-arch.ingestion")

class UnifiedIngestionPipeline:
    """
    Unified, reliable, and idempotent ingestion pipeline for:
    - GitHub repository snapshots
    - Local ZIP archives
    - Multiple source files & folders
    Enforces persistent job states: queued -> validating -> extracting -> profiling -> snapshotting -> indexing -> ready.
    """

    async def run_archive_ingestion(
        self,
        session: AsyncSession,
        job_id: str,
        project_id: str,
        archive_path: Path,
        importer_type: str = "zip_upload"
    ) -> Dict[str, Any]:
        """Runs full 7-step pipeline on a uploaded ZIP archive."""
        stmt = select(ProjectImportJob).where(ProjectImportJob.id == job_id)
        job = (await session.execute(stmt)).scalar_one_or_none()
        p_stmt = select(Project).where(Project.id == project_id)
        project = (await session.execute(p_stmt)).scalar_one_or_none()

        if not job or not project:
            raise ValueError("Job or Project not found")

        try:
            # 1. Validating
            job.status = "validating"
            job.progress_percent = 15
            job.status_message = "Validating archive integrity and size..."
            await session.commit()

            if not archive_path.exists() or not zipfile.is_zipfile(archive_path):
                raise ValueError("Uploaded archive is corrupt or not a valid ZIP file.")

            # 2. Extracting
            job.status = "extracting"
            job.progress_percent = 35
            job.status_message = "Safely extracting files and enforcing security policies..."
            await session.commit()

            snapshot_id = f"snap_{int(time.time())}_{project_id[:8]}"
            snapshot_dir = (settings.STORAGE_DIR / project_id / "snapshots" / snapshot_id).resolve()
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            extracted_files = validate_and_extract_archive(archive_path, snapshot_dir)

            # 3. Snapshotting sources
            job.status = "snapshotting"
            job.progress_percent = 55
            job.status_message = f"Indexing {len(extracted_files)} accepted files into immutable snapshot..."
            await session.commit()

            hasher = hashlib.sha256()
            total_bytes = 0
            created_sources: List[Source] = []

            for f in extracted_files:
                resolved_f = f.resolve()
                rel_path = resolved_f.relative_to(snapshot_dir).as_posix()
                content, sha256, line_count = extract_file_content(resolved_f)
                file_type = detect_file_type(resolved_f)
                f_size = resolved_f.stat().st_size
                total_bytes += f_size
                hasher.update(sha256.encode("utf-8"))

                source = Source(
                    project_id=project_id,
                    file_path=rel_path,
                    file_name=resolved_f.name,
                    file_type=file_type,
                    file_size=f_size,
                    content_hash=sha256,
                    line_count=line_count,
                    storage_path=str(resolved_f),
                    snapshot_id=snapshot_id
                )
                session.add(source)
                created_sources.append(source)

            aggregate_hash = hasher.hexdigest()

            snapshot = SourceSnapshot(
                id=snapshot_id,
                project_id=project_id,
                snapshot_type=importer_type,
                source_hash=aggregate_hash,
                source_count=len(created_sources),
                total_size_bytes=total_bytes,
                storage_path=str(snapshot_dir),
                is_current=True
            )
            session.add(snapshot)

            # Update Project pointers
            project.storage_path = str(snapshot_dir)
            project.current_snapshot_id = snapshot_id
            project.source_count = len(created_sources)
            await session.commit()

            # 4. Profiling
            job.status = "profiling"
            job.progress_percent = 70
            job.status_message = "Profiling application architecture, frameworks, and routes..."
            await session.commit()

            profile_data = project_profiler.analyze_snapshot(
                snapshot_id=snapshot_id,
                project_id=project_id,
                sources=created_sources,
                snapshot_dir=snapshot_dir,
                user_context=project.user_context or {}
            )
            await project_profiler.save_or_update_profile(session, project_id, snapshot_id, profile_data)

            # 5. Indexing (FTS5 + Dense Vectors)
            job.status = "indexing"
            job.progress_percent = 85
            job.status_message = "Generating vector embeddings and SQLite FTS5 indexes..."
            await session.commit()

            created_chunks = await self._index_sources(session, project_id, created_sources)

            # 6. Ready
            job.status = "completed"
            job.progress_percent = 100
            job.status_message = f"Ready: {len(created_sources)} files and {created_chunks} chunks indexed."
            job.files_accepted = len(created_sources)
            job.files_skipped = 0
            job.total_size_bytes = total_bytes
            job.chunks_created = created_chunks
            job.snapshot_id = snapshot_id

            project.status = "ready"
            project.chunk_count = created_chunks
            project.indexing_metadata = {
                "embedding_model": embedding_service.model_name,
                "dimension": embedding_service.dimension,
                "chunks_indexed": created_chunks,
                "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            await session.commit()

            return {
                "status": "completed",
                "snapshot_id": snapshot_id,
                "source_count": len(created_sources),
                "chunk_count": created_chunks
            }

        except Exception as exc:
            logger.error(f"Ingestion job {job_id} failed: {exc}", exc_info=True)
            job.status = "failed"
            job.progress_percent = 100
            job.status_message = "Ingestion failed."
            job.error_message = str(exc)
            project.status = "error"
            await session.commit()
            raise exc

    async def _index_sources(
        self,
        session: AsyncSession,
        project_id: str,
        sources: List[Source]
    ) -> int:
        """Chunks and indexes sources into SQLite FTS5 and dense vector store."""
        await delete_project_fts(session, project_id)

        all_chunk_ids = []
        all_chunk_texts = []
        created_chunks = 0

        for source in sources:
            source_file = Path(source.storage_path)
            if not source_file.exists():
                continue

            content = source_file.read_text(encoding="utf-8", errors="replace")
            chunk_items = chunk_text(source.id, content, source.file_type)

            for item in chunk_items:
                chunk = Chunk(
                    id=item.chunk_id,
                    project_id=project_id,
                    source_id=source.id,
                    chunk_index=item.chunk_index,
                    content=item.content,
                    start_line=item.start_line,
                    end_line=item.end_line,
                    section_heading=item.section_heading,
                    token_count=item.token_count,
                    embedding_id=item.chunk_id
                )
                session.add(chunk)
                created_chunks += 1

                await index_chunk_fts(
                    session,
                    chunk_id=item.chunk_id,
                    project_id=project_id,
                    source_id=source.id,
                    file_path=source.file_path,
                    content=item.content
                )
                all_chunk_ids.append(item.chunk_id)
                all_chunk_texts.append(item.content)

        if all_chunk_texts:
            vectors = embedding_service.embed_batch(all_chunk_texts)
            vector_store.save_vectors(project_id, all_chunk_ids, vectors)

        return created_chunks

unified_ingestion = UnifiedIngestionPipeline()
