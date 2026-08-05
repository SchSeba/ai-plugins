# dra-driver-sriov — Coding

Coding conventions, architecture patterns, and common pitfalls for contributing
to the `k8snetworkplumbingwg/dra-driver-sriov` repository.

---

## Repository Layout

| Directory | Purpose |
|-----------|---------|
| `cmd/dra-driver-sriov/` | Main binary entry point — sets up flags, logging, controller, device state, NRI, and the DRA kubelet plugin |
| `pkg/driver/` | Core DRA kubelet plugin implementation — gRPC lifecycle (PrepareResourceClaims, UnprepareResourceClaims), resource publishing via ResourceSlices |
| `pkg/controller/` | Kubernetes controller for `SriovResourcePolicy` CRD — watches policies and drives device advertisement |
| `pkg/devicestate/` | Device state management — VF discovery from sysfs/PCI, device info, allocation tracking, prepare/unprepare logic |
| `pkg/api/sriovdra/v1alpha1/` | CRD types for `SriovResourcePolicy` and `DeviceAttributes` |
| `pkg/api/virtualfunction/v1alpha1/` | CRD types for `VfConfig` (per-claim VF configuration) |
| `pkg/cdi/` | Container Device Interface (CDI) spec generation for VFs |
| `pkg/cni/` | CNI plugin integration — invokes SR-IOV CNI for network configuration |
| `pkg/nri/` | Node Resource Interface (NRI) plugin — handles pod sandbox events for STANDALONE mode |
| `pkg/podmanager/` | Pod lifecycle management — tracks prepared devices per pod/claim |
| `pkg/host/` | Host system interaction — sysfs reading, netlink operations, RDMA, driver binding, VF configuration |
| `pkg/types/` | Shared type definitions — `PreparedDevice`, `Checkpoint`, `Config` |
| `pkg/consts/` | Constants — driver name, attribute keys, device classes, link types |
| `pkg/flags/` | Command-line flag handling and logging configuration |
| `deployments/container/` | Container image build — Dockerfile and Makefile for CentOS 9 Stream base image |
| `deployments/helm/` | Helm chart for Kubernetes deployment |
| `docker/` | Development container image (`Dockerfile.devel`) with build tools |
| `hack/` | Build scripts, boilerplate templates, virtual cluster deployment scripts |
| `demo/` | Example workload configurations (single VF, multiple VFs, VFIO, Multus integration) |
| `common.mk` | Shared Makefile variables — Go version, tool versions, module path, API definitions |

---

## API Types (CRDs)

### Where types live

- **SriovResourcePolicy / DeviceAttributes**: `pkg/api/sriovdra/v1alpha1/api.go`
- **VfConfig**: `pkg/api/virtualfunction/v1alpha1/api.go`
- **Generated deepcopy**: `pkg/api/*/v1alpha1/zz_generated.deepcopy.go`
- **CRD manifests**: generated into `deployments/helm/dra-driver-sriov/templates/`

### API change workflow

1. Edit types in `pkg/api/sriovdra/v1alpha1/` or `pkg/api/virtualfunction/v1alpha1/`.
2. Run `make generate` to regenerate deepcopy functions and CRD manifests.
3. Run `make fmt` to format generated code.
4. Run `make lint` and `make test` to verify.

### Key CRD concepts

- **SriovResourcePolicy** — opt-in model for device advertisement. Defines
  `resourceFilters` (vendor, device, PF name, PCI address, driver, link type)
  and `deviceAttributesSelector` (label selector matching `DeviceAttributes`
  objects).
- **DeviceAttributes** — decoupled attribute definitions applied to
  policy-matched devices via label selectors.
- **VfConfig** — per-claim configuration parameters (driver mode, ifName,
  NetworkAttachmentDefinition reference, vhost mount).

---

## Code Generation

The project uses `controller-gen` for CRD and deepcopy generation, and
`mockgen` (go.uber.org/mock) for mock generation.

| Generator | Command | Output |
|-----------|---------|--------|
| `controller-gen object` | `make generate-deepcopy` | `zz_generated.deepcopy.go` in each API package |
| `controller-gen crd` | `make generate-crds` | CRD YAML manifests in `deployments/helm/` |
| `mockgen` | `make mock-generate` | Mock files in `pkg/*/mock/` directories |
| All generators | `make generate` | Runs deepcopy + CRDs + mocks |

**Never hand-edit generated files.** Files prefixed with `zz_generated.` or
in `mock/` directories are auto-generated.

Mock generation uses `//go:generate` directives in source files:
- `pkg/host/host.go` → `pkg/host/mock/mock_host.go`
- `pkg/cni/interface.go` → `pkg/cni/mock/mock_cni.go`
- `pkg/devicestate/interface.go` → `pkg/devicestate/mock/mock_devicestate.go`
- `pkg/devicestate/interface.go` → `pkg/devicestate/mock/mock_deviceinfostore.go`
- `pkg/host/rdma_provider.go` → `pkg/host/mock/mock_rdma_provider.go`

---

## Coding Conventions

### Logging

The project uses **klog v2** with contextual logging:

```go
klog.FromContext(ctx).Info("message", "key", value)
klog.FromContext(ctx).Error(err, "message", "key", value)
```

- Always use `klog.FromContext(ctx)` — pass `context.Context` through the call
  chain.
- Do **not** use `fmt.Printf`, `log.Printf`, or `klog.Infof` for runtime
  logging.
- The logging subsystem is configured via `k8s.io/component-base/logs` with
  JSON output support and contextual logging enabled by default.

### Error handling

