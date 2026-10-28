import logging
from sqlalchemy import select, update
from app.db.session import async_session_maker
from app.db.models import Project, ProjectImportJob, Review, AgentTask, EvaluationRun

logger = logging.getLogger("m-arch.recovery")

async def recover_dangling_jobs():
    """
    Scans for jobs, reviews, or tasks that were left in-flight when the process exited.
    Recovers them to clean terminal or recoverable states ('needs_attention' / 'partial')
    so the system never remains stuck in 'indexing' or 'running'.
    """
    async with async_session_maker() as session:
        try:
            # 1. Recover interrupted import/ingestion jobs
            stmt = select(ProjectImportJob).where(
                ProjectImportJob.status.in_([
                    "pending", "validating", "fetching", "extracting", "indexing", "profiling"
                ])
            )
            res = await session.execute(stmt)
            dangling_jobs = res.scalars().all()
            for job in dangling_jobs:
                logger.warning(f"Recovering dangling import job {job.id} (was '{job.status}')")
                job.status = "needs_attention"
                job.status_message = "Process was interrupted by server restart. Click Retry to re-run ingestion safely."
                job.error_message = "Server restarted during job execution."

            # 2. Recover interrupted project statuses
            p_stmt = select(Project).where(Project.status == "indexing")
            p_res = await session.execute(p_stmt)
            dangling_projects = p_res.scalars().all()
            for proj in dangling_projects:
                logger.warning(f"Recovering project {proj.id} from dangling 'indexing' status")
                # If sources exist, set to ready or needs_attention
                if proj.chunk_count > 0:
                    proj.status = "ready"
                else:
                    proj.status = "needs_attention"

            # 3. Recover interrupted reviews
            r_stmt = select(Review).where(Review.status.in_(["pending", "running"]))
            r_res = await session.execute(r_stmt)
            dangling_reviews = r_res.scalars().all()
            for rev in dangling_reviews:
                logger.warning(f"Recovering review {rev.id} from dangling '{rev.status}' status")
                rev.status = "needs_attention"
                rev.limitations = (rev.limitations or "") + " [Review was interrupted by backend restart before full synthesis completed.]"

            # 4. Recover interrupted agent tasks
            t_stmt = select(AgentTask).where(AgentTask.status.in_(["waiting", "running"]))
            t_res = await session.execute(t_stmt)
            dangling_tasks = t_res.scalars().all()
            for task in dangling_tasks:
                task.status = "failed"
                task.error_message = "Agent execution interrupted by server restart."

            # 5. Recover interrupted evaluation runs
            e_stmt = select(EvaluationRun).where(EvaluationRun.status == "running")
            e_res = await session.execute(e_stmt)
            dangling_evals = e_res.scalars().all()
            for ev in dangling_evals:
                ev.status = "needs_attention"
                ev.metrics = ev.metrics or {}
                ev.metrics["interrupted_reason"] = "Server restarted during benchmark run."

            await session.commit()
            if dangling_jobs or dangling_projects or dangling_reviews or dangling_tasks or dangling_evals:
                logger.info(
                    f"Recovery complete: recovered {len(dangling_jobs)} jobs, {len(dangling_projects)} projects, "
                    f"{len(dangling_reviews)} reviews, {len(dangling_tasks)} tasks, {len(dangling_evals)} evals."
                )
            counts = {
                "jobs": len(dangling_jobs),
                "projects": len(dangling_projects),
                "reviews": len(dangling_reviews),
                "tasks": len(dangling_tasks),
                "evals": len(dangling_evals)
            }
            return counts
        except Exception as exc:
            logger.error(f"Error during dangling job recovery: {exc}")
            return {"jobs": 0, "projects": 0, "reviews": 0, "tasks": 0, "evals": 0}
