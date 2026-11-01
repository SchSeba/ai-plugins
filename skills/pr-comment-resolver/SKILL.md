---
name: pr-comment-resolver
description: Resolve PR review comments one-by-one with user approval. Use when the user provides a pull request link and wants to address review comments, resolve PR feedback, or fix code based on reviewer suggestions.
---

# PR Comment Resolver

Resolve pull request review comments interactively, one at a time, with explicit user approval before each change. For every handled comment, prepare an unpublished reply draft and publish it only after the full review is complete, the user confirms the latest changes were pushed, and the user separately approves that exact reply.

## Input Format

```
<repo-folder(optional)> <pull-request-link>
```

- `repo-folder` — optional subdirectory when the workspace contains multiple projects.
- `pull-request-link` — GitHub PR URL (e.g. `https://github.com/owner/repo/pulls/42`).

Parse `owner`, `repo`, and `pullNumber` from the link.

## Workflow

> **CodeGraph-first rule:** If the CodeGraph MCP server is configured and available, use `codegraph_explore` throughout this workflow to understand the code context around review comments — callers, callees, and blast radius of the symbols being discussed. This helps craft better fixes by understanding the full impact. If CodeGraph is available but the project has no `.codegraph/` directory, run `codegraph init` in the project root first to build the initial graph. If CodeGraph is not available, **inform the user** and fall back to manual file reading.

## Reply safeguards

Apply the reply workflow below to every PR, regardless of its owner, repository, or optional local folder. For each actionable comment handled in Step 4, keep a clearly labeled, unpublished proposed reply tied to the original PR and comment. Refresh the draft after the user decides and any approved change is validated so it describes the actual disposition and outcome.

Never publish a reply or otherwise answer a review comment during retrieval, filtering, comment-by-comment review, code changes, validation, final summary, or knowledge persistence. A draft shown to the user is not a published answer. Code-change approval in Step 4 and reply approval in Step 8 are separate decisions. Publish a reply only through Step 8 after both completion gates and that reply's individual approval.

### Step 0 — Read project knowledge (MANDATORY — Do This FIRST)

Before fetching comments or making any changes, read any previously learned knowledge about this project:

