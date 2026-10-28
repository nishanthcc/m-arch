import os
import zipfile
from pathlib import Path
from typing import List, Tuple
from app.core.config import settings

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", 
    ".toml", ".md", ".txt", ".rs", ".go", ".java", ".cpp", ".c", 
    ".h", ".sh", ".sql", ".dockerfile", ".html", ".css", ".env.example",
    ".xml", ".gradle", ".properties", ".cfg", ".ini", ".lock"
}

DISALLOWED_BINARIES = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pyc", ".pyd", ".iso", ".tar",
    ".gz", ".zip", ".7z", ".rar", ".class", ".o", ".a", ".whl", ".jar"
}

def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Ensure path traversal attacks (e.g. ../../) are completely blocked."""
    try:
        base_dir_resolved = base_dir.resolve()
        target_path_resolved = target_path.resolve()
        return base_dir_resolved in target_path_resolved.parents or base_dir_resolved == target_path_resolved
    except Exception:
        return False

def validate_and_extract_archive(archive_path: Path, extract_to: Path) -> List[Path]:
    """
    Safely extract a zip archive preventing zip slip, zip bombs, and excluding binaries/hidden git dirs.
    """
    if not zipfile.is_zipfile(archive_path):
        raise ValueError("The uploaded file is not a valid ZIP archive.")

    extracted_files: List[Path] = []
    extract_to.mkdir(parents=True, exist_ok=True)
    max_total_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024 * 2  # Uncompressed limit: 2x upload limit
    total_uncompressed = 0

    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            infolist = zip_ref.infolist()
            if not infolist:
                raise ValueError("The uploaded ZIP archive is completely empty.")

            # Detect common single root directory (e.g. repo-main/)
            names = [m.filename for m in infolist if not m.is_dir()]
            prefix_to_strip = ""
            if names:
                first_parts = Path(names[0]).parts
                if len(first_parts) > 1:
                    candidate_root = first_parts[0]
                    if all(len(Path(n).parts) > 1 and Path(n).parts[0] == candidate_root for n in names):
                        prefix_to_strip = candidate_root + "/"

            for member in infolist:
                filename = member.filename
                # Check path traversal
                if ".." in Path(filename).parts or filename.startswith(("/", "\\")):
                    continue

                # Strip common prefix if detected
                rel_filename = filename
                if prefix_to_strip and rel_filename.startswith(prefix_to_strip):
                    rel_filename = rel_filename[len(prefix_to_strip):]

                if not rel_filename or rel_filename.endswith("/"):
                    continue

                member_path = Path(rel_filename)
                destination = (extract_to / member_path).resolve()
                if not is_safe_path(extract_to, destination):
                    continue

                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue

                # Skip git internals, node_modules, .venv, caches
                parts = member_path.parts
                if any(p in (".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", ".nuxt") for p in parts):
                    continue

                suffix = member_path.suffix.lower()
                if suffix in DISALLOWED_BINARIES:
                    continue

                # Zip bomb prevention
                total_uncompressed += member.file_size
                if total_uncompressed > max_total_bytes:
                    raise ValueError(f"Extracted archive exceeds safe size threshold ({settings.UPLOAD_MAX_MB * 2}MB).")

                # Extract file safely
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zip_ref.open(member) as source, open(destination, "wb") as target:
                    target.write(source.read())

                extracted_files.append(destination)

    except zipfile.BadZipFile:
        raise ValueError("Corrupt or invalid ZIP archive file.")

    if not extracted_files:
        raise ValueError("ZIP archive contains no supported source code or text files (all files were binaries, excluded, or unsupported).")

    return extracted_files
