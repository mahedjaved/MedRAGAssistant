from guardrails import Guard
from guardrails.validators import detect_jailbreak
from guardrails.exceptions import ValidationError
from fastapi import HTTPException
from config import settings
from logger import logger
import hashlib

# validator parameters accept a list where several validators e.g. detect jailbreak or detect toxicity can be used
# guard = Guard(validators=[detect_jailbreak()])

try:
    injection_guard = Guard(
        validators=[
            detect_jailbreak(threshold=settings.prompt_injection_confidence_threshold)
        ]
    )
except Exception as e:
    logger.error(f"Failed to initialize prompt injection guard: {e}")
    injection_guard = None


def validate_query(query: str) -> None:
    if injection_guard is None:
        logger.warning(r"Prompt injection guard unavailable, skipping check")
        return

    try:
        injection_guard.validate(query) 
    except ValidationError as e:
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        confidence = getattr(e, 'risk_score', getattr(e, 'error_message', 'N/A'))
        logger.warning(f"Injection detected | hash={query_hash} confidence={confidence}")
        raise HTTPException(422, "Your query was flagged as potentially unsafe. Please rephrase your query.")
        return 
    except Exception as e:
        logger.error(f"Prompt injection validator error: {e}")
        return