import json
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.schemas import FindingCreate
from app.prompts.registry import get_prompt_definition

class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="security_agent",
            name="Security Specialist"
        )
        self.prompt_def = get_prompt_definition("security_specialist_v1_1")

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

        # 1. MCP: Retrieve security knowledge base
        sec_kb_res = await self.call_mcp_tool("search_security_knowledge", {"topic": "secrets injection CORS execution credentials"}, session)
        tools_called.append({"tool": "search_security_knowledge", "timestamp": time.time()})
        security_kb = sec_kb_res.get("result", [])

        # 2. MCP: Retrieve relevant source chunks for security patterns
        sec_code_res = await self.call_mcp_tool(
            "search_project_code",
            {"project_id": project_id, "query": "api_key secret password token credentials CORS execute auth sql env", "top_k": 10},
            session
        )
        tools_called.append({"tool": "search_project_code", "timestamp": time.time()})
        retrieved_code = sec_code_res.get("result", [])

        # 3. MCP: Retrieve config files
        docs_res = await self.call_mcp_tool(
            "search_project_documents",
            {"project_id": project_id, "query": ".env docker config settings authorization authentication", "top_k": 6},
            session
        )
        tools_called.append({"tool": "search_project_documents", "timestamp": time.time()})
        retrieved_docs = docs_res.get("result", [])

        all_evidence = retrieved_code + retrieved_docs

        evidence_snippets = []
        for e in all_evidence:
            evidence_snippets.append(
                f"Source: {e.get('display_path')} (Lines {e.get('line_start')}-{e.get('line_end')}):\n{e.get('excerpt')}\n---"
            )

        kb_snippets = []
        for kb in security_kb:
            kb_snippets.append(f"Standard: {kb.get('id')} - {kb.get('title')}\nGuidance: {kb.get('guidance')}\n---")

        system_prompt = self.prompt_def.format_system_prompt()

        user_prompt = f"""
Review Inquiry: {question}

Known Security Standards & Checklists:
{chr(10).join(kb_snippets)}

Retrieved Project Excerpts:
{chr(10).join(evidence_snippets) if evidence_snippets else "No suspicious code or config excerpts retrieved."}

Conduct a rigorous static security review. Verify whether credentials, SQL queries, or dangerous functions exist, and report actionable remediations.
"""

        model_resp = await self.query_model(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            override_mode=override_mode
        )

        findings: List[FindingCreate] = self.parse_findings_json(model_resp.content, all_evidence)
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
            "summary": f"Scanned project configuration and sources against {len(security_kb)} security standards. Produced {len(findings)} findings.",
        }
