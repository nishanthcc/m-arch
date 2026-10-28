from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Source, Chunk, Review, Evidence, AgentTask
from app.services.retrieval.retriever import hybrid_retriever

# Versioned security knowledge collection
SECURITY_KNOWLEDGE_BASE = [
    {
        "id": "SEC-001",
        "title": "CWE-798: Use of Hard-coded Credentials",
        "category": "secrets",
        "severity": "critical",
        "patterns": ["api_key", "secret_key", "password", "bearer", "private_key"],
        "guidance": "Credentials, private keys, or API tokens must never be hard-coded into source files or committed to version control. Use environment variables or dedicated secret managers."
    },
    {
        "id": "SEC-002",
        "title": "CWE-89: Improper Neutralization of Special Elements used in an SQL Command (SQL Injection)",
        "category": "injection",
        "severity": "critical",
        "patterns": ["execute(", "cursor.execute", "f\"SELECT", "f'INSERT", "%s", "raw_query"],
        "guidance": "Ensure all SQL queries strictly use parameterized queries or an ORM with parameter binding. Avoid raw string interpolation in SQL statements."
    },
    {
        "id": "SEC-003",
        "title": "CWE-942: Permissive Cross-Origin Resource Sharing (CORS) Policy",
        "category": "network",
        "severity": "medium",
        "patterns": ["allow_origins=[\"*\"]", "Access-Control-Allow-Origin: *"],
        "guidance": "Wildcard origins in CORS headers allow arbitrary web origins to access private resources if credentials are exchanged. Restrict origins to trusted domains."
    },
    {
        "id": "SEC-004",
        "title": "CWE-94: Code Injection and Arbitrary Execution",
        "category": "code_execution",
        "severity": "critical",
        "patterns": ["eval(", "exec(", "subprocess.Popen(..., shell=True)"],
        "guidance": "Dynamic evaluation of user-supplied strings via eval or shell=True permits remote code execution. Validate and tokenize inputs or use explicit APIs."
    },
    {
        "id": "SEC-005",
        "title": "CWE-312: Cleartext Storage of Sensitive Information in Configuration Files",
        "category": "configuration",
        "severity": "high",
        "patterns": [".env", "docker-compose", "config.json"],
        "guidance": "Ensure local development secret files are included in .gitignore and template .env.example files contain blank placeholders only."
    }
]

async def list_project_sources(session: AsyncSession, project_id: str) -> List[Dict[str, Any]]:
    stmt = select(Source).where(Source.project_id == project_id).order_by(Source.file_path)
    res = await session.execute(stmt)
    sources = res.scalars().all()
    return [
        {
            "id": s.id,
            "file_path": s.file_path,
            "file_name": s.file_name,
            "file_type": s.file_type,
            "file_size": s.file_size,
            "line_count": s.line_count,
            "content_hash": s.content_hash,
        }
        for s in sources
    ]

async def search_project_code(
    session: AsyncSession, project_id: str, query: str, top_k: int = 10
) -> List[Dict[str, Any]]:
    evidence = await hybrid_retriever.retrieve(
        session, project_id=project_id, query=query, top_k=top_k, file_type_filter="code"
    )
    return [e.model_dump() for e in evidence]

async def search_project_documents(
    session: AsyncSession, project_id: str, query: str, top_k: int = 10
) -> List[Dict[str, Any]]:
    evidence = await hybrid_retriever.retrieve(
        session, project_id=project_id, query=query, top_k=top_k
    )
    # Return documents and config
    return [e.model_dump() for e in evidence if e.evidence_type != "code_snippet" or "md" in e.display_path or "json" in e.display_path]

