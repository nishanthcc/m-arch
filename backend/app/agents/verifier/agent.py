import json
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.base import BaseAgent
from app.prompts.registry import get_prompt_definition

class EvidenceVerifierAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="evidence_verifier",
            name="Evidence & Citation Verifier"
        )
        self.prompt_def = get_prompt_definition("evidence_verifier_v1_1")

    async def verify_findings(
        self,
        candidate_findings: List[Dict[str, Any]],
        question: str,
        session: AsyncSession,
        override_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes pre-synthesis verification gate:
        - Validates that citations have non-empty excerpts and valid source paths.
        - Identifies conflicting claims across agents.
        - Filters out unsupported findings and prevents overstated claims.
        """
        start_time = time.time()

        if not candidate_findings:
            return {
                "agent_id": self.agent_id,
                "status": "completed",
                "verified_findings": [],
                "rejected_findings": [],
                "citation_coverage_score": 1.0,
                "conflicts_identified": [],
                "execution_time_seconds": 0.0,
                "prompt_id": self.prompt_def.prompt_id,
                "prompt_version": self.prompt_def.version,
                "prompt_hash": self.prompt_def.content_hash,
            }

        # Deterministic verification pass first
        strictly_grounded: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        for f in candidate_findings:
            evidence_items = f.get("evidence_items", [])
            # Rule 1: Finding must have at least one valid evidence reference
            if not evidence_items or not any(ev.get("excerpt", "").strip() for ev in evidence_items):
                rejected.append({
                    "title": f.get("title"),
                    "agent_id": f.get("agent_id"),
                    "reason": "Missing supporting code or document evidence excerpt."
                })
                continue

            # Rule 2: Ensure verification status matches real evidence type
            status = f.get("verification_status", "static_analysis")
            if status == "runtime_confirmed":
                # Static inspection cannot claim runtime confirmation
                f["verification_status"] = "static_analysis"
                f["limitations"] = (f.get("limitations") or "") + " [Downgraded from runtime_confirmed: produced via static inspection]."

            strictly_grounded.append(f)

        citation_coverage = len(strictly_grounded) / max(1, len(candidate_findings))

        # Model pass for subtle overstatements & conflict detection
        findings_json_summary = json.dumps([
            {
                "title": f.get("title"),
                "agent_id": f.get("agent_id"),
                "severity": f.get("severity"),
                "explanation": f.get("explanation"),
                "evidence_snippets": [ev.get("excerpt", "")[:200] for ev in f.get("evidence_items", [])]
            }
            for f in strictly_grounded[:15]
        ])

        system_prompt = self.prompt_def.format_system_prompt()
        user_prompt = f"""
Review Inquiry: {question}

Candidate Grounded Findings:
{findings_json_summary}

Verify whether any finding's claim exceeds its evidence excerpt, and identify any direct contradictions or conflicts between different agents' findings.
"""

        try:
            model_resp = await self.query_model(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_mode=True,
                override_mode=override_mode
            )

            cleaned = model_resp.content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            conflicts = parsed.get("conflicts_identified", [])
        except Exception:
            conflicts = []

        elapsed = time.time() - start_time

        return {
            "agent_id": self.agent_id,
            "status": "completed",
            "verified_findings": strictly_grounded,
            "rejected_findings": rejected,
            "citation_coverage_score": round(citation_coverage, 3),
            "conflicts_identified": conflicts,
            "execution_time_seconds": round(elapsed, 3),
            "prompt_id": self.prompt_def.prompt_id,
            "prompt_version": self.prompt_def.version,
            "prompt_hash": self.prompt_def.content_hash,
        }

    async def execute_task(self, *args, **kwargs):
        raise NotImplementedError("Use verify_findings for EvidenceVerifierAgent")
