# Network Resources Injector — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `k8snetworkplumbingwg/network-resources-injector` repository.

---

## Review Focus Areas

### Admission Webhook Logic

- **JSON patch correctness**: Every mutation returns a JSON patch. Verify that
  patch operations use correct paths, operations (`add`, `replace`, `remove`),
  and values. Incorrect patches silently corrupt pod specs.
- **Patch ordering**: Parent paths must be created before children. For example,
  `/metadata/annotations` must exist (or be created) before adding a specific
  annotation key. The `appendAddAnnotPatch` function handles this — changes to
  patch generation must preserve this ordering.
- **AdmissionReview response**: The response must always include the request
  UID. An `Allowed: true` response with an empty patch is valid (no mutation
  needed). Verify error responses use proper HTTP status codes.
- **Namespace resolution**: Pods may arrive without a namespace in the
  `ObjectMeta`. The code falls back to `AdmissionRequest.Namespace`, then
  owner reference lookup (ReplicaSet, DaemonSet, StatefulSet,
  ReplicationController). Review any changes to this chain carefully —
  missing namespace causes silent failures.
- **Network selection parsing**: NAD references support two formats — JSON array
  and comma-separated strings. Both must be handled. Namespace defaults must be
  applied correctly. Missing namespaces should log a warning, not fail the pod.

### Resource Injection

- **First-container targeting**: Resource requests/limits are injected into the
  **first container** of the pod by default. Verify changes don't accidentally
  inject into all containers or init containers.
- **Hugepage handling**: Hugepage resources (`hugepages-1Gi`, `hugepages-2Mi`)
  are injected as both requests and limits (they must match in Kubernetes).
  Also verify downward API volumes are created for hugepage resources when the
  feature is enabled.
- **Resource key escaping**: Resource names containing `/` or `~` must be
  escaped for JSON patch paths (`/` → `~1`, `~` → `~0`). The
  `toSafeJSONPatchKey` function handles this.
- **Honor existing resources**: When `enableHonorExistingResources` is active,
  the webhook must not overwrite resources already defined in the pod spec.
  Review the `updateResourcePatch` vs `createResourcePatch` code paths.

### Control Switches

- **CLI flags + ConfigMap override**: Features are initialized from CLI flags
  and can be overridden at runtime via the `nri-control-switches` ConfigMap.
  Verify that new features follow this dual-initialization pattern.
- **Default restoration**: When the ConfigMap is deleted or a key is missing,
  the feature must revert to its initial CLI-flag value (not a hardcoded
  default). The `setActiveToInitialState()` method handles this.
- **Polling interval**: The ConfigMap is polled every 30 seconds. Changes to
  polling logic must handle API errors gracefully — only `IsNotFound` should
  reset defaults; other errors should be logged and skipped.

### User-Defined Injections

- **ConfigMap-driven patches**: User-defined injections are JSON patch
  operations stored in a ConfigMap under the `user-defined-injections` key.
  Verify that invalid JSON in the ConfigMap logs a warning and does not crash
  the webhook.
- **Thread safety**: The `UserDefinedInjections` struct uses a `sync.Mutex`.
  Any code reading or writing `Patchs` must hold the lock.
- **Patch deduplication**: New patches replace existing ones with the same key.
  Removed patches (present in the struct but absent from the ConfigMap) must
  be cleaned up.

### TLS and Security

- **Certificate reloading**: TLS certificates are hot-reloaded via fsnotify.
  Both cert and key files must be updated before the reload triggers. Verify
  changes to the watcher don't cause partial reloads.
- **Client CA validation**: When `--insecure` is false (default), client
  certificates are verified. The `--client-ca` flag is repeatable for multiple
  CAs.
- **TLS configuration**: Cipher suites, minimum TLS version, and curve
  preferences are configurable. Verify that insecure defaults are rejected
  (e.g., TLS versions below 1.2).
- **HTTP/2 disabled by default**: HTTP/2 is disabled via `TLSNextProto`
  (CVE-2023-39325 mitigation). The `--enable-http2` flag must be explicit.
- **Non-root container**: The Dockerfile runs as `USER 1001`. Verify changes
  don't require root privileges.

### NAD Cache

- **Informer-based cache**: NADs are cached using a shared informer. The cache
  is populated on startup and updated via Add/Update/Delete events.
- **Thread safety**: The cache uses `sync.Mutex` for map access. Verify
  concurrent access patterns.
- **Cache key format**: NADs are keyed by `namespace/name`. Verify lookups
  use the correct key format.

---

## Go Code Quality

- **glog logging**: All logging must use `github.com/golang/glog`. Do not
  introduce `klog`, `logrus`, `zerolog`, or `fmt.Printf`.
- **pkg/errors wrapping**: Use `errors.Wrap`, `errors.Errorf`,
  `errors.New` from `github.com/pkg/errors`. Do not use bare `fmt.Errorf`.
