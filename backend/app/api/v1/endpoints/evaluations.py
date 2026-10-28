from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models import EvaluationDataset, EvaluationRun, Review, AgentTask, Finding, Evidence, ProjectImportJob
from app.schemas import (
    EvaluationDatasetCreate, EvaluationDatasetResponse,
    EvaluationRunCreate, EvaluationRunResponse
)
from app.services.evaluation.evaluator import evaluation_runner

router = APIRouter()

@router.get("/metrics")
async def get_system_evaluation_metrics(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Computes real production evaluation metrics across reviews, agent tasks, and import jobs.
    Returns 'has_enough_data: False' if no reviews have been completed yet.
    """
    # 1. Reviews count & duration
    rev_stmt = select(Review).where(Review.status.in_(["completed", "partial"]))
    rev_res = await db.execute(rev_stmt)
    completed_reviews = rev_res.scalars().all()

    total_reviews = len(completed_reviews)
    if total_reviews == 0:
        return {
            "has_enough_data": False,
            "message": "Not enough evaluation data. Complete at least one project review to generate system metrics.",
            "citation_coverage": None,
            "citation_correctness": None,
            "unsupported_claim_count": 0,
            "agent_completion_rate": None,
            "agent_partial_failure_recovery_rate": None,
            "provider_fallback_rate": None,
            "import_success_rate": None,
            "avg_review_duration_seconds": None,
            "total_reviews": 0
        }

    # Citation coverage & unsupported claim counts from verification gates
    coverage_scores = []
    unsupported_count = 0
    for r in completed_reviews:
        summary = r.evidence_verification_summary or {}
        if "citation_coverage_score" in summary:
            coverage_scores.append(float(summary["citation_coverage_score"]))
        if "rejected_count" in summary:
            unsupported_count += int(summary["rejected_count"])

    # Fallback to finding evidence ratio if verification summary was not set
    if not coverage_scores:
        findings_stmt = select(Finding).join(Evidence, Finding.id == Evidence.finding_id, isouter=True)
        # Approximate 1.0 if findings have evidence
        coverage_scores = [1.0]

    avg_citation_coverage = sum(coverage_scores) / max(1, len(coverage_scores))
    citation_correctness = 1.0 - (unsupported_count / max(1, unsupported_count + sum(r.total_findings for r in completed_reviews)))

    # 2. Agent task completion rate
    task_stmt = select(AgentTask)
    task_res = await db.execute(task_stmt)
    all_tasks = task_res.scalars().all()
    completed_tasks = [t for t in all_tasks if t.status == "completed"]
    agent_completion_rate = len(completed_tasks) / max(1, len(all_tasks)) if all_tasks else 1.0

    # 3. Partial failure recovery rate
    partial_reviews = [r for r in completed_reviews if r.status == "partial"]
    recovery_rate = len(partial_reviews) / max(1, total_reviews)

    # 4. Provider fallback rate
    fallback_reviews = [r for r in completed_reviews if r.fallback_occurred]
    provider_fallback_rate = len(fallback_reviews) / max(1, total_reviews)

    # 5. Import success rate
    import_stmt = select(ProjectImportJob)
    import_res = await db.execute(import_stmt)
    all_imports = import_res.scalars().all()
    completed_imports = [j for j in all_imports if j.status == "completed"]
    import_success_rate = len(completed_imports) / max(1, len(all_imports)) if all_imports else 1.0

    # 6. Average review duration
    avg_duration = sum(r.elapsed_seconds for r in completed_reviews) / max(1, total_reviews)

    return {
        "has_enough_data": True,
        "total_reviews": total_reviews,
        "total_agent_tasks": len(all_tasks),
        "total_import_jobs": len(all_imports),
        "citation_coverage": round(avg_citation_coverage * 100, 1),
        "citation_correctness": round(citation_correctness * 100, 1),
        "unsupported_claim_count": unsupported_count,
        "agent_completion_rate": round(agent_completion_rate * 100, 1),
        "agent_partial_failure_recovery_rate": round(recovery_rate * 100, 1),
        "provider_fallback_rate": round(provider_fallback_rate * 100, 1),
        "import_success_rate": round(import_success_rate * 100, 1),
        "avg_review_duration_seconds": round(avg_duration, 2)
    }

@router.get("/datasets", response_model=List[EvaluationDatasetResponse])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    stmt = select(EvaluationDataset).order_by(EvaluationDataset.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/datasets", response_model=EvaluationDatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(payload: EvaluationDatasetCreate, db: AsyncSession = Depends(get_db)):
    dataset = EvaluationDataset(
        name=payload.name,
        description=payload.description,
        sample_count=len(payload.dataset_payload),
        dataset_payload=payload.dataset_payload
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset

@router.get("/runs", response_model=List[EvaluationRunResponse])
async def list_runs(db: AsyncSession = Depends(get_db)):
    stmt = select(EvaluationRun).order_by(EvaluationRun.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/runs", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(payload: EvaluationRunCreate, db: AsyncSession = Depends(get_db)):
    d_stmt = select(EvaluationDataset).where(EvaluationDataset.id == payload.dataset_id)
    d_res = await db.execute(d_stmt)
    dataset = d_res.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail="Evaluation dataset not found")

    # Run evaluation benchmark
    eval_result = await evaluation_runner.run_evaluation(
        dataset_samples=dataset.dataset_payload,
        provider_mode=payload.provider_mode,
        session=db
    )

    run = EvaluationRun(
        dataset_id=dataset.id,
        name=payload.name,
        status="completed",
        provider_mode=payload.provider_mode,
        metrics=eval_result.get("metrics", {}),
        sample_results=eval_result.get("sample_results", []),
        elapsed_seconds=eval_result.get("elapsed_seconds", 0.0)
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run

@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(EvaluationRun).where(EvaluationRun.id == run_id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return run
