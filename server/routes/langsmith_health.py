"""LangSmith health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel
from ..modules.langsmith_tracing import _langsmith_enabled, _langsmith_client

router = APIRouter()

class LangSmithHealth(BaseModel):
    enabled: bool
    configured: bool
    api_key_set: bool

@router.get("/langsmith-health")
async def langsmith_health() -> LangSmithHealth:
    """
    Check if LangSmith is properly configured.
    """
    api_key_set = bool(_langsmith_enabled and _langsmith_client)

    return LangSmithHealth(
        enabled=_langsmith_enabled, configured=api_key_set, api_key_set=api_key_set
    )