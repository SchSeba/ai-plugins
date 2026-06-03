---
name: review-engine
description: Reusable multi-perspective code review engine for local diffs, pull requests, and workflow skills that need a review phase. Use when a workflow must analyze changed files, apply security/performance/language-specific review criteria, orchestrate parallel reviewers, and render a verdict with concrete fixes.
---

# Review Engine

Reusable review workflow for any skill that needs to evaluate code changes.

Use this engine when:
- reviewing local changes or pull requests
- embedding a review phase inside another skill, such as `develop-feature`
- standardizing severity levels, findings, and verdict rules across skills

## Inputs

- Change context: feature description, bug, or PR intent
- Diff content or repository access
- Optional implementation plan
- Optional prior review findings when iterating

## Shared Review Workflow

### Step 1: Get the Diff

Review all changes made during the coding phase. Use `git diff` to see the full diff of changes.

### Step 2: Context Assessment

1. Verify intent alignment: Do the changes actually solve the problem described in the original request? Code can be technically correct but still miss the point.
2. Plan adherence: If an earlier phase produced a plan, verify the implementation follows it. Flag significant deviations.
3. Iteration feedback: If this is iteration > 1, check whether previous review feedback was addressed. Cross-reference prior review items against the current changes.
4. Completeness: Are all files that should have been changed actually changed? Missing tests, missing migrations, missing type updates?
5. No debug artifacts: Check for leftover `console.log`, `fmt.Println`, `print()`, `TODO`, `FIXME`, or hardcoded test values.

### Step 3: Size Assessment

Evaluate the scope of changes:

| Added Lines | Files Changed | Assessment |
|-------------|---------------|------------|
| < 200 | < 10 | Small - ideal |
| 200-500 | 10-20 | Medium - acceptable |
| 500-1000 | 20-40 | Large - flag and suggest splitting |
| > 1000 | > 40 | Very large - strongly recommend decomposition |

Check whether the changes mix unrelated concerns, such as feature + refactor, bug fix + dependency upgrade, or formatting + logic. Flag mixed concerns as medium severity.

### Step 4: Categorize Changed Files

Before reviewing, examine the diff output and categorize the changed files to determine which review perspectives are needed.

Use the mapping and criteria in [review-perspectives.md](review-perspectives.md). Do not apply perspectives with zero relevant changed files. Security Review and Performance Review always apply when code files changed.

### Step 5: Spawn Parallel Sub-Agent Reviewers

Analyze the code changes, their scope, the affected subsystems, and the languages and frameworks involved. Then spawn multiple specialized code review sub-agents to perform independent, parallel reviews. Each sub-agent focuses on a single review perspective relevant to the actual changes, reviews only the files assigned to its expertise, and returns structured findings in a consistent format for aggregation.

Parallel review reduces wall-clock time and ensures each perspective gets dedicated attention. Each sub-agent receives the full review criteria for its perspective and the relevant file diffs, producing focused findings that are easier to aggregate.

#### Determine which reviewers to spawn

From the categorization in Step 4, build the list of review perspectives that have at least one relevant changed file.

Priority order:
1. Security Review
2. Language-specific review (Go / Python / Frontend)
3. Test Review
4. Performance Review
5. Other relevant perspectives (Database, API, Kubernetes, Linux Systems, Dockerfile, Shell & Build Script, Terraform / IaC, Dependency, Documentation, Integration & E2E Test)

Group perspectives that share the same files into a single sub-agent when practical. Do not spawn a reviewer for a perspective with zero relevant changed files.

#### Construct the sub-agent task prompt

For each sub-agent, construct a task prompt that includes:
1. The perspective name and its complete review criteria from [review-perspectives.md](review-perspectives.md)
2. The list of files to review
3. The diff content for those files
4. The change context: feature description, bug, or PR intent
5. The required output format below

Use this template:

```text
You are a specialized {PERSPECTIVE_NAME} code reviewer. Review the following code changes and report findings.

## Change Context
- Feature/Change: {feature description}
- Intent: {what the change is trying to accomplish}

## Your Review Perspective: {PERSPECTIVE_NAME}

{paste the complete review criteria for this perspective from review-perspectives.md}

## Files to Review

{list of files assigned to this perspective}

## Diff

{the diff content for these files}

Read the full content of any file when the diff alone is insufficient to understand context.

## Required Output Format

Return your findings as a structured list. Each finding MUST follow this exact format:

### [{severity}] {title}
**File**: `path/to/file.ext` (lines {N}-{M})
**Category**: {bug|security|performance|style|test|database|api|dependency}
**Reviewer**: {your perspective name}

{Detailed explanation of the issue.}

**How to fix**:
{code showing the correction}

---

Severity levels:
- [CRITICAL]: Data loss, security vulnerability, crash in production
- [HIGH]: Bug affecting correctness, missing error handling, breaking changes
- [MEDIUM]: Performance issue, missing tests, non-ideal patterns
- [LOW]: Style, minor readability, nice-to-have improvements
- [INFO]: Observations, praise, questions for the author

If you find NO issues, return:
### No findings
{Perspective name} review found no issues in the reviewed files.

End with:
### What's Good
- {brief praise for well-written aspects relevant to your perspective}

IMPORTANT: Every finding MUST include a concrete code fix - never just flag an issue without showing how to resolve it.
```

