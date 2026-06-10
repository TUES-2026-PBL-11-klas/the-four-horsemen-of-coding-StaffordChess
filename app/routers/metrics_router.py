"""
Metrics router for Prometheus exposition.
Exposes application metrics at /metrics endpoint for Prometheus scraping.
"""

from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(prefix="", tags=["metrics"])


@router.get("/metrics")
async def metrics():
    """
    Expose Prometheus metrics.
    
    This endpoint is scraped by Prometheus to collect application metrics.
    Metrics include HTTP request counts, durations, and other system metrics.
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
