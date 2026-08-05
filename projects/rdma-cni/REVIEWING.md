# rdma-cni — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `k8snetworkplumbingwg/rdma-cni` repository.

---

## Review Focus Areas

### CNI Plugin Correctness

- **Chained plugin contract**: CmdAdd must reject calls without `PrevResult`
  (`RawPrevResult == nil`). rdma-cni is never standalone — it always runs after
  a delegate plugin (e.g., sriov-cni).
- **RDMA subsystem mode check**: CmdAdd must verify the system RDMA mode is
  `exclusive` before moving devices. If the mode is `shared`, device isolation
  per namespace does not work.
- **Namespace safety**: All namespace operations must run on a thread locked
  via `runtime.LockOSThread()`. The existing `init()` handles this for the
  main goroutine. Any new goroutines performing namespace ops need their own
  lock.
- **CmdDel idempotency**: CmdDel must handle double-deletion gracefully — if
  the cache entry is missing or the namespace is already gone, it should log a
  warning and return nil, not an error. Kubernetes may call CmdDel multiple
  times.
- **CmdDel with empty Netns**: When `args.Netns` is empty (container exited),
  CmdDel should return nil immediately. The RDMA device has already been
  returned to the host namespace by the kernel.
- **Error recovery in CmdAdd**: If the cache save fails after the RDMA device
  has been moved to the container namespace, the device must be moved back to
  the host namespace before returning the error.
- **DeviceID fallback**: When `conf.DeviceID` is empty, the plugin derives it
  from the PrevResult MAC address. Review that this fallback is preserved and
  not accidentally broken.

### Device Handling

- **PCI vs auxiliary devices**: The code path branches on `utils.IsPCIAddress()`.
  PCI addresses match `^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]$`.
  Everything else is treated as an auxiliary device name (e.g.,
  `mlx5_core.sf.4`). Ensure both paths are covered in tests.
- **Single RDMA device expectation**: `getRDMADevice()` expects exactly one
  RDMA device for a given PCI/aux device. Zero devices → error. Multiple
  devices → error (unsupported state). This invariant must be preserved.
- **Namespace file descriptor lifetime**: When moving RDMA devices, the target
  namespace is opened, used, and then closed (`defer targetNs.Close()`). Verify
  that namespace handles are not leaked on error paths.

### State Cache

- **Cache path**: State is cached at `/var/lib/cni/rdma`. The state reference
  key is `<network>-<containerID>-<ifname>`. Ensure uniqueness for multi-
  interface pods.
- **File permissions**: Cache directory uses `0700`, files use `0600`. Verify
  that new code does not relax these permissions.
- **JSON serialization**: The `RdmaNetState` struct is serialized to JSON.
  Adding new fields requires bumping `RdmaNetStateVersion` (minor for additive
  changes, major for breaking changes).

### Code Quality

- **Structured logging**: All logging must use `zerolog` (`log.Info().Msgf`,
  `log.Debug().Msgf`, `log.Warn().Msgf`). Reject `fmt.Printf`, `log.Printf`,
  `klog`, or `logrus` usage.
- **Error wrapping**: Errors should be wrapped with context. Prefer `%w` verb
  when the caller needs to unwrap, `%v` otherwise. Check that error messages
  start lowercase and do not end with punctuation.
- **Import ordering**: stdlib → external → internal. The local prefix
  `github.com/k8snetworkplumbingwg/rdma-cni` must be in its own group.
  `goimports` enforces this.
- **Line length**: Maximum 120 characters (`lll` linter). Long error messages
  can be split across lines.
- **Function complexity**: Maximum cognitive complexity 30 (`gocognit`),
  maximum function length 100 lines / 50 statements (`funlen`). If a function
  exceeds these, it should be refactored.
- **No logrus**: The `depguard` linter denies `github.com/sirupsen/logrus`.
  The project uses zerolog exclusively.

### Testing

- **Unit test coverage**: New logic must have corresponding Ginkgo v2 + Gomega
  tests.
- **Mock consistency**: If an interface changes, mocks must be regenerated with
  `make generate-mocks`. Hand-edited mocks are a review rejection.
- **Both PCI and auxiliary paths**: Test changes that affect device resolution
  must cover both PCI address and auxiliary device name code paths.
- **Error paths**: CmdAdd and CmdDel have multiple error branches (namespace
  open failure, RDMA device not found, cache failures). New error paths need
  test coverage.
