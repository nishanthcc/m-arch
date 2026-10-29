import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.providers import model_router, ProviderMessage, ProviderResponse
from app.mcp import execute_mcp_tool
from app.schemas import FindingCreate, EvidenceItem

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name

    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Call permitted MCP tool with validation."""
        return await execute_mcp_tool(self.agent_id, tool_name, arguments, session)

    async def query_model(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = True,
        override_mode: Optional[str] = None,
        override_model: Optional[str] = None
    ) -> ProviderResponse:
        """Route model request via ModelRouter."""
        messages = [ProviderMessage(role="user", content=user_prompt)]
        return await model_router.route_chat(
            messages=messages,
            system_prompt=system_prompt,
            json_mode=json_mode,
            temperature=0.1,
            agent_role=self.agent_id,
            override_mode=override_mode,
            override_model=override_model
        )

    def parse_findings_json(
        self,
        json_content: str,
        retrieved_evidence: List[Dict[str, Any]]
    ) -> List[FindingCreate]:
        """
        Parses and validates structured JSON finding objects from model output.
        Ensures evidence items are grounded and verification statuses are valid.
        """
        try:
            # Extract JSON block if surrounded by markdown code fences
            cleaned = json_content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned.strip())
        except Exception as exc:
            logger.warning(f"Failed to parse model JSON: {exc}. Raw: {json_content[:200]}")
            return []

        findings_list = data.get("findings", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        valid_findings: List[FindingCreate] = []

        # Index available retrieved evidence by display_path or chunk
        evidence_pool = {e.get("display_path", ""): e for e in retrieved_evidence}

        for item in findings_list:
            try:
                # Map referenced evidence
                ref_evidence_items: List[EvidenceItem] = []
                for ev in item.get("evidence", []):
                    ref_path = ev.get("display_path", "")
                    matching_pool_item = evidence_pool.get(ref_path)

                    ref_evidence_items.append(
                        EvidenceItem(
                            source_id=ev.get("source_id") or (matching_pool_item.get("source_id") if matching_pool_item else "unknown"),
                            display_path=ref_path,
                            line_start=ev.get("line_start"),
                            line_end=ev.get("line_end"),
                            section=ev.get("section"),
                            excerpt=ev.get("excerpt", "")[:1000],
                            evidence_type=ev.get("evidence_type", "code_snippet"),
                            retrieval_method=matching_pool_item.get("retrieval_method", "hybrid") if matching_pool_item else "static_rule",
                            score=matching_pool_item.get("score") if matching_pool_item else 0.85
                        )
                    )

                # Discard critiques without any valid supporting evidence or cited paths
                if not ref_evidence_items:
                    logger.info(f"Discarding critique '{item.get('title')}' - no cited line or file evidence.")
                    continue

                finding = FindingCreate(
                    agent_id=self.agent_id,
                    title=item.get("title", "Untitled Observation"),
                    explanation=item.get("explanation", ""),
                    severity=item.get("severity", "medium").lower(),
                    category=item.get("category", "General"),
                    impact=item.get("impact", "Impact requires inspection."),
                    remediation=item.get("remediation", "Review cited lines."),
                    confidence=float(item.get("confidence", 0.8)),
                    confidence_interpretation=item.get("confidence_interpretation", "Derived from static code evidence"),
                    verification_status=item.get("verification_status", "static_analysis"),
                    limitations=item.get("limitations", "Static analysis only. Runtime behavior not executed."),
                    manual_review_required=bool(item.get("manual_review_required", False)),
                    evidence_items=ref_evidence_items
                )
                valid_findings.append(finding)
            except Exception as e:
                logger.warning(f"Skipping malformed finding: {e}")

        return valid_findings

    @abstractmethod
    async def execute_task(
        self,
        project_id: str,
        review_id: str,
        question: str,
        session: AsyncSession,
        override_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute agent analysis and return structured result payload."""
        pass
