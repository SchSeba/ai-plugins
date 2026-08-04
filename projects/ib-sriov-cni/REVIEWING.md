# ib-sriov-cni — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `k8snetworkplumbingwg/ib-sriov-cni` repository.

---

## Review Focus Areas

### CNI Plugin Correctness

- **cmdDel resilience** — `cmdDel` must tolerate missing resources (cached
  config, netns, network interfaces) per the
  [CNI spec](https://github.com/containernetworking/cni/blob/main/SPEC.md#del-remove-container-from-network-or-un-apply-modifications).
  Failing here causes Kubernetes pod deletion to hang indefinitely.
- **File lock scope** — All VF operations that may cause RDMA device name
  changes must be serialized via the file lock (`lockCNIExecution`). Verify
  that new code paths interacting with VF rebind or RDMA moves are within
  the lock scope.
- **RDMA ↔ SetupVF ordering** — RDMA device moves must happen *before*
  `SetupVF`. Moving an RDMA device to a namespace causes its associated ULP
  (IPoIB) devices to be recreated in the default namespace. Incorrect
  ordering silently breaks RDMA isolation.
- **Deferred cleanup symmetry** — Every resource acquired in `cmdAdd` must
  have a corresponding deferred cleanup in case of error. Check that deferred
  functions reference `retErr` (named return) correctly.
- **PF vs VF code paths** — PF passthrough requires VFIO mode. Verify new
  code does not assume all devices are VFs. Check `IsVFDevice` and
  `VfioPciMode` flags before VF-specific operations.
- **VFIO mode skips** — VFIO devices do not have network interfaces. Verify
  that new code skips network interface operations (IPAM, `SetupVF`,
  `ReleaseVF`) when `VfioPciMode` is true.

### Configuration & Validation

- **Link state values** — Only `auto`, `enable`, and `disable` are valid.
  `LoadConf` validates this. New config fields need similar validation.
- **GUID source priority** — `RuntimeConfig.InfinibandGUID` →
  `CNI_ARGS["guid"]` → (empty). Verify the priority chain is maintained in
  `getGUIDFromConf`.
- **DHCP rejection** — DHCP IPAM is explicitly unsupported. Verify new IPAM
  code paths maintain this restriction.
- **DeviceID is required** — `getNetConfNetns` validates that `DeviceID` is
  not empty. Ensure new config paths do not bypass this check.

### sysfs & Netlink Operations

- **sysfs path construction** — All sysfs reads use `utils.NetDirectory`
  and `utils.SysBusPci` base paths. These are overridable for tests via
  `CreateTmpSysFs()`. Verify new sysfs operations follow this pattern.
- **Netlink error handling** — Netlink operations can fail due to device
  state changes, race conditions, or missing capabilities. All netlink calls
  must have error handling with descriptive messages including device names
  or PCI addresses.
- **VF rebind** — `RebindVf` unbinds then binds the VF through sriovnet.
  This temporarily removes the VF device from the system. Code that accesses
  the VF after rebind must re-discover the device name.

### Interface & Testability

- **Interface usage** — VF operations go through the `Manager` interface.
  Netlink operations go through `NetlinkManager`. PCI operations go through
  `PciUtils`. New system-level operations should follow this pattern for
  testability.
- **Mock updates** — When adding methods to `Manager`, `NetlinkManager`, or
  `PciUtils`, the corresponding mock in `pkg/types/mocks/` must be updated.
- **Test sysfs setup** — When adding new sysfs-reading functions, verify
  that `pkg/utils/testing.go` creates the necessary temporary sysfs entries.

---

## Go Code Quality

- **Error wrapping** — Use `fmt.Errorf("context: %v", err)`. Include
  device identifiers (PCI address, interface name, RDMA device name) in
  error messages.
- **No logging framework** — This project does not use klog, logrus, or
  zerolog. `depguard` blocks logrus. Error reporting flows through CNI's
  skel framework.
- **Import ordering** — stdlib → external → local module. Local prefix:
  `github.com/k8snetworkplumbingwg/ib-sriov-cni`. Enforced by `goimports`.
- **Build tag** — All Go builds require `-tags no_openssl`. Verify new CI
  steps or scripts include this tag.
- **CGO_ENABLED=0** — Static binaries. Do not introduce CGO dependencies.
- **Line length** — 140-character limit enforced by `lll` linter.
- **Function length** — Max 100 lines / 50 statements enforced by `funlen`.
- **Cyclomatic complexity** — Max 15 enforced by `gocyclo`.
- **Magic numbers** — `mnd` linter checks for magic numbers in arguments,
  case statements, conditions, and returns. Use named constants.
- **License header** — New Go files should include the Apache 2.0 license
  header (see `cmd/thin_entrypoint/main.go` for example).

---

## Testing Standards

- **Framework** — Ginkgo v2 + Gomega for all unit tests. Do not introduce
  alternative test frameworks.
- **Mocks** — `stretchr/testify/mock` with generated mocks. Expectations
  are set with `.On(...)` and verified with `.AssertExpectations()`.
- **Fake NS** — Tests must use `fakeNetNS` (local fake) rather than creating
  real network namespaces. Real namespace operations require root privileges
  and cause test instability.
- **sysfs mocking** — Use `CreateTmpSysFs()` / `RemoveTmpSysFs()` for tests
  that interact with sysfs paths. This creates a temporary directory tree
  mimicking `/sys/class/net/` and `/sys/bus/pci/devices/`.
- **Test co-location** — Tests live alongside source files. `sriov_test.go`
  is in the `sriov` package, not in `sriov_test` (white-box testing).
- **Suite files** — Each package has a `*_suite_test.go` file registering
  the Ginkgo test suite with `RegisterFailHandler(Fail)`.

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Missing cmdDel resilience | New cleanup code fails instead of returning nil on missing resources |
| RDMA ordering violation | RDMA device moved after SetupVF — breaks IPoIB recreation |
| Cleanup not deferred | Acquired resources lack deferred release on error path |
| Missing VfioPciMode check | New code performs network operations on VFIO devices |
| Missing PF/VF distinction | Code assumes device is always VF, doesn't check `IsVFDevice` |
| sysfs path hardcoded | Uses literal `/sys/...` path instead of `utils.NetDirectory` / `utils.SysBusPci` |
| Mock not updated | Interface method added but mock in `pkg/types/mocks/` not regenerated |
| Missing sysfs test entries | New sysfs-reading function but `testing.go` not updated |
| Import alias collision | `types` used without alias, conflicting with `containernetworking/cni/pkg/types` |
| Missing build tag | New build/test command omits `-tags no_openssl` |
| Magic number in production code | Numeric literal used instead of named constant |
| Logging framework introduced | Uses logrus, klog, or zerolog (blocked by depguard/project convention) |
| DHCP guard bypassed | New IPAM path doesn't reject DHCP type |
| Error missing device ID | Error message doesn't include PCI address or device name |
| Thread safety | Namespace operations without `runtime.LockOSThread()` |
| Lock scope too narrow | VF rebind or RDMA move outside `lockCNIExecution` scope |

---

## PR Checklist (Reviewer Perspective)

1. Does `make lint` pass cleanly?
2. Does `make test` pass?
3. Does `make hadolint` pass (if Dockerfile changed)?
4. Does `make shellcheck` pass (if shell scripts changed)?
5. Are new functions covered by unit tests?
6. Do test mocks match interface definitions?
7. Is `cmdDel` resilient to missing resources?
8. Are RDMA/VF operations in correct order?
9. Are error messages descriptive (include device identifiers)?
10. Are new sysfs paths using the configurable base variables?
11. Is the `-tags no_openssl` build tag preserved in any new build steps?
12. Does the code handle both VF and PF devices correctly?
13. Does the code handle VFIO mode correctly (skip network operations)?
14. Are deferred cleanups correctly wired to `retErr`?
15. Are new constants defined instead of magic numbers?
16. Does import ordering follow stdlib → external → local convention?

---

## Commit Structure Expectations

- **Self-contained commits** — Each commit should compile and pass tests
  independently.
- **Code + tests together** — New logic and its tests belong in the same
  commit. Do not defer tests to follow-up PRs.
- **Descriptive commit messages** — Include what changed and why. Reference
  related issues if applicable.
- **Small, focused PRs** — Prefer multiple small PRs over large omnibus
  changes. Separate refactoring from feature work.
- **No unrelated changes** — Do not mix formatting fixes, dependency bumps,
  or refactoring into feature PRs.

---

## Reviewer Preferences

- **Test RDMA paths** — RDMA isolation is a critical feature. Changes to
  RDMA-related code paths should include tests that verify the ordering and
  cleanup behavior.
- **Verify cleanup symmetry** — For every resource acquired in `cmdAdd`,
  verify there is a matching release in `cmdDel` and in `cmdAdd`'s error
  deferred functions.
- **Check CNI spec compliance** — The plugin supports all CNI versions via
  `cniVersion.All`. New features must not break backward compatibility with
  older CNI versions.
- **Review sysfs interactions carefully** — sysfs operations are
  kernel-version-dependent. New sysfs paths should be documented with the
  minimum kernel version they require.
- **Verify VFIO/PF edge cases** — VFIO mode and PF passthrough are newer
  features with different code paths. Ensure they are tested independently
  from the standard VF flow.
