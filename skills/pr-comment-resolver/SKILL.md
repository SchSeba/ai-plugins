---
name: pr-comment-resolver
description: Resolve PR review comments one-by-one with user approval. Use when the user provides a pull request link and wants to address review comments, resolve PR feedback, or fix code based on reviewer suggestions.
---

# PR Comment Resolver

Resolve pull request review comments interactively, one at a time, with explicit user approval before each change. Keep each comment's reply unset until its relevant implementation is complete, the final candidate PR change set supports the change, and applicable validation has been checked. The final change set is the PR head compared with its base; while approved work is still uncommitted, inspect the candidate tree against that same base. Publish an eligible reply only after the full review and knowledge persistence are complete, the user confirms the latest reviewed PR head was pushed, and the user separately approves that exact reply.

## Input Format

```text
<repo-folder(optional)> <pull-request-link>
```

- `repo-folder` — optional subdirectory when the workspace contains multiple projects.
- `pull-request-link` — GitHub PR URL (e.g. `https://github.com/owner/repo/pulls/42`).

Parse `owner`, `repo`, and `pullNumber` from the link.

## Workflow

> **CodeGraph-first rule:** If the CodeGraph MCP server is configured and available, use `codegraph_explore` throughout this workflow to understand the code context around review comments — callers, callees, and blast radius of the symbols being discussed. This helps craft better fixes by understanding the full impact. If CodeGraph is available but the project has no `.codegraph/` directory, run `codegraph init` in the project root first to build the initial graph. If CodeGraph is not available, **inform the user** and fall back to manual file reading.

## Reply safeguards

Apply the reply workflow below to every PR, regardless of its owner, repository, or optional local folder. Keep a per-comment record containing the PR URL, original comment URL and ID, inline review-thread ID when available, quoted comment, handling status, and reply state. Start with the reply unset. Draft a concise reply only after the relevant implementation is complete, the final candidate PR change set shows a change that addresses that comment, and applicable validation is checked. Define that change set as the PR head compared with its base. If approved work is not yet committed, inspect the candidate tree against the same base; once committed, use the final head-to-base change set, including fixes amended, squashed, rebased, or incorporated into existing commits. A clean worktree, unchanged commit count, or no newly created commit does not disqualify a fix present in that change set. Record the relevant file and hunk or symbol, the PR base and head revisions when available, and the actual validation outcome with that comment's evidence.

A reply may describe only the concrete applied change supported by that comment's resulting-diff evidence. Do not use a pending-work promise, generic status update, unsupported fix or test claim, or change unrelated to the comment. If there is no checked applied resolution, tell the user clearly that there is no applied resolution to report; leave reply text unset and unavailable for publication.

Never publish a reply or otherwise answer a review comment during retrieval, filtering, comment-by-comment review, code changes, validation, final summary, or knowledge persistence. Code-change approval and reply approval are separate decisions. Publish only an eligible reply through Step 8, after the full-review and latest-push gates and that reply's individual approval.

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

```text
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

Use the following **fallback chain** independently for the inline-review and general-comment endpoints. A source is complete only after every page for both endpoints in use has been retrieved; a successful first response is not enough.

**Source 1 — GitHub MCP (preferred):**

Call `get_review_comments` for inline review comments and `get_comments` for general PR comments, using `perPage: 100`. For each endpoint, follow its next-page metadata or links. If none are exposed, request successive pages with `page` (or the tool's equivalent) until an empty page confirms exhaustion; do not infer exhaustion from a short page unless the API explicitly documents that as its final page. If the MCP method cannot request later pages or establish that pagination is exhausted, treat that endpoint as incomplete and continue to Source 2 for it.

Do not discard resolved, outdated, or superseded comments until Step 2 has checked whether they contain relevant history for a current request.

**Source 2 — `gh` CLI:**

For each endpoint Source 1 could not retrieve completely, use the GitHub CLI's documented pagination feature for the corresponding inline-review or general-comment API endpoint. Verify that it follows every page and that no next page remains before treating that endpoint as complete.

If results from more than one source are combined, deduplicate by comment ID while preserving each comment's original target and status. If pagination fails or cannot be confirmed for either endpoint, retain the available comments but mark history retrieval incomplete.

**Source 3 — Exported / attached PR document:**

If neither API source can establish complete history, the user may provide an exported HTML or text dump of the PR page. Treat it as complete only when its contents or accompanying metadata establish that it includes every page of both inline review comments and general PR comments. If coverage is partial or uncertain, history remains incomplete. In this case:

- Parse comments from the document.
- Treat a comment as **likely still actionable** if:
  - It does NOT have an explicit "resolved" or "outdated" marker.
  - It references code that still exists in the current branch at the referenced location.
  - It was posted **after the most recent commit** (if timestamps are available).
- Treat a comment as **likely resolved/outdated** if:
  - It is visually collapsed or in a "resolved" section.
  - The code it references has been substantially changed or deleted since the comment was posted.
- If coverage is complete but a comment's status or actionability remains unclear, include it as "unverified — from export" so the user can decide. If coverage itself is uncertain, ask for the missing pages before assessing requests.

**Source 4 — Ask the user:**

If no source establishes complete comment history, tell the user exactly what endpoint or pages are blocked:

```text
I could not retrieve PR comments:
- GitHub MCP: <reason it failed or "not configured">
- gh CLI: <reason it failed or "not authenticated">
- No export establishing complete inline and general comment history was provided.

