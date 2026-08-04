# dra-driver-sriov — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `k8snetworkplumbingwg/dra-driver-sriov` repository.

---

## Review Focus Areas

### CRD and API Changes

- **SriovResourcePolicy / DeviceAttributes**: Changes to filtering criteria or
  attribute handling affect which devices are advertised. Verify that new
  filter fields are plumbed through the controller reconciliation logic in
  `pkg/controller/resourcepolicycontroller.go`.
- **VfConfig**: Per-claim configuration changes affect the prepare/unprepare
  lifecycle. Verify new parameters are handled in `pkg/driver/dra_hook.go`,
  `pkg/devicestate/state.go`, and `pkg/devicestate/statehelpers.go`.
- **Deepcopy generation**: Any struct change in `pkg/api/` requires regenerating
  `zz_generated.deepcopy.go`. If the diff includes manual edits to
  `zz_generated.*` files, send it back — run `make generate` instead.
- **CRD manifest updates**: Changes to `sriovdra/v1alpha1` types must include
  updated CRD YAML in `deployments/helm/dra-driver-sriov/templates/`.
- **Backward compatibility**: New fields in CRD specs should have sensible
  zero-value behavior. Existing policies must continue working without changes.

### Device State and Discovery

- **PCI/sysfs interaction** (`pkg/host/`, `pkg/devicestate/discovery.go`):
  Code that reads from `/sys/bus/pci/devices/` or interacts with netlink must
  handle missing/unavailable sysfs entries gracefully. Verify error paths for
  missing VFs, unavailable PFs, or driver rebind failures.
- **Device filtering**: The opt-in model means no devices are advertised without
  a matching `SriovResourcePolicy`. Verify that filter matching logic in the
  controller correctly handles all criteria combinations (vendors, devices,
  pfNames, pciAddresses, pfPciAddresses, drivers, linkType).
- **Attribute keys**: Device attributes use specific prefixes
  (`sriovnetwork.k8snetworkplumbingwg.io/` for driver attributes,
  `k8s.cni.cncf.io/` for Multus attributes). Verify correct prefix usage —
  mixing them up breaks Multus integration or CEL selectors.
- **State consistency**: The device state manager tracks allocated VFs. Verify
  that prepare/unprepare operations correctly update state and persist via
  checkpoint (`checkpoint.json`).

### Configuration Mode Handling

- **STANDALONE vs MULTUS**: Code paths that are mode-specific must check
  `ConfigurationMode`. Common mistake: adding STANDALONE-only logic without
  guarding it, causing failures in MULTUS mode.
- **NRI plugin**: Only active in STANDALONE mode. Any NRI changes must verify
  they are no-ops in MULTUS mode.
- **CNI integration**: In STANDALONE mode, the driver fetches NAD config and
  injects `deviceID`. In MULTUS mode, this is skipped. Verify mode checks
  are in place.
- **Device metadata (KEP-5304)**: CDI-mounted metadata files are only supported
  in STANDALONE mode. Verify that metadata update paths are guarded.

### Driver Lifecycle (gRPC)

- **PrepareResourceClaims**: Must correctly parse `OpaqueDeviceConfig`, allocate
  VFs, apply configuration, generate CDI specs, and return device info. Verify
  error handling at each step — partial failures should not leave state
  inconsistent.
- **UnprepareResourceClaims**: Must restore original driver binding, release VFs,
  clean up CDI specs, and update checkpoint. Verify cleanup is thorough —
  leaked VFs or stale CDI specs are bugs.
- **ResourceSlice publishing**: The `PublishResources` method must include only
  policy-matched (advertised) devices. Verify that controller policy changes
  trigger re-publication.

### Go Code Quality

- **Structured logging**: Use `klog.FromContext(ctx)` with `.Info()` / `.Error()`
  methods. Not `klog.Infof`, `klog.V(x).Infof`, or `fmt.Printf`.
- **Error handling**: Errors must be wrapped with `fmt.Errorf("context: %w", err)`.
  Never swallow errors. Never use bare `return err` without context in exported
  functions.
- **Import ordering**: stdlib → external → k8s.io → project-local. Enforced by
  `goimports` in `.golangci.yml`.
- **Banned packages**: `github.com/sirupsen/logrus` is explicitly denied in
  `.golangci.yml` `depguard` rules.
- **Boilerplate**: Every file needs the Apache 2.0 license header.
- **Context propagation**: Functions should accept and pass `context.Context`.
  The driver extensively uses contextual logging via `klog.FromContext(ctx)`.
- **Interface segregation**: Interfaces are defined in dedicated `interface.go`
  files. Mock generation uses `//go:generate` directives. New interfaces should
  follow this pattern.
- **No `init()` functions**: The linter enforces `gochecknoinits`. Use explicit
  initialization.

### Testing

- **Unit test coverage**: New logic must have tests. The project uses Ginkgo v2
  + Gomega exclusively — do not introduce `testing.T`-only tests.