#### Spawn the sub-agents

Spawn all sub-agents in a single message so they run in parallel. Use the `Subagent` tool for each perspective, set `readonly: true`, and launch them concurrently in one response.

#### Aggregate findings

After all sub-agents have returned:
1. Collect all findings from all sub-agents into a single list.
2. Deduplicate: if two perspectives flagged the same issue on the same file and line range, keep the higher-severity finding and note which perspectives identified it.
3. Sort findings by severity: Critical, High, Medium, Low, Info.
4. Carry forward the aggregated findings to the cross-cutting analysis and verdict.

Fallback: If sub-agent spawning is unavailable or fails, perform the reviews sequentially in-context using the same perspective criteria.

### Step 6: Cross-Cutting Analysis

After aggregating perspective findings, perform these checks that catch bugs individual reviews miss:

1. Trace full user flows end-to-end. Walk through 3-5 realistic scenarios. What is null or undefined at each step? What happens if step N has not completed when step N+1 starts?
2. Audit state assumptions at integration boundaries. When new code reads existing state: when is this state set? Can the new code execute before it is set? What are the race windows?
3. Check first-use and edge scenarios. What if this is the first time? What if the resource does not exist yet? What if the system is mid-transition?
4. Follow data across system boundaries. When frontend and backend coordinate via events, trace what data is available at each event.
5. Distinguish code correctness from integration correctness. Review both the function and its call sites.

### Step 7: Changelog and Breaking Change Detection

1. Detect breaking changes: removed or renamed exports, changed signatures, removed API endpoints, changed CLI flags, or dropped DB columns.
2. Check for a changelog entry: if the repo maintains a changelog and changes are breaking or add features, flag a missing entry.
3. Check for migration notes: if there are DB migrations or config changes, verify upgrade instructions are included.

### Step 8: Severity Levels

| Severity | Criteria |
|----------|----------|
| [CRITICAL] | Data loss, security vulnerability, crash in production |
| [HIGH] | Bug affecting correctness, missing error handling, breaking changes |
| [MEDIUM] | Performance issue, missing tests, non-ideal patterns |
| [LOW] | Style, minor readability, nice-to-have improvements |
| [INFO] | Observations, praise, questions |

### Review Confidence

| Confidence | Criteria |
|------------|----------|
| HIGH | < 500 lines, single language, clear intent, well-understood patterns |
| MEDIUM | 500-1000 lines, mixed languages or unfamiliar patterns |
| LOW | 1000+ lines, multiple frameworks, or heavily truncated diff |

### Step 9: Render Verdict

Use this format:

```text
## Code Review

**Verdict**: APPROVED / CHANGES_REQUESTED

**Summary**: 2-3 sentence overall assessment.

### Findings

#### [{severity}] {title}
**File**: `path/to/file.ext` (lines N-M)
**Category**: {bug|security|performance|style|test|database|api|dependency}

{Detailed explanation}

**How to fix**:
{code showing the correction}

---

(repeat for each finding)

### What's Good
- {praise for well-written code, smart decisions}

### Stats
- Files reviewed: N
- Findings: N critical, N high, N medium, N low, N info
```

#### Verdict rules

- APPROVED: No critical or high findings. Medium and low findings are acceptable.
- CHANGES_REQUESTED: Any critical or high findings, or the code does not meet the acceptance criteria from the plan.

## Optional Interactive Finding Presentation

When a parent workflow needs user approval before acting on each finding, present each finding one at a time:

```text
Issue N of M

1. Code snippet
   File path, line numbers, and the relevant code

2. Issue found by review
   Description of the problem

3. Suggested fix
   Proposed comment and corrected code

Action? (yes / no / skip)
```

Do not proceed to the next finding until the user responds. If the parent workflow is local code review, apply the fix only after explicit approval. If the parent workflow is PR review, publish the comment only after explicit approval.

## Guidelines

- Thoroughness over speed. A well-researched review catches more than a fast skim.
- Focus on correctness, security, testing, and maintainability. Skip pure style nitpicks unless they materially affect readability.
- Every finding MUST include a fix. Never flag an issue without showing how to resolve it.
- Read surrounding code. When the diff is not enough, read the full files and their call sites.
- Understand intent before judging. Read the request, plan, PR description, or linked issues first.
- Flag mixed concerns. Reviews are harder when unrelated work is bundled together.
- Check for breaking changes, migration notes, and missing public documentation when APIs or config change.
- Cross-boundary bugs are the highest-value finds.
- If changes look good, say APPROVED. Do not manufacture issues.
