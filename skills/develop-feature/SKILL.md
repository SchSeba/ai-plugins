---
name: develop-feature
description: Execute a three-phase Plan -> Code -> Review workflow with iterative implementation until the review passes. Enforces production-readiness with extensive logging, comprehensive testing (unit + E2E), multi-agent code review, and build validation. Metrics and tracing are added when the project already has that infrastructure. Use when the user asks to build a feature, fix a bug, or make a structured change and wants planning, production-grade coding, and review in one workflow.
---

# Develop Feature

A three-phase development workflow: **Plan → Code → Review** with automated iteration until the review passes.

Every feature produced by this workflow MUST be **production-ready**: structured logging, comprehensive unit and E2E tests, and a clean build. Metrics and distributed tracing should be added when the project already has that infrastructure in place. No shortcuts.

## Usage

```text
/develop-feature <describe the feature, bug fix, or change you want>
```

## Arguments

- `$ARGUMENTS` - The feature request, bug description, or change specification.

---

## Workflow Overview

Execute these three phases in order. If the review phase requests changes, loop back to the coding phase with the review feedback, then re-review. Repeat until the review passes.

```text
+----------+     +----------+     +----------+
|   PLAN   | --> |   CODE   | --> |  REVIEW  |
+----------+     +----------+     +----------+
                      ^                |
                      |    changes     |
                      |   requested    |
                      +----------------+
```

---

## Phase 1: PLANNING

**Role:** You are a planning agent. You have READ-ONLY access. You do not modify any code in this phase.

**Goal:** Produce a detailed, actionable implementation plan that is self-contained and precise enough for the coding phase to execute without re-analyzing the codebase.

### Step 1.0: Read Project Guidelines (MANDATORY — Do This FIRST)

Before any analysis, read the project's best-practices and contribution guidelines:

1. **Read `AGENTS.md`** — This is the primary source of project conventions, architecture rules, and agent-specific instructions. If this file exists, its rules override any defaults in this skill.
2. **Read `CONTRIBUTING.md`** — Contribution workflow, PR format, commit conventions.
3. **Read `CLAUDE.md`** or equivalent — Additional AI-agent instructions the project maintainers have set.
4. **Read `Makefile` / build scripts** — Understand the build, test, and lint commands available.
5. **Read linting configs** — `.golangci.yml`, `.eslintrc`, `pyproject.toml`, `rustfmt.toml`, etc.

> **Rule:** If any of these files exist and contain instructions, you MUST follow them. Project-specific conventions always take precedence over the generic guidelines in this skill.

### Step 1.1: Gather Context

1. **Read the request thoroughly.**
   - Extract: the problem statement, acceptance criteria, constraints.
   - Search the web if additional context about libraries, APIs, or patterns is needed.

2. **Identify scope.**
   - What is in scope vs. out of scope?
   - Are there related or blocking concerns?

3. **Clarify ambiguities.**
   - List any requirements that are unclear or could be interpreted multiple ways.
   - For each, state your assumption and flag it as needing confirmation.

### Step 1.2: Codebase Scan

1. **Explore the project structure.**
   - Identify the programming language(s) and frameworks in use.
   - Note the directory layout and organizational patterns.

2. **Find project conventions.**
   - Cross-reference with the files read in Step 1.0.
   - Identify the existing logging library, metrics exporter, and tracing setup.
   - Note the test framework, test organization (unit vs. integration vs. E2E), and mock generation tools.

3. **Locate relevant existing code.**
   - Find the files most related to the task (models, services, handlers, tests).
   - Read them to understand existing patterns, naming conventions, and architecture.
   - Identify reusable utilities, helpers, or abstractions already in the codebase.

4. **Map dependencies and call chains.**
   - If the task touches a service, trace who calls it and what it calls.
   - If the task modifies an API endpoint, trace from handler → service → repository.
   - Note cross-component dependencies that may require coordinated changes.

### Step 1.3: Language-Specific Analysis

Based on the languages detected, perform the appropriate deep analysis.

#### Go Projects

