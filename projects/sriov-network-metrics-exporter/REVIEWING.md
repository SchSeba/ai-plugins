# SR-IOV Network Metrics Exporter — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `k8snetworkplumbingwg/sriov-network-metrics-exporter` repository.

---

## Review Focus Areas

### Prometheus Collector Correctness

- **Metric naming**: All metrics must use the `sriov` namespace. VF stats use
  the `vf` subsystem (`sriov_vf_*`). Pod-level metrics use no subsystem
  (`sriov_kubepoddevice`, `sriov_kubepodcpu`).
- **Metric types**: VF counters (bytes, packets, dropped, errors) must be
  `prometheus.CounterValue`. Info/link metrics (pod-device, pod-cpu) use
  `prometheus.CounterValue` with a constant value of `1`.
- **Label consistency**: Labels must match existing conventions — `pf`, `vf`,
  `pciAddr`, `numa_node` for VF metrics; `pod`, `namespace`, `container`,
  `dev_type` for pod-device metrics.
- **Dynamic `Describe`**: The project intentionally uses empty `Describe`
  methods and creates descriptors dynamically in `Collect`. New collectors
  should follow this pattern — do not pre-register metric descriptors.
- **No panics in Collect**: `Collect` must never panic. Use
  `prometheus.MustNewConstMetric` only with validated data. Log and skip
  devices/pods that produce errors.

### Collector Registration

- **`init()` function required**: Every new collector must register itself via
  `register(name, defaultState, factory)` in its `init()` function.
- **Default state**: Collectors that require external infrastructure (kubelet
  socket, cgroup filesystem) should default to `disabled`. Core VF stats
  collectors default to `enabled`.
- **Flag naming**: Collector flags must follow the `--collector.<name>` pattern.
  Path flags must follow the `--path.<name>` pattern.

### Sysfs / Filesystem Access

- **Configurable paths**: All filesystem paths (`/sys/bus/pci/devices`,
  `/sys/class/net`, etc.) must be configurable via `--path.*` flags. Hardcoded
  paths are a review blocker.
- **`io/fs` interface usage**: Filesystem access must go through `io/fs`
  interfaces (`fs.ReadFile`, `fs.ReadDir`, `fs.Glob`, `fs.Stat`) on
  `os.DirFS`-created handles. Direct `os.ReadFile` or `os.Open` calls bypass
  the testable abstraction layer.
- **Symlink resolution**: Use `utils.ResolveFlag()` at startup to resolve
  symlinks. Use `utils.IsSymLink()` to check for symlinks at runtime. Do not
  call `filepath.EvalSymlinks` directly — use the `utils.EvalSymlinks` variable
  to enable test mocking.
- **Path resolution at startup**: All `--path.*` flags must be resolved in
  a `resolve*Filepaths()` function registered in `collectors.ResolveFilepaths()`.

### gRPC / Kubelet API

- **Connection lifecycle**: gRPC connections to the kubelet PodResources socket
  must be created and closed within the `Collect` call. Do not hold long-lived
  connections.
- **Timeout handling**: All gRPC calls must use `context.WithTimeout`. The
  default timeout is 10 seconds (`kubeletConnTimeout`).
- **Error handling**: Failed kubelet connections should be logged and return
  empty results — never crash the exporter.

### Go Code Quality

- **Logging**: Use the `log` standard library package. Do not introduce `klog`,
  `logrus`, `zap`, or other logging frameworks.
- **Error wrapping**: Use `fmt.Errorf` with `%v` for error context. The project
  does not use `%w` or `errors.Is/As` patterns extensively.
- **Import ordering**: stdlib → external → internal (local prefix:
  `github.com/k8snetworkplumbingwg/sriov-network-metrics-exporter`). Enforced
  by `goimports` in the golangci-lint config.
- **Line length**: Maximum 140 characters (enforced by `lll` linter).
- **Function length**: Maximum 100 lines / 50 statements (enforced by `funlen`
  linter).
- **Cyclomatic complexity**: Maximum 15 (enforced by `gocyclo` linter).
- **Magic numbers**: Numbers in arguments, cases, conditions, and returns must
  be named constants (enforced by `mnd` linter). Exempted in test files.
- **No `CGO_ENABLED=1`**: The binary must build with `CGO_ENABLED=0`.

### Testing

- **Test framework**: Tests must use Ginkgo v2 + Gomega. Do not use raw
  `testing.T` assertions.
- **Filesystem mocking**: Mock sysfs access using `fstest.MapFS` and the
  `io/fs` interfaces. Never read from real sysfs paths in tests.
