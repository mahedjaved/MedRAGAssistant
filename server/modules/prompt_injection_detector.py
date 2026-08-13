import hashlib
import logging
from typing import Optional

from fastapi import HTTPException

from ..config import settings
from ..logger import logger


# Patterns are checked case-insensitively against the user query.
INJECTION_PATTERNS: list[str] = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore the above",
    "you are now DAN",
    "pretend you are",
    "act as if you are not bound by",
    "override safety",
    "jailbreak",
    "without any restrictions",
    "do not follow",
    "disregard previous",
    "new mode:",
    "developer mode",
    "unfiltered response",
    "no limitations",
]

logger = logging.getLogger(__name__)

# Singleton guard state.
# This detector has no external dependencies and initializes ready.
_injection_detector_enabled: bool = True


def validate_query(query: str) -> None:
    """Validate a user query for prompt injection attempts.

    Args:
        query: The raw user query string.

    Raises:
        HTTPException: 422 if injection patterns are detected.
    """
    if not settings.prompt_injection_detection_enabled:
        return

    query_lower = query.lower()
    detected_pattern: Optional[str] = None

    for pattern in INJECTION_PATTERNS:
        if pattern.lower() in query_lower:
            detected_pattern = pattern
            break

    if detected_pattern:
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        logger.warning(
            "Prompt injection detected | hash=%s pattern=%s",
            query_hash,
            detected_pattern,
        )
        raise HTTPException(
            status_code=422,
            detail="Your query was flagged as potentially unsafe. Please rephrase your query.",
        )
