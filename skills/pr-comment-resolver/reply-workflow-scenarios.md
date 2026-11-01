# PR reply workflow acceptance scenarios

These documentation scenarios check the reply safeguards in [SKILL.md](SKILL.md) across Kubernetes and other repositories. They do not send live replies.

| Scenario | Expected behavior |
| --- | --- |
| A comment is being reviewed while other comments remain | Show the clearly labeled **Proposed reply (draft — not published)** with the original target identity. Do not write a reply or otherwise answer the reviewer. |
| The final summary or knowledge persistence is incomplete | Do not ask for push confirmation and do not publish a reply. Finish the review sequence first. |
| The user confirmed a push before later comments or fixes were processed | Treat that confirmation as stale. After the final summary and knowledge persistence, request fresh confirmation covering the latest reviewed changes. |
| The full review is complete and the user confirms the latest changes were pushed | Present only the first comment with its exact current draft and target identity; wait for a separate decision. |
| Replies A and B are pending; the user approves A | Publish only A's exact approved text in A's original thread/context. Report its result, then present B and wait. |
| The user declines or skips reply A | Publish nothing for A, record it as declined or skipped, and only then present the next reply. |
| The draft is edited after it was presented for approval | Do not publish the edited version until the user separately approves the revised exact text. |
| The user has not answered an individual approval request | Wait. Do not treat prior code approval, push confirmation, blanket approval, or silence as reply approval. |
| The reply capability is unavailable or the original target identity is uncertain | Leave that draft pending and explain the limitation. Do not substitute a new top-level comment or blindly retry an uncertain write. |
| A draft targets an inline review comment or a general PR comment | Preserve the PR URL and original comment URL/ID; preserve the inline thread ID when available. Publish only in the matching original thread or comment context. |
| No actionable comment entered the one-by-one review | Report that no actionable comments were found. Do not request push confirmation or perform any comment write. |
| The user declines the proposed code change | The refreshed draft says no change was made and reflects the actual reason or disposition; it does not claim the concern was fixed. |
| The target PR is `kubernetes/kubernetes` | Create and refresh an unpublished reply draft for every handled comment, then apply the same full-review, latest-push, and individual-approval gates. |
| The target PR is `example/widgets`, opened from an arbitrary local folder such as `src/odd-name` | Apply the same draft, target-identity, and publication gates as for Kubernetes; neither repository identity nor local folder changes the reply workflow. |