- **Tests in the same commit**: Unit tests belong in the same commit as the code
  they test. Do not defer tests to a follow-up PR.
- **Mock usage**: Tests should use the `mockgen`-generated mocks from `mock/`
  directories. If a new interface needs mocking, add a `//go:generate` directive
  and run `make mock-generate`.
- **envtest dependency**: Controller and API tests require envtest. Verify that
  new tests set up the envtest environment correctly (suite files should import
  envtest).
- **Coverage exclusions**: `_mock.go` files are excluded from coverage reports.
  Do not count mock-heavy packages as "well-tested" without checking real
  coverage.

### Container and Deployment

- **Dockerfile changes**: The runtime image is CentOS 9 Stream with `hwdata`,
  `pciutils`, and `delve`. Verify that new runtime dependencies are added to
  the `yum install` line.
- **Helm chart**: Changes to CRD types must be reflected in generated CRD
  manifests under `deployments/helm/`. Verify that `values.yaml` defaults are
  sensible.
- **Multi-arch support**: The release workflow builds for `linux/amd64`,
  `linux/arm64`, `linux/s390x`, `linux/ppc64le`. Verify that new code does
  not introduce platform-specific assumptions.

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Missing codegen | `zz_generated.deepcopy.go` not updated after type change |
| Stale CRD manifests | `deployments/helm/` CRD YAML does not match updated types |
| Missing boilerplate | New file lacks Apache 2.0 header |
| Hand-edited generated file | Changes in `zz_generated.*` or `mock/` not matching codegen |
| Missing mode guard | STANDALONE-only code runs in MULTUS mode |
| Attribute prefix mismatch | Using driver prefix where Multus prefix is needed (or vice versa) |
| Missing envtest setup | New test file lacks suite bootstrap or envtest configuration |
| Unstructured logging | Uses `fmt.Printf`, `log.Printf`, or `klog.Infof` instead of `klog.FromContext(ctx).Info(...)` |
| Missing test | New behavior has no Ginkgo test |
| Swallowed error | Error returned from function call is not checked or wrapped |
| Stale checkpoint state | Prepare/unprepare does not update checkpoint correctly |
| Missing cleanup in unprepare | VF driver binding not restored, CDI spec not removed |
| Incomplete filter handling | New resource filter field not wired in controller matching logic |
| Leaked VF allocation | Device allocated but not tracked in state manager |
| Build target confusion | Used root Makefile for container build instead of `deployments/container/Makefile` |
| Missing mock regeneration | New interface method not reflected in mock files |
| Banned import used | `logrus` or other denied package imported |

---

## PR Checklist (Reviewer Perspective)

1. Does `make all` pass? (check + test + build)
2. Are generated files regenerated via `make generate`, not hand-edited?
3. Do CRD manifest changes match the API type changes?
4. Are new API fields backward-compatible (zero-value safe)?
5. Are there adequate Ginkgo tests for new logic?
6. Are unit tests in the same commit as the code they test?
7. Is logging done via `klog.FromContext(ctx)` with structured methods?
8. Are errors wrapped with context (`fmt.Errorf("...: %w", err)`)?
9. Is `ConfigurationMode` checked for mode-specific code paths?
10. Are device attribute prefixes correct (driver vs. Multus)?
11. Does prepare/unprepare correctly update checkpoint state?
12. Are there no unrelated changes mixed into the PR?
13. Does the commit message follow the expected format (summary + explanation)?
14. Are new source files covered by Apache 2.0 boilerplate?
15. Is the Helm chart updated if CRD types changed?

---

## Commit Structure

### Expected format

```
Change summary

More detailed explanation of your changes: Why and how.
Wrap it to 72 characters.

[Fixes #NUMBER (or URL to the issue)]
```

### Conventions

- **Branch naming**: Use `dev/` prefix for feature branches
  (`dev/some-topic-branch`).
- **Self-contained commits**: Each commit should be self-contained — code
  changes and their corresponding tests belong in the same commit.
- **Generated code in separate commits**: `zz_generated.*` and CRD manifest
  changes can go in a separate codegen commit for review clarity.
- **Small, focused PRs**: Keep PRs focused on a single change. Large omnibus
  changes are harder to review and more likely to receive pushback.
- **Issue references**: Every PR should reference the GitHub issue it addresses.
  Create an issue first if one doesn't exist.

---

## Reviewer Preferences

- **Small, focused PRs** are preferred over large changes.
- **Separate codegen commits** from manual code changes (makes review easier).
- **Test alongside code** — reviewers will send back PRs that defer tests.
- **Run `make all`** before pushing — don't rely on CI to catch basic issues.
- **Explain mode-specific changes** — clearly document whether code affects
  STANDALONE, MULTUS, or both modes.
- **Update demo/ examples** when changing user-facing behavior (VfConfig
  parameters, resource claim templates, etc.).
- **Test with both configuration modes** when making driver lifecycle changes.
