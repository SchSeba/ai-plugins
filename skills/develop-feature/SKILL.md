---
name: develop-feature
description: Implement an approved feature or bug-fix plan, iterate on multi-perspective review, and validate the result. Use when a plan is ready for coding, review, and validation.
---

# Develop Feature

A three-phase development workflow: **Code -> Review -> Validate** with automated iteration until the review passes. Requires an approved implementation plan as input.

Follow the project's production requirements. Choose tests and instrumentation for the behavior being changed and the failures its users or operators need to detect.

## Usage

```text
/develop-feature <describe the feature, bug fix, or change you want>
```

## Arguments

- `$ARGUMENTS` - The feature request, bug description, or change specification. An approved plan (from the `plan-feature` skill or a prior planning phase) should be available as input.

---

## Workflow Overview

Execute these three phases in order. The plan is an input dependency -- it must exist before this workflow begins. If the review phase requests changes, loop back to the coding phase with the review feedback, then re-review. After approval, verify that the final revision satisfies the project's applicable checks.

```text
                   +----------+     +----------+     +----------+
  [PLAN INPUT] --> |   CODE   | --> |  REVIEW  | --> | VALIDATE |
                   +----------+     +----------+     +----------+
                        ^                |
                        |    changes     |
                        |   requested    |
                        +----------------+
```

> **Plan dependency:** This workflow expects an approved implementation plan as input. The plan can come from:
>
> - The `plan-feature` skill (recommended for complex features)
> - An inline planning phase you performed before invoking this skill
> - A plan document at `docs/plans/{feature-name}-plan.md`
>
> If no plan exists, analyze the task yourself before coding -- but note that the `plan-feature` skill provides a more thorough planning process with multi-subagent investigation.

---

## Phase 2: CODING

Implement the approved plan. On a review iteration, verify the reported behavior on the current revision before changing code.

### Step 2.0: Read Project Guidelines (MANDATORY — Do This FIRST)

Read the current checkout's `AGENTS.md`, `CONTRIBUTING.md` and build configuration for the applicable project rules and validation targets. Consult `.ai-rules/` and the plugin's `projects/<project-name>/` for prior coding, review and validation lessons. Check that those lessons still apply to this revision. Follow the user's instructions and the project's current requirements.

### Step 2.1: Review Context

1. **Read the planning output** from the planning phase (or plan-feature skill).
   - Look for the plan document at `docs/plans/{feature-name}-plan.md`.
   - Follow the plan's ordering and architecture decisions.

2. **If iterating**, use the latest diff and the earlier review to locate the reported behavior. Trace a valid input through its caller and any guards. For a confirmed bug, reproduce the failure at the narrowest practical boundary. If the premise has changed or the input cannot reach that path, record the evidence for the reviewer.

### Step 2.2: Understand the Codebase

Read the files you will change, their callers and nearby tests. Use CodeGraph when available to follow symbols across packages. If the project has no usable index, follow the configured provider's setup instructions to initialize it. If the provider is unavailable, state that limitation and continue with direct source inspection. Match the project's conventions and reuse the existing entry points.

For changes to shared state, identify which producer owns each value, what is stored versus derived, and which readers must agree after update, retry, release or restart. Keep existing callers and persisted data in that analysis. Before mutating borrowed data, inspect the type's copy semantics at the project's dependency version, including any shared backing storage.

When iterating over unordered inputs can produce different outcomes, define which outcome takes precedence. For example, if a fatal input error must surface even when another item is merely ineligible, an early return on the first ineligible item can hide the error.

### Step 2.3: Implement with TDD (Red-Green-Refactor)

For a change in observable behavior, use an existing test when it already captures the contract. When adding a regression test:

1. **RED** — Write a failing test that describes the expected behavior.
   - Descriptive name explaining what's being tested
   - Minimal fixtures
   - Assert the expected outcome
   - Fail for the right reason (not a compile error)

2. **GREEN** — Write the minimum code to make the test pass. Do not optimize yet.

