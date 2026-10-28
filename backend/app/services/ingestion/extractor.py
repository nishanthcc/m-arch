import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple

def detect_file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()

    if suffix in (".md", ".markdown", ".rst"):
        return "markdown"
    elif suffix in (".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env.example") or name in ("dockerfile", "makefile"):
        return "config"
    elif suffix in (".txt", ".log", ".csv"):
        return "text"
    elif suffix in (".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java", ".c", ".cpp", ".h", ".sh", ".sql"):
        return "code"
    return "text"

def extract_file_content(file_path: Path) -> Tuple[str, str, int]:
    """
    Safely read text file with fallback encodings.
    Returns: (text_content, sha256_hash, line_count)
    """
    raw_bytes = file_path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()

    # Try utf-8 then latin-1
    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = raw_bytes.decode("latin-1", errors="replace")

    lines = content.splitlines()
    line_count = len(lines)
    return content, sha256, line_count
