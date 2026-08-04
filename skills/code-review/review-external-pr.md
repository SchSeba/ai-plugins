# Review External PR

Review a pull request authored by someone else (external_pr origin in the dev-task engine).

This variant focuses on **code reviewer** behavior — posting constructive inline comments, evaluating the PR discussion, and submitting a formal review.

## When to Use

Use this review type when:
- The dev-task engine is reviewing a PR authored by an external contributor
- The agent is acting as a code reviewer on someone else's work
- A PR was assigned for review and needs feedback

## Review Focus

1. **Understanding Intent**: Read the PR description, linked issues, and existing discussion to understand what the author intended. Don't review in a vacuum.
2. **Correctness**: Does the code do what the PR description says? Are there edge cases, error handling gaps, or logic errors?
3. **Style & Conventions**: Does the code follow the project's established patterns? Check naming, error wrapping, import organization, and test structure.
4. **Security**: Check for injection vulnerabilities, auth bypasses, secret leaks, and OWASP top 10 issues.
5. **Performance**: Flag N+1 queries, unbounded allocations, missing pagination, or hot-path inefficiencies.
6. **Existing Discussion**: Read all existing PR comments and discussion threads. Respond to open questions. Don't repeat feedback that's already been given.

## Review Actions

### Inline Comments

Post specific, actionable inline comments on the PR using `devtask_pr_review_comment`. Each comment should:
- Reference the specific file and line
- Explain what's wrong and why
- Suggest a concrete fix when possible

### Formal Review Submission

Submit a formal review via `devtask_pr_submit_review`:

| Action | When |
|--------|------|
| `APPROVE` | No blocking issues, code is ready to merge |
| `COMMENT` | Minor suggestions only, not blocking |
| `REQUEST_CHANGES` | Blocking issues that must be addressed |

## Verdict Mapping

Map your assessment to dev-task verdicts:

| Assessment | Dev-Task Verdict | When |
|------------|------------------|------|
| PR looks good | `approved` | Ready to merge |
| Needs author changes | `changes_requested_coding` | Code issues the author should fix |

## Methodology

Follow the [review-engine](../review-engine/SKILL.md) multi-perspective workflow for the detailed review steps, perspectives, and severity criteria.
