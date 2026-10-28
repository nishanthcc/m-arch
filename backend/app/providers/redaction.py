import re
from typing import Tuple

# Common patterns for API keys, tokens, and private credentials
SECRET_PATTERNS = [
    # Generic API Keys / Tokens / Secrets
    (re.compile(r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key|bearer)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{16,})["\']?'), r'\1: "[REDACTED_SECRET]"'),
    # AWS Access Key ID & Secret Key
    (re.compile(r'(?i)(AKIA[0-9A-Z]{16})'), r'[REDACTED_AWS_KEY]'),
    (re.compile(r'(?i)(aws_secret_access_key\s*[:=]\s*["\']?[a-zA-Z0-9/+=]{40}["\']?)'), r'aws_secret_access_key="[REDACTED_AWS_SECRET]"'),
    # GitHub Tokens
    (re.compile(r'(gh[pousr]_[a-zA-Z0-9]{36,})'), r'[REDACTED_GITHUB_TOKEN]'),
    # Slack Tokens
    (re.compile(r'(xox[baprs]-[0-9a-zA-Z\-]{10,})'), r'[REDACTED_SLACK_TOKEN]'),
    # Private Key blocks
    (re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+PRIVATE KEY-----'), r'[REDACTED_PRIVATE_KEY_BLOCK]'),
    # Passwords in URLs
    (re.compile(r'(https?://[a-zA-Z0-9_.-]+:)[^@/\s]+(@)'), r'\1[REDACTED_PASSWORD]\2'),
    # Groq API Keys (gsk_...)
    (re.compile(r'(gsk_[a-zA-Z0-9]{40,})'), r'[REDACTED_GROQ_KEY]'),
]

def redact_secrets(text: str) -> Tuple[str, bool]:
    """
    Safely redacts secrets and credentials from source text before dispatching to external APIs.
    Returns: (redacted_text, was_redacted)
    """
    redacted = text
    modified = False
    for pattern, replacement in SECRET_PATTERNS:
        new_text = pattern.sub(replacement, redacted)
        if new_text != redacted:
            redacted = new_text
            modified = True
    return redacted, modified
