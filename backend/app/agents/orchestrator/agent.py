import time
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.agents.base import BaseAgent
from app.agents.code.agent import CodeTestingAgent
from app.agents.security.agent import SecurityAgent
from app.agents.documentation.agent import DocumentationAgent
from app.agents.dependency.agent import DependencyAgent
from app.agents.verifier.agent import EvidenceVerifierAgent
from app.prompts.registry import get_prompt_definition
from app.a2a import create_a2a_task, complete_a2a_task, fail_a2a_task
from app.core.events import event_bus, ReviewEvent
from app.db.models import Review, Project, AgentTask, Finding, Evidence

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="orchestrator",
            name="M-ARCH Orchestrator"
        )
        self.code_agent = CodeTestingAgent()
        self.security_agent = SecurityAgent()
        self.documentation_agent = DocumentationAgent()
        self.dependency_agent = DependencyAgent()
        self.verifier_agent = EvidenceVerifierAgent()
        self.synthesis_prompt_def = get_prompt_definition("orchestrator_synthesis_v1_1")

    async def run_review(
        self,
        review_id: str,
        project_id: str,
        question: str,
        scope: str,
        session: AsyncSession,
        selected_agents: Optional[List[str]] = None,
        override_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coordinates full A2A multi-agent review with pre-synthesis verification gate and real-time SSE updates.
        """
        start_time = time.time()
        logger.info(f"Starting review {review_id} for project {project_id}")

        # Fetch review and project
        review_stmt = select(Review).where(Review.id == review_id)
        res = await session.execute(review_stmt)
        review = res.scalar_one_or_none()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        project_stmt = select(Project).where(Project.id == project_id)
        proj_res = await session.execute(project_stmt)
        project = proj_res.scalar_one_or_none()

        review.status = "running"
        if project:
            review.source_snapshot_id = project.current_snapshot_id
            review.commit_sha = project.current_commit_sha

        await session.commit()

        await event_bus.publish(
            ReviewEvent(
                review_id=review_id,
                event_type="review_started",
                agent_id=self.agent_id,
                timestamp=datetime.utcnow().isoformat(),
                message="Review started. Initializing A2A agent coordination with Prompt Registry v1.1.0.",
                data={
                    "scope": scope,
                    "question": question,
                    "snapshot_id": review.source_snapshot_id,
                    "commit_sha": review.commit_sha
                }
            )
        )

        # 1. Determine active specialists
        active_agents = []
        if selected_agents:
            if "code_agent" in selected_agents:
                active_agents.append(self.code_agent)
            if "security_agent" in selected_agents:
                active_agents.append(self.security_agent)
            if "documentation_agent" in selected_agents:
                active_agents.append(self.documentation_agent)
            if "dependency_agent" in selected_agents:
                active_agents.append(self.dependency_agent)
        else:
            if scope in ("full", "code_only"):
                active_agents.append(self.code_agent)
            if scope in ("full", "security_only"):
                active_agents.append(self.security_agent)
            if scope in ("full", "architecture", "docs_only"):
                active_agents.append(self.documentation_agent)
            if scope in ("full", "dependencies", "security_only", "code_only"):
                active_agents.append(self.dependency_agent)

        all_findings_raw: List[Dict[str, Any]] = []
        agent_traces: List[Dict[str, Any]] = []
        partial_failure = False

        # 2. Execute A2A Specialist Tasks
        for idx, agent in enumerate(active_agents):
            if idx > 0:
                await asyncio.sleep(2.0)
            task_id = f"task_{review_id}_{agent.agent_id}"
            a2a_task = create_a2a_task(
                task_id=task_id,
                context_id=review_id,
                instruction=f"Perform specialist review on project {project_id} addressing: {question}",
                metadata={"agent_id": agent.agent_id, "project_id": project_id}
            )

            # Record task in DB
            db_task = AgentTask(
                id=task_id,
                review_id=review_id,
                agent_id=agent.agent_id,
                task_name=f"{agent.name} Evaluation",
                status="running",
                input_params={"question": question, "scope": scope}
            )
            session.add(db_task)
            await session.commit()

            await event_bus.publish(
                ReviewEvent(
                    review_id=review_id,
                    event_type="task_started",
                    agent_id=agent.agent_id,
                    timestamp=datetime.utcnow().isoformat(),
                    message=f"{agent.name} began analysis.",
                    data={"task_id": task_id}
                )
            )

            try:
                agent_result = await agent.execute_task(
                    project_id=project_id,
                    review_id=review_id,
                    question=question,
                    session=session,
                    override_mode=override_mode
                )

                # Attach A2A Artifact
                complete_a2a_task(
                    a2a_task,
                    artifact_id=f"art_{task_id}",
                    name=f"{agent.agent_id}_findings",
                    payload=agent_result
                )

                db_task.status = "completed"
                db_task.provider_used = agent_result.get("provider_used")
                db_task.model_used = agent_result.get("model_used")
                db_task.execution_time_seconds = agent_result.get("execution_time_seconds", 0.0)
                db_task.tools_called = agent_result.get("tools_called", [])
                db_task.output_artifact = agent_result
                db_task.prompt_id = agent_result.get("prompt_id")
                db_task.prompt_version = agent_result.get("prompt_version")
                db_task.prompt_hash = agent_result.get("prompt_hash")
                await session.commit()

                # Collect raw findings
                agent_findings = agent_result.get("findings", [])
                all_findings_raw.extend(agent_findings)
                agent_traces.append(agent_result)

                await event_bus.publish(
                    ReviewEvent(
                        review_id=review_id,
                        event_type="task_completed",
                        agent_id=agent.agent_id,
                        timestamp=datetime.utcnow().isoformat(),
                        message=f"{agent.name} completed with {len(agent_findings)} findings.",
                        data={
                            "findings_count": len(agent_findings),
                            "execution_time": agent_result.get("execution_time_seconds"),
                            "prompt_version": agent_result.get("prompt_version")
                        }
                    )
                )

            except Exception as exc:
                logger.error(f"Agent {agent.agent_id} failed: {exc}")
                partial_failure = True
                fail_a2a_task(a2a_task, str(exc))
                db_task.status = "failed"
                db_task.error_message = str(exc)
                await session.commit()

                await event_bus.publish(
                    ReviewEvent(
                        review_id=review_id,
                        event_type="task_failed",
                        agent_id=agent.agent_id,
                        timestamp=datetime.utcnow().isoformat(),
                        message=f"{agent.name} encountered an error: {str(exc)}",
                        data={"error": str(exc)}
                    )
                )

        # 3. Evidence and Citation Verifier Quality Gate
        await event_bus.publish(
            ReviewEvent(
                review_id=review_id,
                event_type="verification_started",
                agent_id=self.verifier_agent.agent_id,
                timestamp=datetime.utcnow().isoformat(),
                message="Evidence Verifier quality gate inspecting candidate findings against source excerpts.",
                data={"candidate_findings_count": len(all_findings_raw)}
            )
        )

        verifier_task_id = f"task_{review_id}_evidence_verifier"
        verifier_task = AgentTask(
            id=verifier_task_id,
            review_id=review_id,
            agent_id=self.verifier_agent.agent_id,
            task_name="Evidence & Citation Quality Gate",
            status="running",
            input_params={"candidate_findings_count": len(all_findings_raw)}
        )
        session.add(verifier_task)
        await session.commit()

        verifier_res = await self.verifier_agent.verify_findings(
            candidate_findings=all_findings_raw,
            question=question,
            session=session,
            override_mode=override_mode
        )

        verified_findings = verifier_res.get("verified_findings", [])
        rejected_findings = verifier_res.get("rejected_findings", [])

        verifier_task.status = "completed"
        verifier_task.provider_used = verifier_res.get("provider_used")
        verifier_task.model_used = verifier_res.get("model_used")
        verifier_task.execution_time_seconds = verifier_res.get("execution_time_seconds", 0.0)
        verifier_task.output_artifact = verifier_res
        verifier_task.prompt_id = verifier_res.get("prompt_id")
        verifier_task.prompt_version = verifier_res.get("prompt_version")
        verifier_task.prompt_hash = verifier_res.get("prompt_hash")
        await session.commit()

        review.evidence_verification_summary = {
            "verified_count": len(verified_findings),
            "rejected_count": len(rejected_findings),
            "citation_coverage_score": verifier_res.get("citation_coverage_score", 1.0),
            "conflicts_identified": verifier_res.get("conflicts_identified", []),
            "prompt_version": verifier_res.get("prompt_version")
        }
        await session.commit()

        await event_bus.publish(
            ReviewEvent(
                review_id=review_id,
                event_type="verification_completed",
                agent_id=self.verifier_agent.agent_id,
                timestamp=datetime.utcnow().isoformat(),
                message=f"Evidence verification complete: {len(verified_findings)} verified, {len(rejected_findings)} filtered for insufficient citation.",
                data=review.evidence_verification_summary
            )
        )

        # 4. Save only grounded & verified findings to DB
        for f_data in verified_findings:
            db_finding = Finding(
                review_id=review_id,
                project_id=project_id,
                agent_id=f_data.get("agent_id", "specialist"),
                title=f_data.get("title", ""),
                explanation=f_data.get("explanation", ""),
                severity=f_data.get("severity", "medium"),
                category=f_data.get("category", "General"),
                impact=f_data.get("impact", ""),
                remediation=f_data.get("remediation", ""),
                confidence=f_data.get("confidence", 0.8),
                confidence_interpretation=f_data.get("confidence_interpretation", ""),
                verification_status=f_data.get("verification_status", "static_analysis"),
                limitations=f_data.get("limitations"),
                manual_review_required=f_data.get("manual_review_required", False)
            )
            session.add(db_finding)
            await session.flush()

            for ev in f_data.get("evidence_items", []):
                db_evidence = Evidence(
                    finding_id=db_finding.id,
                    source_id=ev.get("source_id", "unknown"),
                    display_path=ev.get("display_path", ""),
                    line_start=ev.get("line_start"),
                    line_end=ev.get("line_end"),
                    section=ev.get("section"),
                    excerpt=ev.get("excerpt", ""),
                    evidence_type=ev.get("evidence_type", "code_snippet"),
                    retrieval_method=ev.get("retrieval_method", "hybrid"),
                    score=ev.get("score")
                )
                session.add(db_evidence)

        await session.commit()

        # 5. Orchestrator Synthesis & Conflict Resolution
        await event_bus.publish(
            ReviewEvent(
                review_id=review_id,
                event_type="synthesis_started",
                agent_id=self.agent_id,
                timestamp=datetime.utcnow().isoformat(),
                message="Orchestrator synthesizing verified cross-agent findings.",
                data={"verified_findings_count": len(verified_findings)}
            )
        )

        synthesis_res = await self._synthesize_report(
            question=question,
            findings=verified_findings,
            traces=agent_traces,
            partial_failure=partial_failure,
            override_mode=override_mode
        )

        elapsed_total = time.time() - start_time
        review.status = "partial" if partial_failure else "completed"
        review.summary = synthesis_res.get("summary", "")
        review.limitations = synthesis_res.get("limitations", "")
        review.total_findings = len(verified_findings)
        review.elapsed_seconds = round(elapsed_total, 2)
        review.provider_used = synthesis_res.get("provider_used")
        review.model_used = synthesis_res.get("model_used")
        review.fallback_occurred = synthesis_res.get("fallback_used", False)
        review.trace_metadata = {
            "partial_failure": partial_failure,
            "agent_count": len(active_agents),
            "traces": agent_traces,
            "verifier_summary": review.evidence_verification_summary,
            "orchestrator_prompt": {
                "prompt_id": self.synthesis_prompt_def.prompt_id,
                "version": self.synthesis_prompt_def.version,
                "hash": self.synthesis_prompt_def.content_hash
            }
        }
        await session.commit()

        await event_bus.publish(
            ReviewEvent(
                review_id=review_id,
                event_type="review_completed",
                agent_id=self.agent_id,
                timestamp=datetime.utcnow().isoformat(),
                message=f"Review finalized in {round(elapsed_total, 1)}s with {len(verified_findings)} verified findings. Status: {review.status}.",
                data={"status": review.status, "total_findings": len(verified_findings)}
            )
        )

        return {
            "review_id": review_id,
            "status": review.status,
            "total_findings": len(verified_findings),
            "elapsed_seconds": round(elapsed_total, 2),
            "source_snapshot_id": review.source_snapshot_id,
            "commit_sha": review.commit_sha
        }

    async def _synthesize_report(
        self,
        question: str,
        findings: List[Dict[str, Any]],
        traces: List[Dict[str, Any]],
        partial_failure: bool,
        override_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synthesize executive findings and formal limitations using versioned prompt."""
        findings_summary = []
        for f in findings:
            findings_summary.append(
                f"- [{f.get('severity', 'info').upper()}] {f.get('title')} ({f.get('agent_id')}): {f.get('explanation')}"
            )

        system_prompt = self.synthesis_prompt_def.format_system_prompt()

        user_prompt = f"""
Review Inquiry: {question}
Partial Specialist Failure Occurred: {partial_failure}

Verified Grounded Findings from Specialist Agents ({len(findings)} total):
{chr(10).join(findings_summary) if findings_summary else "No issues or findings identified."}

Provide a structured executive synthesis and an explicit scope and limitations statement.
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
            return {
                "summary": parsed.get("summary", "Review complete."),
                "limitations": parsed.get("limitations", "Static analysis conducted. Runtime behavioral tests not executed."),
                "provider_used": model_resp.provider_name,
                "model_used": model_resp.model_name,
                "fallback_used": model_resp.fallback_used
            }
        except Exception as e:
            logger.warning(f"Fallback synthesis due to model parse error: {e}")
            return {
                "summary": f"Review completed with {len(findings)} verified findings across code, security, dependencies, and documentation.",
                "limitations": "Evaluated strictly via static inspection and RAG retrieval. Project code was not executed.",
                "provider_used": "local",
                "model_used": "rules",
                "fallback_used": False
            }

    async def execute_task(self, *args, **kwargs):
        raise NotImplementedError("Use run_review for OrchestratorAgent")

orchestrator_agent = OrchestratorAgent()
