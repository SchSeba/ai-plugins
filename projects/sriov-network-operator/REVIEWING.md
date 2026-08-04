# SR-IOV Network Operator — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `k8snetworkplumbingwg/sriov-network-operator` repository.

---

## Review Focus Areas

### CRD / API Changes

- **Backward compatibility**: New fields in `api/v1/*_types.go` must be optional
  (pointer types with `omitempty`). Removing or renaming fields is a breaking
  change.
- **Generated code consistency**: After any type change, `make generate` and
  `make manifests` must be re-run. The PR diff should include updated
  `zz_generated.deepcopy.go`, apply configurations, and CRD YAML.
- **CRD YAML propagation**: CRD changes must appear in both `config/crd/bases/`
  and `deployment/sriov-network-operator-chart/crds/`. CI verifies this with
  `make check-manifests`.
- **Webhook validation**: New CRD fields that need validation should have
  corresponding webhook logic in `pkg/webhook/`.
- **Feature gate gating**: New alpha features should be gated behind a feature
  gate in `pkg/featuregate/`. The feature must be disabled by default until
  proven stable.

### Controller Logic

- **Reconciliation idempotency**: Controller reconcile loops must be idempotent —
  calling reconcile multiple times with the same input should produce the same
  result.
- **Error handling and requeue**: Errors from reconciliation must be returned
  (to trigger requeue) or logged at Error level. Never swallow errors silently.
- **Status updates**: Controllers should update CR status to reflect the current
  state. Check that status conditions follow the standard
  `metav1.Condition` pattern used in `api/v1/conditions.go`.
- **Platform awareness**: Controllers that behave differently on Kubernetes vs.
  OpenShift must handle both cases. Check for `vars.ClusterType` usage and
  verify the logic is tested for both platforms.
- **RBAC markers**: Changes to accessed resources require updated RBAC markers
  (`//+kubebuilder:rbac:...`) and a `make manifests` regeneration.

### Config Daemon Changes

- **Host interaction safety**: The config daemon runs as privileged on each node.
  Changes to `pkg/daemon/`, `pkg/host/`, and `pkg/vendors/` must be reviewed
  carefully for:
  - Proper error handling (node misconfiguration can take the node offline)
  - Correct sysfs path construction (PCI addresses, VF indices)
  - Safe NIC firmware operations (especially Mellanox firmware reset)
  - Drain coordination (changes to `pkg/drain/` affect node availability)
- **Bindata script changes**: Shell scripts in `bindata/scripts/` run on nodes
  during configuration. Review for:
  - Shell portability (RHEL, Ubuntu, etc.)
  - Idempotency (scripts may be re-run)
  - Error handling (`set -e` usage)
  - Correct use of `test-bindata-scripts` for coverage

### Plugin Architecture

- **Vendor plugin interface**: New vendor plugins must implement the
  `VendorPlugin` interface in `pkg/plugins/plugin.go`.
- **Plugin registration**: Verify the plugin is registered in the factory and
  selected based on NIC vendor/device IDs.
- **Plugin isolation**: Vendor-specific logic should stay in the plugin, not
  leak into generic controller or daemon code.

### Go Code Quality

- **Structured logging**: Use controller-runtime's zap logger (`log.Info`,
  `log.Error`), not `fmt.Printf`, `klog`, or standard `log`.
- **Error wrapping**: Errors should be wrapped with `fmt.Errorf("context: %w", err)`
  to preserve the error chain.
- **Import ordering**: stdlib → external → k8s.io → project-local. Enforced by
  `goimports` with the local prefix `github.com/k8snetworkplumbingwg/sriov-network-operator`.
- **Boilerplate**: Every new Go file needs the Apache 2.0 license header from
  `hack/boilerplate.go.txt`.
- **No direct `go fmt` calls**: The project uses containerized formatting via
  `make fmt`. Code should be formatted before submission.
- **Dot imports for test frameworks**: Ginkgo and Gomega should be dot-imported
  in `_test.go` files (`.golangci.yml` whitelists this).
- **Constants vs. magic strings**: Repeated string values should use constants
  from `pkg/consts/`. Check for magic numbers and strings in new code.

### Testing

- **Unit test coverage**: New logic must have Ginkgo/Gomega tests. Check that
  both code and tests are in the same PR.
- **Dual platform testing**: Unit tests that depend on cluster type must be
  verified for both `CLUSTER_TYPE=kubernetes` and `CLUSTER_TYPE=openshift`.
- **envtest setup**: Controller tests that use envtest must set up CRDs and
  schemes correctly in the `suite_test.go` file.
- **Mock consistency**: If interfaces change, mocks should be regenerated via
  `make mock-generate`. Stale mocks cause confusing test failures.
- **E2E test coverage**: Changes that affect user-visible behavior (new CRD
  fields, policy behavior, device configuration) should have conformance test
  coverage in `test/conformance/tests/`.
- **No `go test ./...`**: Use the `make test-<dir>` pattern which excludes mock
  and client directories and sets up envtest correctly.

### Bindata / Embedded Manifests

- **Template correctness**: YAML templates in `bindata/manifests/` use Go
  template syntax. Verify template variables are populated correctly.
- **RBAC alignment**: Manifests that create RBAC resources must match the
  operator's service account permissions.
