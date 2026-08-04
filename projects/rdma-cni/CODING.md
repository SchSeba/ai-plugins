# rdma-cni — Coding

Coding conventions, architecture patterns, and common pitfalls for contributing
to the `k8snetworkplumbingwg/rdma-cni` repository.

---

## Repository Layout

| Directory | Purpose |
|-----------|---------|
| `cmd/rdma/` | CNI plugin binary entry point (`main.go` — CmdAdd, CmdDel, CmdCheck) |
| `pkg/rdma/` | RDMA device manager — move devices between namespaces, get/set system RDMA mode |
| `pkg/rdma/rdma_ops.go` | Low-level netlink/rdmamap wrappers (BasicOps interface) |
| `pkg/rdma/mocks/` | Generated mocks for `Manager` and `BasicOps` interfaces (mockery v3) |
| `pkg/cache/` | File-based CNI state cache at `/var/lib/cni/rdma` |
| `pkg/cache/mocks/` | Generated mocks for `StateCache` interface (mockery v3) |
| `pkg/types/` | Type definitions: `RdmaNetConf`, `RdmaNetState`, `CNIArgs` |
| `pkg/utils/` | Utility functions: VF PCI device lookup from MAC, PCI address validation |
| `deployment/` | Kubernetes DaemonSet manifest for deploying the CNI plugin |
| `examples/` | Example CRDs, test pods, SR-IOV device plugin resource YAML |
| `images/` | Container entrypoint script (`entrypoint.sh`) |

---

## CNI Plugin Architecture

### Chained plugin model

rdma-cni is a **chained CNI plugin** — it is never called standalone. It
requires `PrevResult` from a delegate plugin (e.g., sriov-cni) to operate.
If `RawPrevResult` is nil, CmdAdd returns an error.

### Core flow: CmdAdd

1. Parse network configuration (`RdmaNetConf`) from `args.StdinData`.
2. Verify the RDMA subsystem is in **exclusive** mode (`/sys/kernel/rdma_cm/`).
3. Resolve the RDMA device — either from the `deviceID` config field (PCI
   address or auxiliary device name) or by deriving it from the PrevResult
   MAC address via sysfs.
4. Move the RDMA device from the host network namespace to the container
   namespace using netlink (`RdmaLinkSetNsFd`).
5. Save state to the file-based cache (`/var/lib/cni/rdma`).
6. On any failure after the move, restore the RDMA device to the host namespace.

### Core flow: CmdDel

1. Parse configuration.
2. If `args.Netns` is empty (container already exited), return nil — nothing
   to clean up.
3. Load RDMA device state from the cache.
4. Move the RDMA device back from the container namespace to the default
   (host) namespace.
5. Delete the cache entry.

### Core flow: CmdCheck

Currently a no-op — logs the call and returns nil.

### Thread safety

The `init()` function calls `runtime.LockOSThread()` to ensure the main
goroutine stays on the main OS thread. This is **required** because namespace
operations (`unshare`, `setns`) are per-thread, not per-process.

---

## Key Interfaces

### `rdma.Manager`

The high-level interface for RDMA device operations:

- `MoveRdmaDevToNs(rdmaDev string, netNs ns.NetNS) error`
- `GetRdmaDevsForPciDev(pciDev string) []string`
- `GetRdmaDevsForAuxDev(auxDev string) []string`
- `GetSystemRdmaMode() (string, error)`
- `SetSystemRdmaMode(mode string) error`

### `rdma.BasicOps`

Low-level wrappers around `netlink` and `rdmamap` calls. This interface
exists for testability — production code uses real netlink; tests use mocks.

### `cache.StateCache`

File-based state persistence:

- `GetStateRef(network, cid, ifname string) StateRef`
- `Save(ref StateRef, state interface{}) error`
- `Load(ref StateRef, state interface{}) error`
- `Delete(ref StateRef) error`

The cache uses `afero` (in-memory filesystem) for unit tests via the
`fakeFileSystemOps` implementation in `pkg/cache/fs_ops.go`.

---

## Coding Conventions

### Logging

rdma-cni uses **zerolog** (not klog) for structured logging:

```go
log.Info().Msgf("RDMA-CNI: cmdAdd")
log.Debug().Msgf("Network Configuration: %+v", conf)
log.Warn().Msgf("failed to load cache entry(%q). %v", pRef, err)
```

- Default level is `zerolog.InfoLevel`.
- Debug mode is toggled by the `debug` CNI arg (`conf.Args.CNI.Debug`).
- Output goes to `os.Stderr` via `zerolog.ConsoleWriter` (no color, timestamp).
- **Do not** use `fmt.Printf`, `log.Printf`, or `klog` for runtime logging.
- The `govet` linter is configured to check `zerolog.Event.Msgf` format strings.