- Wrap errors with context using `fmt.Errorf("...: %w", err)`.
- The `consts.Backoff` variable defines a standard exponential backoff
  (100ms initial, 2x factor, 5 steps, 2s cap) — use it for retryable
  operations.
- Do not swallow errors silently.

### Import conventions

Import ordering enforced by `goimports` via `.golangci.yml`:

1. Standard library
2. External packages
3. `k8s.io/` packages
4. Project-local packages (`github.com/k8snetworkplumbingwg/dra-driver-sriov/...`)

The `.golangci.yml` configures `goimports` with local prefix
`github.com/k8snetworkplumbingwg/dra-driver-sriov`.

### Naming conventions

- Package-level import aliases follow Kubernetes conventions:
  - `resourceapi` for `k8s.io/api/resource/v1`
  - `k8stypes` for `k8s.io/apimachinery/pkg/types`
  - `configapi` for internal API packages
  - `sriovdratype` for `pkg/types`
- Constants use `CamelCase` with descriptive prefixes (e.g., `AttributePciAddress`,
  `ConfigurationModeStandalone`).
- Interfaces are defined in dedicated `interface.go` files within each package.

### Boilerplate

Every source file must start with the Apache 2.0 license boilerplate.
The template is in `hack/boilerplate.go.txt` and
`hack/boilerplate.generatego.txt` (for generated files).

---

## DRA Driver Patterns

### Architecture

The driver operates as a DRA kubelet plugin with these core components:

1. **Kubelet Plugin** (`pkg/driver/`) — Implements `PrepareResourceClaims` and
   `UnprepareResourceClaims` gRPC methods. Publishes device resources via
   `ResourceSlice` API.
2. **Resource Policy Controller** (`pkg/controller/`) — Watches
   `SriovResourcePolicy` CRDs and computes which devices should be advertised
   based on filtering criteria.
3. **Device State Manager** (`pkg/devicestate/`) — Discovers VFs from sysfs,
   tracks allocation state, handles prepare/unprepare operations.
4. **NRI Plugin** (`pkg/nri/`) — Only active in STANDALONE mode. Intercepts pod
   sandbox events to trigger CNI attach/detach.

### Configuration modes

- **STANDALONE**: NRI plugin active, driver handles CNI attach/detach, supports
  KEP-5304 device metadata.
- **MULTUS**: NRI plugin disabled, relies on Multus for network attachment,
  passes device attributes (`resourceName`, `deviceID`) for Multus consumption.

### Resource claim handling flow

1. `PrepareResourceClaims` receives claims with `ReservedFor` entries.
2. For each claim, the driver parses `OpaqueDeviceConfig` for `VfConfig`.
3. The device state manager allocates VFs and applies configuration (driver
   binding, interface naming).
4. CDI specs are generated for device injection.
5. In STANDALONE mode, CNI attach happens via NRI pod sandbox events.

### Checkpoint pattern

The driver uses a checkpoint file (`checkpoint.json`) to persist prepared device
state across restarts. The `Checkpoint` type in `pkg/types/` implements
marshaling with checksum verification.

---

## Testing Patterns

### Framework

All tests use **Ginkgo v2** + **Gomega** with dot imports:

```go
import (
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)
```

Each package has a suite bootstrap file (`*_suite_test.go`) that registers
the Ginkgo test runner:

```go
func TestPackageName(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Package Suite")
}
```

### Unit tests

- Tests live alongside the code in `*_test.go` files (same package).
- Use `Describe`/`Context`/`It` blocks for BDD-style organization.
- Use `GinkgoT().TempDir()` for temporary directories.
- Mock interfaces using `go.uber.org/mock/mockgen`-generated mocks.

### Test coverage

Tests require **envtest** (controller-runtime) for Kubernetes API interaction:

```bash
# envtest downloads K8s binaries automatically
KUBEBUILDER_ASSETS=$$(setup-envtest use 1.36.x ...) go test ...
```

The `make test` target handles envtest setup automatically.

### Controller tests

Controller tests (`pkg/controller/`) use `envtest` to spin up a real API server
and test the controller reconciliation loop against actual CRDs.

---

## Common Pitfalls

1. **Forgetting to run `make generate`** — Any change to API types in `pkg/api/`
   requires regenerating deepcopy and CRD manifests. CI will catch this with the
   `generate-and-format` check.
2. **Editing generated files** — Files prefixed with `zz_generated.` and files
   in `mock/` directories are auto-generated. Edit the source and re-run
   `make generate` or `make mock-generate`.
3. **Missing envtest setup** — Unit tests that touch Kubernetes APIs need
   envtest assets. The `make test` target handles this, but running `go test`
   directly will fail without `KUBEBUILDER_ASSETS` set.
4. **Configuration mode assumptions** — Code that only works in STANDALONE mode
   (e.g., NRI interactions) must check `ConfigurationMode` before executing.
   MULTUS mode skips NRI and standalone-specific network preparation.
5. **Device attribute prefix mismatch** — Multus attributes use the
   `k8s.cni.cncf.io` prefix, driver-specific attributes use
   `sriovnetwork.k8snetworkplumbingwg.io`. Mixing these up breaks Multus
   integration.
6. **Missing boilerplate** — New files without the Apache 2.0 license header
   will fail CI format checks.
7. **Docker build targets** — Container images are built from
   `deployments/container/Makefile`, not the root Makefile. Use
   `make -f deployments/container/Makefile centos9`.
8. **Containerized builds** — The root Makefile supports `docker-*` targets
   (e.g., `make docker-test`) that run inside a development container built
   from `docker/Dockerfile.devel`.
