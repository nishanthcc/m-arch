import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db, async_session_maker
from app.db.models import Project, Source, Chunk
from app.services.ingestion.chunker import chunk_text
from app.services.embeddings.local_embeddings import embedding_service
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.fts_index import index_chunk_fts, delete_project_fts

router = APIRouter()

async def process_project_indexing(project_id: str):
    async with async_session_maker() as session:
        stmt = select(Project).where(Project.id == project_id)
        res = await session.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            return

        project.status = "indexing"
        await session.commit()

        start_time = time.time()
        # Fetch sources
        s_stmt = select(Source).where(Source.project_id == project_id)
        s_res = await session.execute(s_stmt)
        sources = s_res.scalars().all()

        # Clean existing FTS
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

                # Index SQLite FTS5
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

        # Compute & persist dense vector embeddings locally
        if all_chunk_texts:
            vectors = embedding_service.embed_batch(all_chunk_texts)
            vector_store.save_vectors(project_id, all_chunk_ids, vectors)

        elapsed = time.time() - start_time
        project.chunk_count = created_chunks
        project.status = "ready"
        project.indexing_metadata = {
            "embedding_model": embedding_service.model_name,
            "dimension": embedding_service.dimension,
            "chunks_indexed": created_chunks,
            "elapsed_seconds": round(elapsed, 2),
            "indexed_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        await session.commit()

@router.post("/projects/{project_id}/index")
async def trigger_indexing(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = "indexing"
    await db.commit()

    background_tasks.add_task(process_project_indexing, project_id)
    return {"message": "Indexing started in background", "project_id": project_id, "status": "indexing"}

@router.get("/projects/{project_id}/index/status")
async def get_indexing_status(project_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project.id,
        "status": project.status,
        "source_count": project.source_count,
        "chunk_count": project.chunk_count,
        "metadata": project.indexing_metadata or {}
    }
