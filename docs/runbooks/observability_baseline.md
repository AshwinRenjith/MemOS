# Observability Baseline

> Baseline observability stack for MemoryOS. All services must integrate
> with this stack before shipping features. See PRD §10.4 for alert definitions.

---

## 1. Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  memory-core    │────▶│  OTel Collector  │────▶│  Tempo / Jaeger│  ← Traces
│  memory-worker  │     │  (sidecar)       │────▶│  Prometheus    │  ← Metrics
│  semantic-diff  │     │                  │────▶│  Loki          │  ← Logs
└─────────────────┘     └──────────────────┘     └────────────────┘
                                                        │
                                                        ▼
                                                 ┌────────────────┐
                                                 │   Grafana      │  ← Dashboards
                                                 └────────────────┘
```

---

## 2. Tracing (OpenTelemetry)

### Setup
- **SDK**: `opentelemetry-sdk` + `opentelemetry-instrumentation-fastapi`
- **Exporter**: OTLP gRPC to OTel Collector
- **Sampling**: 100% in staging, 10% head-based in production (adjustable)

### Required Spans
Every API request must produce:
- `http.request` — root span from FastAPI instrumentation
- `memory.write` or `memory.retrieve` — business operation span
- `db.query` — database operation span
- `vectorstore.search` — Qdrant operation span (Phase A+)
- `kafka.publish` — outbox relay span

### Context Propagation
- W3C TraceContext headers (`traceparent`, `tracestate`)
- Custom baggage: `org_id`, `repo_id`, `agent_id`

### Configuration
```python
# services/memory-core/src/memoryos/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def configure_tracing(service_name: str, otlp_endpoint: str) -> None:
    provider = TracerProvider(resource=Resource.create({
        "service.name": service_name,
        "service.version": "0.1.0",
        "deployment.environment": settings.environment,
    }))
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=otlp_endpoint)
    ))
    trace.set_tracer_provider(provider)
```

---

## 3. Metrics (Prometheus)

### Required Metrics (from PRD §10.1 SLOs)

| Metric Name                              | Type      | Labels                            | SLO Target       |
|------------------------------------------|-----------|-----------------------------------|-------------------|
| `memoryos_ingest_ack_duration_seconds`   | Histogram | `org_id`, `priority`, `status`    | p99 ≤ 80ms        |
| `memoryos_durable_commit_duration_seconds`| Histogram | `org_id`, `commit_type`           | p99 ≤ 400ms       |
| `memoryos_retrieval_duration_seconds`    | Histogram | `org_id`, `tier_count`            | p99 ≤ 350ms       |
| `memoryos_audit_query_duration_seconds`  | Histogram | `org_id`                           | p99 ≤ 2s          |
| `memoryos_kafka_consumer_lag`            | Gauge     | `org_id`, `consumer_group`        | < 10,000 events   |
| `memoryos_conflict_records_open`         | Gauge     | `org_id`, `repo_id`               | < 100 per repo    |
| `memoryos_nli_sidecar_healthy`           | Gauge     | `instance`                         | 1 (healthy)       |
| `memoryos_intent_classifier_healthy`     | Gauge     | `instance`                         | 1 (healthy)       |
| `memoryos_writes_total`                  | Counter   | `org_id`, `action`, `data_class`  | —                 |
| `memoryos_retrievals_total`              | Counter   | `org_id`, `fallback_used`         | —                 |
| `memoryos_error_total`                   | Counter   | `org_id`, `error_code`, `endpoint`| —                 |

### Histogram Buckets
```python
LATENCY_BUCKETS = [
    0.005, 0.010, 0.025, 0.050, 0.075, 0.100,   # 5ms–100ms
    0.150, 0.200, 0.300, 0.400, 0.500,           # 150ms–500ms
    0.750, 1.0, 2.0, 5.0, 10.0                   # 750ms–10s
]
```

---

## 4. Logging (Structured — structlog)

### Configuration
```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)
```

### Required Context Fields
Every log line MUST include:
- `org_id` — tenant context
- `trace_id` — correlation to distributed trace
- `operation` — business operation name
- `repo_id` — if applicable
- `agent_id` — if applicable

### Log Levels
| Level    | Usage                                                    |
|----------|----------------------------------------------------------|
| DEBUG    | Internal state, variable values (never in production)    |
| INFO     | Successful operations, state transitions                 |
| WARNING  | Degraded mode activation, fallback triggered             |
| ERROR    | Failed operations, unhandled exceptions                  |
| CRITICAL | Invariant violations, tenant isolation suspect           |

---

## 5. Dashboards (Grafana)

### Required Dashboards (Phase A)

1. **SLO Overview**
   - Ingest ACK p99 (real-time + 7d trend)
   - Durable Commit p99
   - Retrieval p99
   - Error budget burn rate

2. **Write Pipeline**
   - Writes/sec by org
   - Kafka consumer lag
   - Outbox queue depth
   - Action breakdown (WRITTEN, DEDUPLICATED, QUEUED, SANDBOXED, BLOCKED)

3. **Retrieval Performance**
   - Retrievals/sec
   - Score distribution
   - Token budget utilization
   - Fallback mode activation rate

4. **Infrastructure**
   - PostgreSQL connections, query duration, replication lag
   - Qdrant search latency, collection sizes
   - Redis memory usage, hit rate
   - Kafka topic lag, throughput

---

## 6. Alerting (from PRD §10.4)

| Alert Name                           | Trigger                                          | Severity |
|--------------------------------------|--------------------------------------------------|----------|
| HIGH_INGEST_LATENCY                  | Ingest ACK p99 > 80ms for 2 min                 | Critical |
| KAFKA_LAG_HIGH                       | Consumer lag > 10,000 for 5 min                  | Warning  |
| NLI_DEGRADED                         | NLI sidecar health fail for 30 sec               | Warning  |
| CONFLICT_BACKLOG_HIGH                | Open conflicts > 100 per repo                   | Warning  |
| INTENT_SIDECAR_DOWN                  | Intent classifier unavailable > 15 sec           | Critical |
| TENANT_ISOLATION_BREACH_SUSPECTED    | Cross-tenant access pattern detected             | Critical |

---

## 7. Phase Rollout

| Phase   | Observability Scope                                             |
|---------|-----------------------------------------------------------------|
| Phase 0 | structlog configured, OTel SDK installed, Prometheus metrics stub|
| Phase A | Full tracing, SLO metrics, basic Grafana dashboards             |
| Phase B | Security audit logging, governance operation traces             |
| Phase C | ML model metrics, chaos experiment dashboards                   |
| Phase D | Full alerting stack, DR monitoring, cost dashboards              |