3. **REFACTOR** — Clean up while keeping tests green:
   - Extract duplicated logic
   - Improve naming
   - Simplify conditionals
   - But do NOT over-abstract

When a failing test is impractical before implementation, choose the closest check that exercises the change. For wiring, that may be an integration test through the real entry point.

### Step 2.4: Language-Specific Best Practices

#### Go

##### Error Handling

- Wrap errors with context: `fmt.Errorf("service_name: operation: %w", err)`
- Never discard errors. Use sentinel errors for expected conditions.
- Use `errors.Is()` and `errors.As()` — never compare error strings.

##### Interfaces

- Keep interfaces small: 1–3 methods.
- Define interfaces where they are consumed, not where they are implemented.
- Accept interfaces, return structs.

##### Concurrency

- Use `errgroup` for concurrent operations that return errors.
- Always handle goroutine lifecycle — never fire-and-forget.
- Use `context.Context` for cancellation and timeouts.
- Protect shared state with `sync.Mutex` or `sync.RWMutex`.

##### Testing

- Table-driven tests with `t.Run()` for subtests.
- Use `t.Helper()` in test helper functions.
- Test error paths explicitly — not just happy paths.
- Test edge cases: nil inputs, empty slices, zero values, boundary conditions.

##### Performance

- Pre-allocate slices when size is known.
- Use `strings.Builder` for string concatenation in loops.
- Avoid unnecessary copying of large structs.

#### Python

##### Type Hints

- Annotate ALL function signatures. Avoid `Any` unless truly necessary.
- Use `TypedDict` for dictionary shapes, `Protocol` for structural typing.

##### Error Handling

- Use specific exception types — never bare `except:`.
- Use context managers for all resource management.

##### Testing

- Use `pytest` with fixtures. `@pytest.mark.parametrize` for data-driven tests.
- Test async code with `pytest-asyncio`.

##### Frameworks

- **FastAPI**: Pydantic models for validation. `Depends()` for DI.
- **Django**: Follow MVT. Use model managers for complex queries.

#### TypeScript / React

##### Strict Typing

- No `any`. Use `unknown` and narrow instead.
- Use discriminated unions for variant types.

##### React Hooks

- Correct dependency arrays. Cleanup in `useEffect`.
- Use `useCallback` and `useMemo` only when there's a measured performance benefit.

##### Component Design

- Single responsibility. Composition over prop drilling.
- Handle loading, error, and empty states.

##### Accessibility

- Semantic HTML. ARIA attributes. Keyboard navigation.

#### Rust

##### Ownership and Borrowing

- Prefer borrowing (`&T`) over cloning.
- Use `Cow<'_, str>` when a function may or may not need to allocate.

##### Error Handling

- `thiserror` for library errors. `anyhow` for application errors.
- Use the `?` operator for ergonomic error propagation.

### Step 2.5: Observability Implementation

Use existing instrumentation where it answers the operational question. Add a signal when the new behavior creates a failure or transition an operator needs to observe. Use metrics and tracing where the project already supports them.

#### 2.5.1: Structured Logging

Log at the boundary that has the context to explain the event, using the project's library and levels. Check whether the caller already records the failure.

**Log Level Guidelines:**

| Level | When to Use | Examples |
|-------|-------------|---------|
| **DEBUG** | Detailed internal flow for troubleshooting. High-volume, disabled in production by default. | Sanitized diagnostic fields, internal state transitions |
| **INFO** | Significant business events and operational milestones. Always enabled. | Service started, request handled, resource created/updated/deleted, configuration loaded |
| **WARN** | Recoverable issues that deserve attention. May indicate a degraded state. | Retry attempt, deprecated API used, fallback triggered, approaching resource limit |
| **ERROR** | Unrecoverable failures that require investigation. Must not be noisy. | Operation failed after retries, external dependency unreachable, data corruption detected |

**Structured Logging Best Practices:**

