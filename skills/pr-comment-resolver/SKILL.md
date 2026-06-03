---
name: pr-comment-resolver
description: Resolve PR review comments one-by-one with user approval. Use when the user provides a pull request link and wants to address review comments, resolve PR feedback, or fix code based on reviewer suggestions.
---

# PR Comment Resolver

Resolve pull request review comments interactively, one at a time, with explicit user approval before each change.

## Input Format

```
<repo-folder(optional)> <pull-request-link>
```

- `repo-folder` — optional subdirectory when the workspace contains multiple projects.
- `pull-request-link` — GitHub PR URL (e.g. `https://github.com/owner/repo/pulls/42`).

Parse `owner`, `repo`, and `pullNumber` from the link.

## Workflow

### Step 1 — Fetch review comments

Use the GitHub MCP `pull_request_read` tool:

```
server: user-github
toolName: pull_request_read
arguments:
  method: get_review_comments
  owner: <owner>
  repo: <repo>
  pullNumber: <number>
  perPage: 100
```

Fallback: if MCP is unavailable, use `gh`:

```bash
gh api repos/<owner>/<repo>/pulls/<number>/comments
```

Also fetch general PR comments (`get_comments`) in case reviewers left feedback there.

### Step 2 — Filter actionable comments

Review every active unresolved comment, including Bugbot comments, before acting. When fetching GitHub comments, filter out resolved threads first. Read only each comment body and the minimum location or URL needed to act on it; do not read the entire JSON output or other unnecessary payload data.

Discard:
- Resolved threads (`isResolved: true`)
- Pure praise / acknowledgement with no requested change

Keep only comments that request a code change or raise a concern.

Fix only comments you agree with. If you disagree or are unsure, explain that clearly before moving on.

### Step 3 — Present summary

Show the user a numbered list of all actionable comments (one line each) so they see the full scope before starting.

### Step 4 — Process comments ONE BY ONE

For **each** comment, present exactly this format and **stop to wait for user input**:

---

**Comment N of M**

**1. Code snippet** (the relevant code from the current branch, with file path and line numbers)

**2. Reviewer comment**
> Quoted reviewer text

**3. Suggested change**
```
Your proposed code change
```

Approve this change? (yes / no / skip)

---

**CRITICAL: Do NOT proceed to the next comment until the user responds.**

### Step 5 — Apply approved change

After user approves:

1. Apply the change to the file.
2. Run validation:
   ```bash
   make fmt vet lint test
   ```
3. If the validation fails **due to the change**, fix the issues and re-run until clean.
4. Show the user the result, then move to the next comment.

If the user says **no** or **skip**, move to the next comment without changing anything.

### Step 6 — Final summary

After all comments are processed, show:
- How many comments were addressed
- How many were skipped
- Remaining `make` errors (if any unrelated ones exist)

**DO NOT push the branch. DO NOT run `git push`.**

## Important Rules

- If `repo-folder` is provided, `cd` into it before making changes.
- Always read the file before editing to get current content.
- Never batch multiple comment changes together — one at a time only.
- Never push to remote.
- Always add docstrings to new functions.
- Use `--signoff` on any commits, never add `Made-with: Cursor`.