To proceed, please either:
1. Configure a GitHub MCP source that can retrieve every page or authenticate the GitHub CLI.
2. Provide an exported copy of the PR page (HTML or text) that includes every page of both comment streams.
3. Provide the missing pages and confirm they complete the inline and general comment history.
```

### Step 2 — Filter actionable comments

Before assessing a request, confirm that inline and general comment pagination is exhausted or that complete coverage is otherwise established. If any endpoint or page remains unavailable, report exactly what could not be retrieved and mark history incomplete. Do not make a validity disposition or propose a fix until the missing history or context is supplied.

Review fetched inline and general comments before filtering anything out. For every current or potentially actionable request, inspect earlier comments concerning the same or nearby code area: the same file, nearby or overlapping lines, symbol, behavior, or code path. Include resolved and outdated inline threads where available, and general comments that explain the earlier decision. Keep only relevant history, and associate each relevant comment's original URL and ID, inline thread ID when available, active/resolved/outdated status, quote, and stated rationale with the current request. If a field or rationale is unavailable, record that; do not infer it. Read only the comment text and the minimum location or URL needed to assess relevance; do not read the entire JSON output or unrelated payload data.

Reassess both the current request and any earlier rationale against the current code and context. History informs the decision; it does not by itself accept or reject the request. Before suggesting a fix, record a reasoned per-comment disposition: **valid**, **invalid**, or **needs context**, with a brief explanation. For a valid request, state the expected behavior and relevant regression cases. For an API-field rename request, trace the field declaration and relevant references before proposing a fix: inspect dependent functions and helpers, callers, tests and fixtures, and documentation whose names or behavior depend on the field. Record which surrounding names/usages need coordinated changes, why any old-name reference is retained (including compatibility or wire-format names), and include this impact in the expected behavior. Preserve unrelated names and intentional compatibility references; do not apply a blanket rename. For an invalid request, explain why and do not suggest a change. If the request needs context, identify the missing evidence and ask the user; do not assume or propose a change until the ambiguity is resolved. Reviewer assertion or actionability alone is not approval to change code.

Only after this history and validity pass, filter comments for actionability and apply the classification and deduplication rules below. Keep relevant resolved, outdated, or superseded comments as context even when they are excluded from the active work list.

#### Establish production provenance before compatibility changes

Before proposing backward-compatibility handling, inspect the authoritative main/master or documented production baseline at an identified revision. Establish which revision is actually deployed or authoritative; branch spelling alone is not proof, especially when production follows a release branch. Compare the baseline declaration and serialized/wire contract with the PR additions. Record the baseline revision, file/symbol evidence, comparison, and conclusion in the per-comment record before proposing a fix.

Preserve proven existing production contracts where compatibility warrants it. Fields introduced and removed within this unpublished PR require no compatibility shim, legacy-name preservation, or protobuf-number reservation comment solely for backward compatibility. For example, when the PR adds two protobuf fields and then removes one, do not reserve the removed field's number solely for compatibility if evidence confirms it never existed in production. Other independently established protocol constraints still apply. If baseline access or history is unavailable or inconclusive, mark needs context and request evidence; never assume absence. Apply this provenance check to retained old-name references in the rename audit as well.

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

After the history pass, when multiple current requests target the **same code path** (same file and overlapping line range, or same function/symbol):

1. If the later comment supersedes the earlier one (same concern, updated instruction), **keep only the latest** actionable request in the active list, while retaining the earlier comment's target, status, quote, and rationale as context.
2. If the earlier comment requests a **distinct change** from the later one (different concern), **keep both** as separate items.
3. When collapsing, note in the summary (Step 2b) that an older request was superseded and preserve any relevant rationale.

#### Disagreement handling

Fix only comments you agree with. If you disagree or are unsure, explain that clearly before moving on.

### Step 2b — Summarize skipped and excluded comments

Before presenting the actionable list, provide a brief summary of what was filtered out and why. Also note that relevant older discussion was reviewed and retained as context, including resolved or outdated items where available:

```text
Filtered comments:
- X resolved threads (skipped — already resolved)
- Y praise/acknowledgement comments (skipped — no change requested)
- Z superseded comments (collapsed — newer comment covers the same issue)
- W comments from exported document flagged as likely outdated (skipped — code has changed)

