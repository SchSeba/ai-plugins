---
name: code-refactor
description: Refactor and improve code quality across an entire project using parallel specialized sub-agents. Covers Go, TypeScript/React, Python, Rust, Database, Shell/Build, K8s/Config, and Observability domains with a safety-first iterative approach. Use when the user wants to improve code quality, readability, maintainability, or modernize a codebase without breaking functionality.
---

# Code Refactor

A four-phase refactoring workflow: **Analyze → Plan → Refactor → Verify** with iterative sub-agent execution until the entire project is covered.

## Usage

```text
/code-refactor <describe what to refactor, or "full project" for comprehensive coverage>
```

## Arguments

- `$ARGUMENTS` - The refactoring scope, target area, or "full project" for end-to-end coverage. Optional flags the user may include:
  - Specific directories or packages to focus on
  - Technology domains to prioritize
  - Refactoring goals (e.g., "add dependency injection", "improve test coverage", "add observability")

---

## Workflow Overview

Execute these four phases in order. After the Verify phase, loop back to Refactor for the next chunk of work. Repeat until the entire project is covered or the user's specified scope is complete.

```text
+-----------+     +--------+     +-----------+     +----------+
|  ANALYZE  | --> |  PLAN  | --> |  REFACTOR | --> |  VERIFY  |
+-----------+     +--------+     +-----------+     +----------+
                                      ^                 |
                                      |   next chunk    |
                                      |   or fixes      |
                                      +-----------------+
```

---

## Phase 1: ANALYZE (Read-Only)

**Role:** You are an analysis agent. You have READ-ONLY access. You do not modify any code in this phase.

**Goal:** Understand the project structure, tech stack, existing patterns, and identify all refactoring targets across the entire codebase.

### Step 1.1: Project Discovery