- **Function variable mocking**: The project uses replaceable function variables
  (`logFatal`, `utils.EvalSymlinks`, `vfstats.GetLink`) for dependency
  injection in tests. New external calls that need mocking should follow this
  pattern.
- **Test cleanup**: Use `BeforeEach` / `AfterEach` to reset mocked function
  variables and filesystem handles.
- **Coverage**: New code should have accompanying tests. The CI runs
  `make test-coverage` to track coverage.

### Container Image

- **Alpine-based**: The Dockerfile uses Alpine. Do not switch to Debian or
  distroless without discussion.
- **Static binary**: The binary must be statically linked (CGO_ENABLED=0) to
  run on Alpine.
- **Hadolint compliance**: The Dockerfile is linted by Hadolint in CI. DL3018
  (`apk add` without version pinning) is currently ignored.

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Hardcoded sysfs path | Missing `--path.*` flag; path not configurable |
| Direct `os.ReadFile` call | Should use `fs.ReadFile` on an `os.DirFS` handle |
| Missing `init()` registration | New collector not discoverable at runtime |
| Collector defaults to enabled | Infrastructure-dependent collectors should default to `disabled` |
| Missing error handling in Collect | Device/pod errors must be logged and skipped, not fatal |
| `Describe` is populated | Project convention is empty `Describe`; metrics are dynamic |
| Wrong metric namespace | Must use `sriov` namespace via `collectorNamespace` |
| Wrong metric type | VF stats counters must use `prometheus.CounterValue` |
| Label mismatch | New metrics labels don't align with existing conventions |
| Missing test for new collector | All collector logic needs Ginkgo test coverage |
| Real sysfs in test | Test reads from `/sys/` instead of `fstest.MapFS` |
| `go build` without `-tags no_openssl` | Build will fail or produce wrong binary |
| Vendor directory committed | `vendor/` must not be tracked in git |
| Missing `go mod tidy` | CI `go-check` job will fail on `go.mod`/`go.sum` drift |
| `filepath.EvalSymlinks` called directly | Must use `utils.EvalSymlinks` variable for testability |
| Long function exceeding limits | Functions over 100 lines or 50 statements fail `funlen` |
| Magic number in production code | Unnamed numeric literal fails `mnd` linter |
| Import order violation | Local imports not grouped under the module prefix |
| Missing path resolution | New `--path.*` flag not registered in `ResolveFilepaths()` |

---

## PR Checklist (Reviewer Perspective)

1. Does `make lint` pass? (golangci-lint v2 with full linter suite)
2. Does `make test` pass? (Ginkgo v2 unit tests)
3. Does `make build` succeed? (CGO_ENABLED=0, -tags no_openssl)
4. Are new collectors registered via `init()` + `register()`?
5. Are all sysfs paths configurable via `--path.*` flags?
6. Is filesystem access abstracted through `io/fs` interfaces?
7. Do new metrics follow the `sriov` namespace convention?
8. Are metric labels consistent with existing collectors?
9. Are errors in `Collect` logged and skipped (not fatal)?
10. Are there Ginkgo tests for new functionality?
11. Do tests use `fstest.MapFS` instead of real filesystem paths?
12. Is `go.mod` / `go.sum` consistent? (`go mod tidy && git diff --exit-code`)
13. Are there no `vendor/` files in the commit?
14. Does the Dockerfile still build? (`make image-build`)

---

## Commit Structure Expectations

- **Small, focused PRs**: Each PR should address one concern (new collector,
  bug fix, dependency update).
- **Tests with code**: Unit tests for new functionality must be in the same PR
  as the implementation.
- **Clean commit messages**: Describe what changed and why. Reference GitHub
  issues when applicable.
- **No unrelated changes**: Avoid mixing refactors, formatting fixes, or
  dependency bumps with feature work.
- **Signed-off-by**: Not currently enforced, but good practice for
  k8snetworkplumbingwg projects.

---

## Reviewer Preferences

- **Follow existing patterns** — Look at how existing collectors (`sriovdev.go`,
  `pod_cpu_link.go`, `pod_dev_link.go`) are structured and follow the same
  approach.
- **Prefer `io/fs` over direct OS calls** — Testability is a first-class
  concern in this project.
- **Keep the exporter resilient** — A single failing device or pod lookup should
  never crash the exporter. Log and continue.
- **Respect the linter configuration** — The `.golangci.yml` is intentionally
  strict. Do not add `//nolint` directives without justification in a comment.
- **Document new flags** — New `--collector.*` or `--path.*` flags should be
  documented in the README configuration table.
