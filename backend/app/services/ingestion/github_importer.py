import re
import shutil
import tarfile
import zipfile
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from urllib.parse import urlparse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.models import Project, Source, SourceSnapshot, ProjectImportJob
from app.services.ingestion.validator import ALLOWED_EXTENSIONS, DISALLOWED_BINARIES, is_safe_path
from app.services.ingestion.extractor import extract_file_content, detect_file_type

# Strict GitHub HTTPS URL pattern: https://github.com/owner/repo or repo.git
GITHUB_URL_REGEX = re.compile(
    r"^https://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+?)(?:\.git)?/?$"
)

class GitHubSourceImporter:
    @staticmethod
    def validate_github_url(url: str) -> Tuple[str, str]:
        """
        Validates that the URL is strictly an HTTPS GitHub repository URL.
        Rejects SSH, file://, custom hosts, embedded credentials, query params, etc.
        Returns: (owner, repo)
        """
        parsed = urlparse(url.strip())
        if parsed.scheme != "https":
            raise ValueError("Only secure HTTPS URLs are permitted (e.g. https://github.com/owner/repo).")
        if parsed.netloc.lower() != "github.com":
            raise ValueError("Only official GitHub repositories (github.com) are supported.")
        if parsed.username or parsed.password:
            raise ValueError("Embedded credentials in repository URLs are strictly prohibited.")
        if parsed.query or parsed.params or parsed.fragment:
            raise ValueError("Query parameters and URL fragments are not allowed in repository URLs.")

        match = GITHUB_URL_REGEX.match(url.strip())
        if not match:
            raise ValueError("Invalid GitHub repository URL format. Expected: https://github.com/owner/repository")

        owner, repo = match.group(1), match.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo

    async def resolve_commit_sha(
        self,
        owner: str,
        repo: str,
        ref: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Resolves the target ref to an immutable commit SHA via GitHub API.
        Never logs or exposes the access token.
        Returns: (resolved_sha, resolved_ref_name)
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "M-ARCH-GitHub-Importer/1.1.0"
        }
        if access_token and access_token.strip():
            headers["Authorization"] = f"Bearer {access_token.strip()}"

        target_ref = ref.strip() if ref and ref.strip() else "HEAD"

        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # 1. Try resolving ref via commits endpoint
            commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{target_ref}"
            resp = await client.get(commit_url, headers=headers)

            if resp.status_code == 200:
                data = resp.json()
                sha = data.get("sha")
                if sha:
                    return sha, target_ref

            # 2. If ref was not specified or was HEAD, check default branch
            repo_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_resp = await client.get(repo_url, headers=headers)
            if repo_resp.status_code == 200:
                default_branch = repo_resp.json().get("default_branch", "main")
                branch_resp = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/commits/{default_branch}",
                    headers=headers
                )
                if branch_resp.status_code == 200:
                    sha = branch_resp.json().get("sha")
                    if sha:
                        return sha, default_branch

            # Error diagnosis
            if resp.status_code == 404 or repo_resp.status_code == 404:
                raise ValueError(
                    f"GitHub repository '{owner}/{repo}' or ref '{target_ref}' not found. "
                    "If this is a private repository, provide a valid GitHub Personal Access Token (PAT)."
                )
            elif resp.status_code == 401 or resp.status_code == 403:
                raise ValueError("Access denied by GitHub API. Check your rate limits or Personal Access Token permissions.")
            else:
                raise ValueError(f"GitHub API returned error HTTP {resp.status_code} while resolving ref '{target_ref}'.")

    async def fetch_and_extract_snapshot(
        self,
        owner: str,
        repo: str,
        commit_sha: str,
        dest_dir: Path,
        access_token: Optional[str] = None
    ) -> Tuple[List[Path], int, int]:
        """
        Streams shallow archive directly from GitHub via HTTP (disabling all Git hooks/execution).
        Safely extracts files while filtering binaries, symlinks, and path traversal.
        Returns: (extracted_files, accepted_count, skipped_count)
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "M-ARCH-GitHub-Importer/1.1.0"
        }
        if access_token and access_token.strip():
            headers["Authorization"] = f"Bearer {access_token.strip()}"

        archive_url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{commit_sha}"
        temp_dir = dest_dir / f"tmp_{int(time.time())}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        archive_file = temp_dir / "snapshot.tar.gz"

        try:
            # Stream download
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                async with client.stream("GET", archive_url, headers=headers) as resp:
                    if resp.status_code != 200:
                        raise ValueError(f"Failed to download snapshot archive from GitHub (HTTP {resp.status_code})")
                    with open(archive_file, "wb") as f:
                        async for chunk in resp.aiter_bytes(chunk_size=65536):
                            f.write(chunk)

            # Safe extraction
            dest_dir.mkdir(parents=True, exist_ok=True)
            accepted_files: List[Path] = []
            skipped_count = 0

            with tarfile.open(archive_file, "r:gz") as tar:
                members = tar.getmembers()
                # Determine common root prefix (GitHub tarballs nest under owner-repo-sha/)
                prefix_parts = 1

                for member in members:
                    # Skip symlinks, devices, pipes for security
                    if member.issym() or member.islnk() or member.isdev() or member.ischr():
                        skipped_count += 1
                        continue

                    # Strip outer folder
                    member_path = Path(member.name)
                    if len(member_path.parts) <= prefix_parts:
                        continue
                    rel_parts = member_path.parts[prefix_parts:]
                    relative_path = Path(*rel_parts)

                    if ".." in relative_path.parts:
                        skipped_count += 1
                        continue

                    target_dest = (dest_dir / relative_path).resolve()
                    if not is_safe_path(dest_dir, target_dest):
                        skipped_count += 1
                        continue

                    if member.isdir():
                        target_dest.mkdir(parents=True, exist_ok=True)
                        continue

                    # Skip git internal metadata, node_modules, .venv
                    if any(p in (".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build") for p in rel_parts):
                        skipped_count += 1
                        continue

                    suffix = target_dest.suffix.lower()
                    if suffix in DISALLOWED_BINARIES:
                        skipped_count += 1
                        continue

                    # Safe write
                    target_dest.parent.mkdir(parents=True, exist_ok=True)
                    f_in = tar.extractfile(member)
                    if f_in:
                        with open(target_dest, "wb") as f_out:
                            f_out.write(f_in.read())
                        accepted_files.append(target_dest)
                    else:
                        skipped_count += 1

            return accepted_files, len(accepted_files), skipped_count

        finally:
            # Clean up temporary archive file and temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    async def import_repository(
        self,
        session: AsyncSession,
        job_id: str,
        project_id: str,
        repo_url: str,
        ref_name: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coordinates full GitHub import lifecycle:
        1. Validate URL -> 2. Resolve SHA -> 3. Download Snapshot -> 4. Record Snapshot & Sources.
        """
        stmt = select(ProjectImportJob).where(ProjectImportJob.id == job_id)
        res = await session.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise ValueError(f"Import job {job_id} not found")

        p_stmt = select(Project).where(Project.id == project_id)
        p_res = await session.execute(p_stmt)
        project = p_res.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        try:
            # Step 1: Validate URL
            job.status = "validating"
            job.progress_percent = 15
            job.status_message = "Validating GitHub repository URL..."
            await session.commit()

            owner, repo = self.validate_github_url(repo_url)

            # Step 2: Resolve SHA
            job.status = "fetching"
            job.progress_percent = 35
            job.status_message = f"Resolving ref '{ref_name or 'HEAD'}' on {owner}/{repo}..."
            await session.commit()

            resolved_sha, resolved_ref = await self.resolve_commit_sha(
                owner=owner, repo=repo, ref=ref_name, access_token=access_token
            )
            job.resolved_commit_sha = resolved_sha
            job.ref_name = resolved_ref

            # Step 3: Fetch Snapshot
            job.status = "extracting"
            job.progress_percent = 60
            job.status_message = f"Fetching immutable snapshot for commit {resolved_sha[:8]}..."
            await session.commit()

            # Directory for immutable snapshot
            snapshot_id = f"snap_{int(time.time())}_{resolved_sha[:8]}"
            snapshot_storage = (settings.STORAGE_DIR / project_id / "snapshots" / snapshot_id).resolve()
            snapshot_storage.mkdir(parents=True, exist_ok=True)

            accepted_files, accepted_count, skipped_count = await self.fetch_and_extract_snapshot(
                owner=owner,
                repo=repo,
                commit_sha=resolved_sha,
                dest_dir=snapshot_storage,
                access_token=access_token
            )

            # Step 4: Index sources & create Snapshot record
            job.status = "indexing"
            job.progress_percent = 85
            job.status_message = f"Processing {accepted_count} files into source inventory..."
            await session.commit()

            # Compute aggregate source hash
            hasher = hashlib.sha256()
            total_bytes = 0

            # Delete previous project sources for replacement snapshot
            existing_sources_stmt = select(Source).where(Source.project_id == project_id)
            existing_sources = (await session.execute(existing_sources_stmt)).scalars().all()
            for es in existing_sources:
                await session.delete(es)

            # Create new Source records
            created_sources = []
            for file_path in accepted_files:
                rel_path = file_path.resolve().relative_to(snapshot_storage).as_posix()
                content, sha256, line_count = extract_file_content(file_path)
                file_size = file_path.stat().st_size
                total_bytes += file_size
                hasher.update(sha256.encode("utf-8"))
                file_type = detect_file_type(file_path)

                source = Source(
                    project_id=project_id,
                    file_path=rel_path,
                    file_name=file_path.name,
                    file_type=file_type,
                    file_size=file_size,
                    content_hash=sha256,
                    line_count=line_count,
                    storage_path=str(file_path),
                    snapshot_id=snapshot_id
                )
                session.add(source)
                created_sources.append(source)

            aggregate_hash = hasher.hexdigest()

            # Record immutable SourceSnapshot
            snapshot = SourceSnapshot(
                id=snapshot_id,
                project_id=project_id,
                snapshot_type="github",
                commit_sha=resolved_sha,
                ref_name=resolved_ref,
                repo_url=repo_url,
                repo_owner=owner,
                repo_name=repo,
                source_hash=aggregate_hash,
                source_count=accepted_count,
                total_size_bytes=total_bytes,
                storage_path=str(snapshot_storage),
                is_current=True
            )
            session.add(snapshot)

            # Update Project metadata
            project.source_count = accepted_count
            project.storage_path = str(snapshot_storage)
            project.current_snapshot_id = snapshot_id
            project.repo_url = repo_url
            project.current_commit_sha = resolved_sha
            project.status = "ready"

            # Update Job state
            job.status = "completed"
            job.progress_percent = 100
            job.status_message = f"Import completed successfully ({accepted_count} files accepted, {skipped_count} skipped)."
            job.files_accepted = accepted_count
            job.files_skipped = skipped_count
            job.total_size_bytes = total_bytes
            await session.commit()

            return {
                "job_id": job.id,
                "project_id": project.id,
                "status": "completed",
                "repo_name": f"{owner}/{repo}",
                "ref": resolved_ref,
                "commit_sha": resolved_sha,
                "files_accepted": accepted_count,
                "files_skipped": skipped_count,
                "total_size_bytes": total_bytes,
                "snapshot_id": snapshot_id
            }

        except Exception as exc:
            job.status = "failed"
            job.progress_percent = 100
            job.status_message = "Import failed."
            job.error_message = str(exc)
            await session.commit()
            raise exc

github_importer = GitHubSourceImporter()
