---
name: investigate-app
description: Investigate a running production application for bugs, performance issues, stability problems, and optimization opportunities by analyzing pod logs and distributed traces. Spawns parallel specialist sub-agents, cross-references memory for recurring issues, and produces a prioritized improvement plan.
---

# Investigate App

Analyze a running production application by collecting pod logs and Jaeger traces,
spawning parallel specialist sub-agents to review multiple dimensions simultaneously,
and producing a prioritized, actionable improvement plan.

Use this skill when:
- You want to review production behavior for bugs, performance regressions, or stability issues
- You need a structured analysis across multiple dimensions (security, observability, UX, cost, etc.)
- You want to track recurring issues across investigation sessions via memory

## Usage

```text
/investigate-app <kubectl-log-commands> [--jaeger <endpoint>] [--services <service-list>]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `kubectl-log-commands` | **Yes** | One or more kubectl commands to retrieve pod logs (e.g., `kubectl logs -n mynamespace deploy/myapp --since=1h`). Multiple commands can be separated by newlines or semicolons. |
| `--jaeger <endpoint>` | No | Jaeger UI endpoint for trace analysis (e.g., `localhost:16686`). If omitted, tracing analysis runs in log-only mode. |
| `--services <service-list>` | No | Comma-separated list of service names registered in Jaeger. If omitted, the skill discovers services from Jaeger's API. |

**Examples:**

```text
/investigate-app kubectl logs -n production deploy/api-server --since=2h \
  --jaeger localhost:16686 --services api-server,worker,gateway

/investigate-app kubectl logs -n default -l app=myapp --tail=5000

/investigate-app kubectl logs -n prod deploy/frontend --since=30m ; \
  kubectl logs -n prod deploy/backend --since=30m \
  --jaeger http://jaeger.monitoring:16686
```

---

## Workflow Overview

```text
┌───────────────────────────────────────────────────────────────────────┐
│                       INVESTIGATE-APP WORKFLOW                       │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐                                                     │
│  │  Phase 1:    │  Read AGENTS.md, parse arguments, understand        │
│  │  Setup &     │  the project architecture and conventions           │
│  │  Context     │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│  ┌──────▼───────┐                                                     │
│  │  Phase 2:    │  Execute kubectl commands, query Jaeger API,        │
│  │  Data        │  collect raw logs and trace data                    │
│  │  Collection  │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│  ┌──────▼───────┐                                                     │
│  │  Phase 3:    │  Recall known issues from memory to provide         │
│  │  Memory      │  context to sub-agents and detect recurrences       │
│  │  Recall      │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│  ┌──────▼──────────────────────────────────────────────┐              │
│  │  Phase 4: Parallel Analysis                         │              │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │              │
│  │  │  Bug   │ │ Perf   │ │Stable  │ │Tracing │       │              │
│  │  │& Error │ │& Rsrc  │ │& Rely  │ │Analysis│       │              │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │              │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │              │
│  │  │Logging │ │  UX &  │ │Token & │ │Security│       │              │
│  │  │& Obsrv │ │  API   │ │  Cost  │ │& Compl │       │              │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │              │
│  └──────┬──────────────────────────────────────────────┘              │
│         │                                                             │
│  ┌──────▼───────┐                                                     │
│  │  Phase 5:    │  Merge findings, deduplicate, cross-reference       │
│  │  Aggregation │  with memory for recurring issues                   │
│  │  & Dedup     │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│  ┌──────▼───────┐                                                     │
│  │  Phase 6:    │  Prioritized list of improvements with              │
│  │  Improvement │  effort estimates, grouped by theme                 │
│  │  Plan        │                                                     │
│  └──────┬───────┘                                                     │
│         │                                                             │
│  ┌──────▼───────┐                                                     │
│  │  Phase 7:    │  Store all findings and plan in memory              │
│  │  Memory      │  for future investigation sessions                  │
│  │  Persistence │                                                     │
│  └──────────────┘                                                     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Setup & Context

**Goal:** Understand the project, its architecture, and conventions before analyzing data.

### Step 1.1: Read Project Conventions

1. **Read `AGENTS.md`** (or equivalent project guidance file) in the repository root.
   - Understand the project's architecture, coding conventions, and best practices.
   - Note any specific logging, tracing, or observability conventions.
   - This file is the source of truth — follow its instructions throughout the investigation.

2. **Read `README.md`** for high-level project context.
   - Understand what the application does, its components, and service architecture.

3. **Check for existing observability configuration.**
   - Look for OpenTelemetry configuration files, logging libraries, Jaeger integration code.
   - Understand the project's intended observability posture.

### Step 1.2: Parse Arguments

1. **Extract kubectl commands** from the user input.
   - Validate that each command is a `kubectl logs` command.
   - Note the namespace, deployment/pod selectors, and time ranges.

2. **Extract Jaeger endpoint** (if provided).
   - Default to no Jaeger analysis if not provided.
   - Note the protocol (HTTP/HTTPS) and port.

3. **Extract service list** (if provided).
   - If not provided and Jaeger is available, plan to discover services from the Jaeger API.

