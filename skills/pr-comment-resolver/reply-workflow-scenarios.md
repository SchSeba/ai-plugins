# PR reply workflow acceptance scenarios

These documentation scenarios apply to every repository and local folder. They define acceptance behavior for [SKILL.md](SKILL.md); they do not send live replies. Run the repeatable local check from the repository root with `python3 skills/pr-comment-resolver/check_reply_workflow.py`.

## Comment-history pagination

| Scenario | Expected behavior |
| --- | --- |
| A PR has more than 100 inline review comments or general comments, and relevant rationale appears after the first page | Retrieve successive pages for each endpoint until pagination is exhausted, retain the later-page comment's target, status, quote, and rationale, then assess the current request against it. Do not treat the first successful page as complete history. |
| MCP returns the first page but cannot fetch or confirm later pages; the authenticated GitHub CLI's documented pagination feature succeeds | Use the complete fallback results for that endpoint, deduplicate by comment ID if combining sources, and proceed only after both inline and general comment histories are complete. |
| A later page fails, and no other source establishes complete coverage | Name the endpoint and unavailable page or pagination evidence, mark history incomplete, and ask the user for the missing context. Do not assign a valid/invalid disposition or propose a fix. |
| An export omits page metadata and its coverage cannot be established | Treat history as incomplete and ask for the missing pages or confirmation backed by the export; do not assess the request or propose a fix based on a possibly partial history. |

## Positive diff-to-reply fixture

Reviewer comment: “Please reject a nil request before reading req.User.”

Before:

~~~go
func handle(req *Request) error {
    return process(req.User)
}
~~~

Applied diff:

~~~diff
 func handle(req *Request) error {
+    if req == nil {
+        return ErrMissingRequest
+    }
     return process(req.User)
 }
~~~

After the implementation is complete, the current diff is checked against this comment, and applicable validation is recorded as passed, an eligible concise reply is: “Added a nil-request guard that returns ErrMissingRequest before reading req.User.” The evidence record identifies this comment, the changed guard in the resulting diff, and the actual validation outcome. No test claim is needed.

## History-informed assessment and behavior validation

| Scenario | Expected behavior |
| --- | --- |
| An earlier resolved review rejected a nil guard because callers previously guaranteed a non-nil request, but the current API now accepts requests from untrusted callers | Preserve the earlier comment's target, resolved status, quote, and rationale. Reassess against current code and API context; mark the current request valid because the old assumption changed, state that nil must be rejected before reading `req.User`, and list nil and non-nil regression cases before proposing a fix. |
| An earlier comment explains that retrying permission errors breaks the caller's fail-fast behavior, and the current code and context still have that contract | Preserve the earlier rationale and independently reassess the request to retry every error. Mark it invalid with the concrete reason, do not suggest a code change, and keep reply text unset. The earlier comment informs the decision but is not an automatic veto. |
| Relevant earlier discussion cannot be retrieved, or an earlier rationale depends on migration/context that is not available | State which history or context is missing, mark the request needs context, and ask the user for it before proposing a fix or requesting code-change approval. Do not assume the prior request is valid or invalid. |
| Applicable project checks pass, but a focused reproduction still reads `req.User` before rejecting nil | Report the observed behavior mismatch. The change is not resolved and no reply is eligible, despite passing general checks. Fix and recheck or leave the reply unset. |
| The expected nil behavior and regression cases are stated, the approved change enforces them, applicable project checks pass, and focused behavior evidence confirms the result | Record exact check outcomes and observed behavior against the expectation. The resolution may become eligible for a factual reply, subject to the existing final-diff and publication gates. |

## API-field rename impact

Fixture production evidence: the authoritative production baseline is `main` at fixture revision `prod-v1`; `account.go` declares `Account.DisplayName` with `json:"displayName"`, and its serialized contract is confirmed in `API.md` at that revision. These are scenario identifiers, not claims about this repository's production code. The PR comparison therefore establishes an existing production JSON key.

Reviewer request: “Rename `Account.DisplayName` to `Account.DisplayLabel`.” The dependency review records the field declaration, `displayNameFor` helper, its `accountSummary` caller, the corresponding test, and the API guide. `PreferredDisplayName` is unrelated and must remain unchanged.

Before:

~~~go
type Account struct {
    DisplayName          string `json:"displayName"`
    PreferredDisplayName string `json:"preferredDisplayName"`
}

func displayNameFor(account Account) string { return account.DisplayName }
func accountSummary(account Account) string { return displayNameFor(account) }
~~~

Applied diff:

~~~diff
--- a/account.go
+++ b/account.go
@@
-    DisplayName          string `json:"displayName"`
+    DisplayLabel         string `json:"displayName"`
     PreferredDisplayName string `json:"preferredDisplayName"`
@@
-func displayNameFor(account Account) string { return account.DisplayName }
-func accountSummary(account Account) string { return displayNameFor(account) }
+func displayLabelFor(account Account) string { return account.DisplayLabel }
+func accountSummary(account Account) string { return displayLabelFor(account) }
--- a/account_test.go
+++ b/account_test.go
@@
-    got := displayNameFor(account)
+    got := displayLabelFor(account)
--- a/API.md
+++ b/API.md
@@
-`Account.DisplayName` is rendered by `displayNameFor`.
+`Account.DisplayLabel` is rendered by `displayLabelFor`.
~~~

The resulting change coordinates the public field, dependent helper and caller, test, and documentation. The `json:"displayName"` key is intentionally preserved to keep the existing wire format, and `PreferredDisplayName` stays because it is unrelated. The reply can become eligible only after the final change set and applicable validation plus focused behavior evidence confirm this outcome.

| Scenario | Expected behavior |
| --- | --- |
| An API field and its dependent helper, caller, test, and documentation names are renamed together as in the fixture | Record the reference map before approval; verify each dependent update against the resulting change set and focused behavior. The coordinated rename may qualify when applicable checks pass. |
| An old field spelling remains as a documented JSON wire-format key to preserve compatibility | Record the compatibility reason and verify the serialized contract; preserve the intentional old-name reference while updating dependent identifiers. |
| The API field is renamed but a dependent helper, caller, test, or documentation reference remains stale without a compatibility reason | Treat the expected behavior as unproven, report the stale reference, and keep the reply ineligible until the dependency is corrected and checks are repeated. |

## Production-baseline compatibility scenarios

| Scenario | Expected behavior |
| --- | --- |
| An existing production field is renamed, as confirmed by the identified baseline revision and file evidence above | Preserve the established JSON wire key with a recorded compatibility reason and verify serialization. |
| A field exists only in the unpublished PR and is removed before publication | Compare the identified production baseline with the PR additions, record absence and removal evidence, and add no compatibility shim or legacy-name preservation solely for compatibility. |
| The PR adds two protobuf fields, `label = 10` and `hint = 11`, then removes `hint`; the authoritative baseline at fixture revision `prod-v1` has neither field nor those numbers in `account.proto` | Record baseline and PR comparison evidence. Keep `label = 10`; add no protobuf-number reservation comment for removed `hint = 11` solely for backward compatibility. Check any independent protocol constraints separately. |
| The production baseline or relevant history cannot be retrieved | Mark needs context, request revision/file evidence, and do not assume the field is PR-only or propose compatibility handling. |
| Production follows a documented release revision rather than main/master | Compare against that identified production revision; branch naming alone does not establish provenance. |

## Rebase approval scenarios

| Scenario | Expected behavior |
| --- | --- |
| Corrections span multiple PR commits | Keep corrections uncommitted while approval is pending. Show the complete candidate diff and map each correction/hunk to the existing commit SHA and subject it will enter, along with current head/base, target revision, and operation. |
| A correction could reasonably belong in more than one existing commit | Ask the user to clarify its destination; do not guess or begin the rebase. |
| The user reviews the candidate and explicit existing-commit map, then approves the stated rebase | Integrate corrections only into those approved existing commits, without creating fixup commits (including temporary autosquash fixups), then refresh final head-to-base evidence and affected validation before any reply becomes eligible. |
| The user declines or skips the rebase | Leave history unchanged and preserve the uncommitted corrections; do not claim conflicts resolved. |
| The user is silent or gives only code-change approval, push confirmation, reply approval or blanket consent | Wait without rebasing; those decisions do not approve the rebase. |
| Candidate changes, head/base, target revision, operation, or commit-placement map changes after approval | Invalidate stale approval, show the updated candidate and map, and wait for fresh explicit rebase approval. |

