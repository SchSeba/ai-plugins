# Analysis Perspectives Reference

Each perspective below defines a specialist sub-agent that runs in parallel during
the investigation. Every perspective includes:

- **Focus** — what this specialist is looking for
- **Log patterns** — concrete signals to detect in pod logs
- **Trace analysis** — what to check in Jaeger (when applicable)
- **Severity guidance** — how to classify findings
- **Required output format** — consistent structure for aggregation

---

## 1. Bug & Error Analysis

**Focus:**
Identify runtime errors, unhandled exceptions, panics, crashes, and logic bugs
visible in production log output.

**Log patterns:**
- Stack traces, goroutine dumps, core dumps
- Panic / fatal messages
- Nil pointer dereferences, index out of range, map access on nil
- OOM kills (`OOMKilled`, `signal: killed`, `cannot allocate memory`)
- Unhandled error returns (errors logged but not acted upon)
- Repeated error messages indicating a persistent bug
- Segfaults, SIGSEGV, SIGABRT
- Assertion failures
- Unexpected type conversions or cast failures

**Trace analysis:**
- Spans with error status codes
- Spans with exception events or error tags
- Traces that terminate unexpectedly mid-flow
- Operations returning 5xx status codes

**Severity guidance:**

| Severity | Criteria |
|----------|----------|
| CRITICAL | Panic, OOM kill, data corruption, crash loop detected |
| HIGH | Unhandled errors affecting correctness, repeated 5xx on critical paths |
| MEDIUM | Errors that are caught but handled incorrectly, edge-case crashes |
| LOW | Warning-level issues that could escalate under load |
| INFO | Occasional non-critical errors within acceptable thresholds |

**Required output format:**

```text
### [{severity}] {title}
**Perspective**: Bug & Error Analysis
**Evidence**: {exact log line(s) or trace span(s) with timestamps}
**Frequency**: {how often this occurs — count or rate}
**Impact**: {what user/system impact this causes}
**Root cause hypothesis**: {likely cause based on evidence}
**Recommended fix**: {concrete actionable fix}
---
```

---

## 2. Performance & Resource Optimization

**Focus:**
Identify slow operations, resource exhaustion, memory leaks, CPU spikes,
inefficient queries, and throughput bottlenecks.

**Log patterns:**
- Slow query warnings, query timeouts
- High latency log entries (operations taking >1s, or >p99 threshold)
- Connection pool exhaustion (`too many connections`, `connection refused`)
- Memory growth patterns (`GC pause`, heap growth logs)
- CPU throttling indicators (`CPU throttled`, container CPU limit reached)
- Retry storms indicating upstream pressure
- Queue depth warnings, backpressure signals
- Disk I/O warnings, slow filesystem operations
- Large payload warnings

**Trace analysis:**
- Spans with unusually high duration (>p95 for that operation type)
- Sequential operations that could be parallelized
- Repeated calls to the same downstream service within a single trace
- N+1 query patterns visible in trace fan-out
- Missing connection pooling (new connection per request)
- Large gaps between parent and child spans (queuing/scheduling delays)

**Severity guidance:**

| Severity | Criteria |
|----------|----------|
| CRITICAL | Resource exhaustion causing outages, memory leak confirmed |
| HIGH | p99 latency >5x SLO, consistent CPU/memory saturation |
| MEDIUM | Inefficient patterns degrading throughput, avoidable allocations |
| LOW | Minor optimization opportunities, pre-allocation suggestions |
| INFO | Baseline metrics observations, capacity planning notes |

**Required output format:**

```text
### [{severity}] {title}
**Perspective**: Performance & Resource Optimization
**Evidence**: {exact log line(s), trace span durations, or metrics}
**Frequency**: {how often this occurs}
**Impact**: {latency/throughput/resource impact with numbers}
**Root cause hypothesis**: {likely cause}
**Recommended fix**: {concrete actionable fix with expected improvement}
---
```

---

## 3. Stability & Reliability

**Focus:**
Identify crash loops, restart patterns, leader election failures, race conditions,
deadlocks, and any signals that threaten system uptime.

