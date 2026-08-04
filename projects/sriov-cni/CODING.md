# SR-IOV CNI — Coding

Coding conventions, architecture patterns, and common pitfalls for contributing
to the `k8snetworkplumbingwg/sriov-cni` repository.

---

## Repository Layout

| Directory | Purpose |
|-----------|---------|
| `cmd/sriov/` | CNI binary entry point — registers `CmdAdd`, `CmdDel`, `CmdCheck` via `skel.PluginMainFuncs` |
| `pkg/cnicommands/` | Core CNI command implementations (`CmdAdd`, `CmdDel`, `CmdCheck`) |
| `pkg/config/` | CNI NetConf parsing (`LoadConf`, `LoadConfFromCache`), logging init, config caching |
| `pkg/sriov/` | SR-IOV VF management — `SriovManager` handles VF setup, configuration, release, and state restore |
| `pkg/types/` | Type definitions — `NetConf`, `SriovNetConf`, `VfState` structs |
| `pkg/utils/` | Utility functions — sysfs helpers, netlink manager interface, PCI allocator, GARP/NA announcements |
| `pkg/logging/` | Structured logging wrapper around `k8snetworkplumbingwg/cni-log` |
| `test/integration/` | Integration tests using `bash_unit` framework with mocked sysfs and netlink |
| `images/` | Container entrypoint script (`entrypoint.sh`) that copies the CNI binary to the host |
| `docs/` | User-facing documentation |
| `.github/workflows/` | CI workflows — build, test, lint, image push |

---

## CNI Plugin Architecture

### Entry point (`cmd/sriov/main.go`)

The binary registers three CNI operations via the CNI `skel` package:

```go
cniFuncs := skel.CNIFuncs{
    Add:   cnicommands.CmdAdd,
    Del:   cnicommands.CmdDel,
    Check: cnicommands.CmdCheck,
}
skel.PluginMainFuncs(cniFuncs, version.All, "")
```

The `init()` function calls `runtime.LockOSThread()` to pin the goroutine to
the main thread — this is **required** for network namespace operations
(`unshare`, `setns`).

### CmdAdd flow

1. Parse CNI NetConf from stdin (`config.LoadConf`)
2. Set up logging from config (`config.SetLogging`)
3. Parse environment args (MAC override)
4. Open the container network namespace
5. Save original VF state (`FillOriginalVfInfo`)
6. Apply VF configuration — MAC, VLAN, QoS, rates, spoofchk, trust, link state (`ApplyVFConfig`)
7. Move VF to container namespace (`SetupVF`) — skipped in DPDK mode
8. Run IPAM plugin if configured (`ipam.ExecAdd`)
9. Configure IP addresses on the interface (`ipam.ConfigureIface`)
10. Cache NetConf for CmdDel (`utils.SaveNetConf`)
11. Mark PCI address as in-use (`PCIAllocator.SaveAllocatedPCI`)
12. Send Gratuitous ARP / Unsolicited NA for IP reuse scenarios
13. Return CNI Result to stdout

On any failure, cleanup is performed via `defer` — releasing the VF, resetting
VF config, and cleaning up IPAM.

### CmdDel flow

1. Load cached NetConf (`config.LoadConfFromCache`) — returns `nil` on missing
   cache (idempotency)
2. Acquire device lock for the PCI address
3. Delete IPAM allocation (`ipam.ExecDel`)
4. Reset VF configuration via PF (`ResetVFConfig`) — must happen **before**
   `ReleaseVF` because some drivers error when resetting an untrusted VF
5. Move VF back to host namespace (`ReleaseVF`) — skipped in DPDK mode
6. Mark PCI address as released (`DeleteAllocatedPCI`)
7. Clean cached NetConf

### CmdCheck

Currently a no-op — returns `nil`.

### Key interfaces

| Interface | Package | Purpose |
|-----------|---------|---------|
| `sriov.Manager` | `pkg/sriov/` | VF setup, release, config apply/reset, state capture |
| `utils.NetlinkManager` | `pkg/utils/` | Abstraction over `vishvananda/netlink` for testability |
| `sriov.pciUtils` | `pkg/sriov/` | Sysfs PCI/VF discovery operations |

---

## Coding Conventions

### Logging

The project uses structured logging via `pkg/logging/`, which wraps
`k8snetworkplumbingwg/cni-log`:

```go
logging.Debug("message", "key1", value1, "key2", value2)
logging.Info("message", "key1", value1)
logging.Warning("message", "key1", value1)
logging.Error("message", "key1", value1)
```

Every log message automatically includes `cniName`, `containerID`, `netNS`,
and `ifName` context. Log level and file are configured via the CNI NetConf
(`logLevel`, `logFile` fields).

**Do not** use `fmt.Printf` or `log.Printf` — CNI plugins must not write to
stdout (it would corrupt the CNI result JSON). All logging goes to stderr or
a file.

### Error handling

- Wrap errors with context: `fmt.Errorf("SRIOV-CNI failed to load netconf: %v", err)`
- CmdDel must be **idempotent** — return `nil` when cached config is missing
- Use `defer` for cleanup on failure paths in CmdAdd
- Netlink errors (ENODEV, EBUSY) can be transient during VF driver rebind —
  handle gracefully