- **Filesystem mocking**: Cache tests should use `afero.MemMapFs` (via
  `newFakeFileSystemOps()`), not real filesystem operations.
- **Namespace mocking**: Use the `dummyNetNs` pattern (implements `ns.NetNS`
  with a configurable `Fd()`) for namespace tests.

### Dependencies

- **No vendor directory**: The repo uses Go modules without vendoring. PRs
  that add a `vendor/` directory should be rejected.
- **Dependency additions**: New dependencies should be justified. The project
  has a small dependency footprint — adding large frameworks is discouraged.
- **Depguard compliance**: `logrus` is explicitly denied. Any new logging
  dependency must be discussed.

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Missing mock regeneration | Interface changed but `mocks/` not updated — run `make generate-mocks` |
| Hand-edited mock file | Changes in `pkg/*/mocks/` not matching mockery output |
| Logrus import | Using `logrus` instead of `zerolog` — denied by depguard |
| Missing error context | `return err` without wrapping — should be `fmt.Errorf("context: %w", err)` |
| Broken CmdDel idempotency | CmdDel returns error on cache miss — should return nil |
| Missing PCI/aux test path | Only one device type tested — both PCI and auxiliary must be covered |
| Namespace handle leak | `ns.GetNS()` opened but not closed on error path |
| Relaxed file permissions | Cache files created with permissions broader than `0600` |
| Import order violation | Internal imports not in separate group — `goimports` will catch this |
| Magic numbers | Unexplained numeric literals — `mnd` linter will flag these |
| Line too long | Lines exceeding 120 characters — `lll` linter will flag |
| Missing build tag | Manual build without `-tags no_openssl` |
| `fmt.Printf` in runtime code | Should use `log.Info().Msgf()` or equivalent zerolog call |
| Vendor directory committed | Should not exist — repo uses Go modules directly |
| CmdAdd without PrevResult check | New code path that doesn't verify chained plugin contract |
| Thread-unsafe namespace op | Namespace operation in new goroutine without `runtime.LockOSThread()` |

---

## PR Checklist (Reviewer Perspective)

1. Does `make lint` pass? (golangci-lint v2.7.2 with the project config)
2. Does `make test` pass? (Ginkgo v2 unit tests)
3. Does `make build` succeed? (with `-tags no_openssl` and `CGO_ENABLED=0`)
4. Are generated mock files regenerated, not hand-edited?
5. Are new interfaces added to `.mockery.yml` for mock generation?
6. Does new code use zerolog (not logrus, klog, or fmt.Printf)?
7. Are errors wrapped with context (`fmt.Errorf("...: %w", err)`)?
8. Are both PCI and auxiliary device paths tested?
9. Is CmdDel still idempotent after the change?
10. Is the RDMA exclusive-mode check preserved in CmdAdd?
11. Are namespace handles properly closed on all paths (including errors)?
12. Are there no unrelated changes mixed into the PR?
13. Are import groups correct? (stdlib → external → internal)
14. Does the Dockerfile still build? (multi-stage alpine build)
15. Is the `vendor/` directory absent from the PR?

---

## Commit Structure Expectations

- **Self-contained commits**: Code changes and their corresponding tests belong
  in the same commit.
- **Generated code in separate commits**: Mock regeneration (`make generate`)
  should be in its own commit, separate from manual code changes. This makes
  review easier — the reviewer can skip the generated-code commit.
- **Clear commit messages**: Use imperative mood. Reference the component
  affected: `pkg/rdma: add support for auxiliary devices`,
  `pkg/cache: fix file permission on state save`.
- **Small, focused PRs**: Prefer one logical change per PR. Do not mix
  refactoring with new features.

---

## CI Verification

The following CI checks must pass before merge:

| Check | Workflow | What it validates |
|-------|----------|-------------------|
| Build | `buildtest.yaml` | Binary compiles on linux/amd64 |
| Unit Tests | `buildtest.yaml` | All Ginkgo tests pass |
| Coverage | `buildtest.yaml` | Coverage report generated and uploaded |
| golangci-lint | `static-scan.yaml` | All configured linters pass |
| shellcheck | `static-scan.yaml` | Shell scripts are valid |
| hadolint | `static-scan.yaml` | Dockerfile follows best practices |
| CodeQL | `codeql.yaml` | No security vulnerabilities detected |

All CI jobs use Go 1.26.x. There are no E2E or integration test jobs — only
unit tests run in CI.
