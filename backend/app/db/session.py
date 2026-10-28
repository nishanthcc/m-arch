from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
from app.core.config import settings
from app.db.base import Base

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    # Import all models to ensure they are registered with Base.metadata
    import app.db.models  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Create SQLite FTS5 table for full-text search if using sqlite
        if "sqlite" in settings.DATABASE_URL:
            await conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS chunk_fts USING fts5(
                    chunk_id UNINDEXED,
                    project_id UNINDEXED,
                    source_id UNINDEXED,
                    file_path,
                    content,
                    tokenize='porter unicode61'
                );
            """))

            # Automatic SQLite column migrations for v1.1.0
            migrations = [
                ("projects", "current_snapshot_id", "VARCHAR(36)"),
                ("projects", "repo_url", "VARCHAR(512)"),
                ("projects", "current_commit_sha", "VARCHAR(64)"),
                ("sources", "snapshot_id", "VARCHAR(36)"),
                ("reviews", "source_snapshot_id", "VARCHAR(36)"),
                ("reviews", "commit_sha", "VARCHAR(64)"),
                ("reviews", "evidence_verification_summary", "JSON"),
                ("agent_tasks", "prompt_id", "VARCHAR(100)"),
                ("agent_tasks", "prompt_version", "VARCHAR(20)"),
                ("agent_tasks", "prompt_hash", "VARCHAR(64)"),
            ]
            for tbl, col, col_type in migrations:
                try:
                    await conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};"))
                except Exception:
                    pass  # Column already exists

