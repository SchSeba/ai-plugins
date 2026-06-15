# Observability — Refactoring Checklist

Covers code importing logging, metrics, or tracing libraries.

**Important:** Only add observability instrumentation if the project already has the foundational infrastructure (logging library, metrics exporter, tracing SDK) set up. Do not introduce new observability frameworks.

---

## Logging

- Use structured logging (key-value pairs, JSON format) — not `fmt.Println` or `print()`.
- Use appropriate log levels: ERROR for failures needing attention, WARN for degraded but functioning, INFO for significant events, DEBUG for troubleshooting detail.
- Include contextual fields: request ID, user ID, operation name, duration.
- Never log credentials, tokens, API keys, PII, or other sensitive data.
- Log at function boundaries: entry (DEBUG), exit with result (DEBUG/INFO), errors (ERROR).

## Metrics

- Use the project's existing metrics library (Prometheus, OpenTelemetry, StatsD, etc.).
- Standard metrics to add where missing:
  - Request duration histograms for API handlers
  - Error counters by type/component
  - Queue/channel depth gauges for async processing
  - Connection pool utilization
- Follow naming conventions: `<namespace>_<subsystem>_<name>_<unit>` (e.g., `app_http_request_duration_seconds`).
- Use labels for dimensions, but avoid high-cardinality labels (no user IDs or request IDs).

## Tracing

- Use the project's existing tracing SDK (OpenTelemetry, Jaeger, Zipkin, etc.).
- Add spans at significant operation boundaries: HTTP handlers, database queries, external API calls.
- Propagate trace context across service boundaries.
- Add relevant attributes to spans: operation type, entity ID, result status.
- Record errors on spans with `span.RecordError()` and `span.SetStatus()`.

## Correlation

- Pass `context.Context` (Go), request context (Python), or equivalent through all layers.
- Include trace ID and span ID in log entries for log-to-trace correlation.
- Use baggage or context values for cross-cutting concerns (request ID, tenant ID).