- **Resource limits**: DaemonSet manifests should have reasonable resource
  requests and limits.

### Deployment / Helm Chart

- **Chart consistency**: Changes to CRDs must be reflected in
  `deployment/sriov-network-operator-chart/crds/`. The `make manifests` target
  handles this automatically.
- **Values alignment**: New operator configuration options should be exposed in
  the Helm chart's `values.yaml` when appropriate.

### Dockerfile Changes

- **Multi-stage build**: All three Dockerfiles use multi-stage builds with a
  `golang` builder stage and a `centos:stream9` runtime base.
- **Binary placement**: Verify the correct binary is copied to the expected path.
- **Security**: Check for unnecessary packages, proper USER directives (operator
  runs as `65532:65532`, webhook as `1001`), and no leftover build artifacts.
- **Hadolint compliance**: CI runs hadolint on all three Dockerfiles.

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Missing codegen | `zz_generated.deepcopy.go` or apply configs not updated after type change |
| Stale CRD manifests | `config/crd/bases/` or chart CRDs not regenerated after type change |
| Missing boilerplate | New Go file lacks Apache 2.0 header |
| Hand-edited generated file | Changes in `zz_generated.*` or `applyconfiguration/` not matching codegen output |
| Missing webhook validation | New CRD field has no validation in `pkg/webhook/` |
| Missing feature gate | Alpha feature exposed without gate in `pkg/featuregate/` |
| Unstructured logging | Uses `fmt.Printf` or `klog` instead of controller-runtime logger |
| Missing platform test | Test only runs with one `CLUSTER_TYPE` when behavior differs by platform |
| Stale mocks | Interface changed but mocks in `*/mock/` not regenerated |
| Missing `CLUSTER_TYPE` | Test added without `CLUSTER_TYPE` env var, will fail in CI |
| Swallowed error | Error returned from function ignored without logging |
| Non-idempotent reconcile | Reconcile creates duplicate resources on repeated calls |
| Bindata template error | Go template variable misspelled or missing in YAML template |
| Missing chart CRD copy | `make manifests` not run — chart CRDs diverge from `config/crd/bases/` |
| Stale go.mod | Dependencies added without `go mod tidy` — `make check-deps` fails |
| Missing script test | Bindata shell script modified without `make test-bindata-scripts` |
| Vendor-specific logic leak | NIC vendor logic placed in generic controller instead of plugin |
| Unsafe host operation | Config daemon code lacks error handling for sysfs or firmware operations |

---

## PR Checklist (Reviewer Perspective)

1. Does the PR description explain the change and reference an issue?
2. Are all CI jobs passing? (`build`, `test`, `modules`, `manifests`, `golangci`,
   `shellcheck`, `hadolint`)
3. Are generated files regenerated, not hand-edited? (`make generate`,
   `make manifests`)
4. Do new CRD fields have validation (webhook), feature gates (if alpha), and
   proper JSON tags (`omitempty` for optional pointer fields)?
5. Are there adequate tests (unit for both K8s and OpenShift, conformance if
   user-facing)?
6. Are unit tests in the same PR as the code they test?
7. Is `go.mod`/`go.sum` up to date? (`make check-deps`)
8. Is the commit message clear and follows the project format (summary, detail,
   `Fixes #N`)?
9. Are there no unrelated changes mixed into the PR?
10. Are new vendor-specific behaviors isolated in the plugin architecture?
11. Are controller reconcilers idempotent and status updates correct?
12. Are bindata manifest templates valid and tested?
13. Do Dockerfile changes follow multi-stage build conventions and pass hadolint?

---

## Commit Structure Expectations

The project follows a conventional commit format:

```
Change summary

More detailed explanation of your changes: Why and how.
Wrap it to 72 characters.

Fixes #NUMBER
```

- **Small, focused PRs** are preferred over large omnibus changes.
- **Branch naming**: Use `dev/` prefix for feature branches (e.g., `dev/add-vdpa-support`).
- **One logical change per commit** — separate refactoring from feature additions.
- **API changes**: CRD type changes, codegen output, and webhook validation
  should be in the same PR so reviewers see the complete picture.
- **Test changes**: Tests must accompany the code they test — do not defer
  tests to a follow-up PR.

---

## Reviewer Preferences

- **API review first**: CRD type changes are the most critical — review
  `api/v1/*_types.go` before looking at controller or daemon code.
- **Check the codegen diff**: Verify `zz_generated.deepcopy.go` and
  `applyconfiguration/` changes are consistent with type changes (no hand edits).
- **Verify both platforms**: When controller behavior differs by platform, check
  that both Kubernetes and OpenShift paths are tested.
- **Review bindata templates carefully**: YAML template errors are runtime
  failures, not compile-time errors. Verify variable names and indentation.
- **Host safety is paramount**: The config daemon runs with full host access.
  Any change to PCI, sysfs, network namespace, or firmware operations must be
  reviewed with extra care.
- **Feature gate lifecycle**: New features start as disabled by default. Track
  promotion from alpha → beta (enabled by default) → GA (gate removed).
- **E2E flakiness**: E2E tests on `sriov` and `ocp` runners are frequently
  flaky due to hardware infrastructure issues. A single E2E failure on
  self-hosted runners is not necessarily indicative of a code problem — check
  for infrastructure errors before requesting changes.