- **Use structured key-value pairs**, not string concatenation or `fmt.Sprintf` for log fields:

  ```go
  // ✅ GOOD — structured fields
  logger.Info("resource created", "name", resource.Name, "namespace", resource.Namespace, "duration_ms", elapsed.Milliseconds())

  // ❌ BAD — string concatenation
  logger.Info(fmt.Sprintf("resource %s/%s created in %dms", resource.Namespace, resource.Name, elapsed.Milliseconds()))
  ```

- **Include contextual fields** that make debugging easier:
  - Request ID / Correlation ID
  - Resource name, namespace, kind
  - Operation name (create, update, delete, reconcile)
  - Duration for operations
  - Error details (wrapped, not just the message)
  - User/actor identity (when applicable)

- **NEVER log sensitive data:**
  - ❌ Passwords, tokens, API keys, secrets
  - ❌ PII (email addresses, SSNs, credit card numbers)
  - ❌ Full request/response bodies that may contain credentials
  - ✅ Log resource identifiers, operation types, and sanitized metadata

- **For a long-running operation**, start and completion events can help distinguish a stall from a slow success:

  ```go
  func (s *Service) ReconcileResource(ctx context.Context, name string) error {
      logger := s.logger.With("resource", name, "operation", "reconcile")
      logger.Debug("starting reconciliation")

      // ... operation ...

      if err != nil {
          logger.Error("reconciliation failed", "error", err, "duration_ms", elapsed.Milliseconds())
          return fmt.Errorf("reconcile %s: %w", name, err)
      }

      logger.Info("reconciliation completed", "duration_ms", elapsed.Milliseconds(), "changes_applied", changeCount)
      return nil
  }
  ```

#### 2.5.2: Metrics (only if the project already uses metrics)

> **Skip this section if the project has no existing metrics infrastructure.** Check the codebase first for prometheus, otel-metrics, or similar libraries. If none exist, do not add metrics.

Choose a metric when the feature needs a health or performance signal. Follow the project's existing metrics library and naming conventions.

**Metric Types and When to Use Them:**

| Type | When to Use | Naming Convention | Example |
|------|-------------|-------------------|---------|
| **Counter** | Monotonically increasing count of events | `<service>_<operation>_total` | `myservice_requests_total{method="GET", status="200"}` |
| **Gauge** | Current value that can go up or down | `<service>_<resource>_current` | `myservice_active_connections_current` |
| **Histogram** | Distribution of values (latencies, sizes) | `<service>_<operation>_duration_seconds` | `myservice_request_duration_seconds{method="GET"}` |

**Follow the RED Method** for service-level metrics:

- **R**ate — How many requests per second? → Counter
- **E**rrors — How many of those requests fail? → Counter with error label
- **D**uration — How long do requests take? → Histogram

**Metrics Best Practices:**

- Register metrics at initialization, not per-request
- Use consistent label names across all metrics
- Keep cardinality low — do not use unbounded label values (e.g., user IDs, request paths with parameters)
- Add a `status` or `result` label to distinguish success/failure
- Include `_total` suffix for counters, `_seconds` for duration histograms

#### 2.5.3: Distributed Tracing (only if the project already uses tracing)

> **Skip this section if the project has no existing tracing infrastructure.** Check the codebase first for Jaeger, OpenTelemetry, or similar. If none exist, do not add tracing.

Add a span when an operation needs to be followed across service boundaries. Follow the project's existing tracing setup (e.g., Jaeger, OpenTelemetry).

**Tracing Best Practices:**

- **Create spans for significant operations** — not every function, but every meaningful unit of work:

  ```go
  func (s *Service) ProcessItem(ctx context.Context, itemID string) error {
      ctx, span := s.tracer.Start(ctx, "Service.ProcessItem",
          trace.WithAttributes(
              attribute.String("item.id", itemID),
          ),
      )
      defer span.End()

      // ... operation ...

      if err != nil {
          span.RecordError(err)
          span.SetStatus(codes.Error, err.Error())
          return err
      }

      span.SetAttributes(attribute.Int("items.processed", count))
      return nil
  }
  ```

