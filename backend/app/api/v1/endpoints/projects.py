import shutil
import time
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db, async_session_maker
from app.db.models import Project, Source, Chunk, Review, Finding, SourceSnapshot, ProjectImportJob
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    GitHubImportRequest,
    GitHubImportJobResponse,
    SourceSnapshotResponse
)
from app.core.config import settings
from app.services.retrieval.vector_store import vector_store
from app.services.retrieval.fts_index import delete_project_fts
from app.services.ingestion.github_importer import github_importer
from app.api.v1.endpoints.index import process_project_indexing

logger = logging.getLogger(__name__)

router = APIRouter()

async def run_github_import_background(
    job_id: str,
    project_id: str,
    repo_url: str,
    ref_name: Optional[str] = None,
    access_token: Optional[str] = None
):
    """Background runner for GitHub snapshot import and automated indexing."""
    async with async_session_maker() as session:
        try:
            await github_importer.import_repository(
                session=session,
                job_id=job_id,
                project_id=project_id,
                repo_url=repo_url,
                ref_name=ref_name,
                access_token=access_token
            )
            # Automatically chunk, embed, and index new snapshot
            await process_project_indexing(project_id)
        except Exception as exc:
            logger.error(f"GitHub background import job {job_id} failed: {exc}")

@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    stmt = select(Project).order_by(Project.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(
        name=payload.name,
        description=payload.description,
        status="created"
    )
    db.add(project)
    await db.flush()

    # Create project storage directory
    proj_storage = settings.STORAGE_DIR / project.id
    proj_storage.mkdir(parents=True, exist_ok=True)
    project.storage_path = str(proj_storage)

    await db.commit()
    await db.refresh(project)
    return project

# ----------------- GitHub Import Routes -----------------
@router.post("/imports/github", response_model=GitHubImportJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_github_repository(
    payload: GitHubImportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Import a public or private GitHub repository into an immutable source snapshot.
    Validates URL, resolves commit SHA via GitHub API, extracts snapshot via shallow tarball,
    and runs local chunking & embeddings without executing repository code.
    """
    # 1. Validate URL upfront
    try:
        owner, repo = github_importer.validate_github_url(payload.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 2. Get or create project
    if payload.project_id:
        stmt = select(Project).where(Project.id == payload.project_id)
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Target project not found")
    else:
        proj_name = payload.project_name or f"{owner}/{repo}"
        project = Project(
            name=proj_name,
            description=payload.description or f"Imported from {payload.repo_url}",
            status="created",
            repo_url=payload.repo_url
        )
        db.add(project)
        await db.flush()

        proj_storage = settings.STORAGE_DIR / project.id
        proj_storage.mkdir(parents=True, exist_ok=True)
        project.storage_path = str(proj_storage)
        await db.commit()
        await db.refresh(project)

    # 3. Create ProjectImportJob
    job = ProjectImportJob(
        project_id=project.id,
        importer_type="github",
        status="pending",
        progress_percent=5,
        status_message="Import job queued",
        repo_url=payload.repo_url,
        ref_name=payload.ref_name
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # 4. Enqueue background task
    background_tasks.add_task(
        run_github_import_background,
        job.id,
        project.id,
        payload.repo_url,
        payload.ref_name,
        payload.access_token
    )

    return job

@router.get("/imports/{import_id}", response_model=GitHubImportJobResponse)
async def get_import_job_status(import_id: str, db: AsyncSession = Depends(get_db)):
    """Check the real-time progress of a GitHub import job."""
    stmt = select(ProjectImportJob).where(ProjectImportJob.id == import_id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Import job '{import_id}' not found")
    return job

@router.post("/{project_id}/sources/github/refresh", response_model=GitHubImportJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def refresh_github_snapshot(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Re-fetches the repository and creates a new immutable source snapshot.
    Updates the project to the latest commit SHA without overwriting review history.
    """
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.repo_url:
        raise HTTPException(
            status_code=400,
            detail="Project was not imported from a GitHub repository. Cannot refresh snapshot."
        )

    job = ProjectImportJob(
        project_id=project.id,
        importer_type="github",
        status="pending",
        progress_percent=5,
        status_message="Snapshot refresh queued",
        repo_url=project.repo_url,
        ref_name=None
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(
        run_github_import_background,
        job.id,
        project.id,
        project.repo_url,
        None,
        None
    )

    return job

@router.post("/imports/{import_id}/cancel", response_model=GitHubImportJobResponse)
async def cancel_import_job(import_id: str, db: AsyncSession = Depends(get_db)):
    """Cancels an in-progress or queued ingestion job."""
    stmt = select(ProjectImportJob).where(ProjectImportJob.id == import_id)
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found")

    if job.status not in ("completed", "failed", "cancelled"):
        job.status = "cancelled"
        job.status_message = "Job cancelled by user."
        await db.commit()
        await db.refresh(job)
    return job

@router.post("/{project_id}/ingest/retry", response_model=GitHubImportJobResponse)
async def retry_project_ingestion(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Idempotently retries or recovers ingestion for a project whose previous job failed or was interrupted.
    """
    stmt = select(Project).where(Project.id == project_id)
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job_stmt = select(ProjectImportJob).where(ProjectImportJob.project_id == project_id).order_by(ProjectImportJob.created_at.desc())
    job = (await db.execute(job_stmt)).scalar_one_or_none()

    if not job:
        # Create a new job if none exists
        job = ProjectImportJob(
            project_id=project.id,
            importer_type="github" if project.repo_url else "file_upload",
            status="pending",
            progress_percent=5,
            status_message="Retry queued",
            repo_url=project.repo_url or "local_upload"
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

    job.status = "pending"
    job.progress_percent = 5
    job.status_message = "Ingestion retry initialized..."
    job.error_message = None
    project.status = "indexing"
    await db.commit()
    await db.refresh(job)

    if project.repo_url:
        background_tasks.add_task(
            run_github_import_background,
            job.id,
            project.id,
            project.repo_url,
            job.ref_name,
            None
        )
    else:
        # Re-index local sources
        background_tasks.add_task(process_project_indexing, project.id)

    return job

@router.get("/{project_id}/snapshots", response_model=List[SourceSnapshotResponse])
async def list_project_snapshots(project_id: str, db: AsyncSession = Depends(get_db)):
    """List all immutable source snapshots and commit SHAs for a project."""
    stmt = select(SourceSnapshot).where(SourceSnapshot.project_id == project_id).order_by(SourceSnapshot.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

# ----------------- Existing Project CRUD -----------------
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description

    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/cleanup-tests", status_code=status.HTTP_200_OK)
async def cleanup_test_projects(db: AsyncSession = Depends(get_db)):
    """
    Safely removes confirmed automated test projects ('Verifier Test Suite', 'Stuck Project')
    while strictly preserving all user projects, files, and repositories.
    """
    stmt = select(Project).where(Project.name.in_(["Verifier Test Suite", "Stuck Project"]))
    test_projects = (await db.execute(stmt)).scalars().all()
    deleted_count = 0
    for p in test_projects:
        if p.storage_path and Path(p.storage_path).exists():
            shutil.rmtree(p.storage_path, ignore_errors=True)
        vector_store.delete_project_vectors(p.id)
        await delete_project_fts(db, p.id)
        await db.delete(p)
        deleted_count += 1
    await db.commit()
    return {
        "message": f"Successfully cleaned up {deleted_count} automated test projects.",
        "deleted_count": deleted_count
    }

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Clean up local files
    if project.storage_path and Path(project.storage_path).exists():
        shutil.rmtree(project.storage_path, ignore_errors=True)

    # 2. Clean up vector embeddings
    vector_store.delete_project_vectors(project_id)

    # 3. Clean up SQLite FTS5 index
    await delete_project_fts(db, project_id)

    # 4. Delete database record (cascades to sources, chunks, reviews, findings, snapshots, import_jobs)
    await db.delete(project)
    await db.commit()
    return None
