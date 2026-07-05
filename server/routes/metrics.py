from fastapi import APIRouter

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

router = APIRouter()

@router.get("/metrics")
async def metrics() -> Response:
    """
    Endpoint to expose Prometheus metrics, including request counts, token usage, chunk counts, errors, request latency, query latency, and active requests.
    """
    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)