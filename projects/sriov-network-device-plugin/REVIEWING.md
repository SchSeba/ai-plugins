# SR-IOV Network Device Plugin — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `k8snetworkplumbingwg/sriov-network-device-plugin` repository.

---

## Review Focus Areas

### Device Discovery & Sysfs Interaction

- **Nil checks on hardware info** — `ghw` PCI device info and network device
  attributes can be nil when sysfs data is incomplete. Every field access on
  hardware structs must be guarded with nil checks.
- **Sysfs path validation** — Validate paths before reading. Devices can
  disappear between discovery passes (hot-unplug, driver unbind). Handle
  `ENOENT` and `EACCES` gracefully instead of panicking.
- **RDMA subsystem availability** — RDMA device discovery code must handle
  cases where the RDMA subsystem is not loaded on the host.
- **vDPA bus availability** — vDPA device enumeration must validate that the
  vDPA bus is available before attempting discovery.
- **Integer overflow** — Bounds-check user-supplied sizes and PCI device class
  codes before using them in allocations.

### gRPC Device Plugin Server

- **Proper error codes** — Use appropriate gRPC status codes in device plugin
  server responses (not generic `errors.New()`).
- **Context propagation** — gRPC handlers must propagate `context.Context`
  for cancellation and timeouts.
- **Graceful shutdown** — Verify that the server handles SIGHUP, SIGINT,
  SIGTERM, and SIGQUIT signals correctly and stops all gRPC servers cleanly.
- **Resource naming** — Extended resource names must follow Kubernetes naming
  conventions (`<prefix>/<resource-name>`) and the resource prefix must be
  validated.
- **ListAndWatch behavior** — The device list stream must correctly reflect
  device health changes and handle kubelet reconnection.

### Resource Pool & Selector Logic

- **Selector matching** — Device selectors must handle edge cases: empty
  selectors, overlapping selectors across resource definitions, regex patterns
  in vendor/device IDs.
- **Pool boundaries** — Verify that devices are not accidentally shared across
  pools when multiple resource definitions match the same device.
- **ConfigMap parsing** — JSON config parsing must validate required fields and
  provide meaningful error messages for malformed configs.
- **CDI spec generation** — When `--use-cdi` is enabled, verify that CDI specs
  are generated correctly and cleaned up on shutdown.

### Factory Pattern

- **Singleton usage** — The `resourceFactory` uses a singleton pattern. Review
  that test code properly isolates factory state between tests.
- **Info provider selection** — Verify that the correct info providers are
  selected based on device type and VF driver (e.g., VFIO for `vfio-pci`,
  UIO for `igb_uio`).
- **Device type routing** — `netDevice`, `accelerator`, and `auxNetDevice`
  types must route to their correct provider and pool implementations.

### Network Device Specifics

- **NAD (Network Attachment Definition) annotations** — When generating device
  info, NAD resource name annotations must match the Kubernetes resource name.
- **DDP profile handling** — DDP (Dynamic Device Personalization) profile
  selectors read from sysfs and must handle missing or unsupported profiles.
- **pKey selectors** — InfiniBand partition key selectors must validate the
  key format and handle missing pKey assignments.
- **Link type detection** — Network link type (Ethernet vs InfiniBand) must be
  detected correctly from sysfs, not assumed from vendor ID.

---

## Go Code Quality

- **Logging** — The project uses `glog`, not klog or zerolog. Do not introduce
  `logrus` (depguard blocks it). Use appropriate log levels:
  - `glog.Infof` for informational messages.
  - `glog.Warningf` for non-critical issues.
  - `glog.Errorf` for errors that are returned or handled.
  - `glog.Fatalf` only for unrecoverable startup failures.
- **Error wrapping** — Errors must be wrapped with context using
  `fmt.Errorf("...: %w", err)`, not returned bare.
- **Import ordering** — Three groups: stdlib → external → project-internal
  (enforced by `gci` formatter).
- **Line length** — Max 140 characters per line (enforced by `lll` linter).
- **Function length** — Max 100 lines / 50 statements per function (enforced
  by `funlen`). Large functions must be refactored.
- **Magic numbers** — Numeric literals in arguments, cases, conditions, and
  returns are flagged by `mnd`. Use named constants.
- **Cyclomatic complexity** — Max 15 (enforced by `gocyclo`). Complex
  functions must be broken into smaller units.
- **License headers** — Every source file needs a license header. Two styles
  are in use (Intel copyright and NVIDIA SPDX) — follow the style of
  surrounding files.
- **No `init()` functions** — Unless required for registration patterns.
- **US English spelling** — Enforced by `misspell` linter.

---

## Testing Standards

### Test Coverage Requirements

- **New logic must have tests** — All new functions and branches need
  corresponding Ginkgo test cases.
- **Tests in the same commit** — Tests and the code they cover must be in the
  same commit.