**Log patterns:**
- Container restart indicators (`Back-off restarting`, restart count increments)
- Crash loop patterns (repeated start → crash within short intervals)
- Leader election failures or split-brain logs
- Deadlock detection messages, lock timeout errors
- Race condition symptoms (inconsistent state, non-deterministic errors)
- Health check failures (liveness/readiness probe failures)
- Graceful shutdown failures, interrupted cleanup
- Certificate expiration warnings
- DNS resolution failures, service discovery issues
- Network partition or connectivity loss patterns
- Context deadline exceeded on internal operations

**Trace analysis:**
- Traces showing cascading failures across services
- Timeout propagation patterns
- Circuit breaker activations
- Retry amplification across service boundaries
- Partial failures where some spans succeed but others fail within the same trace

**Severity guidance:**

| Severity | Criteria |
|----------|----------|
| CRITICAL | Crash loops, split-brain, data loss risk, cascading failures |
| HIGH | Intermittent restarts, health check flapping, deadlocks |
| MEDIUM | Graceful degradation gaps, missing circuit breakers |
| LOW | Non-critical retry patterns, minor timeout misconfigurations |
| INFO | Stability observations, resilience pattern suggestions |

**Required output format:**

```text
### [{severity}] {title}
**Perspective**: Stability & Reliability
**Evidence**: {exact log line(s) or trace pattern with timestamps}
**Frequency**: {occurrence pattern — continuous, intermittent, under load}
**Impact**: {uptime/availability impact}
**Root cause hypothesis**: {likely cause}
**Recommended fix**: {concrete actionable fix}
---
```

---

## 4. Distributed Tracing Analysis

**Focus:**
Evaluate trace completeness, span coverage, context propagation, and service
dependency visibility within Jaeger. Ensure the tracing infrastructure itself
is healthy and providing actionable data.

**Log patterns:**
- Trace/span ID mismatches or missing correlation
- `trace_id` or `span_id` fields absent from structured logs
- OpenTelemetry SDK errors or exporter failures
- Dropped spans or export buffer overflow warnings
- Sampling configuration messages

**Trace analysis:**
- **Coverage gaps**: services in the architecture that have zero traces
- **Broken propagation**: parent spans with no children where calls are expected
- **Orphaned traces**: child spans that lack a parent (broken context propagation)
- **Missing spans**: HTTP/gRPC calls that should produce spans but do not
- **Inconsistent naming**: span names that are too generic (`HTTP request`) or inconsistent across services
- **Missing attributes**: spans lacking essential tags (`http.status_code`, `db.statement`, `rpc.method`, `error`)
- **Sampling issues**: critical paths with insufficient sampling rate
- **Clock skew**: child spans appearing to start before their parent
- **Service dependency graph**: verify all expected service-to-service edges are visible
- **Trace duration outliers**: traces that are 10x+ longer than their peers

**Severity guidance:**

| Severity | Criteria |
|----------|----------|
| CRITICAL | Entire services missing from traces, broken context propagation across critical paths |
| HIGH | Missing spans on error paths, key attributes absent preventing debugging |
| MEDIUM | Inconsistent span naming, sampling too aggressive on important paths |
| LOW | Minor attribute gaps, cosmetic span naming improvements |
| INFO | Trace infrastructure health observations, coverage statistics |

**Required output format:**

```text
### [{severity}] {title}
**Perspective**: Distributed Tracing Analysis
**Evidence**: {specific trace IDs, service names, or span details}
**Service(s) affected**: {which services are impacted}
**Impact**: {how this affects observability and debugging capability}
**Root cause hypothesis**: {likely cause — SDK misconfiguration, missing instrumentation, etc.}
**Recommended fix**: {concrete actionable fix — code instrumentation, config change, etc.}
---
```

---

## 5. Logging & Observability

**Focus:**
Evaluate log quality, structure, verbosity, and correlation capability.
Ensure logs are actionable for debugging, comply with best practices, and
integrate well with the overall observability stack.

