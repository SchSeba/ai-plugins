# SR-IOV CNI — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `k8snetworkplumbingwg/sriov-cni` repository.

---

## Review Focus Areas

### CNI Specification Compliance

- **CmdAdd must return a valid CNI Result** on success. The result must include
  interface information (name, sandbox path, MAC address) and, when IPAM is
  configured, IP addresses with correct interface indices.
- **CmdAdd must clean up on failure** — all resource allocations (VF config,
  namespace moves, IPAM, PCI allocator) must be reversed via `defer` on error
  paths. Verify that the cleanup order is correct.
- **CmdDel must be idempotent** — calling it twice must not return an error.
  Missing cached config, missing network namespace, and missing VF must all
  be handled gracefully.
- **CmdCheck** is currently a no-op. If it gains functionality, it must
  validate that the VF state matches the expected configuration from
  `prevResult`.
- **IPAM delegation**: Verify that `ipam.ExecAdd` is called with the correct
  stdin data and that IPAM results are properly incorporated into the CNI
  Result. On failure, `ipam.ExecDel` must be called to release the allocation.
- **stdout is sacred**: CNI plugins return results via stdout. No `fmt.Println`,
  `log.Println`, or other stdout writes are allowed — they corrupt the result.

### SR-IOV VF Management

- **VF state save/restore**: `FillOriginalVfInfo` must capture all VF
  attributes (MAC, VLAN, QoS, rates, spoofchk, trust, link state, MTU) before
  modification. `ResetVFConfig` must restore them accurately.
- **Reset before release**: `ResetVFConfig` must be called **before**
  `ReleaseVF` in CmdDel — some NIC drivers error when resetting a VF after
  trust is turned off.
- **Netlink error handling**: Operations against VFs can return ENODEV (VF not
  bound), EBUSY (VF in use), or EINVAL (invalid parameter). Review that these
  are handled or surfaced with context, not swallowed.
- **VLAN protocol byte order**: The `VlanProtoInt` map handles a netlink bug on
  big-endian systems (s390x). Changes to VLAN handling must preserve this
  workaround until the upstream netlink fix is available.
- **DPDK mode**: When `DPDKMode` is true, the VF is **not** moved to the
  container namespace. All code that operates on the VF in the container
  namespace must check this flag.
- **PCI allocator concurrency**: The PCI allocator uses file-based locking to
  prevent concurrent VF allocation/deallocation for the same PCI address.
  Verify lock acquire/release is correct and no deadlock paths exist.

### Network Namespace Operations

- **`runtime.LockOSThread()`**: Any code that performs namespace operations
  must run on a locked OS thread. The main binary handles this in `init()`,
  but tests and new code paths must be verified.
- **Namespace restore**: Moving a VF to a container namespace must be paired
  with a restore on teardown. Verify that `ReleaseVF` moves the VF back to the
  host namespace on all paths.
- **Missing namespace on CmdDel**: When the container namespace is gone (e.g.,
  after node restart), CmdDel must return success after releasing IPAM. Check
  for `ns.NSPathNotExistErr` handling.

### Configuration Parsing

- **JSON tags**: Verify that struct field JSON tags match the expected CNI
  config keys (e.g., `json:"vlan"`, `json:"deviceID"`, `json:"trust,omitempty"`).
- **Backward compatibility**: New config fields must have appropriate zero
  values that do not change behavior for existing configurations.
- **Config caching**: `LoadConfFromCache` must restore the full NetConf
  including IPAM configuration and device information. Changes to NetConf
  fields must verify the cache path still works.
- **MAC address handling**: MAC addresses must be normalized to lowercase
  (`strings.ToLower`). RuntimeConfig MAC takes precedence over env args.

### Logging

- **Appropriate levels**: Debug for verbose tracing, Info for operational
  events, Warning for recoverable issues, Error for failures.
- **No sensitive data in logs**: PCI addresses and interface names are
  acceptable; secrets and tokens are not.
- **Structured fields**: Use key-value pairs consistently (e.g.,
  `"func", "cmdAdd"`, `"DeviceID", netConf.DeviceID`).
- **Log initialization**: `config.SetLogging` must be called at the start
  of every CNI command before any logging.

### Go Code Quality

- **Structured logging**: Use `logging.Debug/Info/Warning/Error`, not
  `fmt.Printf` or `log.Printf`.
- **Error wrapping**: Errors must include context — `fmt.Errorf("failed to
  set up VF: %v", err)`.
- **Import ordering**: stdlib → external → project-internal (enforced by
  `goimports` with local prefix `github.com/k8snetworkplumbingwg/sriov-cni`).
- **No `init()` functions** except the `runtime.LockOSThread()` in `main.go`.
- **Interface-driven design**: New external dependencies should be accessed
  through interfaces for testability.
- **Build tag**: `-tags no_openssl` must be present in all build and test
  commands.

### Testing

- **Unit tests required**: New logic must have Ginkgo/Gomega unit tests.
  Tests must cover both success and failure paths.
