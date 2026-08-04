# SR-IOV Network Metrics Exporter — Coding

Coding conventions, architecture patterns, and common pitfalls for contributing
to the `k8snetworkplumbingwg/sriov-network-metrics-exporter` repository.

---

## Repository Layout

| Directory | Purpose |
|-----------|---------|
| `cmd/` | Binary entry point — HTTP server serving Prometheus `/metrics` on port 9808 |
| `collectors/` | Prometheus collector implementations (VF stats, pod-CPU link, pod-device link) |
| `pkg/utils/` | Path resolution utilities, symlink handling, custom flag types |
| `pkg/vfstats/` | Netlink-based VF statistics retrieval (`vishvananda/netlink`) |
| `deployment/` | Kubernetes manifests — DaemonSet + Service (hostNetwork, sysfs mounts) |
| `docs/` | Prometheus query examples |

---

## Architecture Overview

The exporter is a single Go binary that:

1. Parses CLI flags (collector toggles, filesystem paths, web settings).
2. Registers enabled collectors with the Prometheus default registry.
3. Serves an HTTP `/metrics` endpoint with rate limiting, method filtering, and
   body rejection middleware.

Collectors are **self-registering** — each calls `register()` in its `init()`
function, which creates a CLI flag and adds the collector factory to a global
map. At startup, `Enabled()` iterates the map and instantiates only those
collectors whose flags are `true`.

---

## Collector Pattern

Every collector implements `prometheus.Collector` (the `Describe` + `Collect`
interface). The project follows a specific pattern:

### Registration

```go
func init() {
    register("myCollector", enabled, createMyCollector)
    // or: register("myCollector", disabled, createMyCollector)
}
```

- `enabled` / `disabled` are package-level `bool` constants controlling the
  default state.
- `register()` creates a `--collector.<name>` CLI flag and stores the factory
  function.

### Collector Struct

```go
type myCollector struct {
    name string
    // any static state collected at init time
}
```

Static state (e.g., NUMA topology, PCI device list) is gathered once in the
factory function (`createMyCollector`). Dynamic state is read on every
`Collect()` call.

### Describe

`Describe` is intentionally left empty (no-op) for all collectors in this
project. Metrics are created dynamically in `Collect()` using
`prometheus.NewDesc` + `prometheus.MustNewConstMetric`.

### Collect

`Collect` creates metric descriptors on each invocation because label values
(PCI addresses, pod names, VF IDs) are discovered at scrape time.

```go
desc := prometheus.NewDesc(
    prometheus.BuildFQName(collectorNamespace, subsystem, name),
    "Description.",
    []string{"label1", "label2"}, nil,
)
ch <- prometheus.MustNewConstMetric(desc, prometheus.CounterValue, value, labelVals...)
```

---

## Metric Namespace and Subsystems

- **Namespace**: `sriov` (all metrics are prefixed `sriov_`)
- **VF stats subsystem**: `vf` → metrics like `sriov_vf_tx_bytes`
- **Pod collectors**: no subsystem → metrics like `sriov_kubepoddevice`,
  `sriov_kubepodcpu`, `sriov_cpu_info`

---

## Existing Collectors

| Collector | Flag | Default | Data Source |
|-----------|------|---------|-------------|
| `vfstats` | `--collector.vfstatspriority` | enabled | sysfs or netlink (priority-based) |
| `kubepodcpu` | `--collector.kubepodcpu` | disabled | CPU Manager checkpoint + cgroup cpuset |
| `kubepoddevice` | `--collector.kubepoddevice` | disabled | Kubelet PodResources gRPC API |

### VF Stats Reader Priority

The VF stats collector supports two readers — `sysfs` and `netlink` — selected
per-PF based on a configurable priority list (`--collector.vfstatspriority`).
The first reader that can successfully read stats for VF 0 is used.

```go
type sriovStatReader interface {
    ReadStats(pfName string, vfID string) sriovStats
}
```

---

## Sysfs and Filesystem Access

All sysfs/procfs paths are configurable via CLI flags (`--path.*`). The project
uses Go's `io/fs` package extensively:

- `os.DirFS()` creates filesystem handles from flag values.
- `fs.ReadFile()`, `fs.ReadDir()`, `fs.Glob()`, `fs.Stat()` operate on these
  handles.
