# review-change Workflow

```
review-change [project-path]
```

Review local uncommitted/staged changes in the current project (or a specified path). Every step is mandatory - do not skip any.

After completing the steps below, use the shared review workflow from [../review-engine/SKILL.md](../review-engine/SKILL.md) for analysis, severity levels, review confidence, and optional interactive finding presentation.

---

## Step 1: Setup

1. Determine the working directory:
   - If `project-path` is provided, `cd` into it.
   - Otherwise, use the current workspace root.
2. Verify this is a git repository:
   ```bash
   git rev-parse --is-inside-work-tree
   ```
3. Identify the base branch for comparison:
   ```bash
   git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null || echo "origin/main"
   ```
   Use the result as `{base}`.

## Step 2: Gather the Diff

Get both staged and unstaged changes:

```bash
git diff {base} --stat
git diff {base}
```

If there are no changes against the base branch, fall back to uncommitted changes:

```bash
git diff --stat
git diff
git diff --cached --stat
git diff --cached
```

If still no changes, inform the user and stop.

## Step 3: Context

### 3a: Review Commit History (if commits exist on branch)

If the current branch has commits beyond `{base}`:

```bash
git log {base}..HEAD --oneline
```

Check for:
- **WIP/fixup commits** (`WIP`, `fixup!`, `squash!`, `temp`)
- **Meaningful messages** — do they explain *why*, not just *what*?
- **Logical structure** — one giant commit vs many tiny commits

Flag commit quality issues as **low-severity**.

### 3b: Understand Intent

Look for clues about what the change is trying to accomplish:
- Current branch name (e.g., `feature/add-auth`, `fix/null-pointer`)
- Recent commit messages
- If unclear, ask the user what the change is about before reviewing

## Step 4: Size Assessment

Run the shared Size Assessment from [../review-engine/SKILL.md](../review-engine/SKILL.md) using the diff stats.

## Step 5: Orchestrated Review

Run the shared review workflow from [../review-engine/SKILL.md](../review-engine/SKILL.md) and apply the criteria in [../review-engine/review-perspectives.md](../review-engine/review-perspectives.md).

## Step 6: Present Findings

Use the output format below, then follow the Optional Interactive Finding Presentation from [../review-engine/SKILL.md](../review-engine/SKILL.md).

Map the shared review verdicts like this:
- `APPROVED` -> `CLEAN`
- `CHANGES_REQUESTED` -> `HAS_ISSUES`
- Use `NEEDS_DISCUSSION` when intent or context remains unclear after the review.

When the user approves a finding ("yes"), apply the fix directly to the local file. After applying:

1. Read the file to confirm the change looks correct.
2. Show the user the applied diff snippet.
3. Move to the next finding.

**Do NOT commit or push changes. Do NOT run git add/commit/push.**

### Output Format

```
## Local Review: {branch-name}

**Reviewed at**: {YYYY-MM-DD HH:MM UTC}

**Verdict**: CLEAN / HAS_ISSUES / NEEDS_DISCUSSION

**Review Confidence**: HIGH / MEDIUM / LOW — {brief justification}

**Reviewers Applied**: {list of perspectives used and why}

**Summary**: 2-3 sentence overall assessment.

### Change Context
- **Branch**: {branch-name}
- **Base**: {base-branch}
- **Intent**: {what the change accomplishes, from branch name / commits / user input}
- **Size**: {assessment emoji} — {N} files, +{add} −{del}
- **Commits on branch**: {N} ({quality note}) or "uncommitted changes only"

### Findings
(presented one at a time — see Interactive Finding Presentation in SKILL.md)

### What's Good
- {praise for well-written code, smart design decisions, good coverage}

### Stats
- Size: {assessment} (+{add} −{del}, {files} files)
- Commits: {N} ({quality}) or "uncommitted"
- Reviewers applied / skipped: {lists}
- Findings: {critical} critical, {high} high, {medium} medium, {low} low, {info} info
```