### Error handling

- Wrap errors with context using `fmt.Errorf`:
  `fmt.Errorf("failed to get RDMA device for device ID %s: %w", deviceID, err)`
- Use `%w` for errors that callers should be able to unwrap; use `%v` otherwise.
- Never swallow errors silently — at minimum log them at `Warn` level.
- CmdDel is lenient: cache-miss on load and delete-failure are logged as
  warnings but do not return errors (the container may have already exited).

### Imports

Import ordering enforced by `goimports` (configured in `.golangci.yml`):

1. Standard library
2. External packages (e.g., `github.com/containernetworking/...`,
   `github.com/rs/zerolog`)
3. Internal packages (`github.com/k8snetworkplumbingwg/rdma-cni/...`)

Local prefix for import grouping: `github.com/k8snetworkplumbingwg/rdma-cni`.

### Naming

- Interfaces use descriptive names: `Manager`, `BasicOps`, `StateCache`,
  `FileSystemOps`, `NsManager`.
- Concrete implementations use the `Impl` suffix or descriptive names:
  `rdmaManagerNetlink`, `rdmaBasicOpsImpl`, `FsStateCache`, `stdFileSystemOps`.
- Constants use `PascalCase`: `RdmaSysModeExclusive`, `RdmaSysModeShared`,
  `RdmaNetStateVersion`.

### Build tags

The binary is built with `-tags no_openssl` and `CGO_ENABLED=0` for static
linking. Always include these flags when building manually.

---

## Testing Patterns

### Framework

All tests use **Ginkgo v2 + Gomega**. Dot-imports of Ginkgo and Gomega are
allowed (configured in `.golangci.yml` revive and staticcheck settings).

### Test organization

- Suite bootstrap files: `*_suite_test.go` (e.g., `rdma_suite_test.go`).
- Test files live alongside source: `rdma_test.go` next to `rdma.go`.
- Tests use the **internal test package** pattern (e.g., `package rdma` not
  `package rdma_test`) for white-box testing of unexported types, except for
  suite files which use `package rdma_test`.

### Mocking

- Mocks are generated by **mockery v3** (configured in `.mockery.yml`).
- Mocked interfaces: `rdma.Manager`, `rdma.BasicOps`, `cache.StateCache`.
- Mock files live in `<package>/mocks/` directories.
- Tests combine mockery mocks with testify assertions:
  `rdmaOpsMock.On("RdmaLinkByName", ...).Return(link, nil)` followed by
  `rdmaOpsMock.AssertExpectations(t)`.
- **Never hand-edit generated mock files** — run `make generate-mocks` instead.

### Filesystem mocking

The cache package uses `afero.MemMapFs` via `fakeFileSystemOps` for unit tests
— no actual filesystem I/O during testing.

### Network namespace mocking

Tests use a `dummyNetNs` struct that implements `ns.NetNS` with a configurable
file descriptor, avoiding real namespace operations.

---

## Common Pitfalls

1. **Forgetting `runtime.LockOSThread()`** — Namespace operations require the
   goroutine to be locked to a single OS thread. The `init()` function handles
   this, but any new goroutines that perform namespace ops must also lock.

2. **Assuming DeviceID is always present** — The delegate plugin may not
   populate `deviceID`. CmdAdd has a fallback path that derives it from the
   PrevResult MAC address. New code must handle both cases.

3. **Editing generated mock files** — Files in `pkg/rdma/mocks/` and
   `pkg/cache/mocks/` are auto-generated by mockery. Edit the interfaces,
   then run `make generate-mocks` (or `make generate`).

4. **Missing `-tags no_openssl`** — The build requires this tag. If you build
   with plain `go build`, it will fail or produce incorrect binaries.

5. **RDMA subsystem mode** — The plugin only works when the system RDMA mode
   is `exclusive`. If it is `shared`, CmdAdd returns an error. Tests must
   mock `GetSystemRdmaMode()` to return `exclusive`.

6. **PCI address format** — Valid PCI addresses match
   `^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]$`. Auxiliary device
   names (e.g., `mlx5_core.sf.4`) take a different code path via
   `GetRdmaDevsForAuxDev`.

7. **CmdDel idempotency** — CmdDel must be idempotent. If the cache entry is
   missing (e.g., double-delete), it logs a warning and returns nil. Do not
   change this to return an error.

8. **No vendor directory** — The repo uses Go modules without vendoring. Do
   not run `go mod vendor` or commit a `vendor/` directory.
