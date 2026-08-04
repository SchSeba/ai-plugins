# ib-sriov-cni — Coding

Coding conventions, architecture patterns, and common pitfalls for contributing
to the `k8snetworkplumbingwg/ib-sriov-cni` repository.

---

## Repository Layout

| Directory | Purpose |
|-----------|---------|
| `cmd/ib-sriov-cni/` | CNI plugin binary entry point — `cmdAdd`, `cmdDel`, `cmdCheck` |
| `cmd/thin_entrypoint/` | Container entrypoint — copies CNI binary to host `/opt/cni/bin` |
| `pkg/config/` | CNI netconf parsing and validation (`LoadConf`, `LoadDeviceInfo`, `LoadConfFromCache`) |
| `pkg/sriov/` | SR-IOV VF management — `SetupVF`, `ReleaseVF`, `ApplyVFConfig`, `ResetVFConfig`, GUID handling |
| `pkg/types/` | Type definitions (`NetConf`, `Manager`, `NetlinkManager`, `PciUtils`) and generated mocks |
| `pkg/types/mocks/` | testify/mockery-generated mocks for `Manager`, `NetlinkManager`, `PciUtils` |
| `pkg/utils/` | Utility functions — sysfs operations, GUID validation, RDMA device management, PCI helpers |
| `deployment/` | Kubernetes manifests — DaemonSet YAMLs and example CRDs |
| `deployment/examples/` | Example NetworkAttachmentDefinition and test pod manifests |
| `images/` | Container image scripts — `image_test.sh`, build instructions |
| `docs/` | Documentation assets (topology diagram) |
| `.github/workflows/` | CI workflows — build, test, static analysis, image push |

---

## CNI Plugin Architecture

### Overview

ib-sriov-cni is a **CNI plugin** for InfiniBand SR-IOV devices on Kubernetes.
It manages Virtual Functions (VFs) and optionally Physical Functions (PFs) on
Mellanox ConnectX adapter cards. The plugin handles GUID assignment, RDMA
device namespace isolation, link state management, and IPAM delegation.

### Entry point pattern

The binary is built from `cmd/ib-sriov-cni/main.go`. It uses the standard CNI
skeleton (`skel.PluginMainFuncs`) with three handlers:

```go
skel.PluginMainFuncs(
    skel.CNIFuncs{
        Add:   cmdAdd,
        Del:   cmdDel,
        Check: cmdCheck,
    },
    cniVersion.All, "")
```

`init()` calls `runtime.LockOSThread()` because namespace operations (unshare,
setns) must execute on the main OS thread.

### cmdAdd flow

1. **Parse config** — `getNetConfNetns()` loads and validates the CNI netconf.
2. **Lock** — `lockCNIExecution()` acquires a file lock to serialize VF
   operations across concurrent CNI calls.
3. **VFIO/PF detection** — Determines whether device is VF or PF, detects
   vfio-pci driver binding.
4. **PF passthrough** — PF devices require `vfioPciMode`; they skip VF setup.
5. **VF configuration** — `doVFConfig()` calls `ApplyVFConfig` (GUID, link
   state, VF rebind), optionally moves RDMA device to namespace, then calls
   `SetupVF` (move net device to pod namespace).
6. **IPAM** — `runIPAMPlugin()` delegates to the configured IPAM plugin
   (DHCP is explicitly rejected).
7. **Cache** — `SaveNetConf()` caches config for `cmdDel`.

### cmdDel flow

1. **Load cached config** — `LoadConfFromCache()` reads cached netconf.
2. **IPAM cleanup** — Calls `ipam.ExecDel`.
3. **VF cleanup** — `handleVFCleanup()` releases the VF (moves net device
   back), restores RDMA device to default namespace, resets VF config.
4. **Cache cleanup** — Removes cached netconf on success.

Per the CNI spec, `cmdDel` returns success even if the cached config or
namespace is missing.

### cmdCheck

Currently a no-op (`return nil`).

### Key interfaces

| Interface | Package | Purpose |
|-----------|---------|---------|
| `Manager` | `pkg/types` | VF lifecycle: `SetupVF`, `ReleaseVF`, `ApplyVFConfig`, `ResetVFConfig` |
| `NetlinkManager` | `pkg/types` | Wraps `vishvananda/netlink` for testability |
| `PciUtils` | `pkg/types` | Wraps PCI/sysfs utilities for testability |

All three have mock implementations in `pkg/types/mocks/` for unit testing.

---

## Key Domain Concepts

- **GUID handling** — VF port GUID and node GUID configuration via netlink.
  GUIDs are sourced from `RuntimeConfig.InfinibandGUID`, `CNI_ARGS`, or the
  netconf `guid` field. `FF:FF:FF:FF:FF:FF:FF:FF` is treated as "no GUID"
  and is skipped.
- **RDMA device isolation** — Moving RDMA devices between network namespaces
  via `rdma-cni`. Must be done *before* `SetupVF` because rebinding causes
  RDMA devices to be recreated.
