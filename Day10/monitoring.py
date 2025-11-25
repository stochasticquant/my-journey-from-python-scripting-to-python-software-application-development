# src/inventory_system/monitoring.py
import logging
import time
from functools import wraps
from typing import Any, Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute
from prometheus_client import Counter, Histogram, REGISTRY, generate_latest

# Prometheus metrics
REQUEST_COUNT = Counter(
    "inventory_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "inventory_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)


class MonitoringRoute(APIRoute):
    """Custom APIRoute that wraps each request with Prometheus metrics."""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()

            # Process request
            response = await original_route_handler(request)

            # Record metrics
            duration = time.time() - start_time
            endpoint = request.url.path

            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration)

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code,
            ).inc()

            return response

        return custom_route_handler


def monitor_execution_time(func: Callable) -> Callable:
    """Decorator to log execution time of functions (e.g., service methods)."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            execution_time = time.time() - start_time
            logging.info(
                "Function %s executed in %.4f seconds",
                func.__name__,
                execution_time,
            )

    return wrapper


def metrics_endpoint() -> Response:
    """Return a Response object with Prometheus metrics.

    You can wire this into FastAPI like:

        from fastapi import APIRouter
        from .monitoring import metrics_endpoint

        router = APIRouter()
        @router.get("/metrics")
        def metrics():
            return metrics_endpoint()

    """
    from fastapi import Response as FastAPIResponse  # local import to avoid cycles

    return FastAPIResponse(
        content=generate_latest(REGISTRY),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