async def get_source_excerpt(
    session: AsyncSession, project_id: str, source_id: str, line_start: int, line_end: int
) -> Dict[str, Any]:
    stmt = select(Source).where(
        (Source.id == source_id) | (Source.file_path == source_id),
        Source.project_id == project_id
    )
    res = await session.execute(stmt)
    source = res.scalar_one_or_none()
    if not source:
        return {"error": f"Source '{source_id}' not found in project snapshot."}

    storage_path = Path(source.storage_path)
    if not storage_path.exists():
        return {"error": "Source storage file missing"}

    lines = storage_path.read_text(encoding="utf-8", errors="replace").splitlines()
    start_idx = max(0, line_start - 1)
    end_idx = min(len(lines), line_end)
    excerpt_lines = lines[start_idx:end_idx]

    return {
        "source_id": source.id,
        "file_path": source.file_path,
        "line_start": start_idx + 1,
        "line_end": end_idx,
        "excerpt": "\n".join(excerpt_lines)
    }

async def get_dependency_manifest(session: AsyncSession, project_id: str) -> List[Dict[str, Any]]:
    manifest_names = ["package.json", "requirements.txt", "pyproject.toml", "cargo.toml", "go.mod", "pom.xml"]
    stmt = select(Source).where(Source.project_id == project_id)
    res = await session.execute(stmt)
    sources = res.scalars().all()

    manifests = []
    for s in sources:
        if s.file_name.lower() in manifest_names:
            storage_path = Path(s.storage_path)
            content = storage_path.read_text(encoding="utf-8", errors="replace") if storage_path.exists() else ""
            manifests.append({
                "source_id": s.id,
                "file_path": s.file_path,
                "file_name": s.file_name,
                "content": content[:2500]  # bounded excerpt
            })
    return manifests

async def get_test_inventory(session: AsyncSession, project_id: str) -> Dict[str, Any]:
    stmt = select(Source).where(Source.project_id == project_id)
    res = await session.execute(stmt)
    sources = res.scalars().all()

    test_files = []
    for s in sources:
        path_lower = s.file_path.lower()
        if "test" in path_lower or "spec" in path_lower:
            test_files.append({
                "source_id": s.id,
                "file_path": s.file_path,
                "line_count": s.line_count
            })

    return {
        "total_test_files": len(test_files),
        "test_files": test_files,
        "has_test_suite": len(test_files) > 0
    }

async def search_security_knowledge(topic: str, session: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
    if session:
        try:
            from app.services.knowledge.manager import knowledge_manager
            return await knowledge_manager.search_active_knowledge(session, topic)
        except Exception:
            pass
    topic_lower = topic.lower()
    matches = []
    for item in SECURITY_KNOWLEDGE_BASE:
        if topic_lower in item["title"].lower() or topic_lower in item["category"].lower() or any(p in topic_lower for p in item["patterns"]):
            matches.append(item)
    return matches if matches else SECURITY_KNOWLEDGE_BASE[:3]

async def get_review_evidence(session: AsyncSession, review_id: str) -> List[Dict[str, Any]]:
    stmt = select(Evidence).join(Review, Evidence.finding_id == Review.id)
    # Alternatively fetch via findings for this review
    from app.db.models import Finding
    stmt = select(Evidence).join(Finding, Evidence.finding_id == Finding.id).where(Finding.review_id == review_id)
    res = await session.execute(stmt)
    evidence_list = res.scalars().all()
    return [
        {
            "id": e.id,
            "display_path": e.display_path,
            "line_start": e.line_start,
            "line_end": e.line_end,
            "excerpt": e.excerpt,
            "evidence_type": e.evidence_type,
            "retrieval_method": e.retrieval_method
        }
        for e in evidence_list
    ]

async def get_agent_trace(session: AsyncSession, review_id: str, agent_id: str) -> Dict[str, Any]:
    stmt = select(AgentTask).where(AgentTask.review_id == review_id, AgentTask.agent_id == agent_id)
    res = await session.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        return {"error": "Trace not found"}
    return {
        "task_id": task.id,
        "agent_id": task.agent_id,
        "status": task.status,
        "provider_used": task.provider_used,
        "model_used": task.model_used,
        "execution_time_seconds": task.execution_time_seconds,
        "tools_called": task.tools_called,
        "error_message": task.error_message
    }
