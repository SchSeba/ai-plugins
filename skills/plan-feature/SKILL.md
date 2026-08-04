---
name: plan-feature
description: Planning phase for feature development. Reads the codebase, gathers context, runs multi-subagent parallel investigation, performs language-specific analysis, and produces a detailed implementation plan. Standalone skill that outputs a plan document suitable as input for the develop-feature coding phase.
---

# Plan Feature

A standalone planning workflow that produces a detailed, actionable implementation plan for a feature, bug fix, or change specification.

This skill reads the codebase, gathers context, runs parallel subagent investigations, and outputs a structured plan document. The plan is designed to be self-contained and precise enough for a coding phase (e.g., the `develop-feature` skill) to execute without re-analyzing the codebase.

## Usage

```text
/plan-feature <describe the feature, bug fix, or change you want>
```

## Arguments

- `$ARGUMENTS` - The feature request, bug description, or change specification.

---

## Workflow Overview

Execute these steps in order. The output is a saved plan document and a user-facing summary.

```text
+------------------+     +------------------+     +------------------+
| GATHER CONTEXT   | --> | INVESTIGATE      | --> | DESIGN & PRESENT |
| (Steps 1.0-1.2)  |     | (Steps 1.3-1.4)  |     | (Steps 1.5-1.6)  |
+------------------+     +------------------+     +------------------+
```

---

## Phase 1: PLANNING

**Role:** You are a planning agent. You have READ-ONLY access. You do not modify any code in this phase.

**Goal:** Produce a detailed, actionable implementation plan that is self-contained and precise enough for the coding phase to execute without re-analyzing the codebase.

### Step 1.0: Read Project Guidelines (MANDATORY -- Do This FIRST)

Before any analysis, read the project's best-practices, contribution guidelines, and any previously learned knowledge:

1. **Read `.ai-rules/`** -- If the target project has an `.ai-rules/` directory, read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain previously learned knowledge about this project -- coding conventions, validation commands, and review patterns discovered during past sessions. **This is the highest-priority source** because it reflects confirmed, project-specific knowledge.
2. **Read `projects/<project-name>/`** -- If this plugin repository has a `projects/<project-name>/` directory (where `<project-name>` matches the target project's repo name), read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain knowledge shared across all skills in this plugin, discovered during past sessions with this project.
3. **Read `AGENTS.md`** -- This is the primary source of project conventions, architecture rules, and agent-specific instructions. If this file exists, its rules override any defaults in this skill.
4. **Read `CONTRIBUTING.md`** -- Contribution workflow, PR format, commit conventions.
5. **Read `CLAUDE.md`** or equivalent -- Additional AI-agent instructions the project maintainers have set.
6. **Read `Makefile` / build scripts** -- Understand the build, test, and lint commands available.
7. **Read linting configs** -- `.golangci.yml`, `.eslintrc`, `pyproject.toml`, `rustfmt.toml`, etc.

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
   - **Feature Completeness Gate -- Do NOT skip.** After listing ambiguities, evaluate the request against these criteria:
     - [ ] **Clear problem statement** -- The "what" and "why" are unambiguous.
     - [ ] **Acceptance criteria** -- There are concrete, testable conditions for "done".
     - [ ] **Entry point identified** -- The trigger is known (which API, endpoint, CLI command, controller, or component initiates the flow).
     - [ ] **Exit / success condition** -- What the end-to-end result looks like when the feature works correctly.
     - [ ] **Affected components named** -- All layers, services, or modules that will be touched are identified.
     - [ ] **No critical open questions** -- There are no ambiguities that would force a major re-plan mid-coding.
   - **If ALL criteria are met:** The description is complete -- proceed to Step 1.2 (Codebase Scan).
   - **If ANY criterion is NOT met:** The description has gaps. Invoke the `grill-me` skill to close them:
     1. **Read and follow** the grill-me skill at [../grill-me/SKILL.md](../grill-me/SKILL.md).
     2. **Focus the interview** on the missing criteria identified above. Tell the user which checklist items failed and why.
     3. **Use the grill-me workflow** (Steps 1-6) to conduct a structured interview with the user, one question at a time, until every gap is resolved.
     4. **After the grill session completes**, incorporate the decisions and answers into the feature description and re-evaluate the completeness checklist. All criteria must pass before proceeding.

   > **Rule:** Do not proceed to the Codebase Scan with known gaps in the feature description. An incomplete description leads to an incomplete plan, which leads to wasted coding iterations. It is faster to spend 5 minutes grilling than to re-plan after discovering a missing requirement mid-implementation.

### Step 1.2: Codebase Scan

> **CodeGraph-first rule:** If the CodeGraph MCP server is configured and available, prefer `codegraph_explore` for all codebase exploration -- it returns the relevant symbols' verbatim source, call paths, and blast radius in a single tool call, replacing slow grep/find/read loops. If CodeGraph is available but the project has no `.codegraph/` directory, run `codegraph init` in the project root first to build the initial graph. If CodeGraph is not available, **inform the user** and fall back to manual exploration below.

1. **Explore the project structure.**
   - If CodeGraph is available, use `codegraph_explore` to survey the project structure, entry points, and key modules.
   - Otherwise, identify the programming language(s) and frameworks in use manually.
   - Note the directory layout and organizational patterns.

2. **Find project conventions.**
   - Cross-reference with the files read in Step 1.0.
   - Identify the existing logging library, metrics exporter, and tracing setup.
   - Note the test framework, test organization (unit vs. integration vs. E2E), and mock generation tools.

3. **Locate relevant existing code.**
   - If CodeGraph is available, use `codegraph_explore` with a query describing what you need (e.g., "how does authentication work", "UserService and its callers"). Trust the returned source -- do not re-read files that CodeGraph already provided.
   - Otherwise, find the files most related to the task (models, services, handlers, tests) manually.
   - Identify reusable utilities, helpers, or abstractions already in the codebase.

4. **Map dependencies and call chains.**
   - If CodeGraph is available, use `codegraph_explore` to trace call paths and impact radius between symbols. This surfaces dynamic-dispatch hops that grep cannot follow.
   - Otherwise, manually trace who calls what:
     - If the task touches a service, trace who calls it and what it calls.
     - If the task modifies an API endpoint, trace from handler -> service -> repository.
   - Note cross-component dependencies that may require coordinated changes.

### Step 1.3: Multi-Subagent Parallel Investigation (MANDATORY)

Before designing the plan, you MUST spawn multiple specialized investigation sub-agents in parallel. Each agent investigates a specific dimension of the feature and reports back. This ensures the plan is grounded in the actual codebase conventions, not generic assumptions.

**Spawn these 4 sub-agents in parallel:**

#### Agent A -- Language Best Practices

Investigate the detected language(s) and report:
- **Error handling conventions**: How does this project wrap/propagate errors? Sentinel errors? Custom error types?
- **Naming conventions**: Variable, function, file naming patterns. Acronym casing.
- **Interface patterns**: How are interfaces defined and consumed? Where are mocks generated?
- **Framework-specific idioms**: What framework patterns does the project follow? What would be idiomatic for the new feature?
- **Code organization**: How are files structured within packages/modules?

#### Agent B -- Test Patterns

Investigate the existing test infrastructure and report:
- **Test framework**: Which testing libraries are used? (e.g., `testify`, `gomega`, `pytest`, `vitest`)
- **Test organization**: Where do test files live? How are they named?
- **Mock generation**: What mock library is used? How are mocks structured? Show example mock files.
- **Test helpers**: What shared test utilities, fixtures, or builders exist?
- **Coverage approach**: Is there a coverage threshold? What patterns do existing tests follow?
- **Example test files**: List 2-3 representative test files that the new tests should mirror.

#### Agent C -- Observability Patterns

Investigate the project's observability setup and report:
- **Logging library**: Which logger is used? (e.g., `slog`, `zap`, `klog`, `structlog`, `winston`)
- **Log levels in use**: What log levels appear in the codebase? Show example log calls.
- **Structured fields**: What key-value field names are standard? (e.g., `resource`, `operation`, `duration_ms`)
- **Metrics setup**: Is there a metrics library? What metric names and label conventions are used? If none, report "no metrics infrastructure."
- **Tracing setup**: Is there a tracing library? What span naming conventions are used? If none, report "no tracing infrastructure."

#### Agent D -- Architecture & Security

Investigate the project architecture and report:
- **Dependency injection patterns**: How are dependencies passed? Constructor injection? Globals?
- **Layer architecture**: How are layers separated? (handler -> service -> repository, etc.)
- **Data flow**: How does data move through the system for similar features?
- **Security patterns**: Auth middleware, input validation, RBAC patterns in use.
- **Where new code belongs**: Based on the feature request, recommend which packages/directories the new code should go in.

**After all 4 agents complete**, aggregate their findings into an **Investigation Summary** at the top of the plan (Step 1.6). This summary ensures the plan uses the project's actual conventions, not defaults.

### Step 1.4: Language-Specific Analysis

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
- **Observability**: Identify client-side logging, error tracking, and any browser tracing setup (e.g., Jaeger). Note whether tracing infrastructure exists -- if it does not, skip tracing analysis.
- **Styling**: Check for Tailwind, CSS modules, styled-components.

#### Rust Projects

- **Crate structure**: Check `Cargo.toml` for workspace configuration, feature flags.
- **Error handling**: Check for `thiserror`, `anyhow`, custom error enums.
- **Testing**: Check for `#[cfg(test)]` modules, integration tests in `tests/`.
- **Unsafe code**: Note any `unsafe` blocks and their safety invariants.
- **Observability**: Check for `tracing` crate, `metrics` crate, structured logging setup.

### Step 1.5: Design the Implementation Plan

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

> **Rule:** If the feature touches 2+ layers (handler -> service -> repository), an E2E or integration test is MANDATORY, not optional.

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

### Step 1.6: Save and Present the Plan

Write the complete plan to:

```text
docs/plans/{feature-name}-plan.md
```

**The plan MUST be structured in two parts:**

**Part 1: High-Level Summary** (1-3 paragraphs)
- What will be implemented and why
- Key architecture decisions
- Languages, frameworks, and patterns involved
- Investigation summary: aggregated findings from the 4 sub-agents (Step 1.3)
- Acceptance criteria

**Part 2: Deep Dive -- Per-File Changes**
- For each file to create or modify, provide:
  - Exact file path
  - Action (Create / Modify / Delete)
  - Detailed description of what changes (functions, types, imports, etc.)
  - Dependencies on other files
  - Logging, metrics, and tracing to add in this file
  - Tests that will validate this file's changes

**Output:** Present the full plan (Part 1 + Part 2) to the user.

### Step 1.7: User Approval Gate (MANDATORY -- HARD STOP)

> **FULL STOP.** You MUST NOT proceed to the coding phase without explicit user approval. This is a non-negotiable gate.

After presenting the plan:

1. **Ask the user to review and approve the plan.** Say: _"Please review the plan above. You can approve it to proceed to coding, or provide feedback for revisions."_
2. **Wait for the user's response.** Do NOT start writing implementation code.
3. **If the user provides feedback:**
   - Revise the plan based on the feedback.
   - Re-present the updated plan.
   - Wait for approval again.
   - Repeat this loop until the user explicitly approves.
4. **If the user approves:** The planning phase is complete. The plan document is ready for use by the coding phase (e.g., via the `develop-feature` skill).

> **Rule:** "Approval" means the user explicitly says to proceed (e.g., "looks good", "approved", "go ahead", "LGTM"). Silence or ambiguity is NOT approval -- ask again.

---

## Guidelines

### Planning Standards
- **Thoroughness over speed.** A well-researched plan prevents wasted coding iterations.
- **Be specific about file paths.** Vague references are not actionable.
- **Always include observability and test plans.** These are not afterthoughts.
- **The plan must be self-contained.** A coding agent should be able to execute the plan without re-analyzing the codebase.