- **Mocks for hardware access**: All netlink, sysfs, and namespace operations
  must be mocked in unit tests — never depend on real hardware.
- **Mock synchronization**: If an interface changes, `make mock-generate` must
  be run and the regenerated mocks committed alongside the interface change.
- **Integration test coverage**: Changes to CmdAdd/CmdDel flow should include
  integration test updates in `test/integration/`.
- **No `go test ./...`**: Use `make test` which correctly excludes mock
  packages and applies the timeout.
- **Race detector**: Sensitive concurrent code changes should be validated with
  `make test-race`.

### Container Image

- **Multi-stage build**: Builder stage uses `golang:alpine`; runtime stage uses
  `alpine:3`. No build tools in the final image.
- **Entrypoint script**: `images/entrypoint.sh` copies the CNI binary to the
  host's CNI bin directory. Verify correct source/destination paths and error
  handling.
- **Signal handling**: The entrypoint sleeps indefinitely after copying the
  binary. It must handle SIGTERM for graceful shutdown during DaemonSet updates.

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Stdout pollution | Any `fmt.Print*` or `log.Print*` call in non-test code — corrupts CNI result |
| Missing cleanup on failure | CmdAdd allocates a resource but lacks `defer` cleanup on error |
| Non-idempotent CmdDel | CmdDel returns error when cache or namespace is missing |
| Broken import order | Imports not grouped as stdlib / external / project-internal |
| Missing build tag | `go build` or `go test` without `-tags no_openssl` |
| Stale mocks | Interface changed but `make mock-generate` not run |
| Missing VF state field | New VF attribute not captured in `FillOriginalVfInfo` / `ResetVFConfig` |
| Reset after release | `ResetVFConfig` called after `ReleaseVF` — driver error on untrusted VF |
| Hardcoded MAC case | MAC address not lowercased before comparison or storage |
| Missing DPDK check | Namespace operation performed without checking `netConf.DPDKMode` |
| Unlocked namespace ops | Network namespace operation without `runtime.LockOSThread()` |
| Missing PCI lock | PCI allocator accessed without `allocator.Lock()` |
| Missing error context | Raw error returned without wrapping (`return err` instead of `fmt.Errorf("...: %v", err)`) |
| Log to stdout | Using `fmt.Println` instead of `logging.*` — breaks CNI protocol |
| Missing test for error path | New error handling code has no test for the failure case |
| VLAN byte order | VLAN protocol value hardcoded without considering s390x big-endian fix |
| Config cache mismatch | New NetConf field not preserved through save/load cache cycle |
| Missing IPAM cleanup | IPAM `ExecAdd` called but `ExecDel` not deferred on failure |

---

## PR Checklist (Reviewer Perspective)

1. Does `make all` pass? (`fmt` + `lint` + `build`)
2. Do unit tests pass? (`make test` or `make test-race`)
3. Do integration tests pass? (`sudo make test-integration`)
4. Is the CI green? (buildtest, static-scan, codeql)
5. Are new/changed interfaces accompanied by updated mocks (`make mock-generate`)?
6. Does new code have adequate unit tests covering success and failure paths?
7. Are CNI operations (CmdAdd/CmdDel) idempotent and clean up on failure?
8. Is stdout clean (no `fmt.Print*` in non-test code)?
9. Are errors wrapped with context?
10. Is structured logging used (not `fmt.Printf` or `log.Printf`)?
11. Do import groups follow stdlib → external → project-internal order?
12. Are network namespace operations guarded by `runtime.LockOSThread()`?
13. Is DPDK mode checked before any namespace operation?
14. Are VF state fields captured and restored symmetrically?
15. Is the `-tags no_openssl` build tag preserved in any new build/test commands?
16. Does the PR description explain the change clearly with issue reference?

---

## Commit Structure Expectations

- **Branch prefix**: `dev/` branches for feature work (per CONTRIBUTING.md)
- **Commit message format**:
  ```
  Change summary

  Detailed explanation: why and how.
  Wrap to 72 characters.

  Fixes #NUMBER
  ```
- **Small, focused PRs**: One feature or fix per PR. Large omnibus changes
  are harder to review and more likely to be rejected.
- **Tests with code**: Unit tests must be in the same commit as the code they
  test. Do not defer tests to follow-up PRs.
- **Generated code**: Mock regeneration should be in a separate commit or
  clearly labeled in the commit message.

---

## Reviewer Preferences

- **Small PRs** over large ones — easier to review, faster to merge.
- **Issue reference** — PRs should reference the issue they fix.
- **NIC compatibility** — CONTRIBUTING.md encourages testing with various NICs.
  PRs that change VF behavior should mention which NICs were tested.
- **`cnitool` testing** — For isolated CNI testing, use
  `containernetworking/cni/cnitool` as recommended in CONTRIBUTING.md.
- **OWNERS file** — Merges require approval from maintainers listed in `OWNERS`
  (zeeke, SchSeba, Eoghan1232) or admins (adrianchiris, dougbtv).
