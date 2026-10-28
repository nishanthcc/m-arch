import hashlib
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.db.models import SecurityKnowledgeSource

logger = logging.getLogger(__name__)

BUNDLED_BASELINE_COLLECTIONS: List[Dict[str, Any]] = [
    {
        "id": "mitre_cwe_baseline_v2024",
        "name": "MITRE Common Weakness Enumeration (CWE) Baseline",
        "organization": "MITRE Corporation",
        "canonical_url": "https://cwe.mitre.org/data/definitions/1000.html",
        "version_date": "2024-06-25",
        "license": "MITRE CWE Terms of Use (Public Attribution)",
        "coverage_category": "Vulnerability Weaknesses & Injection Flaws",
        "source_type": "bundled_baseline",
        "agent_ids": ["security_agent", "code_agent"],
        "records": [
            {
                "id": "CWE-798",
                "title": "Use of Hard-coded Credentials",
                "category": "secrets",
                "severity": "critical",
                "patterns": ["api_key", "secret_key", "password", "bearer", "private_key", "token"],
                "guidance": "Credentials, private keys, or API tokens must never be hard-coded into source files or committed to version control. Use environment variables or dedicated secret managers."
            },
            {
                "id": "CWE-89",
                "title": "Improper Neutralization of Special Elements in SQL Command (SQL Injection)",
                "category": "injection",
                "severity": "critical",
                "patterns": ["execute(", "cursor.execute", "f\"SELECT", "f'INSERT", "%s", "raw_query"],
                "guidance": "Ensure all SQL queries strictly use parameterized queries or an ORM with parameter binding. Avoid raw string interpolation in SQL statements."
            },
            {
                "id": "CWE-94",
                "title": "Improper Control of Generation of Code (Code Injection)",
                "category": "code_execution",
                "severity": "critical",
                "patterns": ["eval(", "exec(", "subprocess.Popen(..., shell=True)"],
                "guidance": "Dynamic evaluation of user-supplied strings via eval or shell=True permits remote code execution. Validate and tokenize inputs or use explicit APIs."
            },
            {
                "id": "CWE-312",
                "title": "Cleartext Storage of Sensitive Information in Configuration Files",
                "category": "configuration",
                "severity": "high",
                "patterns": [".env", "docker-compose", "config.json"],
                "guidance": "Ensure local development secret files are included in .gitignore and template .env.example files contain blank placeholders only."
            }
        ]
    },
    {
        "id": "owasp_api_security_v2023",
        "name": "OWASP API Security Top 10 Standards",
        "organization": "Open Web Application Security Project (OWASP)",
        "canonical_url": "https://owasp.org/API-Security/editions/2023/en/0x11-t10/",
        "version_date": "2023-11-15",
        "license": "Creative Commons Attribution-ShareAlike 4.0",
        "coverage_category": "API Gateway, Transport & Access Control",
        "source_type": "bundled_baseline",
        "agent_ids": ["security_agent", "documentation_agent"],
        "records": [
            {
                "id": "API1:2023",
                "title": "Broken Object Level Authorization (BOLA)",
                "category": "authorization",
                "severity": "critical",
                "patterns": ["user_id", "req.params.id", "item_id"],
                "guidance": "Validate that the authenticated caller has explicit ownership or tenant permission before retrieving or mutating object IDs passed in endpoint parameters."
            },
            {
                "id": "API7:2023",
                "title": "Server Side Request Forgery (SSRF)",
                "category": "network",
                "severity": "high",
                "patterns": ["requests.get(url)", "fetch(url)", "http_client.get(target)"],
                "guidance": "Restrict outbound HTTP requests initiated from user-provided URLs to explicit allowlists; reject private IP ranges (127.0.0.1, 169.254.169.254, 10.0.0.0/8)."
            },
            {
                "id": "API8:2023",
                "title": "Security Misconfiguration & Permissive CORS",
                "category": "network",
                "severity": "medium",
                "patterns": ["allow_origins=[\"*\"]", "Access-Control-Allow-Origin: *"],
                "guidance": "Wildcard origins in CORS headers allow arbitrary web origins to access private resources if credentials are exchanged. Restrict origins to trusted domains."
            }
        ]
    }
]

def compute_collection_hash(data: Dict[str, Any]) -> str:
    content = f"{data.get('id')}:{data.get('version_date')}:{json.dumps(data.get('records', []), sort_keys=True)}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

