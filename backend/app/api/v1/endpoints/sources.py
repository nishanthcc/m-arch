import os
import shutil
import hashlib
import time
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import Project, Source, SourceSnapshot, ProjectProfile, Chunk
from app.schemas import SourceResponse, SourceExcerptResponse, ProjectProfileResponse, ProjectUserContextUpdate
from app.core.config import settings
from app.services.ingestion.validator import validate_and_extract_archive, ALLOWED_EXTENSIONS, DISALLOWED_BINARIES, is_safe_path
from app.services.ingestion.extractor import extract_file_content, detect_file_type
from app.services.ingestion.chunker import chunk_text
from app.services.profiling.profiler import project_profiler
from app.services.embeddings.local_embeddings import embedding_service
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.fts_index import index_chunk_fts, delete_project_fts

router = APIRouter()

@router.get("/projects/{project_id}/sources", response_model=List[SourceResponse])
async def list_project_sources(project_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Source).where(Source.project_id == project_id).order_by(Source.file_path)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/projects/{project_id}/sources", response_model=List[SourceResponse], status_code=status.HTTP_201_CREATED)
async def upload_project_sources(
    project_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided for upload.")

    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    storage_root = (Path(project.storage_path) if project.storage_path else (settings.STORAGE_DIR / project.id)).resolve()
    storage_root.mkdir(parents=True, exist_ok=True)

    created_sources: List[Source] = []
    hasher = hashlib.sha256()
    total_bytes = 0
    snapshot_type = "file_upload"
    snapshot_id = f"snap_{int(time.time())}_{project.id[:8]}"

    for upload_file in files:
        filename = upload_file.filename or "unknown_file"
        file_bytes = await upload_file.read()

        if len(file_bytes) == 0:
            continue

        # Check maximum file size
        max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' ({round(len(file_bytes)/(1024*1024), 2)}MB) exceeds maximum limit of {settings.UPLOAD_MAX_MB}MB"
            )

        # 1. Handle ZIP archive upload
        if filename.lower().endswith(".zip"):
            snapshot_type = "zip_upload"
            temp_zip = (storage_root / f"temp_{int(time.time())}_{filename}").resolve()
            temp_zip.parent.mkdir(parents=True, exist_ok=True)
            temp_zip.write_bytes(file_bytes)
            extracted_dir = (storage_root / "repo").resolve()
            try:
                extracted_files = validate_and_extract_archive(temp_zip, extracted_dir)
            except ValueError as val_err:
                temp_zip.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail=str(val_err))
            finally:
                temp_zip.unlink(missing_ok=True)

            for ext_file in extracted_files:
                resolved_ext = ext_file.resolve()
                rel_path = resolved_ext.relative_to(extracted_dir).as_posix()
                content, sha256, line_count = extract_file_content(ext_file)
                file_type = detect_file_type(ext_file)
                f_size = ext_file.stat().st_size
                total_bytes += f_size
                hasher.update(sha256.encode("utf-8"))

                source = Source(
                    project_id=project.id,
                    file_path=rel_path,
                    file_name=ext_file.name,
                    file_type=file_type,
                    file_size=f_size,
                    content_hash=sha256,
                    line_count=line_count,
                    storage_path=str(ext_file),
                    snapshot_id=snapshot_id
                )
                db.add(source)
                created_sources.append(source)

        # 2. Handle Individual Source Files / Folder Uploads
        else:
            # Clean filename and check path traversal
            clean_filename = filename.replace("\\", "/").lstrip("/")
            if ".." in clean_filename:
                continue

            dest_file = (storage_root / clean_filename).resolve()
            if not is_safe_path(storage_root, dest_file):
                continue

            suffix = dest_file.suffix.lower()
            if suffix in DISALLOWED_BINARIES:
                continue

            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(file_bytes)
            content, sha256, line_count = extract_file_content(dest_file)
            file_type = detect_file_type(dest_file)
            total_bytes += len(file_bytes)
            hasher.update(sha256.encode("utf-8"))

            source = Source(
                project_id=project.id,
                file_path=clean_filename,
                file_name=dest_file.name,
                file_type=file_type,
                file_size=len(file_bytes),
                content_hash=sha256,
                line_count=line_count,
                storage_path=str(dest_file),
                snapshot_id=snapshot_id
            )
            db.add(source)
            created_sources.append(source)

    if not created_sources:
        raise HTTPException(
            status_code=400,
            detail="No valid source files were accepted (files may have been empty, binary, or unsupported)."
        )

    # Mark existing snapshots as not current
    prev_snaps = (await db.execute(select(SourceSnapshot).where(SourceSnapshot.project_id == project.id))).scalars().all()
    for ps in prev_snaps:
        ps.is_current = False

    # Create immutable SourceSnapshot
    snapshot = SourceSnapshot(
        id=snapshot_id,
        project_id=project.id,
        snapshot_type=snapshot_type,
        source_hash=hasher.hexdigest(),
        source_count=len(created_sources),
        total_size_bytes=total_bytes,
        storage_path=str(storage_root),
        is_current=True
    )
    db.add(snapshot)

    project.source_count = project.source_count + len(created_sources)
    project.current_snapshot_id = snapshot_id
    project.status = "indexing"
    await db.commit()

    # Step: Profile Application
    profile_data = project_profiler.analyze_snapshot(
        snapshot_id=snapshot_id,
        project_id=project.id,
        sources=created_sources,
        snapshot_dir=storage_root,
        user_context=project.user_context or {}
    )
    await project_profiler.save_or_update_profile(db, project.id, snapshot_id, profile_data)

    # Step: Chunk and Index Sources into FTS5 and Vector Embeddings
    all_chunk_ids = []
    all_chunk_texts = []
    created_chunks = 0

    for src in created_sources:
        src_path = Path(src.storage_path)
        if not src_path.exists():
            continue
        c_text = src_path.read_text(encoding="utf-8", errors="replace")
        chunk_items = chunk_text(src.id, c_text, src.file_type)

        for item in chunk_items:
            chunk = Chunk(
                id=item.chunk_id,
                project_id=project.id,
                source_id=src.id,
                chunk_index=item.chunk_index,
                content=item.content,
                start_line=item.start_line,
                end_line=item.end_line,
                section_heading=item.section_heading,
                token_count=item.token_count,
                embedding_id=item.chunk_id
            )
            db.add(chunk)
            created_chunks += 1

            await index_chunk_fts(
                db,
                chunk_id=item.chunk_id,
                project_id=project.id,
                source_id=src.id,
                file_path=src.file_path,
                content=item.content
            )
            all_chunk_ids.append(item.chunk_id)
            all_chunk_texts.append(item.content)

    if all_chunk_texts:
        vectors = embedding_service.embed_batch(all_chunk_texts)
        vector_store.save_vectors(project.id, all_chunk_ids, vectors)

    project.chunk_count = created_chunks
    project.status = "ready"
    project.indexing_metadata = {
        "embedding_model": embedding_service.model_name,
        "dimension": embedding_service.dimension,
        "chunks_indexed": created_chunks,
        "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    await db.commit()

    for s in created_sources:
        await db.refresh(s)

    return created_sources

@router.get("/projects/{project_id}/profile", response_model=ProjectProfileResponse)
async def get_project_profile(
    project_id: str,
    snapshot_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the evidence-grounded project profile for a snapshot.
    If snapshot_id is not specified, uses the current active snapshot.
    """
    p_stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(p_stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    target_snapshot = snapshot_id or project.current_snapshot_id
    if not target_snapshot:
        raise HTTPException(status_code=404, detail="No source snapshot exists for this project")

    prof_stmt = select(ProjectProfile).where(
        ProjectProfile.project_id == project_id,
        ProjectProfile.snapshot_id == target_snapshot
    )
    profile = (await db.execute(prof_stmt)).scalar_one_or_none()

    if not profile:
        # Dynamically compute profile from snapshot sources if profile record is missing
        src_stmt = select(Source).where(Source.project_id == project_id, Source.snapshot_id == target_snapshot)
        sources = (await db.execute(src_stmt)).scalars().all()
        if not sources:
            src_stmt2 = select(Source).where(Source.project_id == project_id)
            sources = (await db.execute(src_stmt2)).scalars().all()

        storage_root = Path(project.storage_path) if project.storage_path else (settings.STORAGE_DIR / project_id)
        profile_data = project_profiler.analyze_snapshot(
            snapshot_id=target_snapshot,
            project_id=project_id,
            sources=sources,
            snapshot_dir=storage_root,
            user_context=project.user_context or {}
        )
        profile = await project_profiler.save_or_update_profile(db, project_id, target_snapshot, profile_data)

    return profile

@router.patch("/projects/{project_id}/context", response_model=ProjectProfileResponse)
async def update_project_user_context(
    project_id: str,
    payload: ProjectUserContextUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Allows user to optionally describe project purpose, deployment environment,
    sensitive data, intended users, and review goals.
    Keeps user-provided information separate from automatic detection.
    """
    p_stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(p_stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    ctx = dict(project.user_context or {})
    if payload.purpose is not None:
        ctx["purpose"] = payload.purpose
    if payload.deployment_env is not None:
        ctx["deployment_env"] = payload.deployment_env
    if payload.sensitive_data is not None:
        ctx["sensitive_data"] = payload.sensitive_data
    if payload.intended_users is not None:
        ctx["intended_users"] = payload.intended_users
    if payload.review_goals is not None:
        ctx["review_goals"] = payload.review_goals

    project.user_context = ctx
    await db.commit()

    # Update profile user context if active profile exists
    if project.current_snapshot_id:
        prof_stmt = select(ProjectProfile).where(
            ProjectProfile.project_id == project_id,
            ProjectProfile.snapshot_id == project.current_snapshot_id
        )
        profile = (await db.execute(prof_stmt)).scalar_one_or_none()
        if profile:
            profile.user_context = ctx
            await db.commit()
            await db.refresh(profile)
            return profile

    # Fallback to getting profile
    return await get_project_profile(project_id=project_id, db=db)

@router.get("/projects/{project_id}/architecture-graph")
async def get_project_architecture_graph(
    project_id: str,
    snapshot_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Returns the evidence-grounded architecture and dependency graph."""
    profile = await get_project_profile(project_id=project_id, snapshot_id=snapshot_id, db=db)
    return profile.architecture_graph

@router.delete("/projects/{project_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(project_id: str, source_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Source).where(Source.id == source_id, Source.project_id == project_id)
    res = await db.execute(stmt)
    source = res.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    storage_path = Path(source.storage_path)
    if storage_path.exists():
        storage_path.unlink(missing_ok=True)

    await db.delete(source)
    await db.commit()
    return None

@router.get("/sources/{source_id}/excerpt", response_model=SourceExcerptResponse)
async def get_source_excerpt(
    source_id: str,
    line_start: int = 1,
    line_end: int = 50,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Source).where(Source.id == source_id)
    res = await db.execute(stmt)
    source = res.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    storage_path = Path(source.storage_path)
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Storage file not found on disk")

    lines = storage_path.read_text(encoding="utf-8", errors="replace").splitlines()
    start_idx = max(0, line_start - 1)
    end_idx = min(len(lines), line_end)
    content = "\n".join(lines[start_idx:end_idx])

    return SourceExcerptResponse(
        source_id=source.id,
        file_path=source.file_path,
        line_start=start_idx + 1,
        line_end=end_idx,
        content=content
    )
