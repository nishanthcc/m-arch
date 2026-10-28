import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import init_db, async_session_maker
from app.db.models import Project, Source, Chunk
from app.services.ingestion.extractor import extract_file_content, detect_file_type
from app.services.ingestion.chunker import chunk_text
from app.services.ingestion.github_importer import github_importer
from app.services.embeddings.local_embeddings import embedding_service
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.fts_index import index_chunk_fts, search_fts
from app.services.retrieval.retriever import hybrid_retriever
from app.mcp import mcp_server, execute_mcp_tool
from app.a2a import get_official_agent_card, create_a2a_task, complete_a2a_task
from app.providers import model_router
from app.prompts.registry import get_prompt_definition
from app.agents import DependencyAgent, EvidenceVerifierAgent
from app.services.knowledge.manager import knowledge_manager

async def run_pipeline_test():
    print("=== 1. Initializing Database & Tables ===")
    await init_db()
    print("Database, SQLite FTS5 table, and v1.1.0 snapshot tables verified.")

    print("\n=== 2. Testing GitHub URL Validator (v1.1.0 Security) ===")
    owner, repo = github_importer.validate_github_url("https://github.com/google/gemma-cookbook")
    assert owner == "google" and repo == "gemma-cookbook", f"Failed parsing: {owner}/{repo}"
    print(f"Accepted valid public GitHub URL: {owner}/{repo}")

    owner_git, repo_git = github_importer.validate_github_url("https://github.com/octocat/Hello-World.git")
    assert owner_git == "octocat" and repo_git == "Hello-World"
    print(f"Accepted valid .git URL: {owner_git}/{repo_git}")

    # Validate strict rejection of dangerous or non-GitHub URLs
    invalid_urls = [
        "git@github.com:owner/repo.git",
        "file:///etc/passwd",
        "https://evil.com/owner/repo",
        "https://github.com/owner/repo?cmd=rm+-rf",
        "https://user:password@github.com/owner/repo"
    ]
    for inv in invalid_urls:
        try:
            github_importer.validate_github_url(inv)
            raise AssertionError(f"Expected failure for {inv} but passed!")
        except ValueError:
            pass
    print("Strictly rejected all SSH, file://, query-param, custom-host, and embedded credential URLs.")

    print("\n=== 3. Testing Versioned Prompt Registry (v1.1.0) ===")
    prompts_to_check = [
        "orchestrator_synthesis_v1_1",
        "code_specialist_v1_1",
        "security_specialist_v1_1",
        "documentation_specialist_v1_1",
        "dependency_specialist_v1_1",
        "evidence_verifier_v1_1"
    ]
    for pid in prompts_to_check:
        pdef = get_prompt_definition(pid)
        assert pdef.version == "1.1.0", f"Unexpected version for {pid}: {pdef.version}"
        assert len(pdef.content_hash) == 64, f"Invalid SHA-256 hash for {pid}"
        print(f"Loaded prompt {pdef.prompt_id} (v{pdef.version}) [Hash: {pdef.content_hash[:10]}...]")

    async with async_session_maker() as session:
        # Create a test project
        print("\n=== 4. Creating Test Project with Snapshot Tracking ===")
        project = Project(
            name="Test Microservice v1.1.0",
            description="Sample project to verify M-ARCH end-to-end ingestion, RAG, and quality gates",
            repo_url="https://github.com/example/auth-service"
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        print(f"Created project: {project.id} ({project.name})")

        # Ingest a sample source file
        print("\n=== 5. Ingesting Source Code & Config ===")
        sample_code = """
import os
import sqlite3

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")
# Potential security risk: Hardcoded token
API_SECRET_KEY = "test_secret_token_1234567890"

def get_user(user_id):
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    # SQL query vulnerable to injection
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    return cursor.fetchone()
"""
        sample_file = Path(project.storage_path or f"./data/storage/{project.id}") / "auth.py"
        sample_file.parent.mkdir(parents=True, exist_ok=True)
        sample_file.write_text(sample_code, encoding="utf-8")

        content, sha256, lines = extract_file_content(sample_file)
        source = Source(
            project_id=project.id,
            file_path="auth.py",
            file_name="auth.py",
            file_type="code",
            file_size=len(sample_code),
            content_hash=sha256,
            line_count=lines,
            storage_path=str(sample_file)
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)
        print(f"Ingested source: {source.file_path} (lines: {source.line_count}, hash: {source.content_hash[:10]}...)")

        # Chunk and Index
        print("\n=== 6. Chunking, Vector Embedding & SQLite FTS5 Indexing ===")
        chunks = chunk_text(source.id, content, source.file_type)
        chunk_ids = []
        chunk_texts = []
        for chk in chunks:
            db_chunk = Chunk(
                id=chk.chunk_id,
                project_id=project.id,
                source_id=source.id,
                chunk_index=chk.chunk_index,
                content=chk.content,
                start_line=chk.start_line,
                end_line=chk.end_line
            )
            session.add(db_chunk)
            await index_chunk_fts(session, chk.chunk_id, project.id, source.id, source.file_path, chk.content)
            chunk_ids.append(chk.chunk_id)
            chunk_texts.append(chk.content)

        await session.commit()
        vectors = embedding_service.embed_batch(chunk_texts)
        vector_store.save_vectors(project.id, chunk_ids, vectors)
        print(f"Indexed {len(chunks)} chunks into vector store and SQLite FTS5 table.")

        # Hybrid Retrieval
        print("\n=== 7. Testing Hybrid RAG Retrieval (Dense + FTS5 + RRF) ===")
        evidence = await hybrid_retriever.retrieve(
            session, project_id=project.id, query="SQL injection database query cursor", top_k=3
        )
        print(f"Retrieved {len(evidence)} evidence candidates:")
        for ev in evidence:
            print(f" - [{ev.retrieval_method}] {ev.display_path} (L{ev.line_start}-{ev.line_end}) Score={ev.score}")

        # Testing Evidence Verifier Quality Gate
        print("\n=== 8. Testing Evidence & Citation Verifier Quality Gate ===")
        verifier = EvidenceVerifierAgent()
        candidate_findings = [
            {
                "agent_id": "security_agent",
                "title": "SQL Injection in get_user",
                "explanation": "Query uses raw string concatenation with user_id parameter.",
                "severity": "critical",
                "verification_status": "runtime_confirmed",  # Should be downgraded to static_analysis
                "evidence_items": [
                    {
                        "source_id": source.id,
                        "display_path": "auth.py",
                        "line_start": 12,
                        "line_end": 14,
                        "excerpt": "query = 'SELECT * FROM users WHERE id = ' + str(user_id)"
                    }
                ]
            },
            {
                "agent_id": "security_agent",
                "title": "Fabricated Remote Buffer Overflow",
                "explanation": "No excerpt provided for this hallucinated issue.",
                "severity": "critical",
                "verification_status": "inference",
                "evidence_items": []  # Should be rejected by quality gate!
            }
        ]

        verification_result = await verifier.verify_findings(
            candidate_findings=candidate_findings,
            question="Is this project secure?",
            session=session
        )
        assert len(verification_result["verified_findings"]) == 1, "Expected exactly 1 verified finding"
        assert len(verification_result["rejected_findings"]) == 1, "Expected 1 rejected finding"
        assert verification_result["verified_findings"][0]["verification_status"] == "static_analysis"
        print(f"Verifier gate succeeded: {len(verification_result['verified_findings'])} verified, {len(verification_result['rejected_findings'])} ungrounded claims rejected.")

        # Testing Versioned Security Knowledge Collection
        print("\n=== 9. Testing Security Knowledge Manager (v1.1.0) ===")
        collections = await knowledge_manager.list_collections(session)
        print(f"Total knowledge collections seeded: {len(collections)}")
        for c in collections:
            print(f" - {c.name} ({c.organization}, {c.version_date}) [{c.record_count} records]")

        # Testing Clean Purge
        print("\n=== 10. Purging Test Artifacts ===")
        vector_store.delete_project_vectors(project.id)
        from app.services.retrieval.fts_index import delete_project_fts
        await delete_project_fts(session, project.id)
        await session.delete(project)
        await session.commit()
        if sample_file.exists():
            sample_file.unlink(missing_ok=True)
        if sample_file.parent.exists():
            import shutil
            shutil.rmtree(sample_file.parent, ignore_errors=True)
        print("Test project purged cleanly.")

    print("\nALL M-ARCH v1.1.0 SYSTEM TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_pipeline_test())
