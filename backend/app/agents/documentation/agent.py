import json
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.schemas import FindingCreate
from app.prompts.registry import get_prompt_definition

class DocumentationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="documentation_agent",
            name="Documentation & Deployment Specialist"
        )
        self.prompt_def = get_prompt_definition("documentation_specialist_v1_1")

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

        # 1. MCP: Retrieve project documents & markdown files
        docs_res = await self.call_mcp_tool(
            "search_project_documents",
            {"project_id": project_id, "query": "README install setup deployment docker architecture guide api", "top_k": 8},
            session
        )
        tools_called.append({"tool": "search_project_documents", "timestamp": time.time()})
        retrieved_docs = docs_res.get("result", [])

        # 2. MCP: List sources to check documentation coverage
        sources_res = await self.call_mcp_tool("list_project_sources", {"project_id": project_id}, session)
        tools_called.append({"tool": "list_project_sources", "timestamp": time.time()})
        sources = sources_res.get("result", [])

        doc_snippets = []
        for d in retrieved_docs:
            doc_snippets.append(
                f"Document: {d.get('display_path')} (Section: {d.get('section') or 'General'}, Lines {d.get('line_start')}-{d.get('line_end')}):\n{d.get('excerpt')}\n---"
            )

        system_prompt = self.prompt_def.format_system_prompt()

        user_prompt = f"""
Review Inquiry: {question}

Total Sources in Project: {len(sources)}

Retrieved Documentation & Operational Excerpts:
{chr(10).join(doc_snippets) if doc_snippets else "No documentation (README, deployment guides) found in project."}

Review whether deployment instructions, required environment variables, setup commands, and architecture overviews are adequately documented.
"""

        model_resp = await self.query_model(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            override_mode=override_mode
        )

        findings: List[FindingCreate] = self.parse_findings_json(model_resp.content, retrieved_docs)
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
            "summary": f"Reviewed documentation and operational guides across {len(retrieved_docs)} sections. Produced {len(findings)} findings.",
        }
