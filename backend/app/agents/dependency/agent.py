import json
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.schemas import FindingCreate
from app.prompts.registry import get_prompt_definition

class DependencyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="dependency_agent",
            name="Dependency & Supply Chain Specialist"
        )
        self.prompt_def = get_prompt_definition("dependency_specialist_v1_1")

    async def execute_task(
        self,
        project_id: str,
        review_id: str,
        question: str,
        session: AsyncSession,
        override_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        tools_called = []

        # 1. MCP: List project sources to assess lockfile and SBOM presence
        sources_res = await self.call_mcp_tool("list_project_sources", {"project_id": project_id}, session)
        tools_called.append({"tool": "list_project_sources", "timestamp": time.time()})
        sources = sources_res.get("result", [])

        # 2. MCP: Extract dependency manifests
        manifests_res = await self.call_mcp_tool("get_dependency_manifest", {"project_id": project_id}, session)
        tools_called.append({"tool": "get_dependency_manifest", "timestamp": time.time()})
        manifests = manifests_res.get("result", [])

        # Check for lockfiles and SBOM declarations in file list
        lockfile_patterns = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock", "go.sum", "requirements.lock"]
        sbom_patterns = ["sbom", "bom.json", "bom.xml", "spdx", "cyclonedx"]

        found_lockfiles = [s["file_path"] for s in sources if any(p in s["file_name"].lower() for p in lockfile_patterns)]
        found_sboms = [s["file_path"] for s in sources if any(p in s["file_name"].lower() for p in sbom_patterns)]

        manifest_summary = []
        retrieved_evidence = []
        for m in manifests:
            content_snippet = m.get("content", "")[:1800]
            manifest_summary.append(f"Manifest: {m.get('file_path')}\n{content_snippet}\n---")
            retrieved_evidence.append({
                "source_id": m.get("source_id"),
                "display_path": m.get("file_path"),
                "line_start": 1,
                "line_end": min(60, len(content_snippet.splitlines())),
                "excerpt": content_snippet,
                "retrieval_method": "manifest_inspection",
                "score": 0.95
            })

        system_prompt = self.prompt_def.format_system_prompt()
        user_prompt = f"""
Review Inquiry: {question}

Total Sources Available: {len(sources)}
Dependency Manifests Found ({len(manifests)}):
{chr(10).join(manifest_summary) if manifest_summary else "No dependency manifests located."}

Lockfiles Detected: {json.dumps(found_lockfiles)}
SBOM Declarations Detected: {json.dumps(found_sboms)}

Evaluate dependency pin safety, lockfile integrity, licensing indicators, and supply chain posture. Ground every finding in specific lines from the manifest files.
"""

        model_resp = await self.query_model(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            override_mode=override_mode
        )

        findings: List[FindingCreate] = self.parse_findings_json(model_resp.content, retrieved_evidence)
        elapsed = time.time() - start_time

        return {
            "agent_id": self.agent_id,
            "status": "completed",
            "findings": [f.model_dump() for f in findings],
            "provider_used": model_resp.provider_name,
            "model_used": model_resp.model_name,
            "fallback_used": model_resp.fallback_used,
            "execution_time_seconds": round(elapsed, 3),
            "tools_called": tools_called,
            "prompt_id": self.prompt_def.prompt_id,
            "prompt_version": self.prompt_def.version,
            "prompt_hash": self.prompt_def.content_hash,
            "summary": f"Inspected {len(manifests)} dependency manifests. Identified {len(findings)} supply chain findings.",
            "lockfiles_present": len(found_lockfiles) > 0,
            "sbom_present": len(found_sboms) > 0
        }