- **Interfaces**: Identify interfaces to implement or extend. Check for mock generation patterns (`mockgen`, `mockery`, `testify/mock`). Note which interfaces need new mocks.
- **Error handling**: Check the project's error wrapping convention. Look for sentinel errors. Note the pattern used.
- **Testing patterns**: Find existing test files. Check for test helpers, table-driven tests. Note the testing library used (`testify`, stdlib, `gomega`).
- **Concurrency**: If applicable, identify existing concurrency patterns. Note potential race conditions.
- **Database/ORM**: Check model definitions, migration patterns, query conventions.
- **Observability**: Identify the logging library (`slog`, `zap`, `logrus`, `klog`), metrics library (`prometheus`, `otel`), and tracing setup (`opentelemetry`, `jaeger`). Note existing patterns for structured fields, metric names, and span naming.

#### Python Projects

- **Type hints**: Check the level of type hint usage. Note whether `mypy` or `pyright` is configured.
- **Async patterns**: Check for `asyncio`, `FastAPI`, `aiohttp`. Note sync vs. async conventions.
- **Testing**: Find `conftest.py` files, pytest fixtures, parametrize decorators.
- **Dependencies**: Check `pyproject.toml`, `requirements.txt`. Note the dependency management tool.
- **Framework patterns**: For Django, check MVT patterns. For FastAPI, check Pydantic models and dependency injection.
- **Observability**: Identify logging (`logging`, `structlog`, `loguru`), metrics (`prometheus_client`, `opentelemetry`), and tracing setup.

#### TypeScript / React Projects

- **Component patterns**: Functional components with hooks vs. class components. State management approach.
- **TypeScript config**: Read `tsconfig.json` for strict mode settings. Check for path aliases.
- **Testing**: Look for Jest/Vitest config, React Testing Library, Cypress/Playwright for E2E.
- **API client**: Check how the frontend communicates with the backend.
- **Observability**: Identify client-side logging, error tracking, and any browser tracing setup (e.g., Jaeger). Note whether tracing infrastructure exists — if it does not, skip tracing analysis.
- **Styling**: Check for Tailwind, CSS modules, styled-components.

#### Rust Projects

- **Crate structure**: Check `Cargo.toml` for workspace configuration, feature flags.
- **Error handling**: Check for `thiserror`, `anyhow`, custom error enums.
- **Testing**: Check for `#[cfg(test)]` modules, integration tests in `tests/`.
- **Unsafe code**: Note any `unsafe` blocks and their safety invariants.
- **Observability**: Check for `tracing` crate, `metrics` crate, structured logging setup.

### Step 1.4: Design the Implementation Plan

Produce a structured plan with the following sections.

#### Summary

One paragraph describing what will be implemented and why.

#### Architecture Decisions

If the task requires design choices, list each decision with:
- **Decision**: What you chose
- **Alternatives considered**: What else you considered
- **Rationale**: Why this approach wins

#### Files to Create or Modify

For each file, specify:
- **Path**: Exact file path
- **Action**: Create / Modify / Delete
- **Changes**: What specifically changes
- **Dependencies**: Which other files depend on this one

Order files by dependency.

#### Implementation Steps (Ordered)

Numbered, concrete steps. Each step should:
- Reference specific files and functions
- Be small enough to complete in one focused effort
- State its acceptance criterion
- Note dependencies on prior steps

#### Observability Plan

> **Logging is MANDATORY for every feature.** Metrics and tracing are only required if the project already has metrics/tracing infrastructure. If the project does not use metrics or tracing, skip those sub-sections.

##### Logging Plan

For each new code path, specify:
- **Log line description**: What event is being logged
- **Log level**: DEBUG / INFO / WARN / ERROR (see level guidelines in Phase 2)
- **Structured fields**: What key-value pairs to include (e.g., `resource_name`, `operation`, `duration_ms`, `error`)
- **Sensitive data check**: Confirm no passwords, tokens, PII, or secrets will be logged

##### Metrics Plan (only if the project already uses metrics)

> **Skip this section if the project has no existing metrics infrastructure.** Check for prometheus, otel-metrics, or similar in the codebase first.

For each new operation or resource, specify:
- **Metric name**: Following project naming conventions (e.g., `myservice_operation_total`, `myservice_operation_duration_seconds`)
- **Metric type**: Counter / Gauge / Histogram
- **Labels/dimensions**: What dimensions to track (e.g., `status`, `method`, `resource_type`)
- **What it measures**: Clear description of what this metric represents

##### Tracing Plan (only if the project already uses tracing)

> **Skip this section if the project has no existing tracing infrastructure.** Check for Jaeger, OpenTelemetry, or similar in the codebase first.

For each significant operation, specify:

- **Span name**: Following OpenTelemetry naming conventions (e.g., `ServiceName.OperationName`)
- **Span attributes**: What key-value pairs to attach (e.g., `resource.id`, `operation.type`)
- **Parent context**: Where the span context comes from (HTTP header, gRPC metadata, parent span)
- **Error recording**: How errors will be recorded on the span

#### Unit Test Plan

For each new or modified function, list specific test cases:
- **Test name**: Descriptive name following project conventions
- **Scenario**: What is being tested
- **Setup**: What data/mocks are needed
- **Assertion**: What the expected outcome is

Include edge cases: nil/empty inputs, zero values, boundary conditions, error paths, concurrent access.

> **Coverage rule:** Every new public function MUST have at least one test. Every error path MUST be tested. Aim for meaningful coverage of all new code paths.

#### E2E / Integration Test Plan

For cross-component or user-facing changes:
- **Test scenario**: End-to-end flow being validated
- **Components involved**: Which layers participate
- **Mocking strategy**: What external dependencies are mocked and how (HTTP mocks, DB test fixtures, fake implementations)
- **Setup**: Real DB? Mock HTTP? Test fixtures? Environment variables?
- **Assertions**: What must be true across component boundaries
- **Teardown**: How test state is cleaned up

> **Rule:** If the feature touches 2+ layers (handler → service → repository), an E2E or integration test is MANDATORY, not optional.

#### Acceptance Criteria

Checkable criteria derived from the request:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] ...

#### Risks and Open Questions

- Potential breaking changes
- Performance implications
- Security considerations
- Unclear requirements (with assumptions stated)

### Step 1.5: Save the Plan

Write the complete plan to:

```text
docs/plans/{feature-name}-plan.md
```

**Output:** Present the plan to the user before proceeding to the coding phase.

---

## Phase 2: CODING

**Role:** You are a staff-level coding agent. You write production-grade code, not prototypes.

**Goal:** Implement the plan from Phase 1 (or address review feedback if iterating). Every line of code you write must be ready for production: observable, tested, and clean.

### Critical Rules

1. **Follow the plan** from Phase 1. If no plan exists, analyze the task yourself.
2. **If iterating after a review**, your PRIMARY job is to address every item from the review feedback. You MUST fix ALL issues — not just the critical ones.
3. **Every new feature must include logging.** Metrics and tracing should be added only if the project already uses them.
4. **Add docstrings or equivalent function-level documentation** to every new function.
5. **Every new function must have tests** — both unit tests and E2E tests where applicable.

### Step 2.0: Read Project Guidelines (MANDATORY — Do This FIRST)

Before writing any code, re-read the project's best-practices files:

1. **Read `AGENTS.md`** — Follow all project-specific rules and conventions.
2. **Read `CONTRIBUTING.md`** and any other project guidelines.
3. **Read `Makefile`** — Know the exact build, test, and lint commands.

> **Rule:** Project-specific conventions from these files ALWAYS override the generic guidelines below. If `AGENTS.md` says "use `klog`", you use `klog` even if the guidelines below suggest `slog`.

### Step 2.1: Review Context

1. **Read the planning output** from Phase 1.
   - Follow the plan's ordering and architecture decisions.

2. **If iterating**, read the review feedback from the previous cycle.
   - Address every `CHANGES_REQUESTED` item. Do not skip any.
   - If a reviewer flagged a bug, write a test that reproduces it FIRST, then fix it.

### Step 2.2: Understand the Codebase

Before writing code:

1. **Read files you will modify.** Understand their current structure, imports, and conventions.
2. **Read adjacent files.** If modifying a service, also read its handler, repository, and tests.
3. **Check for project guidelines** (`AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `Makefile`).
4. **Match existing patterns.** Your code must look like it belongs in this codebase.
5. **Identify the existing observability setup.** Find how the project does logging, metrics, and tracing. Use the SAME libraries and patterns.

### Step 2.3: Implement with TDD (Red-Green-Refactor)

For each logical change:

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

When TDD is impractical (wiring code, configuration, UI layout), write the code first but add tests immediately after.

### Step 2.4: Language-Specific Best Practices

#### Go

**Error Handling**
- Wrap errors with context: `fmt.Errorf("service_name: operation: %w", err)`
- Never discard errors. Use sentinel errors for expected conditions.
- Use `errors.Is()` and `errors.As()` — never compare error strings.

**Interfaces**
- Keep interfaces small: 1–3 methods.
- Define interfaces where they are consumed, not where they are implemented.
- Accept interfaces, return structs.

**Concurrency**
- Use `errgroup` for concurrent operations that return errors.
- Always handle goroutine lifecycle — never fire-and-forget.
- Use `context.Context` for cancellation and timeouts.
- Protect shared state with `sync.Mutex` or `sync.RWMutex`.

**Testing**
- Table-driven tests with `t.Run()` for subtests.
- Use `t.Helper()` in test helper functions.
- Test error paths explicitly — not just happy paths.
- Test edge cases: nil inputs, empty slices, zero values, boundary conditions.

**Performance**
- Pre-allocate slices when size is known.
- Use `strings.Builder` for string concatenation in loops.
- Avoid unnecessary copying of large structs.

#### Python

**Type Hints**
- Annotate ALL function signatures. Avoid `Any` unless truly necessary.
- Use `TypedDict` for dictionary shapes, `Protocol` for structural typing.

**Error Handling**
- Use specific exception types — never bare `except:`.
- Use context managers for all resource management.

**Testing**
- Use `pytest` with fixtures. `@pytest.mark.parametrize` for data-driven tests.
- Test async code with `pytest-asyncio`.

**Frameworks**
- **FastAPI**: Pydantic models for validation. `Depends()` for DI.
- **Django**: Follow MVT. Use model managers for complex queries.

#### TypeScript / React

**Strict Typing**
- No `any`. Use `unknown` and narrow instead.
- Use discriminated unions for variant types.

**React Hooks**
- Correct dependency arrays. Cleanup in `useEffect`.
- Use `useCallback` and `useMemo` only when there's a measured performance benefit.

**Component Design**
- Single responsibility. Composition over prop drilling.
- Handle loading, error, and empty states.

**Accessibility**
- Semantic HTML. ARIA attributes. Keyboard navigation.

#### Rust

**Ownership and Borrowing**
- Prefer borrowing (`&T`) over cloning.
- Use `Cow<'_, str>` when a function may or may not need to allocate.

**Error Handling**
- `thiserror` for library errors. `anyhow` for application errors.
- Use the `?` operator for ergonomic error propagation.

### Step 2.5: Observability Implementation

> **Logging is MANDATORY for every feature.** Metrics and tracing should only be added if the project already has existing metrics/tracing infrastructure. If the project does not use metrics or tracing, skip sections 2.5.2 and 2.5.3 and focus on logging only.

#### 2.5.1: Structured Logging

Add log lines at appropriate levels throughout your new code. Follow the project's existing logging library and patterns.

**Log Level Guidelines:**

| Level | When to Use | Examples |
|-------|-------------|---------|
| **DEBUG** | Detailed internal flow for troubleshooting. High-volume, disabled in production by default. | Variable values, internal state transitions, detailed request/response payloads |
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

- **Log at entry and exit points** of significant operations:
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

Add metrics to track the health and performance of your new code. Follow the project's existing metrics library and naming conventions.


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

Add trace spans to your new code so operations can be followed across service boundaries. Follow the project's existing tracing setup (e.g., Jaeger, OpenTelemetry).

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

Apply to ALL code regardless of language.

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
- **N+1 Queries**: Never fetch related records in a loop.

#### Clean Architecture

- **Separation of Concerns**: Handler → Service → Repository. Don't skip layers.
- **Dependency Injection**: Pass dependencies as constructor parameters.
- **Single Responsibility**: Each function does one thing.
- **Don't Repeat Yourself**: But three similar lines is better than a premature abstraction.

#### Documentation

- **Docstrings**: Add docstrings or equivalent function-level documentation to every new function.
- **Comments**: Comments explain WHY, not WHAT. Only comment when the reason is non-obvious.

### Step 2.7: Comprehensive Testing (MANDATORY)

> **Untested code is incomplete code.** You MUST write both unit tests and E2E/integration tests for every new feature.

#### 2.7.1: Unit Tests

Every new or modified function MUST have unit tests. Follow these requirements:

**Test Structure:**
- **Table-driven tests** with descriptive subtests (e.g., `t.Run("returns error when input is nil", ...)`)
- **One test function per behavior**, not one monolithic test per function
- **Arrange-Act-Assert** pattern for clear test organization
- Use `t.Helper()` in Go test helpers, `@pytest.fixture` in Python

**What to Test:**
- ✅ Happy path — the expected normal behavior
- ✅ Error paths — every error return, every exception catch
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

**Test Quality Rules:**
- No `time.Sleep` in tests — use synchronization primitives or polling with timeout
- No shared mutable state between tests — each test sets up its own data
- Use `t.Cleanup()` / `t.TempDir()` in Go, `tmp_path` fixture in Python
- Tests must be deterministic — no flaky tests depending on timing or ordering

#### 2.7.2: E2E / Integration Tests

When the feature touches multiple components or layers, E2E tests are MANDATORY.

**When E2E Tests are Required:**
- Feature touches 2+ layers (handler → service → repository)
- Feature involves external service communication
- Feature adds a new API endpoint
- Feature changes data flow across component boundaries

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
- Observability: log messages were emitted, metrics were updated (when testable)

#### 2.7.3: Test Coverage Verification

After writing tests:
- Run the test suite and verify all new tests pass
- Check that every new public function has at least one test
- Check that every error path is tested
- Check that edge cases identified in the plan are covered

### Step 2.8: Build Validation (MANDATORY)

> **You MUST validate that the code compiles, passes lint, and passes tests before finishing.**

Run the project's build validation commands. **You MUST discover the correct commands** by reading `AGENTS.md`, `Makefile`, `package.json`, or `Cargo.toml` — do NOT assume any default commands. Look up the exact `make` targets for linting, testing, and building in the project's own documentation.

**Rules for Build Validation:**
1. **Fix ONLY issues in your own code.** Other coding agents may be working in parallel on other features. Do not modify files you didn't create or change.
2. **If lint fails**, fix the lint issues in your files only.
3. **If tests fail**, investigate whether the failure is in your new tests or existing tests:
   - Your new tests failing → Fix your code or tests.
   - Existing tests failing due to your changes → Fix your changes.
   - Existing tests failing independently → Note in your summary, do not fix.
4. **If build fails**, fix compilation/build errors in your files only.
5. **Iterate** — Run validation again after fixes. Repeat until clean.

### Step 2.9: Verify Your Work

Before finishing, perform a final verification:

1. **Read back every file you modified.** Check for:
   - Syntax errors or missing imports
   - Debug code that should be removed (`fmt.Println`, `console.log`, `print()`)
   - Hardcoded values that should be configurable
   - TODO/FIXME comments that should be resolved
   - Consistent formatting

2. **Observability checklist:**
   - [ ] Logging: Entry/exit log lines on all significant operations
   - [ ] Logging: Correct log levels (not everything at INFO)
   - [ ] Logging: Structured key-value fields, not string concatenation
   - [ ] Logging: No sensitive data logged (passwords, tokens, PII)

3. **Test coverage checklist:**
   - [ ] Every new public function has at least one unit test
   - [ ] Every error path is tested
   - [ ] Edge cases covered: nil/empty inputs, zero values, boundaries
   - [ ] E2E tests cover multi-layer flows
   - [ ] E2E tests mock external dependencies properly
   - [ ] No flaky tests (no `time.Sleep`, no order-dependence)

4. **Check cross-file consistency.** If you added a field to a struct, did you update all serialization? If you added an API endpoint, is it documented?

5. **Run build validation** — see Step 2.8 and Step 2.10.

### Step 2.10: Final Validation — Mock Generators, Linting, and Tests (MANDATORY)

> **This is the FINAL step before review.** You MUST run mock generators, linters, and tests before declaring your coding work complete. Use ONLY `make` commands — do not run tools manually.

**Procedure:**

1. **Read `AGENTS.md`** (or equivalent project guidelines) to find the exact `make` targets for:
   - Mock generation (if applicable)
   - Linting
   - Unit tests
   - Full build

2. **Run the commands in order:** Execute the `make` targets discovered from `AGENTS.md` / `Makefile` in this order: mock generation → linting → tests → build. Do NOT guess or assume target names — use exactly what the project specifies.

3. **Fix any failures** in your code ONLY:
   - If mock generation fails → update your interfaces or mock configuration
   - If linting fails → fix lint issues in YOUR files only
   - If tests fail → fix YOUR tests or YOUR code (not other agents' code)
   - If build fails → fix compilation errors in YOUR files only

4. **Re-run until clean.** Iterate the cycle until all commands pass without errors on YOUR code.

> **CRITICAL RULES:**
> - **ONLY use `make` commands.** Do not run `go test ./...`, `golangci-lint run`, `pytest`, or any tool directly. The `Makefile` is the single source of truth for how to run these tools.
> - **Check `AGENTS.md` first** for the correct make targets. Different projects use different target names.
> - **Fix ONLY your own code.** Other coding agents may be working in parallel. Do not modify files outside your feature scope.

---

## Phase 3: REVIEW

**Role:** You are a code review agent. You have READ-ONLY perspective — you identify issues but do not fix them yourself.

**Goal:** Thoroughly review the code changes from Phase 2 and either approve them or request specific changes.

### Step 3.0: Read Project Guidelines

Before reviewing, read `AGENTS.md` and other project convention files to ensure you review against the project's actual standards, not just generic best practices.

### Step 3.1: Spawn Multi-Agent Review

**You MUST spawn multiple specialized code review sub-agents** to review the changes in parallel. Do not perform all reviews in a single pass — parallel sub-agent review provides broader coverage and catches more issues.

Use the reusable review workflow in [../review-engine/SKILL.md](../review-engine/SKILL.md) and the perspective criteria in [../review-engine/review-perspectives.md](../review-engine/review-perspectives.md).

When running the review as part of `develop-feature`, pass the following context into the review:
- The original request
- The saved plan from `docs/plans/{feature-name}-plan.md`
- The full diff for the current iteration
- Prior review findings if this is iteration > 1

### Step 3.2: Review Verification Checklist

The review MUST verify ALL of the following:

#### Functional Correctness
- [ ] The changes solve the user's request
- [ ] The implementation follows the saved plan or clearly improves upon it
- [ ] Previous review findings were fully addressed (if iterating)
- [ ] Every finding includes a concrete code fix

#### Observability
- [ ] Structured logging at appropriate levels on all new code paths
- [ ] No sensitive data in log messages
- [ ] Metrics added for new operations (counters, histograms) *(if project uses metrics)*
- [ ] Tracing spans on significant operations with proper error recording *(if project uses tracing)*
- [ ] Context propagation maintained through the call chain *(if project uses tracing)*

#### Testing
- [ ] Unit tests exist for every new public function
- [ ] Error paths are tested, not just happy paths
- [ ] Edge cases covered (nil, empty, zero, boundary)
- [ ] E2E/integration tests exist for multi-layer changes
- [ ] Mocks properly simulate external dependencies
- [ ] No flaky test patterns (`time.Sleep`, shared state, ordering)

#### Build & Quality
- [ ] Build validation (lint, test, build) passes cleanly
- [ ] No debug artifacts left in code
- [ ] Documentation added for new public APIs/functions

---

## Iteration Loop

If the review verdict is `CHANGES_REQUESTED`:

1. Collect ALL findings from the review.
2. Go back to **Phase 2: CODING** with the review findings as input.
3. **The coder MUST fix ALL issues** found by the reviewers — critical, high, medium, AND low severity. Not just the critical ones.
4. After coding, run build validation again (lint, test, build).
5. Proceed to **Phase 3: REVIEW** again.
6. Repeat until the review verdict is `APPROVED`.

Maximum iterations: **3**. If still not approved after 3 iterations, present all remaining findings to the user and ask for guidance.

> **Rule:** Do NOT approve with known issues. If reviewers found real problems, fix them. The iteration loop exists for a reason.

---

## Guidelines

### Quality Standards
- **Production quality, not prototypes.** Write code you'd approve in a code review.
- **Every function has clear input/output contracts.** No hidden side effects.
- **Handle ALL error paths.** If something can fail, handle it.
- **Don't over-engineer.** Solve the actual problem. No speculative generality.

### Planning Standards
- **Thoroughness over speed.** A well-researched plan prevents wasted coding iterations.
- **Be specific about file paths.** Vague references are not actionable.
- **Always include observability and test plans.** These are not afterthoughts.

### Coding Standards
- **Match the codebase.** Your code must look like it belongs in this project.
- **Follow `AGENTS.md` and project conventions** — they override everything in this skill.
- **Add docstrings to every new function.**
- **Logging is mandatory.** Metrics and tracing should be added only if the project already uses them.
- **Comments explain WHY, not WHAT.** Only comment when the reason is non-obvious.
- **Tests are mandatory.** Both unit tests and E2E tests for multi-layer features.

### Review Standards
- **Focus on what matters.** Correctness, security, observability, testing, and code quality. Skip pure style nitpicks.
- **If changes look good, say APPROVED.** Do not manufacture issues.
- **Every review finding MUST have a fix.** Never flag without showing the resolution.
- **ALL review findings must be addressed** before approval. No "we'll fix it later."