class KnowledgeManager:
    async def seed_baseline_if_needed(self, session: AsyncSession) -> None:
        """Seed bundled baseline knowledge sources if not already present."""
        for coll in BUNDLED_BASELINE_COLLECTIONS:
            stmt = select(SecurityKnowledgeSource).where(SecurityKnowledgeSource.id == coll["id"])
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                h = compute_collection_hash(coll)
                rec = SecurityKnowledgeSource(
                    id=coll["id"],
                    name=coll["name"],
                    organization=coll["organization"],
                    canonical_url=coll["canonical_url"],
                    version_date=coll["version_date"],
                    license=coll.get("license"),
                    record_count=len(coll.get("records", [])),
                    coverage_category=coll["coverage_category"],
                    is_enabled=True,
                    source_type=coll["source_type"],
                    agent_ids=coll.get("agent_ids", ["security_agent"]),
                    records=coll.get("records", []),
                    version_hash=h
                )
                session.add(rec)
        await session.commit()

    async def list_collections(self, session: AsyncSession) -> List[SecurityKnowledgeSource]:
        await self.seed_baseline_if_needed(session)
        stmt = select(SecurityKnowledgeSource).order_by(SecurityKnowledgeSource.created_at.desc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def get_collection(self, session: AsyncSession, collection_id: str) -> Optional[SecurityKnowledgeSource]:
        stmt = select(SecurityKnowledgeSource).where(SecurityKnowledgeSource.id == collection_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    async def create_collection(
        self,
        session: AsyncSession,
        data: Dict[str, Any]
    ) -> SecurityKnowledgeSource:
        coll_id = data.get("id") or f"custom_{hashlib.sha256(data['name'].encode('utf-8')).hexdigest()[:12]}"
        records = data.get("records", [])
        h = compute_collection_hash({"id": coll_id, "version_date": data.get("version_date", "v1"), "records": records})

        new_source = SecurityKnowledgeSource(
            id=coll_id,
            name=data["name"],
            organization=data.get("organization", "User Custom"),
            canonical_url=data.get("canonical_url", "https://custom-standard.local"),
            version_date=data.get("version_date", "2026-10-27"),
            license=data.get("license", "Internal Proprietary"),
            record_count=len(records),
            coverage_category=data.get("coverage_category", "Custom Security Rules"),
            is_enabled=data.get("is_enabled", True),
            source_type="user_imported",
            agent_ids=data.get("agent_ids", ["security_agent"]),
            records=records,
            version_hash=h
        )
        session.add(new_source)
        await session.commit()
        await session.refresh(new_source)
        return new_source

    async def toggle_collection(
        self,
        session: AsyncSession,
        collection_id: str,
        is_enabled: bool
    ) -> Optional[SecurityKnowledgeSource]:
        stmt = select(SecurityKnowledgeSource).where(SecurityKnowledgeSource.id == collection_id)
        res = await session.execute(stmt)
        source = res.scalar_one_or_none()
        if not source:
            return None
        source.is_enabled = is_enabled
        await session.commit()
        await session.refresh(source)
        return source

    async def search_active_knowledge(
        self,
        session: AsyncSession,
        topic: str
    ) -> List[Dict[str, Any]]:
        """Searches across all currently enabled security knowledge collections."""
        await self.seed_baseline_if_needed(session)
        stmt = select(SecurityKnowledgeSource).where(SecurityKnowledgeSource.is_enabled == True)
        res = await session.execute(stmt)
        sources = res.scalars().all()

        topic_lower = topic.lower()
        matches = []

        for s in sources:
            for rec in s.records:
                patterns = [p.lower() for p in rec.get("patterns", [])]
                title = rec.get("title", "").lower()
                cat = rec.get("category", "").lower()
                guidance = rec.get("guidance", "").lower()

                if (
                    topic_lower in title
                    or topic_lower in cat
                    or any(p in topic_lower for p in patterns)
                    or any(kw in guidance for kw in topic_lower.split())
                ):
                    matches.append({
                        **rec,
                        "collection_id": s.id,
                        "collection_name": s.name,
                        "collection_version": s.version_date,
                        "source_type": s.source_type
                    })

        return matches if matches else [
            {
                "id": "CWE-798",
                "title": "Use of Hard-coded Credentials",
                "category": "secrets",
                "severity": "critical",
                "guidance": "Credentials, private keys, or API tokens must never be hard-coded into source files.",
                "collection_id": "mitre_cwe_baseline_v2024",
                "collection_name": "MITRE Common Weakness Enumeration (CWE) Baseline",
                "source_type": "bundled_baseline"
            }
        ]

knowledge_manager = KnowledgeManager()
