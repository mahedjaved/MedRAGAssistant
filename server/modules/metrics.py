from prometheus_client import Counter, Gauge, Histogram

# Define Prometheus metrics
request_count = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

token_usage = Counter(
    "token_usage_total", "Total number of tokens used", ["method", "endpoint"]
)

chunk_count = Counter(
    "chunk_count_total", "Total number of chunks processed", ["method", "endpoint"]
)

errors = Counter(
    "http_request_errors_total",
    "Total number of HTTP request errors",
    ["method", "endpoint", "status_code"],
)

request_latency = Histogram(
    "http_request_latency_seconds",
    "Histogram of HTTP request latency in seconds",
    ["method", "endpoint"],
)

query_latency = Histogram(
    "query_latency_seconds",
    "Histogram of query latency in seconds",
    ["method", "endpoint"],
)

active_requests = Gauge(
    "active_http_requests", "Number of active HTTP requests", ["method", "endpoint"]
)

prompt_injection_attempts_total = Counter(
    "prompt_injection_attempts_total",
    "Total number of detected prompt injection attempts",
    ["endpoint", "result"]  # result: "blocked" or "allowed"
)