### Step 1.3: Determine Applicable Perspectives

Not all 8 analysis perspectives may be relevant. Determine applicability:

| Perspective | When to include |
|-------------|----------------|
| Bug & Error Analysis | Always |
| Performance & Resource Optimization | Always |
| Stability & Reliability | Always |
| Distributed Tracing Analysis | Only when Jaeger endpoint is provided |
| Logging & Observability | Always |
| User Experience & API Quality | When the application serves user-facing APIs or UIs |
| Token & Cost Optimization | When the application integrates with LLM/AI APIs |
| Security & Compliance | Always |

If you cannot determine applicability from project context, include all perspectives
and let each sub-agent report "no findings" if the perspective does not apply.

---

## Phase 2: Data Collection

**Goal:** Gather raw log data and trace information for analysis.

### Step 2.1: Collect Pod Logs

1. **Execute each kubectl logs command** provided by the user.
2. **Capture the full output** of each command.
3. If the output is very large (>50,000 lines), consider:
   - Splitting into manageable chunks for sub-agents
   - Noting the total volume — excessive log volume is itself a finding
4. **Tag each log block** with its source (namespace/deployment/pod).

### Step 2.2: Collect Jaeger Traces (if endpoint provided)

1. **Query the Jaeger API** to discover available services:
   ```
   GET http://{jaeger-endpoint}/api/services
   ```

2. **For each service**, retrieve recent traces:
   ```
   GET http://{jaeger-endpoint}/api/traces?service={service-name}&limit=100&lookback=2h
   ```

3. **Retrieve the service dependency graph**:
   ```
   GET http://{jaeger-endpoint}/api/dependencies?endTs={now}&lookback=7200000
   ```

4. **Identify high-latency and error traces** for deeper inspection:
   - Sort traces by duration descending — collect the top-10 slowest
   - Filter for traces with error tags — collect up to 20 error traces

5. If the user provided a service list, **verify all listed services appear in Jaeger**.
   Missing services are an immediate finding for the Tracing Analysis perspective.

### Step 2.3: Summarize Collected Data

Before proceeding to analysis, produce a brief summary:

```text
## Data Collection Summary
- Log sources: {count} deployments across {count} namespaces
- Total log lines: {count}
- Time range: {earliest timestamp} to {latest timestamp}
- Jaeger: {available/not available}
- Services in Jaeger: {list or "N/A"}
- Error traces found: {count}
- Slowest trace duration: {duration or "N/A"}
```

---

## Phase 3: Memory Recall

**Goal:** Retrieve previously stored findings to provide context to sub-agents and detect recurring issues.

### Step 3.1: Search Memory for Prior Findings

Search memory for previous investigation results related to this project:

```text
Recall queries:
- "investigate-app findings {project-name}"
- "production bugs {project-name}"
- "performance issues {project-name}"
- "stability issues {project-name}"
- "tracing gaps {project-name}"
```

### Step 3.2: Compile Known Issues

From memory results, compile a structured list:

```text
## Known Issues from Previous Investigations
1. [{severity}] {title} — Found on {date}, status: {fixed/recurring/unresolved}
2. ...
```

If no prior findings exist, note: `"No prior investigation results found in memory."`

This list is passed to every sub-agent so they can flag recurrences.

---

## Phase 4: Parallel Analysis

**Goal:** Spawn specialist sub-agents, one per applicable perspective, to analyze the collected data concurrently.

### Step 4.1: Prepare Sub-Agent Prompts

For each applicable perspective, construct a task prompt using the **Sub-Agent Prompt Template**
defined in [analysis-perspectives.md](analysis-perspectives.md).

Each sub-agent receives:
1. Its complete perspective criteria (from analysis-perspectives.md)
2. The collected pod logs (all sources)
3. The collected Jaeger trace data (if available)
4. The known issues list from Phase 3
5. Project context from AGENTS.md

### Step 4.2: Spawn Sub-Agents

Spawn all applicable sub-agents in a single call so they run in parallel.
Use read-only sub-agents since they only analyze data, not modify code.

**Important considerations:**
- If sub-agent spawning is unavailable or fails, fall back to sequential in-context analysis using the same perspective criteria.
- Set appropriate timeouts — trace analysis may take longer than log-only analysis.
- Each sub-agent should return structured findings in the required output format.

### Step 4.3: Collect Results

Wait for all sub-agents to complete and collect their structured findings.

---

## Phase 5: Aggregation & Deduplication

**Goal:** Merge findings from all perspectives, remove duplicates, and cross-reference with memory.

### Step 5.1: Merge All Findings

Collect all findings from all sub-agents into a single list.

### Step 5.2: Deduplicate

When two or more perspectives flag the same underlying issue:
1. Keep the finding with the highest severity.
2. Note which perspectives identified it (increases confidence).
3. Merge the evidence from all perspectives into the surviving finding.

**Deduplication signals:**
- Same log line or trace span referenced by multiple perspectives
- Same root cause described in different terms
- Same recommended fix from different angles

### Step 5.3: Cross-Reference with Memory

