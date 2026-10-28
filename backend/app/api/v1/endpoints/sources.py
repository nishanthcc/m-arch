import os
import shutil
import hashlib
import time
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import Project, Source, SourceSnapshot
from app.schemas import SourceResponse, SourceExcerptResponse
from app.core.config import settings
from app.services.ingestion.validator import validate_and_extract_archive, ALLOWED_EXTENSIONS, DISALLOWED_BINARIES, is_safe_path
from app.services.ingestion.extractor import extract_file_content, detect_file_type

router = APIRouter()

@router.get("/projects/{project_id}/sources", response_model=List[SourceResponse])
async def list_project_sources(project_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Source).where(Source.project_id == project_id).order_by(Source.file_path)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/projects/{project_id}/sources", response_model=List[SourceResponse], status_code=status.HTTP_201_CREATED)
async def upload_project_sources(
    project_id: str,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files were provided for upload.")

    stmt = select(Project).where(Project.id == project_id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    storage_root = (Path(project.storage_path) if project.storage_path else (settings.STORAGE_DIR / project.id)).resolve()
    storage_root.mkdir(parents=True, exist_ok=True)

    created_sources: List[Source] = []
    hasher = hashlib.sha256()
    total_bytes = 0
    snapshot_type = "file_upload"
    snapshot_id = f"snap_{int(time.time())}_{project.id[:8]}"

    for upload_file in files:
        filename = upload_file.filename or "unknown_file"
        file_bytes = await upload_file.read()

        if len(file_bytes) == 0:
            continue

        # Check maximum file size
        max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' ({round(len(file_bytes)/(1024*1024), 2)}MB) exceeds maximum limit of {settings.UPLOAD_MAX_MB}MB"
            )

        # 1. Handle ZIP archive upload
        if filename.lower().endswith(".zip"):
            snapshot_type = "zip_upload"
            temp_zip = (storage_root / f"temp_{int(time.time())}_{filename}").resolve()
            temp_zip.parent.mkdir(parents=True, exist_ok=True)
            temp_zip.write_bytes(file_bytes)
            extracted_dir = (storage_root / "repo").resolve()
            try:
                extracted_files = validate_and_extract_archive(temp_zip, extracted_dir)
            except ValueError as val_err:
                temp_zip.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail=str(val_err))
            finally:
                temp_zip.unlink(missing_ok=True)

            for ext_file in extracted_files:
                resolved_ext = ext_file.resolve()
                rel_path = resolved_ext.relative_to(extracted_dir).as_posix()
                content, sha256, line_count = extract_file_content(ext_file)
                file_type = detect_file_type(ext_file)
                f_size = ext_file.stat().st_size
                total_bytes += f_size
                hasher.update(sha256.encode("utf-8"))

                source = Source(
                    project_id=project.id,
                    file_path=rel_path,
                    file_name=ext_file.name,
                    file_type=file_type,
                    file_size=f_size,
                    content_hash=sha256,
                    line_count=line_count,
                    storage_path=str(ext_file),
                    snapshot_id=snapshot_id
                )
                db.add(source)
                created_sources.append(source)

        # 2. Handle Individual Source Files / Folder Uploads
        else:
            # Clean filename and check path traversal
            clean_filename = filename.replace("\\", "/").lstrip("/")
            if ".." in clean_filename:
                continue

            dest_file = (storage_root / clean_filename).resolve()
            if not is_safe_path(storage_root, dest_file):
                continue

            suffix = dest_file.suffix.lower()
            if suffix in DISALLOWED_BINARIES:
                continue

            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(file_bytes)
            content, sha256, line_count = extract_file_content(dest_file)
            file_type = detect_file_type(dest_file)
            total_bytes += len(file_bytes)
            hasher.update(sha256.encode("utf-8"))

            source = Source(
                project_id=project.id,
                file_path=clean_filename,
                file_name=dest_file.name,
                file_type=file_type,
                file_size=len(file_bytes),
                content_hash=sha256,
                line_count=line_count,
                storage_path=str(dest_file),
                snapshot_id=snapshot_id
            )
            db.add(source)
            created_sources.append(source)

    if not created_sources:
        raise HTTPException(
            status_code=400,
            detail="No valid source files were accepted (files may have been empty, binary, or unsupported)."
        )

    # Create immutable SourceSnapshot
    snapshot = SourceSnapshot(
        id=snapshot_id,
        project_id=project.id,
        snapshot_type=snapshot_type,
        source_hash=hasher.hexdigest(),
        source_count=len(created_sources),
        total_size_bytes=total_bytes,
        storage_path=str(storage_root),
        is_current=True
    )
    db.add(snapshot)

    project.source_count = project.source_count + len(created_sources)
    project.current_snapshot_id = snapshot_id
    project.status = "ready"
    await db.commit()

    for s in created_sources:
        await db.refresh(s)

    return created_sources

@router.delete("/projects/{project_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(project_id: str, source_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Source).where(Source.id == source_id, Source.project_id == project_id)
    res = await db.execute(stmt)
    source = res.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    storage_path = Path(source.storage_path)
    if storage_path.exists():
        storage_path.unlink(missing_ok=True)

    await db.delete(source)
    await db.commit()
    return None

@router.get("/sources/{source_id}/excerpt", response_model=SourceExcerptResponse)
async def get_source_excerpt(
    source_id: str,
    line_start: int = 1,
    line_end: int = 50,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Source).where(Source.id == source_id)
    res = await db.execute(stmt)
    source = res.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    storage_path = Path(source.storage_path)
    if not storage_path.exists():
        raise HTTPException(status_code=404, detail="Storage file not found on disk")

    lines = storage_path.read_text(encoding="utf-8", errors="replace").splitlines()
    start_idx = max(0, line_start - 1)
    end_idx = min(len(lines), line_end)
    content = "\n".join(lines[start_idx:end_idx])

    return SourceExcerptResponse(
        source_id=source.id,
        file_path=source.file_path,
        line_start=start_idx + 1,
        line_end=end_idx,
        content=content
    )