**Log patterns:**
- Unstructured log lines mixed with structured (JSON) output
- Missing or inconsistent log levels (debug logs in production, errors logged as info)
- Missing correlation IDs / request IDs / trace IDs in log entries
- Sensitive data in logs (passwords, tokens, API keys, PII, credit card numbers)
- Excessive log volume (repeated identical messages, debug-level verbosity in production)
- Log lines that lack sufficient context (e.g., `"error occurred"` with no details)
- Timestamp format inconsistencies
- Missing error context (error message without the operation that caused it)
- Log rotation or truncation issues (incomplete lines)

**Trace analysis:**
- Logs not correlated with trace spans (missing `trace_id` in log fields)
- Events on spans not matching corresponding log entries
- Log-level mismatches between what spans report and what logs say

**Severity guidance:**

| Severity | Criteria |
|----------|----------|
| CRITICAL | Sensitive data (secrets, PII) in logs |
| HIGH | Missing correlation IDs on critical paths, errors logged without context |
| MEDIUM | Inconsistent log levels, excessive volume impacting costs, unstructured logs |
| LOW | Minor formatting issues, missing optional fields |
| INFO | Log quality observations, volume statistics, improvement suggestions |

**Required output format:**

```text
### [{severity}] {title}
**Perspective**: Logging & Observability
**Evidence**: {exact log line(s) demonstrating the issue}
**Frequency**: {how common this pattern is}
**Impact**: {debugging difficulty, compliance risk, cost impact}
**Recommended fix**: {concrete actionable fix — log format change, level adjustment, etc.}
---
```

---

## 6. User Experience & API Quality

**Focus:**
Analyze production behavior from the end-user and API consumer perspective.
Identify patterns that degrade user experience, cause confusion, or indicate
unreliable API behavior.

**Log patterns:**
- Slow response time warnings (p95/p99 latency exceeding SLOs)
- High error rate on specific endpoints
- Timeout patterns on user-facing operations
- Retry storms from client-side retries
- Rate limiting activations
- Request payload validation failures (indicating confusing API contract)
- Deprecated endpoint usage still occurring
- Authentication/authorization failures from legitimate users
- 4xx error clusters indicating UX or documentation issues

**Trace analysis:**
- End-to-end request latency for user-facing operations
- Error rates per endpoint/operation
- Latency distribution across service hops for a single user request
- Waterfall analysis of user-critical paths
- Client retry patterns visible in repeated trace roots with same parameters
- Partial success patterns (some downstream calls succeed, others fail)

**Severity guidance:**

| Severity | Criteria |
|----------|----------|
| CRITICAL | User-facing endpoints consistently returning errors or timing out |
| HIGH | p99 latency >SLO, frequent retry storms, broken user flows |
| MEDIUM | Degraded response times, confusing error messages, deprecated endpoint usage |
| LOW | Minor UX improvements, better error messages, response format consistency |
| INFO | Usage patterns, endpoint popularity, feature adoption observations |

**Required output format:**

```text
### [{severity}] {title}
**Perspective**: User Experience & API Quality
**Evidence**: {log lines, trace data, error rates, or latency numbers}
**Affected endpoint/operation**: {specific API path or user action}
**User impact**: {what the user experiences}
**Frequency**: {how often users encounter this}
**Recommended fix**: {concrete actionable fix}
---
```

---

## 7. Token & Cost Optimization

**Focus:**
For AI-powered services and LLM-integrated applications, identify excessive
token usage, prompt inefficiency, unnecessary API calls, and caching
opportunities that drive up operational costs.

**Log patterns:**
- Token count per request (input/output/total)
- LLM API call frequency and cost indicators
- Large prompt/context window usage
- Repeated identical or near-identical API calls (missing caching)
- Prompt template expansion producing unnecessarily large payloads
- Fallback or retry calls to LLM APIs on transient failures
- Embedding generation for duplicate content
- Streaming vs. non-streaming mode inefficiencies
- Model selection patterns (using expensive models for simple tasks)