Remaining actionable comments: N
```

This ensures the user is confident that older/outdated comments were reviewed and intentionally excluded, not accidentally missed.

### Step 3 — Present summary

Show the user a numbered list of the current requests so they see the full scope before starting. For each request, include its history-informed disposition and reason; for valid requests, also state the expected behavior. Include relevant earlier comment identities/statuses and their rationale. Invalid requests get an explanation and no proposed fix. For a request marked needs context, state what is missing and ask for that context before proposing a fix or requesting code-change approval.

**If no actionable comments remain**, say so clearly:

```text
No unresolved actionable review comments found on this PR.
All comments are either resolved, praise/acknowledgement, or superseded.
```

Do not imply there may be more comments or ask the user to double-check unless you used an exported document (Source 3), in which case add:

```text
Note: Comments were retrieved from an exported document, not the live API.
If GitHub access becomes available, consider re-fetching to verify nothing was missed.
```

### Step 4 — Process comments ONE BY ONE

For each request with a valid disposition, create or update its per-comment record, present this format, and stop to wait for the user's code-change decision. Record invalid requests with the reason and no proposed fix; for requests needing context, ask for that context and wait before suggesting a change. Do not draft a reply in this step.

---

#### Comment N of M

**1. Original target:** PR URL, original comment URL and ID, and inline review-thread ID when available. Preserve these identifiers with this comment throughout the workflow.

##### 2. Reviewer comment

> Quoted reviewer text

**3. Related history:** earlier comment URL/ID and thread ID when available, status, quote, and rationale; say when none was found or a detail is unavailable

**4. Validity assessment:** valid / invalid / needs context, with the reason. History informs this decision but does not determine it.

**5. Expected behavior and relevant regression cases:** required for a valid request

**6. Handling status:** awaiting code-change decision for a valid request

**7. Code snippet** (the relevant code from the current branch, with file path and line numbers)

##### 8. Suggested change

```text
Your proposed code change
```

Approve this change? (yes / no / skip)

Ask this only for a valid request with a proposed change. Invalid requests have no change to approve; needs-context requests wait for the missing information and a fresh assessment.

**Reply state:** unset — no reply text exists. Do not draft until the approved implementation is complete and checked in Step 5.

---

**CRITICAL: Do NOT proceed to the next comment until the user responds.**

The yes/no/skip prompt approves only the code change, never a reply. Keep the comment identity, quote, handling status, and reply state associated in the same record.

### Step 5 — Apply approved change and validate

For each valid request, restate its expected behavior and relevant regression cases before applying the user's approved change. After applying it:

1. Run repo-specific validation commands:

   **Discover the correct commands** using this priority order:
   1. Target project's `.ai-rules/VALIDATION.md`
   2. Plugin repo project knowledge: `projects/<project-name>/VALIDATION.md`
   3. `AGENTS.md`, `Makefile`, `package.json`, `Cargo.toml`, or equivalent project files
   4. `CONTRIBUTING.md`

   Do NOT assume any default targets — each project has its own names for formatting, linting, vetting, and testing.

   - If the project has no recognizable build system or the available targets are unclear, tell the user what you found and ask which commands to run.
   - Do NOT run tools directly (e.g., `go test ./...`, `golangci-lint run`, `pytest`). Use `make` targets or the project's specified task runner.

2. For API-field rename requests, compare the reference map recorded in Step 4 with the resulting change set. Verify that dependent identifiers and call sites are updated where warranted, tests/fixtures and documentation reflect the expected names, and each retained old-name reference has a recorded reason. Preserve intentional compatibility or wire-format references instead of requiring a blanket replacement. A stale dependent reference or unexplained retained name means the expected behavior is unproven and the reply is ineligible until it is addressed. Include this audit in the focused behavior evidence and report the actual applicable validation outcomes.

3. Perform a focused behavior check against the stated expectation and regression cases. Use a targeted reproduction or regression test when feasible; otherwise trace the resulting code and diff against the expected behavior and relevant edge cases. Record what was checked and the observed result. Passing general project checks alone does not establish the expected behavior.
4. Present a **validation summary** after each change:

   ```text
   Validation after Comment N:
   - Ran: <exact command 1>  →  ✅ PASS / ❌ FAIL
   - Ran: <exact command 2>  →  ✅ PASS / ❌ FAIL
   - ...

   Notes:
   - <any commands that were adapted from defaults, and why>
   - <any failures unrelated to this change>
   ```

5. If an applicable project check fails because of the change, or the focused behavior check fails or does not demonstrate the expectation, fix the issue and repeat the checks. A comment is not eligible for a reply while an applicable check is failed or blocked, or expected behavior remains unproven. Record unrelated failures in the validation summary without claiming they passed.
6. Show the user the result and actual validation outcomes, then move to the next comment.

If the user says **no** or **skip**, make no code change and leave the reply unset. Tell the user: **No applied resolution to report** — followed by the actual disposition. Do not turn that status into a reply draft.

#### Separate approval before any rebase

Before executing any rebase, show the actual applied Git changes, including the final candidate PR change set and staged or unstaged corrections, current head revision, and intended target revision/branch and rebase operation. Let the user review that concrete candidate, then wait for separate explicit user rebase approval. Do not execute a rebase before this review and approval.

Code-change approval, push confirmation, reply approval, silence or blanket consent do not substitute for rebase approval. Decline or skip leaves history unchanged; silence means wait. Changed candidate changes, head, target revision, or operation invalidate approval and require presenting the updated candidate and obtaining fresh approval. If approval is unavailable, preserve completed independent edits and report the pending rebase gate without claiming conflict resolution. After an approved rebase, perform the evidence refresh below and repeat affected validation; never push.

#### Determine reply eligibility

After an approved implementation is complete, and again after any later code edit or revert:

1. Inspect the current resulting diff against the original comment. Record per comment the concrete file and relevant hunk or symbol that addresses the concern. A shared change may address several comments only when the evidence and association are recorded separately for each one.
2. Record the actual validation outcome for that implementation, including exact checks and results. Applicable checks must pass. If no automated check applies, record that fact and the manual diff checks performed. Keep unrelated failures visible and accurately described.
3. Only now draft a short, factual explanation of the concrete behavior changed. Every claim must match both the original concern and its recorded diff evidence. Mention tests or other checks only when their recorded result supports the claim. Do not use a generic acknowledgement, a pending or future-work promise, a claim that the concern was fixed without matching diff evidence, or a claim about unrelated changes.
4. If the request was assessed as invalid or still needs context, the user declined or skipped the change, implementation is incomplete, the change was reverted, no related change appears in the current diff, an applicable check failed or is blocked, or the focused behavior evidence does not support the expected behavior, keep reply text unset and mark the record ineligible. Tell the user clearly: **No applied resolution to report** — [actual reason]. Do not propose a reply or publish a status message.

Any later edit that changes the relevant diff or validation state invalidates that comment's evidence and draft. After every rebase, re-evaluate the evidence against the new final head-to-base change set. If the rebase changes relevant content or validation state, invalidate the affected evidence and draft, recheck applicable validation, and draft again only after the new evidence qualifies. A rebase that only changes commit arrangement while leaving the relevant change and validation evidence intact does not require an uncommitted worktree diff or a new commit. If an already presented reply is affected, its approval is invalid; changes after push confirmation also require completing the review again and obtaining fresh push confirmation for the latest reviewed PR head.

### Step 6 — Final summary

After all comments are processed, show:

- How many comments have a checked applied resolution and how many were declined, skipped, incomplete, or otherwise have no applied resolution to report
- How many comments were filtered out in Step 2b (resolved, superseded, etc.)
- Each request's history-informed validity disposition and reason, including relevant earlier comment identities, statuses, and rationale
- Stated expected behavior and focused behavior-check results alongside actual project validation outcomes and remaining errors, including unrelated failures
- Each eligible comment's exact reply draft, handling status, original target identity, and recorded diff evidence
- For each ineligible comment, state **No applied resolution to report** with the actual reason; keep its reply unset

Keep every eligible reply unpublished until Step 8.

#### Optional: Fresh fetch verification

If GitHub API access is available (MCP or `gh`), suggest re-fetching PR comments to verify no new or missed comments exist:

```text
All approved fixes have been applied. Would you like me to re-fetch PR comments
from GitHub to verify no unresolved comments were missed?
```

This is especially recommended when the original comments were retrieved from an exported document (Source 3). If the re-fetch finds new actionable comments, return to Step 2 and process them through Steps 3–5. Keep each new reply unset until its relevant implementation and checks qualify under Step 5, then update the final summary; do not proceed to knowledge persistence or reply confirmation until the comments are handled.

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

Run this step after the Step 6 final summary and all Step 7 knowledge persistence are complete. If no comment has an eligible reply, report that there is no applied resolution to report for ineligible comments and end without a push-confirmation request or comment write. Never ask the user to approve or publish an ineligible status message.

#### Push confirmation gate

After the full review and knowledge persistence are complete, and only when at least one eligible reply exists, ask the user to explicitly confirm that the latest reviewed PR head has been pushed. This includes any relevant edits made during knowledge persistence. If no changes were made, the user may explicitly confirm that the reviewed state is current and there is nothing to push. A confirmation given before this step, before later comments were processed, or before later fixes does not satisfy the gate; ask again after the final summary. Never infer confirmation from code-change approval, branch or remote state, or a detected commit, and never push on the user’s behalf. Until the gate is met, leave every eligible draft pending and do not answer any comment. If a later edit invalidates resolution evidence, complete the required checks and review again before asking for fresh confirmation.

#### Separate approval for each reply

After the push gate is met:

1. Recheck that the current diff and validation evidence still support the next eligible reply. Present only that comment's original quote and URL/ID/thread identity, handling status, and exact current reply. Ask whether the user approves that exact reply for that exact comment. Wait for the answer before writing or presenting another reply. A general or blanket approval does not approve any individual reply.
2. Never present an ineligible comment for reply approval. If its resolution evidence is absent or stale, leave the reply unset, report **No applied resolution to report** with the actual reason, and do not publish.
3. Publish only after explicit approval of the exact text and while its evidence remains current. Use an available supported capability that replies in the original inline review thread or original general-comment context. Do not substitute an unrelated top-level comment. If the capability or target identity is unavailable or uncertain, leave the draft pending and explain why.
4. Post exactly the approved text. If the text changes after it was shown, present the revised exact text and get fresh approval. If a write result is uncertain, verify whether it posted before considering a retry; do not blindly send a duplicate.
5. After each answer, report whether that reply was posted, declined, skipped, or left pending. A no/skip response publishes nothing; only after receiving it may you move to the next eligible reply. Silence means wait. Obtain a separate explicit decision for every remaining reply.
6. If the user requests or approves a new code fix after push confirmation, stop the reply sequence. Apply and validate the fix through the normal review steps, recheck affected diff evidence, complete the final summary and knowledge persistence, then obtain fresh confirmation that the latest changes were pushed before resuming. Any changed reply text also requires fresh approval.

Use the supported integration’s reply operation for the matching original target; do not invent an API or claim success without a confirmed write. Do not resolve threads automatically. At completion, report posted, declined, skipped, and pending eligible replies accurately, along with comments that have no applied resolution to report. See [reply workflow acceptance scenarios](reply-workflow-scenarios.md).

## Important Rules

- If `repo-folder` is provided, `cd` into it before making changes.
- Always read the file before editing to get current content. If CodeGraph is available, use `codegraph_explore` to understand the surrounding code context (callers, callees, impact) before making changes.
- Never batch multiple code changes or comment replies together — obtain separate approval and process one item at a time.
- Never push to remote.
- Always add docstrings to new functions.
- Use `--signoff` on any commits, never add `Made-with: Cursor`.