- **Propagate context** — Always pass `ctx` through the call chain. Never create a new background context mid-operation.
- **Name spans clearly** — Use `ServiceName.OperationName` format (e.g., `ResourceController.Reconcile`, `DBClient.Query`).
- **Record errors on spans** — Use `span.RecordError(err)` and `span.SetStatus(codes.Error, ...)` for failures.
- **Add relevant attributes** — Resource identifiers, operation type, batch size, but NOT sensitive data.
- **Link child spans** — When an operation triggers sub-operations, they should be child spans of the parent.

### Step 2.6: Cross-Cutting Concerns

Use the considerations that apply to the changed path and its contract.

#### Security (OWASP Top 10)

- **Injection**: Parameterize all database queries. Never concatenate user input.
- **Broken Auth**: Verify auth on every endpoint.
- **Sensitive Data**: Never log credentials, tokens, API keys, or PII.
- **XSS**: Sanitize all user-generated content before rendering.
- **Insecure Deserialization**: Validate all deserialized input.

#### Performance

- **Timeouts**: Add timeouts to ALL external calls.
- **Connection Pooling**: Reuse HTTP clients and database connections.
- **Pagination**: All list endpoints MUST support pagination.
- **Repeated work**: Estimate cost from both data size and call frequency. In a per-candidate loop, a scan of all records multiplies by the candidate count. For optional features, check the disabled and enabled-but-unused paths before adding a cache or index. Measure if the trade-off is unclear.

#### Clean Architecture

- **Separation of Concerns**: Handler → Service → Repository. Don't skip layers.
- **Dependency Injection**: Pass dependencies as constructor parameters.
- **Single Responsibility**: Each function does one thing.
- **Don't Repeat Yourself**: But three similar lines is better than a premature abstraction.

#### Documentation

- **Docstrings**: Follow repository requirements for public interfaces. Document contracts a caller could otherwise misread, such as ownership, units, missing values or failure behavior.
- **Comments**: Comments explain WHY, not WHAT. Only comment when the reason is non-obvious.

### Step 2.7: Test the Changed Behavior

Choose the lowest test level that distinguishes the new behavior from the previous one. Extend the existing harness if it already varies relevant configurations. Retain baseline expectations for supported modes, including existing data when a feature is disabled.

#### 2.7.1: Unit Tests

**Test Structure:**

- **Table-driven tests** with descriptive subtests (e.g., `t.Run("returns error when input is nil", ...)`)
- Group cases by behavior with names that identify the scenario
- **Arrange-Act-Assert** pattern for clear test organization
- Use `t.Helper()` in Go test helpers, `@pytest.fixture` in Python

**What to Test:**

- ✅ Happy path — the expected normal behavior
- ✅ Error paths — failures that change the caller-visible outcome
- ✅ Edge cases — nil/null inputs, empty slices/lists, zero values, boundary conditions
- ✅ Concurrent access — if the code uses goroutines, locks, or shared state
- ✅ Input validation — invalid inputs, malformed data, missing required fields

**Mocking:**

- Mock external dependencies (HTTP clients, databases, file systems)
- Use the project's existing mock generation tool. Popular choices by language:
  - **Go**: `mockgen`, `mockery`, `testify/mock`
  - **Python**: `pytest-mock`, `unittest.mock`
  - **Frontend (JS/TS)**: `jest.mock`, `vitest`, `sinon`
  - **Rust**: `mockall`
- Mocks must match real interface behavior — never skip error cases in mocks
- Verify mock interactions when the side effect IS the behavior (e.g., "ensure the cache was invalidated")
- When fixtures must reconstruct production state, reuse the production state builder where available. Specify expected results independently from the implementation being tested.
- Compare the complete result promised by the contract, including fields expected to be absent. Mask only genuinely variable details, such as generated IDs, and check their required properties separately.

**Test Quality Rules:**

- No `time.Sleep` in tests — use synchronization primitives or polling with timeout
- No shared mutable state between tests — each test sets up its own data
- Use `t.Cleanup()` / `t.TempDir()` in Go, `tmp_path` fixture in Python
- Tests must be deterministic — no flaky tests depending on timing or ordering