## Acceptance scenarios

| Scenario | Expected behavior |
| --- | --- |
| A comment is being reviewed while other comments remain | Preserve its PR URL, original comment URL and ID, inline thread ID when available, quote, and handling status. Reply state remains unset; show no proposed reply before implementation. |
| An approved change is fully applied and checked | Inspect the final PR head-to-base change set against this specific comment, record its file and relevant hunk or symbol plus actual validation results, then draft a concise factual reply about the applied behavior. |
| One change addresses multiple comments | Preserve a separate comment identity and diff-evidence association for each. Draft only when the evidence shows how the change resolves that specific comment. |
| Generic acknowledgement such as “This is being handled” | Reject it as a reply: it does not explain a concrete applied change. |
| Pending or future-work text such as “I am reviewing this concern” or “I will update this after checking” | Reject it. Do not draft before the implementation and checks are complete. |
| A diff for another concern is cited as resolution evidence | Reject the reply for this comment. A nearby or shared-file change is insufficient unless its resulting behavior addresses this comment. |
| A reply claims a fix absent from the diff | Keep reply unset and report **No applied resolution to report** with the actual reason. |
| An otherwise valid fixture reply gains “All tests passed” without recorded test evidence | Reject the complete reply; this fixture supports the nil-request guard only, so the added test claim has no evidence. |
| A reply claims tests passed but no such checks ran, or the recorded checks failed | Reject the claim. Do not draft while an applicable validation check is failed or blocked. |
| The user declines or skips the code change | Make no change, keep reply unset, and state **No applied resolution to report** with the actual disposition. |
| The implementation is incomplete, reverted, or absent from the current diff | Keep reply unset and state **No applied resolution to report** with the actual reason. |
| Applicable validation fails or is blocked | Keep reply unset and state **No applied resolution to report**. A code approval, push confirmation, or reply approval cannot make it eligible. |
| No automated check applies to the changed files | Record that no automated check applies and the manual diff checks performed. Draft only if the completed relevant change is confirmed by those checks. |
| A later edit or revert changes the relevant diff or validation state | Invalidate the affected evidence and draft. Recheck before drafting; any prior reply approval and latest-push confirmation affected by the edit are stale. |
| An approved rebase integrates a fix into its mapped existing commits and the worktree is clean | If the final PR head-to-base change set still contains the relevant fix and applicable validation is checked, keep it eligible. A clean worktree or lack of a newly created commit does not disqualify it; no fixup commit is created. |
| A rebase changes the relevant content or validation state after a draft was prepared | Treat the prior evidence and draft as stale. Recheck the new final PR head-to-base change set and applicable validation before drafting again; latest-push confirmation must cover the final reviewed PR head. |
| Final summary or knowledge persistence is incomplete | Do not ask for push confirmation and do not publish. Finish the full review and knowledge step first. |
| All review and knowledge steps are complete and eligible replies exist | Ask for explicit confirmation that the latest reviewed changes were pushed. Earlier confirmation, branch state, or a detected commit is insufficient. |
| No comment has an eligible reply | State that there is no applied resolution to report for ineligible comments. Do not ask for push confirmation or perform a comment write. |
| User confirms latest push; replies A and B are eligible | Present only A's original quote, target identity, and exact reply; wait for separate approval. Publish only A if approved, then present B. |
| User approves A, declines B, or does not answer | Publish only A's exact approved text. Record B as declined if declined; if unanswered, wait. Never infer approval from silence or blanket approval. |
| Reply text changes after it was approved for presentation | Obtain fresh approval for the revised exact text before publishing it. |
| Reply operation is unavailable, target identity is uncertain, or a write result is uncertain | Leave the reply pending; do not substitute a top-level comment or blindly retry. Verify an uncertain write first. |
| A reply targets an inline review comment or general PR comment | Preserve the original comment URL and ID, plus inline thread ID when available. Reply only in its matching original context. |
| No actionable comment entered Step 4 | Report that no actionable comments were found. Do not ask for push confirmation or perform a comment write. |
| Target PR is kubernetes/kubernetes or example/widgets from an arbitrary local folder | Apply the same eligibility, evidence, identity, full-review, latest-push, and individual-approval rules. Repository and folder names do not change the workflow. |