### Import Ordering

The `.golangci.yml` enforces import ordering via `goimports` with local prefix:

```
github.com/k8snetworkplumbingwg/sriov-cni
```

Standard ordering: stdlib → external → k8s.io → local project.

```go
import (
    "fmt"
    "net"

    "github.com/containernetworking/cni/pkg/skel"
    "github.com/vishvananda/netlink"

    "github.com/k8snetworkplumbingwg/sriov-cni/pkg/config"
    "github.com/k8snetworkplumbingwg/sriov-cni/pkg/logging"
)
```

### Naming conventions

- Interfaces are defined in the package that uses them (e.g., `pciUtils` in
  `pkg/sriov/`, `NetlinkManager` in `pkg/utils/`)
- Mock files live in `mocks/` subdirectories within each package
- Unexported interfaces use camelCase (e.g., `pciUtils`)
- Exported interfaces use PascalCase (e.g., `NetlinkManager`, `Manager`)
- Build tag: `-tags no_openssl` is required for all builds

### Build tag

All Go builds use `-tags no_openssl`. This is set in the Makefile via
`GO_TAGS ?= -tags no_openssl`. Always include this tag when running `go build`
or `go test` manually.

---

## Dependencies

| Dependency | Purpose |
|------------|---------|
| `containernetworking/cni` | CNI specification types and skeleton (`skel.PluginMain`) |
| `containernetworking/plugins` | IPAM delegation (`ipam.ExecAdd/Del`), namespace handling (`ns.GetNS`) |
| `k8snetworkplumbingwg/cni-log` | Structured logging library for CNI plugins |
| `vishvananda/netlink` | Linux netlink operations — VF configuration, link management |
| `vishvananda/netns` | Network namespace operations (transitive) |
| `onsi/ginkgo/v2` + `onsi/gomega` | Test framework |
| `stretchr/testify` | Mock support for unit tests |

Dependencies are managed with Go modules (`go.mod` / `go.sum`). No vendor
directory is tracked.

---

## Testing Patterns

### Unit tests

- Tests live alongside the code: `sriov_test.go` next to `sriov.go`
- **Ginkgo v2 + Gomega** framework — test suites initialized via
  `*_suite_test.go` files
- External dependencies (netlink, sysfs) are mocked via interfaces
  (`NetlinkManager`, `pciUtils`)
- Mocks are generated with **mockery v2** and stored in `pkg/*/mocks/`
- Test coverage is measured with `go test -cover`

### Integration tests

- Live in `test/integration/` — use the `bash_unit` shell test framework
- Use a **mocked CNI binary** (`test/integration/sriov_mocked.go`) that
  operates against:
  - A fake sysfs filesystem (created by `pkg/utils/testing.go:CreateTmpSysFs`)
  - A mocked netlink library (`pkg/utils/testing.go:MockNetlinkLib`)
- Netlink calls are recorded to a `.calls` file that tests assert against
- Tests require `sudo` for network namespace operations
- Build with coverage instrumentation: `GOCOVERDIR=... make test-integration`

### E2E tests

- Run via the **sriov-network-operator** E2E test suite in CI
- Not in this repo — CI checks out `sriov-network-operator` and runs its
  conformance tests against a locally-built sriov-cni image
- Run on self-hosted `sriov` runners with actual SR-IOV hardware

---

## Common Pitfalls

1. **Missing `runtime.LockOSThread()`** — Network namespace operations require
   the goroutine to be pinned to the OS thread. The `init()` in `main.go`
   handles this, but be aware when writing tests.

2. **Writing to stdout** — CNI plugins communicate results via stdout. Any
   `fmt.Println` or similar call will corrupt the CNI result JSON. Use the
   `logging` package (writes to stderr or file).

3. **Non-idempotent CmdDel** — CmdDel can be called multiple times by kubelet.
   It must succeed even when the cached config or network namespace is missing.

4. **VF reset ordering** — `ResetVFConfig` must be called **before**
   `ReleaseVF` because some NIC drivers error when resetting a VF netdev after
   trust is turned off.

5. **Missing `no_openssl` build tag** — The project requires `-tags no_openssl`
   for all builds. Omitting it will cause build failures.

6. **DPDK mode** — When `DPDKMode` is true, the VF is not moved to the
   container namespace and no IP configuration is applied. Code must check
   `netConf.DPDKMode` before namespace operations.

7. **PCI allocator locking** — The PCI allocator uses file-based locking to
   prevent concurrent VF allocation. Always use `allocator.Lock()`/defer
   unlock patterns.

8. **VLAN protocol byte order** — The `VlanProtoInt` map in `pkg/types/`
   handles a netlink bug on big-endian systems (s390x). Be aware of this when
   working with VLAN configuration.

9. **Mock generation** — Run `make mock-generate` after changing any interface
   (`NetlinkManager`, `pciUtils`). The generated mocks must be committed.

10. **Integration test cleanup** — Integration tests create network namespaces
    and temporary files under `test/integration/tmp/`. Set
    `INT_TEST_SKIP_CLEANUP=true` to preserve artifacts for debugging.
