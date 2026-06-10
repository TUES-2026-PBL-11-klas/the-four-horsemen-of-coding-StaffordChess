"""
Prometheus metrics middleware and setup.
Tracks HTTP request metrics for monitoring and observability.
"""

import time
from typing import Callable
from fastapi import Request
from prometheus_client import Counter, Histogram, Gauge
import logging

# Metrics definitions
http_request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_request_size = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
)

http_response_size = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
)

active_requests = Gauge(
    'http_requests_active',
    'Active HTTP requests',
    ['method', 'endpoint']
)

logger = logging.getLogger(__name__)


async def metrics_middleware(request: Request, call_next: Callable):
    """
    Middleware to track HTTP request metrics for Prometheus.
    
    Records:
    - Request count by method, endpoint, and status code
    - Request duration
    - Request and response sizes
    - Active request count
    """
    if request.url.path == "/metrics":
        return await call_next(request)
    
    method = request.method
    endpoint = request.url.path

    active_requests.labels(method=method, endpoint=endpoint).inc()

    request_size = 0
    if request.headers.get("content-length"):
        request_size = int(request.headers.get("content-length", 0))
    http_request_size.labels(method=method, endpoint=endpoint).observe(request_size)
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"Request failed: {method} {endpoint}")
        active_requests.labels(method=method, endpoint=endpoint).dec()
        raise
    
    duration = time.time() - start_time
    status_code = response.status_code
    
    response_size = 0
    if response.headers.get("content-length"):
        response_size = int(response.headers.get("content-length", 0))
    http_response_size.labels(method=method, endpoint=endpoint).observe(response_size)
    
    http_request_count.labels(method=method, endpoint=endpoint, status=status_code).inc()
    http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    active_requests.labels(method=method, endpoint=endpoint).dec()
    
    return response