- **No focused tests** — `FIt`, `FDescribe`, `FContext`, `FWhen` are forbidden
  by `ginkgolinter`. CI will fail if any are left in.
- **Mock regeneration** — After changing interfaces in `pkg/types/`,
  `pkg/utils/`, or `pkg/cdi/`, mocks must be regenerated via
  `make generate-mocks`.

### Test Patterns

- Tests use **Ginkgo v2 + Gomega** with dot-imports.
- Table-driven tests using Ginkgo `DescribeTable` / `Entry` are preferred for
  selector and matcher logic.
- Sysfs interactions are tested via mock file systems and test fixtures in
  `pkg/utils/testdata/`.
- gRPC server tests should use the `pool_stub.go` test helpers.

### What Reviewers Should Check

1. Are edge cases covered? (empty lists, nil devices, missing sysfs files)
2. Are error paths tested? (device disappearance, malformed config, permission errors)
3. Do tests use mocks appropriately? (no real sysfs access in unit tests)
4. Is the race detector clean? (`make test-race` passes)
5. Are new test helper functions placed in `testing.go` files (excluded from lint)?

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Missing nil check on device info | `ghw` structs can return nil — guard all field access |
| Bare error return | Error returned without wrapping context |
| Logrus import | `logrus` is blocked by depguard — use `glog` |
| Magic number | Numeric literal in logic — use a named constant |
| Function too long | Over 100 lines or 50 statements — refactor |
| Focused Ginkgo test | `FIt` / `FDescribe` left in — will fail CI |
| Missing mock regeneration | Interface changed but mocks not updated |
| Direct `go build` | Missing `-tags no_openssl` — use `make build` |
| Vendor files committed | Vendor directory is not tracked in git |
| Sysfs path not validated | Reading sysfs without checking path existence first |
| Unchecked error | Error return value ignored (errcheck) |
| Wrong import order | Imports not grouped as stdlib / external / project |
| Code duplication | Similar blocks > 100 tokens — extract to function |
| Missing license header | New file without Apache 2.0 header |
| DDP builder Go version bumped | Dockerfile DDP stage must stay at Go 1.20 |
| gRPC error without status code | Using `errors.New()` instead of `status.Errorf()` |
| Missing CDI cleanup | CDI specs not cleaned up in shutdown path |
| Overlapping device selectors | Multiple resource defs matching same device |
| Test accessing real sysfs | Unit test reading from host `/sys` instead of mock |

---

## PR Checklist (Reviewer Perspective)

1. Does `make all` pass? (lint + build + test)
2. Does `make test-race` pass? (race detector)
3. Are all new/changed interfaces mocked? (`make generate-mocks`)
4. Do new files have a license header? (Apache 2.0)
5. Are imports ordered correctly? (stdlib → external → project)
6. Are errors wrapped with context? (not bare returns)
7. Are there tests for new logic? (in the same commit)
8. Is the function length within limits? (100 lines / 50 statements)
9. Are nil checks in place for hardware info structs?
10. Is sysfs access guarded against device disappearance?
11. Are no `FIt` / `FDescribe` focused tests present?
12. Is the vendor directory left out of the changeset?
13. Does the Dockerfile DDP stage still use Go 1.20?
14. Are no `logrus` imports introduced?
15. Do ConfigMap/JSON config changes have validation and error messages?

---

## Commit Structure Expectations

- **Descriptive commit messages** — Follow the format:
  ```
  Change summary

  More detailed explanation of changes.
  Wrap to 72 characters.

  Fixes #NUMBER
  ```
- **Self-contained commits** — Code changes and their tests belong in the same
  commit.
- **Topic branches** — Branch names should use `dev/` prefix per
  CONTRIBUTING.md (e.g., `dev/add-vdpa-support`).
- **Small, focused PRs** — Each PR should address a single concern. Large
  feature work should be split into incremental PRs.
- **No unrelated changes** — Keep formatting fixes, dependency bumps, and
  refactoring in separate PRs from feature work.

---

## Reviewer Preferences

- **Hardware safety first** — Any code touching sysfs, PCI enumeration, or
  device allocation gets extra scrutiny. Race conditions in device discovery
  can cause kernel-level issues.
- **Interface-driven design** — New device types or providers should implement
  the interfaces in `pkg/types/types.go`. Don't bypass the factory pattern.
- **Config backward compatibility** — Changes to the ConfigMap JSON schema must
  be backward compatible. Old configs must still parse and work.
- **Test isolation** — Tests must not depend on host hardware state. Use mocks
  and test fixtures for all sysfs and netlink interactions.
- **E2E flakiness awareness** — The `sriov-operator-e2e-test` job runs on
  self-hosted runners with real SR-IOV hardware and is frequently flaky.
  `podman build` exit code 125 is an infrastructure error, not a code issue —
  do not block PRs on this.
