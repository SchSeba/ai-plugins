# review-pr Workflow

```
review-pr <pr-url>
```

Review a GitHub pull request. Every step is mandatory - do not skip any.

After completing the steps below, use the shared review workflow from [../review-engine/SKILL.md](../review-engine/SKILL.md) for analysis, severity levels, review confidence, and optional interactive finding presentation.

---

## Step 1: Setup

1. Use the GitHub MCP or `gh` CLI to fetch PR metadata (title, body, labels, base/head branches, linked issues).
2. Clone or checkout the PR branch under `/tmp` if full file access is needed beyond the diff.

## Step 2: PR Context & Commit Quality

Understand the **intent** before reviewing code.

### 2a: Read PR Description & Linked Issues

Extract from the PR metadata:
- What problem is being solved (from the body)
- Linked issues (`Fixes #N`, `Closes #N`, `Resolves #N`, or linked URLs)
- Labels and milestone

If linked issues exist, fetch their descriptions:

```bash
gh issue view {issue_number} --repo {owner}/{repo} --json title,body
```

Use this context throughout the review to validate the code addresses the stated problem.

### 2b: Review Commit History

```bash
gh pr diff {number} --repo {owner}/{repo} --stat
git log {base}..HEAD --oneline
```

Check for:
- **WIP/fixup commits** that should have been cleaned up (`WIP`, `fixup!`, `squash!`, `temp`)
- **Meaningful messages** — do they explain *why*, not just *what*?
- **Logical structure** — one giant commit that should be split, or many tiny commits that should be squashed?

Flag commit quality issues as **low-severity** unless they indicate deeper problems.

## Step 3: Size Assessment

Run the shared Size Assessment from [../review-engine/SKILL.md](../review-engine/SKILL.md) using the diff stats.

## Step 4: Orchestrated Review

Run the shared review workflow from [../review-engine/SKILL.md](../review-engine/SKILL.md) and apply the criteria in [../review-engine/review-perspectives.md](../review-engine/review-perspectives.md).

## Step 5: Check CI Status

```bash
gh pr checks {number} --repo {owner}/{repo}
```

If any checks are **failing**:

1. Identify which checks failed.
2. Fetch failure logs:
   ```bash
   gh run view {run_id} --repo {owner}/{repo} --log-failed
   ```
3. Diagnose: code issue from the PR, flaky test, infra issue, or pre-existing failure on base branch?
4. For code issues, cross-reference with the diff and include a finding with a concrete fix.

## Step 6: Save Review

Write the full review to the docs workspace using numbered revisions.

1. List existing reviews:
   ```
   workspace(action: "list", path: "docs/pr-reviews/")
   ```
   Look for `{repo}-pr{number}-revision-*.md`. Use next available number, starting at 1.

2. Write the review:
   ```
   workspace(action: "write", path: "docs/pr-reviews/{repo}-pr{number}-revision-{N}.md", content: "<review>")
   ```

## Step 7: Present Findings

Use the output format below, then follow the Optional Interactive Finding Presentation from [../review-engine/SKILL.md](../review-engine/SKILL.md).

Map the shared review verdicts like this:
- `APPROVED` -> `APPROVE`
- `CHANGES_REQUESTED` -> `REQUEST_CHANGES`
- Use `NEEDS_DISCUSSION` when context remains incomplete or ambiguous.

When the user approves a finding ("yes"), publish the comment to GitHub using the GitHub MCP or `gh` CLI.

**Do NOT publish to GitHub unless the user explicitly approves each finding.**

### Output Format

The **first line** MUST be the clickable link to the saved review:

```
📄 [View full review](pr-reviews/{repo}-pr{number}-revision-{N}.md)

**Revision**: {N} | **Head SHA**: `{sha}` | **Reviewed at**: {YYYY-MM-DD HH:MM UTC}

## PR Review: #{number} — {title}

**Verdict**: APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION

**Review Confidence**: HIGH / MEDIUM / LOW — {brief justification}

**Reviewers Applied**: {list of perspectives used and why}

**Summary**: 2-3 sentence overall assessment.

### PR Context
- **Intent**: {what the PR accomplishes}
- **Linked Issues**: {issue numbers or "None"}
- **Size**: {assessment emoji} — {N} files, +{add} −{del}
- **Commits**: {N} commits — {quality note}

### CI Status
**Overall**: ✅ All passing / ❌ {N} failing / ⏳ Pending

| Check | Status | Details |
|-------|--------|---------|
| {name} | ✅/❌/⏳ | {detail} |

### Findings
(presented one at a time — see Interactive Finding Presentation in SKILL.md)

### What's Good
- {praise for well-written code, smart design decisions, good coverage}

### Stats
- CI checks: {passed}/{total}
- PR size: {assessment} (+{add} −{del}, {files} files)
- Commits: {N} ({quality})
- Reviewers applied / skipped: {lists}
- Findings: {critical} critical, {high} high, {medium} medium, {low} low, {info} info
```
