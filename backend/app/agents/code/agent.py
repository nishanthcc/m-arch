import json
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.schemas import FindingCreate
from app.prompts.registry import get_prompt_definition

class CodeTestingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="code_agent",
            name="Code & Testing Specialist"
        )
        self.prompt_def = get_prompt_definition("code_specialist_v1_2")

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

        # 1. MCP: Inspect sources & dependencies
        sources_res = await self.call_mcp_tool("list_project_sources", {"project_id": project_id}, session)
        tools_called.append({"tool": "list_project_sources", "timestamp": time.time()})
        sources = sources_res.get("result", [])

        manifests_res = await self.call_mcp_tool("get_dependency_manifest", {"project_id": project_id}, session)
        tools_called.append({"tool": "get_dependency_manifest", "timestamp": time.time()})
        manifests = manifests_res.get("result", [])

        test_inv_res = await self.call_mcp_tool("get_test_inventory", {"project_id": project_id}, session)
        tools_called.append({"tool": "get_test_inventory", "timestamp": time.time()})
        test_inventory = test_inv_res.get("result", {})

        # 2. MCP: Retrieve relevant code snippets
        code_search_res = await self.call_mcp_tool(
            "search_project_code",
            {"project_id": project_id, "query": f"{question} error handling testing architecture config", "top_k": 8},
            session
        )
        tools_called.append({"tool": "search_project_code", "timestamp": time.time()})
        retrieved_code = code_search_res.get("result", [])

        # Build context for LLM
        evidence_summary = []
        for c in retrieved_code:
            evidence_summary.append(
                f"File: {c.get('display_path')} (Lines {c.get('line_start')}-{c.get('line_end')}):\n{c.get('excerpt')}\n---"
            )

        manifest_summary = []
        for m in manifests:
            manifest_summary.append(f"Manifest: {m.get('file_path')}\n{m.get('content')[:1000]}\n---")

        system_prompt = self.prompt_def.format_system_prompt()

        user_prompt = f"""
Review Inquiries: {question}

Total Sources Available: {len(sources)}
Test Inventory: {json.dumps(test_inventory)}
Dependency Manifests Found: {len(manifests)}
{chr(10).join(manifest_summary)}

Retrieved Code Excerpts:
{chr(10).join(evidence_summary) if evidence_summary else "No code excerpts retrieved."}

STRICT EVIDENCE & SOURCING RULES:
1. Map every critique to a specific file path and exact line number from the retrieved evidence.
2. If you cannot cite a valid line number from the snapshot for a critique, you MUST discard that critique entirely.
3. Every finding must include an 'evidence' array citing real display_path, line_start, line_end, and excerpt.
4. Output strictly valid JSON with a 'findings' list.
"""

        model_resp = await self.query_model(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            override_mode=override_mode
        )

        findings: List[FindingCreate] = self.parse_findings_json(model_resp.content, retrieved_code)
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
            "summary": f"Analyzed {len(sources)} files and {len(retrieved_code)} code blocks. Produced {len(findings)} findings.",
            "test_inventory": test_inventory
        }