- **Import ordering**: stdlib → external → k8s.io → local project. Enforced
  by `goimports` with local prefix
  `github.com/k8snetworkplumbingwg/network-resources-injector`.
- **License headers**: Every new file must have the Apache 2.0 boilerplate.
- **Build tags**: Production code may need `-tags no_openssl`. Test code
  needs `-tags unittests`. Verify new test files are properly tagged.
- **No `init()` functions**: The codebase does not use `init()` except in
  test suites (Ginkgo bootstrap). Do not add `init()` in production code.

---

## Testing Requirements

- **Unit tests required**: All new logic in `pkg/` must have unit tests.
- **Ginkgo v1**: Tests use Ginkgo v1 (`github.com/onsi/ginkgo`), not v2.
  Do not mix versions within existing test files.
- **Same-package testing**: Unit tests are in the same package as the code
  they test (white-box testing). This allows testing unexported functions.
- **Test suite file**: Each package with tests needs a
  `*_suite_test.go` that bootstraps the Ginkgo runner.
- **Coverage**: `scripts/test.sh` generates coverage profiles. New code
  should not significantly decrease coverage.
- **E2E scope**: If a change affects webhook mutation behavior visible from
  a pod perspective, consider adding or updating E2E tests in `test/e2e/`.

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Wrong logging library | Using `klog`, `logrus`, or `fmt.Printf` instead of `glog` |
| Wrong error wrapping | Using `fmt.Errorf` instead of `errors.Wrap` / `errors.Errorf` |
| Missing build tag | New test file missing `unittests` build tag awareness |
| Incorrect patch path | JSON patch path not properly escaped (`/` → `~1`) |
| Patch ordering bug | Child patch created before parent path exists |
| Missing namespace fallback | Namespace resolution skipping owner reference lookup |
| Thread-unsafe access | Reading/writing `UserDefinedInjections.Patchs` or cache map without lock |
| Missing license header | New file without Apache 2.0 boilerplate |
| Wrong Ginkgo version | Importing `ginkgo/v2` in a file that uses Ginkgo v1 |
| Broken import order | Local imports not grouped after k8s.io imports |
| Resource leak | HTTP response body not closed (caught by `bodyclose` linter) |
| Hardcoded namespace | Using `"default"` or `"kube-system"` instead of the configurable namespace |
| Missing error handling | Swallowing errors from ConfigMap polling or NAD lookups |
| Container runs as root | Dockerfile change removes `USER 1001` |
| Hugepage mismatch | Injecting hugepage request without matching limit |

---

## PR Checklist (Reviewer Perspective)

1. Does `make lint` pass? (golangci-lint v2 with all enabled linters)
2. Does `make test` pass? (unit tests with `-race` and `unittests` tag)
3. Does `make` pass? (build with `no_openssl` tag)
4. Do new files have the Apache 2.0 license header?
5. Are new/changed functions covered by unit tests?
6. Is logging done via `glog` (not klog/logrus/fmt)?
7. Are errors wrapped with `pkg/errors` (not `fmt.Errorf`)?
8. Are JSON patch operations correctly ordered and paths properly escaped?
9. Is thread safety maintained for shared state (cache, control switches,
   user-defined injections)?
10. Do import groups follow stdlib → external → k8s.io → local ordering?
11. Are new features gated behind control switches (CLI flag + ConfigMap)?
12. Does the Dockerfile still run as non-root (`USER 1001`)?
13. Is there no unrelated formatting or whitespace noise in the diff?

---

## Commit Structure Expectations

- **Self-contained commits**: Code changes and their tests belong in the same
  commit. Do not defer tests to a follow-up.
- **Clear commit messages**: Describe what and why. Reference issues when
  applicable.
- **No mixed concerns**: Separate functional changes from refactoring,
  dependency updates, or formatting fixes.
- **Signed-off-by**: Not strictly enforced but encouraged for DCO compliance.
- **Small, focused PRs**: Prefer multiple small PRs over one large omnibus
  change. Webhook mutation logic is complex — smaller diffs are easier to
  review for correctness.

---

## Reviewer Preferences

- **Mutation correctness over cleverness**: The webhook modifies pod specs at
  admission time. Incorrect mutations are invisible until pods fail at runtime.
  Prioritize correctness and clarity over brevity.
- **Test the patch output**: Unit tests should verify the exact JSON patch
  generated, not just that "no error occurred". The webhook's contract is the
  patch — test it explicitly.
- **Backward compatibility**: Changes to mutation behavior affect all pods in
  the cluster. Ensure new features are gated behind control switches and
  default to the previous behavior.
- **Security posture**: The webhook has cluster-wide privileges. Review RBAC
  changes in `deployments/auth.yaml` carefully. The principle of least
  privilege applies.
- **Error tolerance**: The webhook must never crash the pod creation flow for
  non-SR-IOV pods. If a NAD lookup fails or an annotation is malformed,
  the webhook should log a warning and allow the pod through.