#### 2.7.2: E2E / Integration Tests

Use an integration test when the behavior depends on how components exchange data, preserve state, or recover from failure. Use an end-to-end test when the user-visible outcome requires the full stack and existing coverage cannot establish it.

**E2E Test Structure:**

- Set up the full component chain (or as much as practical)
- Mock ONLY external dependencies outside your system boundary (third-party APIs, cloud services)
- Use real implementations for internal components when possible
- Test the full request/response cycle

**Mocking Strategy for E2E Tests:**

- **HTTP mocks**: Use `httptest.NewServer` (Go), `responses` / `aioresponses` (Python), `msw` (TypeScript)
- **Database mocks**: Use test databases, in-memory SQLite, or transaction rollback patterns
- **Message queue mocks**: Use in-memory implementations or test containers
- **File system mocks**: Use `t.TempDir()` (Go), `tmp_path` (Python)

**What to Assert in E2E Tests:**

- The full operation completes successfully
- Side effects occurred (data written, events emitted, caches updated)
- Error responses have correct status codes and messages
- When a scenario should be blocked, keep other prerequisites satisfiable and assert the decision the component owns. Where recovery matters, remove the blocking condition and verify progress.

### Step 2.8: Validate the Change

Discover the applicable formatting, generation, lint, test and build commands from the current project's instructions, build files and CI. Use local `.ai-rules/VALIDATION.md` and the plugin's `projects/<project-name>/VALIDATION.md` as starting points. Confirm recorded commands still match the checkout.

Use focused checks while iterating. Regenerate affected mocks or generated outputs using the project's workflow, inspect their diff, and run the matching verifiers. For an unexpected failure, compare with the base revision under the same inputs and configuration when practical. Fix failures caused by the change and report unrelated or unverified failures with the evidence.

### Step 2.9: Inspect the Complete Diff

Read the diff before requesting review. Check dependent serializers, comparisons, public documentation, interface implementations and mocks where their contract changed. Look for debug code, unrelated edits and formatting changes. After a rebase, compare against the new base and the pre-rebase change to catch lost upstream behavior, displaced tests or a reintroduced duplicate implementation. Recheck the affected paths.

Record the checks run, what they establish and any gaps for the reviewer.

### Step 2.10: Persist Verified Project Knowledge

When the task yields a reusable lesson, use the two knowledge layers below within the authorized repositories. Record the specific contract or decision and its supporting code, test, or accepted resolution on the relevant revision. An early proposal, an outdated thread, or a resolution flag alone is insufficient evidence of a defect.

Both layers use the same three-file structure:

- **`CODING.md`** — Best practices learned during this task: patterns from PR review comments, CI investigation findings, coding conventions discovered, pitfalls to avoid.
- **`VALIDATION.md`** — Exact validation and build commands that mirror CI. Include formatting, vetting/type-checking, linting, testing, and building commands — the goal is to run the same validations CI runs locally, so issues are caught before pushing.
- **`REVIEWING.md`** — Review patterns and insights: what kinds of issues reviewers catch, preferred fix approaches, coding standards enforced during review, common reviewer expectations for this project.

#### Layer 1: Target project's `.ai-rules/` directory

Write to `.ai-rules/CODING.md`, `.ai-rules/VALIDATION.md`, and `.ai-rules/REVIEWING.md` inside the target project's own repository.

This captures knowledge that lives alongside the project code. Since the `.ai-rules/` folder is inside the target project repo itself, no `<project-name>` subdirectory is needed — the project identity is implicit from the repo.

#### Layer 2: Plugin repo's `projects/<project-name>/` directory

Write to `projects/<project-name>/CODING.md`, `projects/<project-name>/VALIDATION.md`, and `projects/<project-name>/REVIEWING.md` in this plugin repository (the repo where this skill lives).