1. **Read `.ai-rules/`** — If the target project has an `.ai-rules/` directory, read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain previously learned coding conventions, validation commands, and review patterns. Apply coding conventions from `CODING.md` when crafting fixes. Use validation commands from `VALIDATION.md` in Step 5. Use review patterns from `REVIEWING.md` to better understand reviewer expectations.
2. **Read `projects/<project-name>/`** — If this plugin repository has a `projects/<project-name>/` directory (where `<project-name>` matches the target project's repo name), read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain knowledge shared across all skills in this plugin, discovered during past sessions with this project.
3. **Read `AGENTS.md`** — Follow all project-specific rules and conventions.

> **Rule:** Knowledge from `.ai-rules/`, `projects/<project-name>/`, and `AGENTS.md` takes precedence over generic guidelines in this skill.

### Step 1 — Fetch PR metadata and review comments

#### 1a — Fetch PR metadata

Before fetching comments, retrieve the PR metadata to identify the **head branch** and **base branch**. Compare the head branch to the currently checked-out branch to confirm you are on the correct branch.

Use the GitHub MCP `pull_request_read` tool:

```
server: user-github
toolName: pull_request_read
arguments:
  method: get_pull_request
  owner: <owner>
  repo: <repo>
  pullNumber: <number>
```

Extract from the response:
- `head.ref` — the PR branch name
- `base.ref` — the target branch name

**Branch validation:** Compare `head.ref` to the current git branch. If they don't match, **stop immediately** and inform the user which branch you're on vs. which branch the PR expects. Do NOT apply changes to the wrong branch.

#### 1b — Fetch review comments

Use the following **fallback chain** — try each source in order and stop at the first one that succeeds:

**Source 1 — GitHub MCP (preferred):**

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

Also fetch general PR comments (`get_comments`) in case reviewers left feedback there.

**Source 2 — `gh` CLI:**

```bash
gh api repos/<owner>/<repo>/pulls/<number>/comments
gh api repos/<owner>/<repo>/issues/<number>/comments
```

**Source 3 — Exported / attached PR document:**

If MCP is unavailable and `gh` is unauthenticated, the user may provide an exported HTML or text dump of the PR page. In this case:

- Parse comments from the document.
- Treat a comment as **likely still actionable** if:
  - It does NOT have an explicit "resolved" or "outdated" marker.
  - It references code that still exists in the current branch at the referenced location.
  - It was posted **after the most recent commit** (if timestamps are available).
- Treat a comment as **likely resolved/outdated** if:
  - It is visually collapsed or in a "resolved" section.
  - The code it references has been substantially changed or deleted since the comment was posted.
- When in doubt, include the comment in the actionable list but flag it as "unverified — from export" so the user can decide.

**Source 4 — Ask the user:**

If none of the above sources work, tell the user exactly what is blocked:

```
I could not retrieve PR comments:
- GitHub MCP: <reason it failed or "not configured">
- gh CLI: <reason it failed or "not authenticated">
- No exported PR document was provided.

To proceed, please either:
1. Configure GitHub MCP or authenticate `gh auth login`.
2. Provide an exported copy of the PR page (HTML or text).
3. Paste the review comments directly.
```

### Step 2 — Filter actionable comments

Review every active unresolved comment, including bot comments (e.g., Bugbot, CodeRabbitAI), before acting. When fetching GitHub comments, filter out resolved threads first. Read only each comment body and the minimum location or URL needed to act on it; do not read the entire JSON output or other unnecessary payload data.

#### Classification rules

**Actionable — keep:**
- Comments that explicitly request a code change.
- Comments that raise a concern implying a change is needed.
- **Reviewer questions that imply a requested change** — e.g., "Should this be handling the error case?" or "Wouldn't it be better to use X here?" are actionable if they clearly suggest the current code is wrong or suboptimal. Classify these as actionable and present the implied change to the user.

**Not actionable — discard:**
- Resolved threads (`isResolved: true`).
- Pure praise / acknowledgement with no requested change.
- Genuine questions seeking clarification that do NOT imply a code change (e.g., "What does this constant represent?" with no suggestion to rename or document it).

**Ambiguous reviewer questions:** If a comment is phrased as a question but you're unsure whether it implies a change, **keep it** and present it to the user as "Reviewer question (may imply a change)" so they can decide.

#### Deduplication — collapsing superseded comments

When multiple comments target the **same code path** (same file and overlapping line range, or same function/symbol):

1. If the later comment supersedes the earlier one (same concern, updated instruction), **keep only the latest** actionable comment.
2. If the earlier comment requests a **distinct change** from the later one (different concern), **keep both** as separate items.
3. When collapsing, note in the summary (Step 2b) that an older comment was superseded.

#### Disagreement handling

Fix only comments you agree with. If you disagree or are unsure, explain that clearly before moving on.

### Step 2b — Summarize skipped and excluded comments

Before presenting the actionable list, provide a brief summary of what was filtered out and why:

```
Filtered comments:
- X resolved threads (skipped — already resolved)
- Y praise/acknowledgement comments (skipped — no change requested)
- Z superseded comments (collapsed — newer comment covers the same issue)
- W comments from exported document flagged as likely outdated (skipped — code has changed)

Remaining actionable comments: N
```

This ensures the user is confident that older/outdated comments were reviewed and intentionally excluded, not accidentally missed.

### Step 3 — Present summary

Show the user a numbered list of all actionable comments (one line each) so they see the full scope before starting.

**If no actionable comments remain**, say so clearly:

```
No unresolved actionable review comments found on this PR.
All comments are either resolved, praise/acknowledgement, or superseded.
```

Do not imply there may be more comments or ask the user to double-check unless you used an exported document (Source 3), in which case add:

```
Note: Comments were retrieved from an exported document, not the live API.
If GitHub access becomes available, consider re-fetching to verify nothing was missed.
```

### Step 4 — Process comments ONE BY ONE

For each actionable comment, present this format, append the reply-draft block below, and stop to wait for user input.

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

**4. Proposed reply (draft — not published)**
- **Original target:** retain the PR URL and original comment URL and ID. For an inline review comment, also retain its review-thread ID when available. For a general PR comment, retain its original comment URL and ID.
- **Handling status:** `awaiting code-change decision` until the user decides; update it after processing to reflect the actual result.
- **Draft reply:** “I am reviewing this concern. I will update this draft after deciding whether to make the change and checking any approved change.”

This is a local draft, not an answer to the reviewer. Do not claim a change is complete before it is applied and validation is known. The yes/no/skip prompt above approves only the code change, never the reply. Keep the draft and original target identity together.

### Step 5 — Apply approved change and validate

After user approves:

1. Apply the change to the file.
2. Run repo-specific validation commands:

   **Discover the correct commands** using this priority order:
   1. Target project's `.ai-rules/VALIDATION.md`
   2. Plugin repo project knowledge: `projects/<project-name>/VALIDATION.md`
   3. `AGENTS.md`, `Makefile`, `package.json`, `Cargo.toml`, or equivalent project files
   4. `CONTRIBUTING.md`

   Do NOT assume any default targets — each project has its own names for formatting, linting, vetting, and testing.

   - If the project has no recognizable build system or the available targets are unclear, tell the user what you found and ask which commands to run.
   - Do NOT run tools directly (e.g., `go test ./...`, `golangci-lint run`, `pytest`). Use `make` targets or the project's specified task runner.

3. Present a **validation summary** after each change:

   ```
   Validation after Comment N:
   - Ran: <exact command 1>  →  ✅ PASS / ❌ FAIL
   - Ran: <exact command 2>  →  ✅ PASS / ❌ FAIL
   - ...

   Notes:
   - <any commands that were adapted from defaults, and why>
   - <any failures unrelated to this change>
   ```

4. If the validation fails **due to the change**, fix the issues and re-run until clean. If a failure is **unrelated** to the change (pre-existing issue), note it but proceed.
5. Show the user the result, then move to the next comment.

If the user says **no** or **skip**, make no code change. Update the reply draft as described below before moving to the next comment.

#### Refresh the reply draft

Update each comment’s draft after the user’s decision and any validation are complete:

- If addressed, state the actual change and relevant validation result.
- If declined or skipped, state that no change was made and give the actual reason or user-requested disposition.
- If the work is incomplete or validation failed, state that accurately; do not describe it as fixed.

Keep the original comment identity with the draft. Do not publish it here.

### Step 6 — Final summary

After all comments are processed, show:
- How many comments were addressed
- How many were skipped
- How many were filtered out in Step 2b (resolved, superseded, etc.)
- Remaining validation errors (if any unrelated ones exist)
- Each handled comment’s reply draft and handling status; keep all drafts unpublished until Step 8.

#### Optional: Fresh fetch verification

If GitHub API access is available (MCP or `gh`), suggest re-fetching PR comments to verify no new or missed comments exist:

```
All approved fixes have been applied. Would you like me to re-fetch PR comments
from GitHub to verify no unresolved comments were missed?
```

This is especially recommended when the original comments were retrieved from an exported document (Source 3). If the re-fetch finds new actionable comments, return to Step 2, process them through Steps 3–5, create and refresh their reply drafts, and update the final summary; do not proceed to knowledge persistence or reply confirmation until they are handled.

**DO NOT push the branch. DO NOT run `git push`.**

### Step 7 — Self-Improving Knowledge Persistence

> **After resolving PR comments, persist what you learned.** This creates a self-improving feedback loop so future review-fix sessions on the same project benefit from accumulated knowledge.

You MUST persist learned knowledge into **two layers**. Both use the same three-file structure:

- **`CODING.md`** — Best practices learned from this PR review: reviewer-requested patterns, coding conventions enforced, common mistakes flagged, pitfalls to avoid.
- **`VALIDATION.md`** — Exact validation and build commands used to verify fixes. Include formatting, vetting/type-checking, linting, testing, and building commands — the goal is to capture the exact commands that work for this project.
- **`REVIEWING.md`** — Review patterns and insights: what kinds of issues reviewers catch, preferred fix approaches, coding standards enforced during review, common reviewer expectations for this project.

#### Layer 1: Target project's `.ai-rules/` directory

Write to `.ai-rules/CODING.md`, `.ai-rules/VALIDATION.md`, and `.ai-rules/REVIEWING.md` inside the target project's own repository.

This captures knowledge that lives alongside the project code. Since the `.ai-rules/` folder is inside the target project repo itself, no `<project-name>` subdirectory is needed — the project identity is implicit from the repo.

#### Layer 2: Plugin repo's `projects/<project-name>/` directory

Write to `projects/<project-name>/CODING.md`, `projects/<project-name>/VALIDATION.md`, and `projects/<project-name>/REVIEWING.md` in this plugin repository (the repo where this skill lives).

This captures knowledge shared across ALL skills in this plugin repo. Any skill can read from `projects/<project-name>/` to benefit from knowledge discovered by other skills. For example, review patterns discovered by `pr-comment-resolver` are also available to `develop-feature` and `code-review`.

#### What to persist

**In `VALIDATION.md`:**
- Every validation command run during fix verification (exact `make` targets or equivalent).
- The correct order to run them.
- Any targets requiring special flags, environment variables, or build tags.
- Any CI-only validations that cannot be run locally — note as "CI-only, skip locally".

**In `CODING.md`:**
- Reviewer-requested coding patterns (e.g., "always use `errors.Wrap` instead of `fmt.Errorf` for wrapping").
- Common review findings for this project (e.g., "reviewers consistently flag missing nil checks on interface methods").
- Architecture conventions enforced during review (e.g., "all public functions must have godoc comments").
- Patterns the reviewer approved — things that work well and should be replicated.
- Any corrections or preferences expressed by reviewers that apply broadly.

**In `REVIEWING.md`:**
- What kinds of issues reviewers consistently catch for this project.
- Preferred fix approaches (e.g., "reviewers prefer `errors.Wrap` over `fmt.Errorf` for wrapping").
- Coding standards enforced during review (e.g., "all public functions must have godoc comments").
- Common reviewer expectations and patterns (e.g., "reviewers check for proper RBAC annotations on new controllers").

#### Persistence rules

1. **Append, don't replace.** If `CODING.md`, `VALIDATION.md`, or `REVIEWING.md` already exists, read it first and append new knowledge. Do not overwrite previously learned content.
2. **Deduplicate.** If the new knowledge is already captured, skip it.
3. **Create directories** if they don't exist (`.ai-rules/` in the target project, `projects/<project-name>/` in this plugin repo).
4. **Persist after all fixes are applied.** Write knowledge files after all approved changes pass validation, so the content reflects confirmed patterns.
5. **Include a timestamp header** for each entry so it's clear when the knowledge was captured.

### Step 8 — Approve and publish replies

Run this step after the Step 6 final summary and all Step 7 knowledge persistence are complete. If no actionable comment entered Step 4, there are no reply drafts and this step ends without a push-confirmation request or comment write.

#### Push confirmation gate

After the full review is complete, ask the user to explicitly confirm that the latest reviewed changes have been pushed. This includes any relevant edits made during knowledge persistence. If no changes were made, the user may explicitly confirm that the reviewed state is current and there is nothing to push. A confirmation given before this step, before later comments were processed, or before later fixes does not satisfy the gate; ask again after the final summary. Never infer confirmation from code-change approval, branch or remote state, or a detected commit, and never push on the user’s behalf. Until the gate is met, leave every draft pending and do not answer any comment.

#### Separate approval for each reply

After the push gate is met:

1. Present only the next comment, its original quote and URL/ID/thread identity, its handling status, and the exact current reply draft. Ask whether the user approves that exact reply to that exact comment. Wait for the answer before writing or presenting the next draft. A general or blanket approval does not approve any individual reply.
2. Publish only after an explicit approval of the exact text. Use an available supported capability that replies in the original inline review thread or original general-comment context. Do not substitute an unrelated top-level comment. If the capability or target identity is unavailable or uncertain, leave the draft pending and explain why.
3. Post exactly the approved text. If the text changes after it was shown, present the revised exact text and get fresh approval. If a write result is uncertain, verify whether it posted before considering a retry; do not blindly send a duplicate.
4. After each answer, report whether that reply was posted, declined, skipped, or left pending. A no/skip response publishes nothing; only after receiving it may you move to the next comment. Silence means wait. Obtain a separate explicit decision for every remaining reply.
5. If the user requests or approves a new code fix after push confirmation, stop the reply sequence. Apply and validate the fix through the normal review steps, refresh affected drafts, complete the final summary and knowledge persistence, then obtain fresh confirmation that the latest changes were pushed before resuming. Any changed reply text also requires fresh approval.

Use the supported integration’s reply operation for the matching original target; do not invent an API or claim success without a confirmed write. Do not resolve threads automatically. At completion, report posted, declined, skipped, and pending replies accurately. See [reply workflow acceptance scenarios](reply-workflow-scenarios.md).

## Important Rules

- If `repo-folder` is provided, `cd` into it before making changes.
- Always read the file before editing to get current content. If CodeGraph is available, use `codegraph_explore` to understand the surrounding code context (callers, callees, impact) before making changes.
- Never batch multiple code changes or comment replies together — obtain separate approval and process one item at a time.
- Never push to remote.
- Always add docstrings to new functions.
- Use `--signoff` on any commits, never add `Made-with: Cursor`.
