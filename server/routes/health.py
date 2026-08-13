from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..modules.load_vectorstore import index
from ..config import settings
from ..logger import logger

router = APIRouter()


@router.get("/health")
async def health_check():
    pinecone_status = "unverified"
    groq_status = "unverified"
    overall_status = "healthy"

    # Pinecone check
    try:
        index.describe_index_stats()
        pinecone_status = "ok"
    except Exception as e:
        pinecone_status = "unreachable"
        overall_status = "degraded"
        logger.exception(f"Pinecone health check failed: {e}")

    # Groq check
    if settings.groq_api_key_resolved:
        groq_status = "ok"
    else:
        groq_status = "no key configured"
        overall_status = "degraded"

    return {
        "status": overall_status,
        "version": "1.0",
        "checks": {
            "pinecone": pinecone_status,
            "groq_api": groq_status,
        },
    }
