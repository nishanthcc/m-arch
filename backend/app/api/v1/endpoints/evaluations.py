from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models import EvaluationDataset, EvaluationRun, Review, AgentTask, Finding, Evidence, ProjectImportJob, Project
from app.schemas import (
    EvaluationDatasetCreate, EvaluationDatasetResponse,
    EvaluationRunCreate, EvaluationRunResponse
)
from app.services.evaluation.evaluator import evaluation_runner

router = APIRouter()

@router.get("/metrics")
async def get_system_evaluation_metrics(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Computes real production evaluation metrics across reviews, agent tasks, and import jobs.
    Supports scoping to a specific project_id or global aggregation ('All Projects').
    Returns exact sample counts/numerators and denominators beside percentages (e.g. '8/10 (80%)').
    """
    project_name = None
    if project_id:
        p_res = await db.execute(select(Project).where(Project.id == project_id))
        project_obj = p_res.scalar_one_or_none()
        if not project_obj:
            raise HTTPException(status_code=404, detail="Project not found")
        project_name = project_obj.name

    # 1. Reviews count & duration (scoped if project_id specified)
    rev_stmt = select(Review).where(Review.status.in_(["completed", "partial"]))
    if project_id:
        rev_stmt = rev_stmt.where(Review.project_id == project_id)
    rev_res = await db.execute(rev_stmt)
    completed_reviews = rev_res.scalars().all()

    total_reviews = len(completed_reviews)
    if total_reviews == 0:
        return {
            "has_enough_data": False,
            "project_id": project_id,
            "project_name": project_name or "All Projects",
            "message": f"Not enough evaluation data for {project_name or 'the selected scope'}. Complete at least one review to generate metrics.",
            "total_reviews": 0,
            "citation_coverage": None,
            "citation_correctness": None,
            "unsupported_claim_count": 0,
            "agent_completion_rate": None,
            "agent_partial_failure_recovery_rate": None,
            "provider_fallback_rate": None,
            "import_success_rate": None,
            "avg_review_duration_seconds": None,
        }

    # Citation coverage & unsupported claim counts strictly from verification gates
    coverage_num = 0
    coverage_den = 0
    unsupported_count = 0
    for r in completed_reviews:
        summary = r.evidence_verification_summary or {}
        v_cnt = summary.get("verified_count")
        if v_cnt is not None:
            coverage_num += int(v_cnt)
            r_cnt = int(summary.get("rejected_count", 0))
            coverage_den += (int(v_cnt) + r_cnt)
        elif r.total_findings > 0:
            coverage_num += r.total_findings
            coverage_den += r.total_findings

        if "rejected_count" in summary and summary["rejected_count"] is not None:
            unsupported_count += int(summary["rejected_count"])

    cov_pct = round((coverage_num / max(1, coverage_den)) * 100, 1) if coverage_den > 0 else None
    citation_coverage_data = {
        "numerator": coverage_num,
        "denominator": coverage_den,
        "percentage": cov_pct,
        "formatted": f"{coverage_num}/{coverage_den} ({cov_pct}%)" if cov_pct is not None else "Not Measured"
    }

    total_findings_count = sum(r.total_findings for r in completed_reviews)
    corr_den = unsupported_count + total_findings_count
    corr_pct = round((total_findings_count / max(1, corr_den)) * 100, 1) if corr_den > 0 else None
    citation_correctness_data = {
        "numerator": total_findings_count,
        "denominator": corr_den,
        "percentage": corr_pct,
        "formatted": f"{total_findings_count}/{corr_den} ({corr_pct}%)" if corr_pct is not None else "Not Measured"
    }

    # 2. Agent task completion rate
    rev_ids = [r.id for r in completed_reviews]
    task_stmt = select(AgentTask).where(AgentTask.review_id.in_(rev_ids)) if rev_ids else select(AgentTask)
    task_res = await db.execute(task_stmt)
    all_tasks = task_res.scalars().all()
    completed_tasks = [t for t in all_tasks if t.status == "completed"]
    task_den = len(all_tasks)
    task_num = len(completed_tasks)
    task_pct = round((task_num / max(1, task_den)) * 100, 1) if task_den > 0 else None
    agent_completion_data = {
        "numerator": task_num,
        "denominator": task_den,
        "percentage": task_pct,
        "formatted": f"{task_num}/{task_den} ({task_pct}%)" if task_pct is not None else "Not Measured"
    }

    # 3. Partial failure recovery rate
    reviews_with_failures = [
        r for r in completed_reviews
        if r.fallback_occurred or (r.trace_metadata and r.trace_metadata.get("partial_failure"))
    ]
    recovered_reviews = [
        r for r in reviews_with_failures
        if r.status in ("completed", "partial") and r.total_findings > 0
    ]
    rec_den = len(reviews_with_failures)
    rec_num = len(recovered_reviews)
    rec_pct = round((rec_num / max(1, rec_den)) * 100, 1) if rec_den > 0 else 100.0
    recovery_data = {
        "numerator": rec_num,
        "denominator": rec_den,
        "percentage": rec_pct,
        "formatted": f"{rec_num}/{rec_den} ({rec_pct}%)" if rec_den > 0 else "0/0 (100.0%)"
    }

    # 4. Provider fallback rate
    fallback_reviews = [r for r in completed_reviews if r.fallback_occurred]
    fb_num = len(fallback_reviews)
    fb_den = total_reviews
    fb_pct = round((fb_num / max(1, fb_den)) * 100, 1)
    fallback_data = {
        "numerator": fb_num,
        "denominator": fb_den,
        "percentage": fb_pct,
        "formatted": f"{fb_num}/{fb_den} ({fb_pct}%)"
    }

    # 5. Import success rate
    import_stmt = select(ProjectImportJob)
    if project_id:
        import_stmt = import_stmt.where(ProjectImportJob.project_id == project_id)
    import_res = await db.execute(import_stmt)
    all_imports = import_res.scalars().all()
    completed_imports = [j for j in all_imports if j.status in ("completed", "ready")]
    imp_den = len(all_imports)
    imp_num = len(completed_imports)
    imp_pct = round((imp_num / max(1, imp_den)) * 100, 1) if imp_den > 0 else 100.0
    import_data = {
        "numerator": imp_num,
        "denominator": imp_den,
        "percentage": imp_pct,
        "formatted": f"{imp_num}/{imp_den} ({imp_pct}%)" if imp_den > 0 else "0/0 (100.0%)"
    }

    # 6. Average review duration
    avg_duration = round(sum(r.elapsed_seconds for r in completed_reviews) / max(1, total_reviews), 2)

    return {
        "has_enough_data": True,
        "project_id": project_id,
        "project_name": project_name or "All Projects",
        "total_reviews": total_reviews,
        "total_agent_tasks": task_den,
        "total_import_jobs": imp_den,
        "citation_coverage": citation_coverage_data,
        "citation_correctness": citation_correctness_data,
        "unsupported_claim_count": unsupported_count,
        "agent_completion_rate": agent_completion_data,
        "agent_partial_failure_recovery_rate": recovery_data,
        "provider_fallback_rate": fallback_data,
        "import_success_rate": import_data,
        "avg_review_duration_seconds": avg_duration
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
        status=eval_result.get("status", "completed"),
        dataset_version="1.2.0",
        provider_mode=payload.provider_mode,
        metrics=eval_result.get("metrics", {}),
        sample_results=eval_result.get("sample_results", []),
        execution_summary=eval_result.get("execution_summary", {}),
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
