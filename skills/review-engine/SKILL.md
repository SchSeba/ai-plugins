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

Identify the base and the revision under review. For a PR, record the head SHA. For local work, include the staged, unstaged and new files in scope. Read the complete change against its base. When a hunk omits a guard, producer or consumer, use CodeGraph when available to trace its callers and callees. If the project has no usable index, follow the configured provider's setup instructions to initialize it. If the provider is unavailable, state that limitation and inspect the source directly.

### Step 2: Context Assessment

1. Verify intent alignment: Do the changes actually solve the problem described in the original request? Code can be technically correct but still miss the point.
2. Plan adherence: If an earlier phase produced a plan, verify the implementation follows it. Flag significant deviations.
3. Revisit prior feedback against this revision. Read the thread through its latest replies, then check the current code and tests. After a rebase, compare with the new base to see whether upstream behavior and regression cases survived, including cases moved within a file.
4. Completeness: Are all files that should have been changed actually changed? Missing tests, missing migrations, missing type updates?
5. No debug artifacts: Check for leftover `console.log`, `fmt.Println`, `print()`, `TODO`, `FIXME`, or hardcoded test values.

### Step 3: Size Assessment

Use the diff statistics as rough planning estimates.

| Added lines | Files changed | Size |
|-------------|---------------|------|
| < 200 | < 10 | Small |
| 200–500 | 10–20 | Medium |
| 500–1000 | 20–40 | Large |
| > 1000 | > 40 | Very large |

Identify generated files, their source definitions and the project's regeneration checks. On a large change, review coherent commits or subsystems, then check their integration in the final diff. Suggest a split when unrelated work obscures behavior or independently reviewable changes have been mixed.

### Step 4: Categorize Changed Files

Use the mapping in [review-perspectives.md](review-perspectives.md) to select the sections that apply to the behavior under review. Consider security and performance when code changes. Include affected consumers and tests even if their files are unchanged.

### Step 5: Spawn Parallel Sub-Agent Reviewers

Group related perspectives and assign independent, read-only reviews of distinct risks or subsystems. Give each reviewer the request, the base and head, relevant diffs and perspective criteria, and access to surrounding code. The agent coordinating the review owns the combined verdict. If parallel review is unavailable, cover the same perspectives sequentially.

Ask each reviewer for findings in the Step 9 format with their perspective attached, or a short account of what they checked if they found none. For a suspected regression, request a supported input, the path it takes, the expected and actual outcomes, and the difference from the base. A focused test or a trace through the code can establish the failure.

As the coordinator, verify each candidate against the source. Look for evidence that could invalidate it, such as validation before the call, a feature gate, a later change or a test with the same preconditions. Deduplicate by cause and assign severity from the verified impact. If a consequential assumption remains open, ask a specific question and say what would settle it. Report pre-existing behavior, superseded concerns and agreed follow-ups separately when they affect the decision. Sort confirmed findings by severity.

### Step 6: Cross-Cutting Analysis

Trace the changed behavior through real entry points. For shared state, identify which component owns each value, which data is authoritative, and how the next consumer sees an update. Follow a transition likely to break that contract, such as replacing an in-flight result with a stored one, cancelling one of two users of the same resource, or reading older data after a feature is disabled. Include first use and partial completion when they change the outcome.

### Step 7: Changelog and Breaking Change Detection

1. Detect breaking changes: removed or renamed exports, changed signatures, removed API endpoints, changed CLI flags, or dropped DB columns.
2. Check for a changelog entry: if the repo maintains a changelog and changes are breaking or add features, flag a missing entry.
3. Check for migration notes: if there are DB migrations or config changes, verify upgrade instructions are included.

### Step 8: Severity Levels

| Severity | Criteria |
|----------|----------|
| [CRITICAL] | Data loss, security vulnerability, crash in production |
| [HIGH] | Reachable incorrect result, unhandled failure or incompatible change with significant impact |
| [MEDIUM] | Bounded performance or maintainability issue, or a concrete gap in coverage of changed behavior |
| [LOW] | Style, minor readability, nice-to-have improvements |
| [INFO] | Observations, praise, questions |

### Review Confidence

Assess confidence from the evidence inspected. Use HIGH when the affected paths and their contracts are verified, MEDIUM when some behavior is inferred, and LOW when substantial code or context was unavailable. Name the missing evidence when it affects the verdict.

### Step 9: Render Verdict

Use this format:

```text
## Code Review

**Verdict**: APPROVED / CHANGES_REQUESTED

**Summary**: Revision reviewed, overall assessment and any material coverage limits.

### Findings

#### [{severity}] {title}
**File**: `path/to/file.ext` (lines N-M)
**Category**: {bug|security|performance|style|test|database|api|dependency}

{Trigger, expected and actual outcomes, and supporting code or test evidence}

**How to fix**:
{actionable correction or regression test, with a code suggestion when useful}

---

(repeat for each finding)

### What's Good
- {praise for well-written code, smart decisions}

### Stats
- Files reviewed: N
- Findings: N critical, N high, N medium, N low, N info
```

#### Verdict rules

- APPROVED: The reviewed change meets the acceptance criteria and has no verified critical or high findings. Medium and low findings can remain advisory.
- CHANGES_REQUESTED: There is a verified critical or high finding, or a specific acceptance criterion is unmet.
- If missing context prevents a verdict, identify the question for the parent workflow. Recheck affected findings and anchors if the revision changes before reporting.

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

- Focus on correctness, security, testing and maintainability. Flag style only when it materially affects readability or violates a project requirement.
- Give an actionable correction for confirmed findings. Explain an unresolved question in terms of the evidence needed to answer it.
- If changes look good, say APPROVED. Do not manufacture issues.
