# Kubernetes — Reviewing

## Canonical requirements and routing

Use the current [pull request process](https://www.kubernetes.dev/docs/guide/pull-requests/),
[OWNERS guide](https://www.kubernetes.dev/docs/guide/owners/) and
[API change process](https://github.com/kubernetes/community/blob/main/contributors/devel/sig-architecture/api_changes.md).
These sources and the target checkout take precedence over historical review
preferences recorded here. Do not carry forward individual reviewer assignments,
feature-specific API names, or old PR status.

For API changes, request API review through the documented SIG Architecture/API
process and relevant SIG/KEP owners. Track API/conceptual review separately from
allocator and scheduler implementation review: approval of the schema does not
establish allocation correctness, scheduling behavior or integration coverage.
Inspect the nearest and inherited OWNERS files (including aliases and
`no_parent_owners` boundaries) across all changed paths. Route each area to
reviewers/approvers with coverage; a single area approval may leave others uncovered.

`/lgtm` signals satisfactory review; `/approve` records ownership approval by
eligible approvers. They serve distinct purposes and their labels/coverage depend
on current configuration. Contributors may request assignment with
`/assign @username`; assignment does not grant approver authority. Check the
[deployed command help](https://prow.k8s.io/command-help) and
[Prow plugin configuration](https://github.com/kubernetes/test-infra/blob/master/config/prow/plugins.yaml)
rather than assuming every commenter can apply approvals.

Complete CLA requirements. On first/external contributions, an authorized trusted
organization member must inspect whether the PR is safe to test and grant
`/ok-to-test`; the author cannot self-authorize trust. Trust and CLA are separate
prerequisites. Once trusted, contributors can request configured jobs; details
and draft behavior are in [validation guidance](VALIDATION.md).

Use a draft for unfinished work and explain remaining TODOs. Drafts suppress
automatic Prow jobs; trusted users can request manual jobs when appropriate.
Use `/hold` to prevent Tide picking up unfinished work, and `/hold cancel`
when ready and authorized. Inspect the actual draft state, hold/WIP and other
do-not-merge labels rather than assuming readiness from the title.

Refresh the PR description after scope changes or rebases: summarize the final
behavior, API/KEP decisions, commit review map, actual test results and known gaps.
Follow the [release-note guide](https://www.kubernetes.dev/docs/guide/release-notes/)
with a fenced `release-note` block containing a user-facing summary, or literal
`NONE` when no release note is warranted. Do not leave stale feature descriptions.
The current PR guide also requires AI assistance disclosure and direct human
responses to reviewers without relying on AI tools. For Kubernetes, keep resolver
analysis internal and have the contributor engage directly; generic reply
eligibility does not override that project policy.

## Review organization — scoped heuristics

These are general review aids, not universal Kubernetes commit requirements.

- Separate conceptual/API work, generated artifacts and allocator/scheduler
  implementation into reviewable commits when this helps the requested review
  split. Keep associated unit, validation and strategy tests with their logical
  implementation commits; do not mandate a test-only commit.
- Agree exceptions and final squash organization with reviewers. Preserve
  incremental fixups while reviewers need them; do not require a particular KEP
  prefix or squash every manual change into one commit.
- After every rebase, inspect the final head-to-base change set and commit
  organization. Ensure tests and generated artifacts stayed with the intended
  changes, and recheck any invalidated evidence.
- Keep independent concerns separate even when they share a symbol. Retain all
  source links when grouping related discussion. Contributor “done” is a claim,
  and an outdated comment can still describe an unresolved behavior.

## Code and test review — checkout-dependent checks

Use current API conventions and comparable code, not mechanical rules inferred
from one review. Check optionality/nullability and serialization, list/map
semantics and bounds, protobuf numbering, validation/defaulting/conversions,
feature gates and stored-object compatibility. Establish production provenance
before proposing compatibility handling for PR-only additions.

Field comments become OpenAPI descriptions: start with the field name, use complete
sentences and consistent terminology, and explain enduring behavior, contracts or
non-obvious rationale independently of review history. Flag review-conversation
references or redundant assurances unless specifically requested, while preserving
useful semantics such as whether allocations already in flight are included.

For strategy/feature-gate transitions, consider create enabled/disabled and update
enabled/disabled, including preservation of previously stored gated fields.
Check validation error paths, not just direct validator tests; callers must
actually invoke validation. Trace allocator invariants and scheduler behavior
through integration tests where the boundary matters. Use current supported
declarative markers; document limitations rather than guessing support.

Regenerate generated code from source. Verify apply configurations, descriptions,
OpenAPI and compatibility artifacts where applicable. Review Go API compatibility
for affected staging modules using the checkout's policy; do not prescribe a
universal changelog or allowlist workaround. Follow existing logging, context,
imports, boilerplate and test-helper patterns supported by the checkout/toolchain.

## CI and merge readiness

Use [VALIDATION.md](VALIDATION.md) for revision-pinned failure diagnosis.
Required tests, CLA, review/ownership coverage and mergeability are independent
gates. Inspect the [PR dashboard](https://prow.k8s.io/pr) and
[Tide pool](https://prow.k8s.io/tide) against the current head.

A confirmed conflict or needs-rebase condition requires rebase/conflict work,
review of the preserved proposal and affected validation. A Tide conflict is not
a failed unit test to retry. Unknown mergeability remains unverified.
Passing focused local tests does not clear missing approvals, holds, required
CI or merge conflicts. Check all these gates again after a rebase.
