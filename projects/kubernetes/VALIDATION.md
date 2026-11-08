# Kubernetes — Validation

## Authority and scope

Use the target checkout's AGENTS/CONTRIBUTING files, Makefile, script help and
current CI configuration to discover exact commands, arguments and prerequisites.
This is conditional project knowledge, not a universal pre-push sequence.
The [contributor PR process](https://www.kubernetes.dev/docs/guide/pull-requests/)
describes broad submission checks; use focused feedback while developing, then
satisfy applicable submission/required checks. Do not silently replace required
checks with a passing subset.

## Checkout-dependent script inventory

These paths are discovery hints; confirm they exist and inspect their current
interfaces before running. Run applicable scripts from the Kubernetes root.
Verifiers may use temporary worktrees or regenerate files; inspect side effects
and prerequisites rather than assuming every verifier is read-only.

| Area | Discover matching checker/generator |
|------|------------------------------------|
| Boilerplate and formatting | `hack/verify-boilerplate.sh`, `hack/verify-gofmt.sh` |
| Go lint and imports | `hack/verify-golangci-lint.sh`, `hack/verify-imports.sh`, `hack/verify-import-aliases.sh`, `hack/verify-import-boss.sh` |
| Generated code | `hack/verify-codegen.sh`, `hack/update-codegen.sh` |
| OpenAPI snapshots | `hack/verify-openapi-spec.sh`, `hack/update-openapi-spec.sh` |
| API descriptions | `hack/verify-description.sh`, `hack/verify-fieldname-docs.sh` |
| API compatibility | `hack/update-generated-api-compatibility-data.sh`, checkout compatibility tests |
| Feature gates | `hack/verify-featuregates.sh`, `hack/update-featuregates.sh` |
| Public staging Go API diff | `hack/apidiff.sh` with actual base revision and affected staging module |
| Metrics, docs, E2E ownership | Relevant `hack/verify-*` and `hack/update-*` scripts discovered from changed inputs |

Do not assume a codegen target list or that one generator produces every artifact.
Identify source markers and dependent generated outputs, run matching generators,
review their diff, then matching verifiers. Regenerate artifacts rather than
editing them. Preserve unrelated work; inspect clean-tree requirements before
using a generator/verifier. Do not stash or discard work blindly.

Discover etcd/protoc and other helper version/PATH requirements in the scripts and
test harness. Use the checkout's documented installation method. Do not fabricate
a pass when integration infrastructure is missing.

## Focused tests

Map the changed behavior and its call paths to existing tests and repository test
targets. Select actual package/test filters from the checkout; do not copy a
historical PR's API names, package paths or test names as defaults.

- API changes: validation boundaries and rejection paths, defaulting/conversion,
  serialization, registry strategy and gated create/update behavior.
- Allocation changes: capacity/accounting invariants, invalid input and failure
  recovery, concurrent or repeated operations where relevant.
- Scheduler changes: plugin/state lifecycle, claim/resource availability, retries
  and scheduling behavior under changed allocation rules.
- Cross-boundary changes: focused API/allocation/scheduler integration scenarios;
  E2E coverage where user-visible behavior requires it.

Start focused checks after regeneration, then broaden to applicable submission and
required CI checks. Report exact commands, selected scope, environment, candidate
revision/content and actual outcomes. A focused unit pass does not establish API
compatibility or end-to-end behavior.

## Prow permissions and efficient requests

Sources: [Prow plugins](https://docs.prow.k8s.io/docs/components/plugins/),
[deployed command help](https://prow.k8s.io/command-help),
[trigger implementation/help](https://github.com/kubernetes-sigs/prow/blob/main/pkg/plugins/trigger/trigger.go)
and [Kubernetes PR process](https://www.kubernetes.dev/docs/guide/pull-requests/).
Check live help/config for the target repository before issuing commands.

External/first contributors need CLA and an authorized trusted member's safety
review and `/ok-to-test`. A contributor cannot grant their own trust.
On a trusted PR, contributors can request `/test <job>` for a configured job.
Draft PRs do not automatically start jobs; a trusted user can manually request
appropriate draft tests. Do not turn a draft ready solely to spend CI resources.
Use the available job list to select affected jobs, including manual required jobs
when configuration calls for them.

Inspect failures before a retry. `/retest` reruns failed jobs and may be broader
than intended: prefer a named `/test <job>` to rerun a diagnosed affected failure
selectively. Do not assume `/retest <job>` is supported. Avoid blanket requests
for every job while known source failures or conflicts remain.

## Failure audit and blockers

Prioritize configured required checks; retain advisory/unknown status explicitly.
For each failure record check/job URL, tested SHA, required/advisory status,
failed step, first causal error, classification, evidence and next action.

| Classification | Evidence and response |
|----------------|-----------------------|
| Source defect | Trace first causal failure to changed code/inputs; repair and run focused checks |
| Infrastructure | Logs show runner/network/provisioning failure; request appropriate recovery or selective rerun |
| Unrelated/pre-existing | Compare immutable base/head and affected inputs; document separate recovery |
| Flaky | Cite test history or reproduction evidence; selective retry may help, but does not erase failure |
| Unknown | Retrieve missing logs/context; do not guess or recommend a retry as diagnosis |

A timeout alone does not prove infrastructure: it can be a product deadlock or
resource regression. Inspect raw job logs and artifacts, not only the summary
tail. A newer commit invalidates old-SHA results as acceptance evidence.
Record pending checks as pending, failures as failures, and unavailable local
prerequisites as blocked.

Inspect current Tide/PR dashboard merge criteria, required checks, approval
coverage, CLA, draft/hold/do-not-merge labels and head/base mergeability.
Actual merge conflicts are blocking rebase/conflict actions, not retry targets.
After conflict repair, verify the preserved proposal and rerun affected checks.
Unknown mergeability remains unverified; no passing local check clears it.