**Trace analysis:**
- LLM API call spans with duration and token counts as attributes
- Sequential LLM calls that could be batched or parallelized
- Redundant embedding computations within a single request flow
- Cache hit/miss ratios on LLM response caches
- Preprocessing spans showing excessive context assembly time

**Severity guidance:**

| Severity | Criteria |
|----------|----------|
| CRITICAL | Runaway token usage causing budget overruns, missing rate limiting |
| HIGH | Consistently using expensive models for simple tasks, zero caching on repeated calls |
| MEDIUM | Prompt inefficiency, duplicate embedding generation, suboptimal batching |
| LOW | Minor prompt optimization opportunities, model tier tuning |
| INFO | Token usage statistics, cost breakdown observations, caching effectiveness |

**Required output format:**

```text
### [{severity}] {title}
**Perspective**: Token & Cost Optimization
**Evidence**: {token counts, API call logs, cache miss rates}
**Estimated cost impact**: {approximate cost savings if fixed}
**Frequency**: {how often this pattern occurs}
**Recommended fix**: {concrete actionable fix — caching, prompt optimization, model selection, etc.}
---
```

---

## 8. Security & Compliance

**Focus:**
Identify security violations, credential exposure, authentication failures,
authorization bypasses, and compliance risks visible in runtime logs and traces.

**Log patterns:**
- Secrets, tokens, API keys, passwords appearing in log output
- Authentication failures (repeated failed logins, brute force indicators)
- Authorization failures (RBAC denials, forbidden access)
- Unusual access patterns (requests from unexpected IPs, abnormal request volumes)
- Certificate expiration warnings or TLS handshake failures
- CORS violations
- Input validation bypasses or injection attempt indicators
- Privilege escalation attempts
- Audit log gaps (operations that should be logged but are not)
- Insecure protocol usage (HTTP instead of HTTPS, unencrypted connections)

**Trace analysis:**
- Unauthenticated requests reaching backend services
- Authorization checks missing on certain service hops
- Sensitive data visible in span attributes or tags
- Traces showing access to resources without proper RBAC validation
- Cross-tenant data access patterns

**Severity guidance:**

| Severity | Criteria |
|----------|----------|
| CRITICAL | Credentials/secrets in logs, authentication bypass, data breach risk |
| HIGH | RBAC violations, missing auth on endpoints, injection vectors |
| MEDIUM | Excessive permission usage, audit log gaps, TLS warnings |
| LOW | Minor compliance improvements, additional hardening opportunities |
| INFO | Security posture observations, access pattern statistics |

**Required output format:**

```text
### [{severity}] {title}
**Perspective**: Security & Compliance
**Evidence**: {exact log line(s) or trace data — redact actual secrets}
**Risk**: {what an attacker could exploit or what compliance rule is violated}
**Impact**: {data exposure, unauthorized access, compliance failure}
**Recommended fix**: {concrete actionable fix — redaction, RBAC change, config hardening, etc.}
---
```

---

## Sub-Agent Prompt Template

When spawning a specialist sub-agent, use this template. Replace placeholders
with the actual data.

```text
You are a specialist production application analyst focused on **{PERSPECTIVE_NAME}**.

## Your Analysis Perspective

{paste the complete perspective section from above, including Focus, Log patterns,
Trace analysis, Severity guidance, and Required output format}

## Application Context

- Project: {project name from AGENTS.md}
- Services: {list of services under investigation}
- Environment: production

## Data Sources

### Pod Logs
{paste the collected log output}

### Jaeger Traces (if available)
{paste trace summaries, service dependency graph, or specific trace analysis}

## Known Issues from Memory
{paste any previously recorded issues from memory search, or "No prior issues found."}

## Instructions

1. Analyze ALL provided data through your specialist lens.
2. Cross-reference with known issues — note if any finding is a recurrence.
3. For each finding, follow the Required Output Format exactly.
4. Sort findings by severity: CRITICAL → HIGH → MEDIUM → LOW → INFO.
5. At the end, provide a brief summary of your perspective's overall health assessment.
6. If you find NO issues in your domain, explicitly state that.

Return ONLY structured findings in the required format. Do not add commentary outside findings.
```
