from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def index_chunk_fts(
    session: AsyncSession, chunk_id: str, project_id: str, source_id: str, file_path: str, content: str
):
    """Index or update chunk content in SQLite FTS5 virtual table."""
    await session.execute(
        text("""
            INSERT OR REPLACE INTO chunk_fts (chunk_id, project_id, source_id, file_path, content)
            VALUES (:chunk_id, :project_id, :source_id, :file_path, :content)
        """),
        {
            "chunk_id": chunk_id,
            "project_id": project_id,
            "source_id": source_id,
            "file_path": file_path,
            "content": content,
        }
    )

async def search_fts(
    session: AsyncSession, project_id: str, query: str, limit: int = 15
) -> List[Tuple[str, float]]:
    """
    Search SQLite FTS5 table using BM25 ranking.
    Returns: [(chunk_id, score)]
    """
    # Clean query to avoid syntax errors in SQLite FTS5
    safe_terms = [t for t in query.replace('"', '').replace("'", "").split() if len(t) > 1]
    if not safe_terms:
        return []

    fts_query = " OR ".join(safe_terms[:8])
    try:
        result = await session.execute(
            text("""
                SELECT chunk_id, rank
                FROM chunk_fts
                WHERE chunk_fts MATCH :query AND project_id = :project_id
                ORDER BY rank
                LIMIT :limit
            """),
            {"query": fts_query, "project_id": project_id, "limit": limit}
        )
        rows = result.fetchall()
        # In FTS5, lower rank is better (more negative/closer to 0)
        # We normalize to positive score
        return [(r[0], abs(float(r[1]))) for r in rows]
    except Exception:
        return []

async def delete_project_fts(session: AsyncSession, project_id: str):
    await session.execute(
        text("DELETE FROM chunk_fts WHERE project_id = :project_id"),
        {"project_id": project_id}
    )