For each finding, check against the known issues list from Phase 3:
- **Recurring issue**: Flag with `⚠️ RECURRING` — this was found before and may indicate the fix was incomplete or reverted.
- **New issue**: No prior record in memory.
- **Resolved issue**: Previously known issue that no longer appears — note as resolved.

### Step 5.4: Sort and Classify

Sort the deduplicated findings:

1. **By severity**: CRITICAL → HIGH → MEDIUM → LOW → INFO
2. **Within same severity**: recurring issues first (they need more attention)
3. **Group by theme**: bugs, performance, stability, observability, security, UX, cost

---

## Phase 6: Improvement Plan

**Goal:** Transform findings into a prioritized, actionable improvement plan.

### Step 6.1: Generate the Plan

For each finding (or group of related findings), create an improvement item:

```text
## Improvement Plan

### Priority 1: {theme} — {title}
**Severity**: {CRITICAL/HIGH/MEDIUM/LOW}
**Recurring**: {Yes — seen N times / No}
**Findings**: {list of finding IDs that contribute to this item}

**Problem:**
{concise description of the issue}

**Evidence:**
{key log lines, trace data, or metrics}

**Proposed fix:**
{specific, actionable steps to resolve — file paths, code changes, config changes}

**Effort estimate:** {small / medium / large}
**Risk if not fixed:** {description of impact if left unaddressed}

---
```

### Step 6.2: Prioritization Criteria

Order the improvement plan using this priority matrix:

| Priority | Criteria |
|----------|----------|
| P0 — Immediate | CRITICAL severity OR recurring CRITICAL/HIGH issues |
| P1 — This sprint | HIGH severity, non-recurring |
| P2 — Next sprint | MEDIUM severity with measurable impact |
| P3 — Backlog | LOW severity, nice-to-have improvements |
| P4 — Monitor | INFO-level observations, track but no action needed now |

### Step 6.3: Summary Statistics

End the plan with aggregate statistics:

```text
## Investigation Summary

| Metric | Value |
|--------|-------|
| Total findings | {count} |
| Critical | {count} |
| High | {count} |
| Medium | {count} |
| Low | {count} |
| Info | {count} |
| Recurring issues | {count} |
| New issues | {count} |
| Resolved issues (no longer seen) | {count} |
| Perspectives analyzed | {count} of 8 |
| Services covered | {list} |
| Time range analyzed | {range} |
```

---

## Phase 7: Memory Persistence

**Goal:** Store all findings and the improvement plan in memory for future investigation sessions.

### Step 7.1: Store Findings

For each finding at MEDIUM severity or above, store it in memory with:
- The finding title and severity
- The evidence (key log lines or trace data)
- The recommended fix
- The date of this investigation
- Whether it was a recurrence

### Step 7.2: Store the Improvement Plan

Store a summary of the improvement plan including:
- Total finding counts by severity
- The P0 and P1 items specifically
- Any recurring issues and their recurrence count

### Step 7.3: Update Resolved Issues

For any issues previously in memory that were NOT found in this investigation:
- Update their memory entry to note they appear resolved
- Include the date they were last seen and the date they were confirmed resolved

### Step 7.4: Store Investigation Metadata

Store a brief record of this investigation run:

```text
investigate-app run: {date}
Project: {project name}
Services analyzed: {list}
Time range: {range}
Findings: {critical}/{high}/{medium}/{low}/{info}
Recurring: {count}
New: {count}
```

---

## Guidelines

- **AGENTS.md is the authority.** Always read and follow the project's AGENTS.md file before starting analysis. It defines project-specific conventions and expectations.
- **Memory is essential.** Always check memory before analysis to avoid re-discovering known issues, and always write findings back to memory when done. This creates a historical record that makes each investigation more valuable than the last.
- **Evidence over opinion.** Every finding must include concrete evidence — exact log lines, trace span IDs, timestamps, or metrics. Never speculate without data.
- **Actionable fixes only.** Every finding must include a specific, implementable fix. "Needs improvement" is not a valid recommendation.
- **Severity must be earned.** Do not inflate severity. Use the criteria tables in each perspective strictly.
- **Respect production.** Do not execute commands that could affect production. This skill is read-only analysis — it collects logs and reads traces, nothing more.
- **Deduplication matters.** The same issue seen from multiple perspectives is one issue with high confidence, not multiple issues. Aggregate, do not multiply.
- **Recurring issues are priorities.** An issue that keeps appearing despite prior fixes deserves escalated attention and root cause investigation.
- **Context is king.** Log lines without context are noise. Always note the timestamp, pod, namespace, and surrounding context for every piece of evidence.
- **Volume is a signal.** If the application produces an excessive volume of logs, that is itself a finding. Excessive logging impacts performance and increases costs.
- **Tracing gaps are first-class findings.** Missing instrumentation makes future debugging harder. Treat observability gaps as seriously as bugs.
- **Do not hardcode commands.** The user provides the kubectl commands and Jaeger endpoint. Discover project-specific conventions from AGENTS.md or equivalent files. Do not assume specific CLI tools, make targets, or project structures.