- Paths are resolved and symlinks evaluated at startup via
  `utils.ResolveFlag()`.

This pattern enables testing with `fstest.MapFS` without touching real sysfs.

---

## Coding Conventions

### Logging

The project uses the Go standard library `log` package:

```go
log.Printf("message: %v", value)
log.Fatalf("fatal: %v", err)    // exits the process
```

Do **not** use `fmt.Printf` for runtime logging. Do **not** use `klog` — this
project does not depend on it.

Fatal errors during startup use a testable wrapper:

```go
var logFatal = func(msg string, args ...any) {
    log.Fatalf(msg, args...)
}
```

### Error Handling

- Return errors up the call stack; log them at the collector level.
- Use `fmt.Errorf` for error wrapping (not `pkg/errors`).
- Collectors should **not** crash on per-device errors — log and skip the
  device.

### Import Ordering

The `.golangci.yml` enforces import ordering via `goimports` with local prefix:

```
github.com/k8snetworkplumbingwg/sriov-network-metrics-exporter
```

Standard ordering: stdlib → external → k8s.io → local project.

### Naming

- Package names are short, lowercase, single-word where possible.
- Collector structs use camelCase: `sriovDevCollector`, `kubepodCPUCollector`.
- Constants use camelCase: `collectorNamespace`, `vfStatsSubsystem`.
- Exported functions use PascalCase: `Enabled()`, `PodResources()`,
  `ResolveFlag()`.

### Build Tags

The binary is built with:

- `CGO_ENABLED=0` (static binary)
- `-tags no_openssl` (avoids OpenSSL dependency)
- `-ldflags '-s -w'` (strip debug info)

---

## Testing Patterns

### Unit Tests

- Tests live alongside the source: `collectors/sriovdev_test.go` next to
  `collectors/sriovdev.go`.
- Use **Ginkgo v2 + Gomega** framework (not `testing` package directly).
- `fstest.MapFS` is used extensively to mock sysfs and procfs paths.
- The `logFatal` variable is overridden in tests to prevent `os.Exit`.
- Netlink calls are mocked by replacing the `vfstats.GetLink` variable.
- Symlink evaluation is mocked via the `utils.EvalSymlinks` variable.

### Test Structure

```go
var _ = Describe("Component", func() {
    BeforeEach(func() { /* setup mocks */ })
    AfterEach(func() { /* cleanup */ })

    Context("when condition", func() {
        It("should behave", func() {
            Expect(result).To(Equal(expected))
        })
    })
})
```

### No Integration / E2E Tests

The project currently has **no integration or E2E tests** in the repository.
E2E validation happens via the SR-IOV Network Operator's test suite.

---

## Dependencies

| Dependency | Purpose |
|------------|---------|
| `prometheus/client_golang` | Prometheus metrics exposition |
| `prometheus/client_model` | Prometheus metric types |
| `vishvananda/netlink` | VF stats via netlink |
| `golang.org/x/time` | HTTP rate limiting |
| `google.golang.org/grpc` | Kubelet PodResources gRPC client |
| `k8s.io/kubelet` | PodResources API types (v1) |
| `onsi/ginkgo/v2` + `onsi/gomega` | Test framework |

---

## Common Pitfalls

1. **Forgetting `-tags no_openssl`** — The build requires this tag. Use
   `make build`, do not run `go build` directly without it.
2. **Using real sysfs paths in tests** — Always mock filesystem access using
   `fstest.MapFS` and the `io/fs` interfaces. Never read from `/sys/` in tests.
3. **Adding a collector without `init()` registration** — New collectors must
   call `register()` in their `init()` function or they won't be discoverable.
4. **Hardcoding sysfs paths** — All paths must be configurable via `--path.*`
   flags and resolved through `utils.ResolveFlag()`.
5. **Panicking on device errors** — Individual device read failures should be
   logged, not fatal. The exporter must keep running for other devices.
6. **Breaking the `Describe` no-op convention** — All collectors leave
   `Describe` empty. Dynamic metric creation in `Collect` is intentional.
7. **Forgetting `CGO_ENABLED=0`** — The binary must be statically linked for
   the Alpine-based container image.
8. **Not running `go mod tidy`** — CI checks that `go.mod` and `go.sum` are
   consistent. Always run `go mod tidy` after dependency changes.
