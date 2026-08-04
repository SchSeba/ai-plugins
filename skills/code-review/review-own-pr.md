# Review Own PR

Review changes the agent itself produced (own_pr or issue origin in the dev-task engine).

This variant focuses on **internal QA** — the reviewer evaluates the coding agent's work against the plan, checks for completeness, and ensures production readiness.

## When to Use

Use this review type when:
- The dev-task engine is reviewing changes it produced (own PR or issue-originated task)
- The agent completed a coding phase and needs self-review before marking done
- A CI check passed/failed and the review phase is re-evaluating

## Review Focus

1. **Plan Adherence**: Compare every planned change against the actual diff. Flag deviations — missing files, extra files, or scope creep.
2. **Correctness Against Requirements**: Do the changes actually solve the original issue/task description? Code can be technically correct but miss the point.
3. **Test Coverage**: Every new function, method, or branch must have corresponding tests. Flag untested code paths.
4. **Observability**: Verify logging at appropriate levels (Debug for routine, Info for significant operations, Warn for recoverable errors). Verify metrics and tracing spans for new functionality.
5. **Build Validation**: Confirm lint, test, and build all pass. If CI results are available, cross-check them.
6. **No Debug Artifacts**: Check for leftover `console.log`, `fmt.Println`, `print()`, `TODO`, `FIXME`, hardcoded test values, or commented-out code.

## Verdict Mapping

Map your assessment to dev-task verdicts:

| Assessment | Dev-Task Verdict | When |
|------------|------------------|------|
| All good, ready to merge | `approved` | No blocking issues found |
| Code needs fixes | `changes_requested_coding` | Implementation bugs, missing tests, lint issues |
| Plan was wrong/incomplete | `changes_requested_planning` | Fundamental approach needs rethinking |

## PR Comment Evaluation

When existing PR comments are present, classify each as:

- **AGREE**: The comment identifies a real issue. Include it in your findings.
- **DISAGREE**: The comment is incorrect or no longer relevant. Explain why.
- **BORDERLINE**: Valid concern but not blocking. Note as optional improvement.

## Methodology

Follow the [review-engine](../review-engine/SKILL.md) multi-perspective workflow for the detailed review steps, perspectives, and severity criteria.
