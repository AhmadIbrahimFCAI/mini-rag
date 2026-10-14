import time

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

METRICS_PATH = "/AsgRgF4Jzfu6OGmF"

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

# Total requests by method / endpoint / status code
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

# Latency (custom buckets give better p95/p99 resolution than the defaults)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)

# Requests currently being processed (saturation / concurrency)
REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Unhandled exceptions, by type
REQUEST_EXCEPTIONS = Counter(
    "http_request_exceptions_total",
    "Total unhandled exceptions raised while processing requests",
    ["method", "endpoint", "exception_type"],
)

# Payload sizes
REQUEST_SIZE = Histogram(
    "http_request_size_bytes",
    "HTTP request body size in bytes (from Content-Length)",
    ["method", "endpoint"],
    buckets=(100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000),
)
RESPONSE_SIZE = Histogram(
    "http_response_size_bytes",
    "HTTP response body size in bytes (from Content-Length)",
    ["method", "endpoint"],
    buckets=(100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000),
)

# Error counters by class (handy for simple alerting without PromQL regex)
HTTP_4XX = Counter(
    "http_client_errors_total", "Total 4xx responses", ["method", "endpoint"]
)
HTTP_5XX = Counter(
    "http_server_errors_total", "Total 5xx responses", ["method", "endpoint"]
)

# Static app info / uptime
APP_INFO = Gauge("app_info", "Application info", ["version"])
APP_START_TIME = Gauge(
    "app_start_time_seconds", "Unix time the application started"
)


def _get_endpoint(request: Request) -> str:
    """
    Return the route *template* (e.g. /users/{user_id}) instead of the raw path
    (/users/42). This prevents label-cardinality explosion, which can blow up
    Prometheus memory. Unmatched paths (404 scans, bots) collapse into one label.
    """
    route = request.scope.get("route")
    return route.path if route else "unmatched"


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Don't measure the metrics endpoint itself
        if request.url.path == METRICS_PATH:
            return await call_next(request)

        method = request.method
        # The route template isn't known until routing has happened, so the
        # in-progress gauge uses a fixed "all" endpoint label (method only).
        start_time = time.perf_counter()
        status_code = 500
        response = None
        in_progress = REQUESTS_IN_PROGRESS.labels(method=method, endpoint="all")
        in_progress.inc()

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            endpoint = _get_endpoint(request)
            REQUEST_EXCEPTIONS.labels(
                method=method, endpoint=endpoint, exception_type=type(exc).__name__
            ).inc()
            raise
        finally:
            duration = time.perf_counter() - start_time
            endpoint = _get_endpoint(request)
            in_progress.dec()

            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
            REQUEST_COUNT.labels(
                method=method, endpoint=endpoint, status=str(status_code)
            ).inc()

            if 400 <= status_code < 500:
                HTTP_4XX.labels(method=method, endpoint=endpoint).inc()
            elif status_code >= 500:
                HTTP_5XX.labels(method=method, endpoint=endpoint).inc()

            # Request size
            req_len = request.headers.get("content-length")
            if req_len and req_len.isdigit():
                REQUEST_SIZE.labels(method=method, endpoint=endpoint).observe(
                    int(req_len)
                )

            # Response size (only available when Content-Length is set;
            # streaming responses won't have it)
            if response is not None:
                resp_len = response.headers.get("content-length")
                if resp_len and resp_len.isdigit():
                    RESPONSE_SIZE.labels(method=method, endpoint=endpoint).observe(
                        int(resp_len)
                    )


def setup_metrics(app: FastAPI, version: str = "1.0.0"):
    """
    Setup Prometheus metrics middleware and endpoint.

    Note: prometheus_client's default registry already exports process and
    runtime metrics (CPU, memory, open FDs, GC stats, Python info) for free.
    """
    APP_INFO.labels(version=version).set(1)
    APP_START_TIME.set_to_current_time()

    app.add_middleware(PrometheusMiddleware)

    @app.get(METRICS_PATH, include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Example: custom business / dependency metrics you can use anywhere in the app
# ---------------------------------------------------------------------------
# DB_QUERY_LATENCY = Histogram(
#     "db_query_duration_seconds",
#     "Database query latency in seconds",
#     ["operation"],
# )
# EXTERNAL_CALLS = Counter(
#     "external_api_calls_total",
#     "Calls to external services",
#     ["service", "outcome"],
# )

# Usage:
#   with DB_QUERY_LATENCY.labels(operation="select_user").time():
#       row = await db.fetch_one(...)
#
#   EXTERNAL_CALLS.labels(service="payments", outcome="success").inc()









# from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
# from fastapi import FastAPI, Request, Response
# from starlette.middleware.base import BaseHTTPMiddleware
# import time


# # Define metrics
# REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
# REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])


# class PrometheusMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         start_time = time.time()
        
#         # Process the request
#         response = await call_next(request)

#         # Record metrics after request is processed
#         duration = time.time() - start_time
#         endpoint = request.url.path

#         REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(duration)
#         REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()

#         return response


# def setup_metrics(app: FastAPI):
#     """
#     Setup Prometheus metrics middleware and endpoint
#     """
#     # Add Prometheus middleware
#     app.add_middleware(PrometheusMiddleware)

#     @app.get("/AsgRgF4Jzfu6OGmF", include_in_schema=False)
#     def metrics():
#         return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