This captures knowledge shared across ALL skills in this plugin repo. Any skill can read from `projects/<project-name>/` to benefit from knowledge discovered by other skills. For example, validation commands discovered by `develop-feature` are also available to `pr-comment-resolver` and `code-review`.

#### What to persist

**In `VALIDATION.md`:**

- Every `make` target (or equivalent task runner command) discovered for: formatting, vetting, linting, testing, building, mock generation.
- The correct order to run them.
- Any targets that require special flags, environment variables, or build tags (e.g., `-tags sqlite_fts5`).
- Any CI-only validations that cannot be run locally (e.g., tests requiring live infrastructure) — note these as "CI-only, skip locally".

**In `CODING.md`:**

- Coding conventions learned from PR review feedback (e.g., "use structured logging, not fmt.Println").
- Architecture patterns specific to this project (e.g., "all new handlers must implement the Middleware interface").
- CI investigation findings (e.g., "npm audit in web-lint can cause flaky failures due to new CVEs").
- Common pitfalls (e.g., "the vendor directory is NOT tracked in git — do not commit vendor/ files").
- Reviewer preferences with their scope and rationale when the project adopted them.

**In `REVIEWING.md`:**

- What kinds of issues reviewers consistently catch for this project.
- Preferred fix approaches (e.g., "reviewers prefer `errors.Wrap` over `fmt.Errorf` for wrapping").
- Coding standards enforced during review (e.g., "all public functions must have godoc comments").
- Common reviewer expectations and patterns (e.g., "reviewers check for proper RBAC annotations on new controllers").

#### Persistence rules

1. **Append, don't replace.** If `CODING.md`, `VALIDATION.md`, or `REVIEWING.md` already exists, read it first and append new knowledge. Do not overwrite previously learned content.
2. **Deduplicate.** If the new knowledge is already captured, skip it.
3. **Create directories** if they don't exist (`.ai-rules/` in the target project, `projects/<project-name>/` in this plugin repo).
4. **Verify before recording.** Record which commands passed on this revision and identify CI-only checks separately.
5. **Include a timestamp header** for each entry so it's clear when the knowledge was captured.

---

## Phase 3: REVIEW

**Role:** You are a code review agent. You have READ-ONLY perspective — you identify issues but do not fix them yourself.

**Goal:** Thoroughly review the code changes from Phase 2 and either approve them or request specific changes.

Use the [shared review engine](../review-engine/SKILL.md) for reviewer selection, independent perspectives, aggregation and the verdict. Supply the request, approved plan, current base and change set, applicable project guidance, validation results and prior findings. The review should check whether the evidence covers the acceptance criteria through real callers.

### Iteration Loop

For `CHANGES_REQUESTED`, fix the verified blocking findings and unmet acceptance criteria. Handle in-scope suggestions as appropriate and explain disagreements or deferrals with current code or tests. Run the checks affected by the edits and send the updated diff through review. If blockers remain after three iterations, report them to the user with the remaining decision or evidence needed.

---

## Phase 4: FINAL VALIDATION

After approval, check the validation results against the final revision. Run outstanding project-required checks, including the full suite when required. Rerun checks invalidated by implementation, generated output, dependency or base changes. Reuse passing results for unchanged inputs.

Report the commands and their results, which behaviors were covered, and any required checks still blocked or pending in CI. Fix regressions within scope and return substantive fixes to review. Declare the change complete when the acceptance criteria and applicable checks are satisfied.

---

## Guidelines

### Quality Standards

- **Production quality, not prototypes.** Write code you'd approve in a code review.
- **Every function has clear input/output contracts.** No hidden side effects.
- **Handle ALL error paths.** If something can fail, handle it.
- **Don't over-engineer.** Solve the actual problem. No speculative generality.

### Planning and Coding Standards

- Use the approved plan, project rules and nearby implementation as the reference for scope and conventions.
- Test the contract at the boundary where a regression would be observable. Document non-obvious behavior and use instrumentation where it aids diagnosis.

### Review Standards

- Apply the shared review engine's evidence, severity and verdict criteria.
- Carry actionable findings into the next iteration and report residual risks accurately.