1. **Read project documentation.**
   - Look for `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `CLAUDE.md`, or equivalent files.
   - Understand the project's purpose, architecture, and team conventions.

2. **Discover build and test commands.**
   - Read `Makefile`, `package.json` scripts, `Cargo.toml`, `pyproject.toml`, or equivalent build configuration.
   - Identify the exact commands for: build, test, lint, format, and any other verification steps.
   - **Do NOT assume commands.** Always read them from project files. Do not hardcode or guess.

3. **Detect the technology stack.**
   - Scan file extensions, import statements, and configuration files.
   - Categorize: primary language(s), frameworks, testing libraries, observability libraries, database drivers.

### Step 1.2: Baseline Health Check

**Before any refactoring, the project must be in a green state.**

1. Run the discovered build command. Record the result.
2. Run the discovered test command. Record the result.
3. Run the discovered lint command (if one exists). Record the result.

If the baseline is **not green**, report the failures to the user and **STOP**. Do not refactor a broken project. Explain what needs to be fixed first.

### Step 1.3: Codebase Inventory

Walk the entire directory tree and build an inventory:

1. **File catalog** — For each source file, record:
   - Path
   - Language / technology domain
   - Line count
   - Number of exported functions/methods (approximate)

2. **Domain classification** — Assign each file to a technology domain using the mapping in [refactor-perspectives.md](refactor-perspectives.md). Each domain has its own checklist under `perspectives/` — read only the relevant domain files. Files may belong to multiple domains (e.g., a Go file with database queries belongs to both "Go Backend" and "Database").

3. **Size analysis** — Flag files that exceed these thresholds:
   - Files > 400 lines → candidates for splitting
   - Functions > 50 lines → candidates for decomposition
   - Packages/modules with > 15 files → candidates for sub-package extraction

### Step 1.4: Existing Patterns Assessment

For each technology domain present in the project, assess the current state:

1. **Dependency injection** — Are dependencies passed as constructor parameters? Are interfaces used at boundaries? Or is there tight coupling with concrete types?

2. **Testing patterns** — What testing framework is used? What is the mock strategy? Is there a pattern for test helpers? Approximate test coverage level.

3. **Observability** — Does the project already have logging, metrics, or tracing infrastructure? Which libraries/frameworks? Where is it initialized? Only plan to add observability instrumentation if the project already has the foundational setup.

4. **Error handling** — What conventions exist? Wrapped errors? Sentinel errors? Custom error types?

5. **Documentation** — Are there docstrings on functions? What style? What percentage of exported functions have documentation?

6. **File organization** — What is the package/module layout pattern? Is there a clear separation of concerns?

### Step 1.5: Refactoring Target Identification

Scan the entire codebase and flag files, functions, and packages that need attention. For each target, note:

- **What** needs to change (e.g., "add interface for service", "split file", "add docstrings")
- **Why** it needs to change (e.g., "tight coupling prevents testing", "file too large to navigate")
- **Risk level** — Low (cosmetic), Medium (structural but safe), High (changes signatures or behavior)

Categories of targets:

| Category | Trigger | Risk |
|----------|---------|------|
| Missing interfaces / DI | Concrete type dependencies at boundaries | Medium |
| Missing or weak tests | Functions without test coverage, missing edge cases | Low |
| Missing docstrings | Exported functions without documentation | Low |
| Large files | > 400 lines, no logical separation | Medium |
| Large functions | > 50 lines, doing multiple things | Medium |
| Duplicated code | Similar logic in multiple places | Medium |
| Missing observability | Logging/metrics/tracing gaps where infrastructure exists | Low |
| Inconsistent patterns | Mixed conventions within the same domain | Low |
| Missing error handling | Discarded errors, bare panics, generic catches | High |
| Tight coupling | Cross-package concrete dependencies | Medium |

### Step 1.6: Save the Analysis

Write the complete analysis to:

```text
docs/plans/code-refactor-analysis.md
```

Include: project overview, tech stack, baseline results, file inventory summary, pattern assessment, and the full list of refactoring targets grouped by domain.

**Output:** Present the analysis summary to the user before proceeding to Phase 2.

---

## Phase 2: PLAN (Read-Only)

**Role:** You are a planning agent. You have READ-ONLY access. You do not modify any code in this phase.

**Goal:** Create an ordered, chunked refactoring plan that maximizes impact while minimizing risk of breaking changes.

### Step 2.1: Prioritize Refactoring Targets

Order targets by dependency and risk:

1. **Foundation first** — Interfaces, dependency injection, and structural changes that other refactoring depends on.
2. **Testing infrastructure** — Mock generation, test helpers, test utilities that enable better tests.
3. **Error handling and safety** — Missing error handling, unsafe patterns.
4. **Test coverage** — New tests, improved tests, edge case coverage.
5. **Observability** — Logging, metrics, tracing (only where infrastructure already exists).
6. **Documentation** — Docstrings, comments explaining "why".
7. **Cosmetic** — File splitting, naming improvements, code formatting consistency.

### Step 2.2: Group by Technology Domain

Assign refactoring targets to sub-agent specializations. The exact set of sub-agents depends on the project's tech stack. Common specializations:

- **Go Backend** — Go source files (non-test): interfaces, DI, error handling, patterns
- **Go Testing** — Go test files: GinkgoV2 migration, table-driven tests, mocks, coverage
- **TypeScript / React Frontend** — Components, hooks, state management, typing
- **Frontend Testing** — Jest/Vitest, React Testing Library, E2E tests
- **Database** — Schema, migrations, query optimization, ORM patterns
- **Shell / Build / CI** — Shell scripts, Makefiles, CI pipelines, Dockerfiles
- **Kubernetes / Config** — K8s manifests, Helm charts, operator code
- **Observability** — Logging, metrics, tracing instrumentation across all domains
- **Python Backend** — Python source files: type hints, async patterns, frameworks
- **Rust** — Ownership patterns, error handling, crate structure

Only create sub-agents for domains that exist in the project.

### Step 2.3: Chunk by Dependency

Within each domain, group files into chunks that can be refactored together without breaking intermediate states:

1. **Identify dependency chains.** If file A imports file B, and both need refactoring, they should be in the same chunk or B should be refactored first.
2. **Keep chunks small enough** for a single sub-agent to handle thoroughly (roughly 5-15 files per chunk).
3. **Order chunks** so that foundational changes come before dependent changes.

### Step 2.4: Define Iteration Rounds

Organize chunks into iteration rounds:

- **Round 1**: Foundation — Interfaces, DI, structural changes across all domains
- **Round 2**: Testing — Mocks, test helpers, new test coverage
- **Round 3**: Quality — Error handling, observability, documentation
- **Round 4**: Polish — File splitting, naming, consistency, remaining targets

Each round should leave the project in a buildable, testable state.

### Step 2.5: Save the Plan

Write the complete refactoring plan to:

```text
docs/plans/code-refactor-plan.md
```

Include: prioritized target list, domain assignments, chunk breakdown, iteration rounds, and risk assessment for each chunk.

**Output:** Present the plan summary to the user before proceeding to Phase 3.

---

## Phase 3: REFACTOR (Write Access)

**Role:** You are a staff-level refactoring agent orchestrating parallel specialized sub-agents. You write production-grade code that preserves all existing functionality.

**Goal:** Execute the current iteration round from the plan, using parallel sub-agents for each technology domain.

### Critical Rules

1. **NEVER break existing functionality.** Every change must preserve the current behavior. If you are unsure whether a change is safe, do not make it.
2. **Follow the plan** from Phase 2. Execute the current round's chunks.
3. **Add docstrings** to every function you touch, if it does not already have one.
4. **If iterating after a verification failure**, your PRIMARY job is to fix whatever broke.

### Step 3.1: Pre-Refactor Verification

Before making any changes in this round:

1. Run the build command. It must pass.
2. Run the test command. It must pass.

If either fails, diagnose and fix the issue before proceeding with new refactoring work.

### Step 3.2: Spawn Parallel Sub-Agents

For each technology domain that has work in the current round, spawn a specialized sub-agent. Each sub-agent receives:

1. **Its domain specialization** and the complete refactoring checklist from the relevant `perspectives/*.md` file (see [refactor-perspectives.md](refactor-perspectives.md) for the mapping)
2. **The specific files** assigned to it in this round's chunk
3. **The refactoring targets** identified for those files
4. **The project's existing patterns** (from the analysis) so it matches conventions
5. **The critical rules** above

Use this template for each sub-agent task prompt:

```text
You are a specialized {DOMAIN_NAME} refactoring agent. Your job is to improve code quality in the assigned files WITHOUT BREAKING any existing functionality.

## Project Context
- Project: {project name and description}
- Build command: {discovered build command}
- Test command: {discovered test command}
- Existing patterns: {relevant patterns from the analysis}

## Your Domain: {DOMAIN_NAME}

{paste the complete refactoring checklist for this domain from refactor-perspectives.md}

## Files to Refactor

{list of files with their identified targets}

## Refactoring Targets for These Files

{specific targets from the plan for each file}

## Critical Rules

1. NEVER break existing functionality. Preserve all current behavior.
2. Add docstrings to every function you touch.
3. Follow the project's existing conventions and patterns.
4. If you introduce an interface, ensure all existing callers are updated.
5. If you split a file, ensure all imports are updated.
6. If you change a function signature, update all call sites.
7. Run the build and test commands after your changes to verify nothing broke.

## What to Do

For each file:
1. Read the file and understand its current purpose and dependencies.
2. Read adjacent files (callers, callees, tests) to understand the impact of changes.
3. Apply the refactoring targets identified in the plan.
4. Add docstrings to all functions.
5. Follow the domain-specific checklist.
6. Verify your changes compile and tests pass.

## Output

Report what you changed:
- Files modified (with summary of changes)
- Files created (if splitting)
- Files deleted (if consolidating)
- Tests added or modified
- Any issues encountered
- Build/test results after changes
```

Spawn all sub-agents concurrently. If the project has many files, split a single domain across multiple sub-agents (e.g., "Go Backend - pkg/api" and "Go Backend - pkg/service").

### Step 3.3: Collect and Integrate Results

After all sub-agents complete:

1. **Review each sub-agent's output.** Check for conflicts between sub-agents (e.g., two agents modifying the same file).
2. **Resolve conflicts** if any exist — prefer the change that is more aligned with the plan.
3. **Verify integration.** Run the build and test commands to confirm all changes work together.
4. **If integration fails**, identify which sub-agent's changes caused the failure and fix them.

### Step 3.4: Post-Refactor Smoke Test

After integrating all sub-agent changes:

1. Run the full build command. It must pass.
2. Run the full test suite. It must pass.
3. Run lint (if available). Address any new lint violations introduced by the refactoring.

If any step fails:
- Identify the specific change that caused the failure.
- Fix it immediately.
- Re-run verification.
- If a fix requires reverting a refactoring change, revert it and note it for the next round.

---

## Phase 4: VERIFY

**Role:** You are a verification agent reviewing the refactoring changes for quality and safety.

**Goal:** Confirm that all changes improve code quality without breaking functionality, and decide whether to continue with the next round or finish.

### Step 4.1: Run Full Verification

1. Run the build command. Record the result.
2. Run the full test suite. Record the result.
3. Run lint (if available). Record the result.

All must pass. If any fail, go back to Phase 3 to fix the issues.

### Step 4.2: Review Changes

Use the reusable review workflow in [../review-engine/SKILL.md](../review-engine/SKILL.md) and the perspective criteria in [../review-engine/review-perspectives.md](../review-engine/review-perspectives.md).

When running the review for code-refactor, pass the following context:
- The original refactoring request
- The saved analysis from `docs/plans/code-refactor-analysis.md`
- The saved plan from `docs/plans/code-refactor-plan.md`
- The diff for the current round
- Prior verification findings if this is a fix iteration

The review MUST specifically check:
1. **No functionality was broken.** Existing behavior is preserved.
2. **Refactoring targets were addressed.** The planned improvements were made.
3. **New code follows project conventions.** Style, patterns, and naming match the existing codebase.
4. **Docstrings are present** on all touched functions.
5. **No regressions** in test coverage.

### Step 4.3: Decide Next Action

After the review:

- **If the review found critical or high issues:** Go back to Phase 3 to fix them. Maximum 3 fix iterations per round before escalating to the user.
- **If the review passed and more rounds remain:** Proceed to Phase 3 with the next round from the plan.
- **If the review passed and all rounds are complete:** Proceed to the Finalization step.

---

## Finalization

After all iteration rounds are complete and verified:

### Step F.1: Update Project Documentation

1. **Update `AGENTS.md`** (create if it does not exist):
   - Document structural changes (new files, moved files, split files)
   - Document new patterns introduced (interfaces, DI, testing conventions)
   - Document best practices decisions made during refactoring
   - This helps future agents and coding sessions quickly understand the project

2. **Update `README.md`** if structural changes affect:
   - Project layout or directory structure
   - Build or test instructions
   - Development workflow

### Step F.2: Final Summary

Present a comprehensive summary to the user:

```text
## Code Refactoring Complete

### Rounds Completed: N of N

### Changes by Domain
| Domain | Files Modified | Files Created | Files Deleted | Tests Added |
|--------|---------------|---------------|---------------|-------------|
| ... | ... | ... | ... | ... |

### Key Improvements
- {list the most impactful changes}

### Patterns Introduced
- {list new patterns: interfaces, DI, testing conventions, etc.}

### Observability Added
- {list new logging, metrics, or tracing — only if infrastructure existed}

### Documentation Updated
- AGENTS.md: {what was added}
- README.md: {what was changed, if anything}

### Remaining Items
- {anything that was identified but not addressed, with explanation}

### Build/Test Status
- Build: ✅ PASS
- Tests: ✅ PASS (N tests, +M new)
- Lint: ✅ PASS
```

---

## Iteration Controls

### Maximum Iterations

- **Fix iterations per round**: 3 (if a round's changes keep failing verification, escalate to user)
- **Total rounds**: Defined by the plan in Phase 2. Typically 3-5 rounds for a full project.
- **If the user specified a scope** (not "full project"), complete only the rounds relevant to that scope.

### When to Stop

Stop iterating when:
1. All planned rounds are complete and verified, OR
2. The user's specified scope is fully addressed, OR
3. A round exceeds 3 fix iterations (escalate to user), OR
4. The user explicitly says to stop

### Resuming Work

If the refactoring is interrupted or the user wants to continue later:
1. Read the saved plan from `docs/plans/code-refactor-plan.md`
2. Check which rounds are complete (look at git history or saved progress)
3. Resume from the next incomplete round

---

## Guidelines

- **Safety over ambition.** A correct refactoring that covers 80% of the project is better than an ambitious refactoring that breaks things.
- **Preserve behavior.** Refactoring changes structure, not behavior. If a test starts failing, the refactoring introduced a bug.
- **Match existing patterns.** New code should look like it belongs in this codebase.
- **Incremental progress.** Each round should leave the project in a better state than before, fully buildable and testable.
- **Docstrings on everything.** Every function you touch gets a docstring if it does not have one.
- **No hardcoded commands.** Always discover build, test, and lint commands from project files.
- **Observability is additive only.** Only add logging/metrics/tracing where the project already has the infrastructure set up.
- **DI enables testing.** Dependency injection is not an end in itself — it enables better mocking and testing.
- **Split for readability.** File splitting should follow logical boundaries. Each file should have a clear, single purpose.
- **Iterate until done.** The goal is comprehensive coverage of the entire project, not a partial improvement.
- **Update documentation last.** AGENTS.md and README updates happen after all code changes are verified.
- **Be explicit about what you changed and why.** Future agents and humans need to understand your decisions.
