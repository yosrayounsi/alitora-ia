
# app/telemetry/metrics.py
from prometheus_client import Counter, Histogram

REQS = Counter("ai_requests_total", "AI requests total", ["model", "action"])
TOKENS = Counter("ai_tokens_total", "Tokens total", ["model", "type"])  # type=input/output
LAT = Histogram("ai_latency_seconds", "Latency", ["stage"])  # stage=gateway/model/rag