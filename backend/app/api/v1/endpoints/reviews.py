from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db, async_session_maker
from app.db.models import Review, Finding, Evidence, Project, AgentTask
from app.schemas import (
    ReviewCreate, ReviewResponse, FindingResponse, ReviewReportResponse
)
from app.agents.orchestrator.agent import orchestrator_agent
from app.core.events import event_bus
from app.services.reports.exporter import generate_markdown_report, generate_html_report
from app.core.config import settings

router = APIRouter()

async def execute_review_in_background(
    review_id: str,
    project_id: str,
    question: str,
    scope: str,
    selected_agents: Optional[List[str]],
    provider_mode: Optional[str]
):
    async with async_session_maker() as session:
        try:
            await orchestrator_agent.run_review(
                review_id=review_id,
                project_id=project_id,
                question=question,
                scope=scope,
                session=session,
                selected_agents=selected_agents,
                override_mode=provider_mode
            )
        except Exception as exc:
            import traceback
            traceback.print_exc()

@router.get("", response_model=List[ReviewResponse])
async def list_reviews(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Review)
        .options(selectinload(Review.tasks))
        .order_by(Review.created_at.desc())
    )
    if project_id:
        stmt = stmt.where(Review.project_id == project_id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=ReviewResponse)
async def create_review(
    payload: ReviewCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Verify project exists
    p_stmt = select(Project).where(Project.id == payload.project_id)
    p_res = await db.execute(p_stmt)
    project = p_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    mode = payload.provider_mode or settings.AI_MODE
    review = Review(
        project_id=payload.project_id,
        question=payload.question,
        scope=payload.scope,
        status="pending",
        provider_mode=mode
    )
    db.add(review)
    await db.commit()
    # Launch background review execution
    background_tasks.add_task(
        execute_review_in_background,
        review_id=review.id,
        project_id=review.project_id,
        question=review.question,
        scope=review.scope,
        selected_agents=payload.selected_agents,
        provider_mode=payload.provider_mode
    )

    stmt = select(Review).options(selectinload(Review.tasks)).where(Review.id == review.id)
    review_loaded = (await db.execute(stmt)).scalar_one()
    return review_loaded

@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Review)
        .options(selectinload(Review.tasks))
        .where(Review.id == review_id)
    )
    res = await db.execute(stmt)
    review = res.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@router.get("/{review_id}/events")
async def stream_review_events(review_id: str):
    """Server-Sent Events (SSE) live progress stream."""
    return EventSourceResponse(event_bus.sse_generator(review_id))

@router.get("/{review_id}/findings", response_model=List[FindingResponse])
async def get_review_findings(
    review_id: str,
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    manual_review_only: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Finding)
        .options(selectinload(Finding.evidence_items))
        .where(Finding.review_id == review_id)
        .order_by(Finding.confidence.desc())
    )
    if severity:
        stmt = stmt.where(Finding.severity == severity.lower())
    if category:
        stmt = stmt.where(Finding.category == category)
    if agent_id:
        stmt = stmt.where(Finding.agent_id == agent_id)
    if verification_status:
        stmt = stmt.where(Finding.verification_status == verification_status)
    if manual_review_only:
        stmt = stmt.where(Finding.manual_review_required == True)

    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{review_id}/report", response_model=ReviewReportResponse)
async def get_review_report(review_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Review)
        .options(selectinload(Review.tasks), selectinload(Review.project))
        .where(Review.id == review_id)
    )
    res = await db.execute(stmt)
    review = res.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    # Fetch findings with evidence
    f_stmt = (
        select(Finding)
        .options(selectinload(Finding.evidence_items))
        .where(Finding.review_id == review_id)
    )
    f_res = await db.execute(f_stmt)
    findings = f_res.scalars().all()

    # Severity distribution
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
    for f in findings:
        sev = f.severity.lower()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    findings_dicts = [FindingResponse.model_validate(f).model_dump() for f in findings]
    tasks_dicts = [AgentTask.model_validate(t).model_dump() if hasattr(t, 'model_dump') else {
        "agent_id": t.agent_id, "task_name": t.task_name, "status": t.status,
        "execution_time_seconds": t.execution_time_seconds, "provider_used": t.provider_used,
        "model_used": t.model_used
    } for t in review.tasks]

    project_name = review.project.name if review.project else "Project"

    md_report = generate_markdown_report(
        project_name=project_name,
        question=review.question,
        status=review.status,
        summary=review.summary or "",
        limitations=review.limitations or "",
        findings=findings_dicts,
        tasks=tasks_dicts
    )

    html_report = generate_html_report(
        project_name=project_name,
        question=review.question,
        status=review.status,
        summary=review.summary or "",
        limitations=review.limitations or "",
        findings=findings_dicts,
        tasks=tasks_dicts
    )

    return ReviewReportResponse(
        review_id=review.id,
        project_name=project_name,
        question=review.question,
        status=review.status,
        summary=review.summary,
        limitations=review.limitations,
        total_findings=review.total_findings,
        findings_by_severity=severity_counts,
        findings=[FindingResponse.model_validate(f) for f in findings],
        agent_traces=review.tasks,
        markdown_report=md_report,
        html_report=html_report
    )
