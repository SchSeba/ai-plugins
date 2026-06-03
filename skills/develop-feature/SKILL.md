---
name: develop-feature
description: Execute a three-phase Plan -> Code -> Review workflow with iterative implementation until the review passes. Use when the user asks to build a feature, fix a bug, or make a structured change and wants planning, production-grade coding, and review in one workflow.
---

# Develop Feature

A three-phase development workflow: **Plan -> Code -> Review** with automated iteration until the review passes.

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
   - Read `CLAUDE.md`, `CONTRIBUTING.md`, `.editorconfig`, or similar files.
   - Check for linting configs (`.golangci.yml`, `.eslintrc`, `pyproject.toml`, `rustfmt.toml`).
   - Read the `Makefile` or build scripts to understand the build/test/lint workflow.

3. **Locate relevant existing code.**
   - Find the files most related to the task (models, services, handlers, tests).
   - Read them to understand existing patterns, naming conventions, and architecture.
   - Identify reusable utilities, helpers, or abstractions already in the codebase.

4. **Map dependencies and call chains.**
   - If the task touches a service, trace who calls it and what it calls.
   - If the task modifies an API endpoint, trace from handler -> service -> repository.
   - Note cross-component dependencies that may require coordinated changes.

### Step 1.3: Language-Specific Analysis

Based on the languages detected, perform the appropriate deep analysis.

#### Go Projects

- **Interfaces**: Identify interfaces to implement or extend. Check for mock generation patterns. Note which interfaces need new mocks.
- **Error handling**: Check the project's error wrapping convention. Look for sentinel errors. Note the pattern used.
- **Testing patterns**: Find existing test files. Check for test helpers, table-driven tests. Note the testing library used.
- **Concurrency**: If applicable, identify existing concurrency patterns. Note potential race conditions.
- **Database/ORM**: Check model definitions, migration patterns, query conventions.

#### Python Projects

- **Type hints**: Check the level of type hint usage. Note whether `mypy` or `pyright` is configured.
- **Async patterns**: Check for `asyncio`, `FastAPI`, `aiohttp`. Note sync vs. async conventions.
- **Testing**: Find `conftest.py` files, pytest fixtures, parametrize decorators.
- **Dependencies**: Check `pyproject.toml`, `requirements.txt`. Note the dependency management tool.
- **Framework patterns**: For Django, check MVT patterns. For FastAPI, check Pydantic models and dependency injection.

#### TypeScript / React Projects

- **Component patterns**: Functional components with hooks vs. class components. State management approach.
- **TypeScript config**: Read `tsconfig.json` for strict mode settings. Check for path aliases.
- **Testing**: Look for Jest/Vitest config, React Testing Library, Cypress/Playwright for E2E.
- **API client**: Check how the frontend communicates with the backend.
- **Styling**: Check for Tailwind, CSS modules, styled-components.

#### Rust Projects

- **Crate structure**: Check `Cargo.toml` for workspace configuration, feature flags.
- **Error handling**: Check for `thiserror`, `anyhow`, custom error enums.
- **Testing**: Check for `#[cfg(test)]` modules, integration tests in `tests/`.
- **Unsafe code**: Note any `unsafe` blocks and their safety invariants.

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

#### Unit Test Plan

For each new or modified function, list specific test cases:
- **Test name**: Descriptive name following project conventions
- **Scenario**: What is being tested
- **Setup**: What data/mocks are needed
- **Assertion**: What the expected outcome is

Include edge cases: nil/empty inputs, zero values, boundary conditions, error paths, concurrent access.

#### Integration / E2E Test Plan

For cross-component changes:
- **Test scenario**: End-to-end flow being validated
- **Components involved**: Which layers participate
- **Setup**: Real DB? Mock HTTP? Test fixtures?
- **Assertions**: What must be true across component boundaries

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

**Goal:** Implement the plan from Phase 1 (or address review feedback if iterating).

### Critical Rules

1. **Follow the plan** from Phase 1. If no plan exists, analyze the task yourself.
2. **If iterating after a review**, your PRIMARY job is to address every item from the review feedback.
3. **Add docstrings or equivalent function-level documentation** to every new function.

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
3. **Check for project guidelines** (`CLAUDE.md`, `CONTRIBUTING.md`, `Makefile`).
4. **Match existing patterns.** Your code must look like it belongs in this codebase.

### Step 2.3: Implement with TDD (Red-Green-Refactor)

For each logical change:

1. **RED** - Write a failing test that describes the expected behavior.
   - Descriptive name explaining what's being tested
   - Minimal fixtures
   - Assert the expected outcome
   - Fail for the right reason (not a compile error)

2. **GREEN** - Write the minimum code to make the test pass. Do not optimize yet.

3. **REFACTOR** - Clean up while keeping tests green:
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
- Use `errors.Is()` and `errors.As()` - never compare error strings.

**Interfaces**
- Keep interfaces small: 1-3 methods.
- Define interfaces where they are consumed, not where they are implemented.
- Accept interfaces, return structs.

**Concurrency**
- Use `errgroup` for concurrent operations that return errors.
- Always handle goroutine lifecycle - never fire-and-forget.
- Use `context.Context` for cancellation and timeouts.
- Protect shared state with `sync.Mutex` or `sync.RWMutex`.

**Testing**
- Table-driven tests with `t.Run()` for subtests.
- Use `t.Helper()` in test helper functions.
- Test error paths explicitly - not just happy paths.
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
- Use specific exception types - never bare `except:`.
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

### Step 2.5: Cross-Cutting Concerns

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

- **Separation of Concerns**: Handler -> Service -> Repository. Don't skip layers.
- **Dependency Injection**: Pass dependencies as constructor parameters.
- **Single Responsibility**: Each function does one thing.
- **Don't Repeat Yourself**: But three similar lines is better than a premature abstraction.

#### Documentation

- **Docstrings**: Add docstrings or equivalent function-level documentation to every new function.
- **Comments**: Comments explain WHY, not WHAT. Only comment when the reason is non-obvious.

### Step 2.6: Verify Your Work

Before finishing:

1. **Read back every file you modified.** Check for:
   - Syntax errors or missing imports
   - Debug code that should be removed
   - Hardcoded values that should be configurable
   - TODO/FIXME comments that should be resolved
   - Consistent formatting

2. **Check test coverage.** Every new function should have at least one test. Every error path should be tested.

3. **Verify cross-file consistency.** If you added a field to a struct, did you update all serialization?

4. **Run available linting/checking commands** if the project has them (for example, `make lint`, `make test`).

---

## Phase 3: REVIEW

**Role:** You are a code review agent. You have READ-ONLY perspective - you identify issues but do not fix them yourself.

**Goal:** Thoroughly review the code changes from Phase 2 and either approve them or request specific changes.

### Shared Review Workflow

Use the reusable review workflow in [../review-engine/SKILL.md](../review-engine/SKILL.md) and the perspective criteria in [../review-engine/review-perspectives.md](../review-engine/review-perspectives.md).

When running the review as part of `develop-feature`, pass the following context into the review:
- the original request
- the saved plan from `docs/plans/{feature-name}-plan.md`
- the full diff for the current iteration
- prior review findings if this is iteration > 1

The review MUST verify:
1. The changes solve the user's request.
2. The implementation follows the saved plan or clearly improves upon it.
3. Previous review findings were fully addressed before approving the change.
4. Every finding includes a concrete code fix.

---

## Iteration Loop

If the review verdict is `CHANGES_REQUESTED`:

1. Collect all findings from the review.
2. Go back to **Phase 2: CODING** with the review findings as input.
3. The coder MUST address every critical and high finding. Medium findings should be addressed if reasonable.
4. After coding, proceed to **Phase 3: REVIEW** again.
5. Repeat until the review verdict is `APPROVED`.

Maximum iterations: **3**. If still not approved after 3 iterations, present all remaining findings to the user and ask for guidance.

---

## Guidelines

- **Thoroughness over speed.** A well-researched plan prevents wasted coding iterations.
- **Production quality, not prototypes.** Write code you'd approve in a code review.
- **Be specific about file paths.** Vague references are not actionable.
- **Always include test plans.** Untested code is incomplete code.
- **Respect existing patterns.** New code should follow conventions already in the codebase.
- **Every function has clear input/output contracts.** No hidden side effects.
- **Add docstrings to every new function.**
- **Comments explain WHY, not WHAT.** Only comment when the reason is non-obvious.
- **Handle ALL error paths.** If something can fail, handle it.
- **Don't over-engineer.** Solve the actual problem. No speculative generality.
- **Focus on what matters in review.** Correctness, security, testing, and code quality. Skip pure style nitpicks.
- **If changes look good, say APPROVED.** Do not manufacture issues.
- **Every review finding MUST have a fix.** Never flag without showing the resolution.