- **VF rebind** — `ApplyVFConfig` unbinds and rebinds the VF to apply GUID
  changes. Ordering with RDMA namespace moves is critical.
- **IPoIB addresses** — InfiniBand over IP uses 20-byte hardware addresses.
  Alt-name cleanup strips the `nAltName` from VF links.
- **PKey** — Partition key configuration, managed externally by ib-kubernetes.
- **File locking** — `gofrs/flock` serializes concurrent CNI invocations to
  prevent RDMA resource name changes.
- **VFIO mode** — For vfio-pci bound devices (VMs/kubevirt). Skips network
  interface configuration. Auto-detected by checking driver binding in sysfs.
- **PF passthrough** — Physical Functions can be passed through in VFIO mode
  only. VF-style network configuration is not applicable for PFs.

---

## Coding Conventions

### Error handling

- Wrap errors with `fmt.Errorf("context: %v", err)` — no sentinel errors, no
  `pkg/errors`.
- Always include the device ID or PCI address in error messages for
  debuggability.
- `cmdDel` must tolerate missing resources gracefully (per CNI spec).
- Deferred cleanup uses named return values (`retErr`) to check for errors.

### Logging

- The project does **not** use a logging framework. There are no `klog`,
  `logrus`, or `zerolog` calls.
- `depguard` blocks `github.com/sirupsen/logrus` imports.
- Error reporting flows through CNI's `skel` framework, which prints errors
  to stdout as JSON.
- `fmt.Printf` is used sparingly in `thin_entrypoint` only.

### Imports

- Import ordering enforced by `goimports` with local prefix:
  `github.com/k8snetworkplumbingwg/ib-sriov-cni`
- Standard library → external → local module.
- Dot-imports are allowed for test frameworks: `ginkgo/v2`, `gomega`,
  `gomega/gstruct`.
- The CNI types package is aliased as `localtypes` in `main.go` to avoid
  collision with `containernetworking/cni/pkg/types`.

### Naming

- File names match the package purpose: `sriov.go`, `config.go`, `types.go`,
  `utils.go`, `rdma.go`.
- Test files: `*_test.go` alongside source files.
- Suite files: `*_suite_test.go` in each package (Ginkgo convention).
- Mock files: `pkg/types/mocks/<InterfaceName>.go` (testify convention).

### Build tags

- `-tags no_openssl` is passed to all Go build commands.
- `CGO_ENABLED=0` for static binaries.

---

## Testing Patterns

### Unit tests

- **Framework**: Ginkgo v2 + Gomega for BDD-style tests.
- **Mocks**: `stretchr/testify/mock` with generated mocks in `pkg/types/mocks/`.
- **Fake network namespace**: Tests define `fakeNetNS` implementing `ns.NetNS`
  to avoid real namespace operations.
- **Fake netlink**: `FakeLink` struct wraps `netlink.LinkAttrs` for testing.
- **sysfs mocking**: `pkg/utils/testing.go` provides `CreateTmpSysFs()` and
  `RemoveTmpSysFs()` to create temporary sysfs directory structures for tests
  that read from `/sys/class/net/` or `/sys/bus/pci/devices/`.
- Tests are co-located with source: `sriov_test.go` next to `sriov.go`.

### Image tests

- `images/image_test.sh` runs the container image with `--no-sleep` and
  verifies the binary is copied to the output directory.
- Invoked via `make test-image`.

### No E2E tests

- The repository has no Go-based E2E tests. E2E testing is done at the
  operator level via the SR-IOV Network Operator.

---

## Common Pitfalls

1. **RDMA device ordering** — RDMA devices must be moved to the namespace
   *before* `SetupVF`. Moving an RDMA device to a namespace causes its
   associated ULP (IPoIB) devices to be recreated in the default namespace.
2. **VF rebind side effects** — `ApplyVFConfig` rebinds the VF, which
   recreates RDMA resources. RDMA device names may change if CNI operations
   are not serialized via the file lock.
3. **Missing sysfs paths in tests** — When adding new sysfs-reading
   functions, update `pkg/utils/testing.go` with the necessary temporary
   directory/file entries.
4. **GUID validation** — The default GUID `FF:FF:FF:FF:FF:FF:FF:FF` means
   "no GUID set". Treat it as empty, not as a valid GUID to configure.
5. **DHCP not supported** — The plugin explicitly rejects DHCP IPAM. This is
   by design and must not be changed.
6. **CNI spec compliance for cmdDel** — `cmdDel` must return success even
   when the cached config or netns path is missing. Failing here causes
   Kubernetes pod deletion to hang.
7. **Thread locking** — `runtime.LockOSThread()` in `init()` is mandatory.
   Namespace operations fail if the goroutine migrates to a different OS
   thread.
8. **PF vs VF distinction** — PF passthrough is only supported in VFIO mode.
   Code must check `IsVFDevice` before attempting VF-specific operations
   like `SetupVF`, `ApplyVFConfig`, or IPAM.
9. **Build tag** — Always use `-tags no_openssl`. Omitting it causes build
   failures from transitive dependencies.
