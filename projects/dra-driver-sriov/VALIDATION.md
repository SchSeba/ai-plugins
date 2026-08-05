# dra-driver-sriov — Validation

Pre-push verification, code generation, and test commands for the
`k8snetworkplumbingwg/dra-driver-sriov` repository. All commands are run from
the repository root.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Format code | `make fmt` |
| Check formatting | `make assert-fmt` |
| Lint | `make lint` |
| Vet | `make vet` |
| Run all checks | `make check` (= `assert-fmt` + `vet` + `lint`) |
| Unit tests | `make test` |
| Tests with coverage | `make test-coverage` |
| Coverage report | `make coverage` |
| Build all binaries | `make cmds` (or `make binaries` or `make build`) |
| All (check + test + build) | `make all` |
| Generate all (deepcopy + CRDs + mocks) | `make generate` |
| Generate deepcopy only | `make generate-deepcopy` |
| Generate CRDs only | `make generate-crds` |
| Generate mocks only | `make mock-generate` |
| Update vendored deps | `make vendor` |
| Build container image | `make -f deployments/container/Makefile centos9` |

---

## Formatting and Linting

### Code formatting

```bash
# Apply gofmt -s to all Go files
make fmt

# Check formatting without modifying files (exits non-zero if issues found)
make assert-fmt
```

### Linting

```bash
make lint
```

The linter is configured via `.golangci.yml` (v2 format) with these key
settings:

- **Enabled linters**: errcheck, govet, staticcheck, gosec, gocritic,
  ineffassign, unused, unparam, bodyclose, errname, exhaustive,
  gochecknoinits, goconst, misspell, and more.
- **Excluded paths**: `vendor/`, `.cache/`, `.config/`
- **Excluded files**: `*_mock.go` and `zz_generated.*.go` (all linters skipped)
- **Test exclusions**: gosec, dupl, goconst skipped in `_test.go` files
- **Import ordering**: `goimports` with local prefix
  `github.com/k8snetworkplumbingwg/dra-driver-sriov`
- **Denied packages**: `github.com/sirupsen/logrus` (use klog instead)

### Vet

```bash
make vet
```

Runs `go vet` across all packages.

### Combined check

```bash
# Runs: assert-fmt + vet + lint
make check
```

---

## Testing

### Unit tests

```bash
# Run all unit tests with coverage
make test
```

This command:
1. Downloads envtest K8s API server binaries (version `1.36.x`) via
   `setup-envtest` from `sigs.k8s.io/controller-runtime/tools/setup-envtest`.
2. Sets `KUBEBUILDER_ASSETS` to point to the downloaded binaries.
3. Runs `go test -v -coverprofile=coverage.out ./...`.

**Important**: Do **not** run `go test ./...` directly — tests require the
envtest binaries for controller and API tests. Always use `make test`.

### Coverage

```bash
# Test with atomic coverage mode
make test-coverage

# Test + print coverage report (excludes mock files)
make coverage
```

The `coverage` target filters out `_mock.go` files from the coverage report
to give accurate coverage numbers for real code.

### Running specific tests

To run tests for a specific package:

```bash
# Set envtest assets first
export KUBEBUILDER_ASSETS=$(go run sigs.k8s.io/controller-runtime/tools/setup-envtest@release-0.20 use 1.36.x --bin-dir=./bin/envtest -p path)

# Then run the specific package
go test -v ./pkg/devicestate/...
go test -v ./pkg/driver/...
```

---

## Code Generation

### Full generation

```bash
# Generate deepcopy + CRDs + mocks
make generate
```

### Deepcopy generation

```bash
make generate-deepcopy
```

Uses `controller-gen` (version `v0.20.0`) to generate `zz_generated.deepcopy.go`
for both API packages:
- `pkg/api/virtualfunction/v1alpha1/`
- `pkg/api/sriovdra/v1alpha1/`

### CRD generation

```bash
make generate-crds
```

Generates CRD YAML manifests into `deployments/helm/dra-driver-sriov/templates/`
(only for the `sriovdra/v1alpha1` API).

### Mock generation

```bash
make mock-generate
```

Installs `mockgen` (go.uber.org/mock `v0.6.0`) and runs `go generate ./...`
across the project. Mock files are placed in `mock/` subdirectories of each
package.

---

## Building

### Binaries

```bash
# Build all binaries (dra-driver-sriov)
make cmds

# Build for specific platform
GOOS=linux GOARCH=arm64 make cmds

# Build to a specific output directory
PREFIX=/tmp/output make cmds

# Build all packages without producing binaries (compile check)
make build
```

Binaries are built with:
- `CGO_LDFLAGS_ALLOW='-Wl,--unresolved-symbols=ignore-in-object-files'`
- `-ldflags "-s -w -X main.version=$(VERSION)"`

### Container image

```bash
# Build CentOS 9 Stream-based container image
make -f deployments/container/Makefile centos9

# Override image name and tool
CONTAINER_TOOL=podman IMAGE_NAME=localhost/dra-driver-sriov VERSION=latest \
  make -f deployments/container/Makefile centos9
```

The Dockerfile is at `deployments/container/Dockerfile`:
- **Builder stage**: `golang:<GOLANG_VERSION>` — compiles the binary.
- **Runtime stage**: CentOS 9 Stream — includes `hwdata`, `pciutils`.

---

## Helm Chart

### Prepare chart

```bash
VERSION=v1.0.0 GITHUB_TOKEN=<token> GITHUB_REPO_OWNER=<owner> make chart-prepare
```

Requires the `yq` binary (auto-installed to `bin/yq` from v4.50.1 release).

### Push chart

```bash
VERSION=v1.0.0 GITHUB_TOKEN=<token> GITHUB_REPO_OWNER=<owner> make chart-push
```

### Install chart locally

```bash
helm upgrade -i dra-driver-sriov --create-namespace -n dra-driver-sriov \
  ./deployments/helm/dra-driver-sriov/
```

---

## E2E Tests and Virtual Clusters

### Full E2E (requires SR-IOV hardware)

```bash
make e2e-tests
```

Deploys a virtual K8s cluster using kcli, installs the DRA driver via Helm, and
runs E2E tests. **Requires SR-IOV hardware** (runs on `[sriov]`-labeled CI
runners).

### Single-node virtual cluster E2E

```bash
make ci-single-node-e2e
```

Deploys a single-node virtual cluster for CI testing. This is used in the
`virtual-e2e.yaml` workflow and runs on standard GitHub Actions runners.

### Manual virtual cluster management

```bash
# Deploy cluster (keep after completion)
SKIP_DELETE=TRUE make deploy-virtual-k8s-cluster

# Deploy single-node cluster (keep after completion)
SKIP_DELETE=TRUE make deploy-single-node-virtual-cluster

# Delete cluster
make delete-virtual-k8s-cluster

# Redeploy driver on existing cluster
make redeploy-dra-driver-virtual-cluster
```

---

## Tool Versions

All tool versions are defined in `common.mk`:

| Tool | Version | Variable |
|------|---------|----------|
| Go | 1.26 | `GOLANG_VERSION` |
| golangci-lint | v2.7.2 | `GOLANGCI_LINT_VERSION` |
| controller-gen | v0.20.0 | `CONTROLLER_GEN_VERSION` |
| mockgen | v0.6.0 | `MOCKGEN_VERSION` |
| moq | v0.4.0 | `MOQ_VERSION` |
| client-gen | v0.29.2 | `CLIENT_GEN_VERSION` |
| yq | v4.50.1 | `YQ_VERSION` (in Makefile) |
| envtest K8s | 1.36.x | `ENVTEST_K8S_VERSION` (in Makefile) |

---

## CI Pipeline

### Workflows

| Workflow | File | Triggers | What it does |
|----------|------|----------|--------------|
| CI | `ci.yaml` | PR / push to main | generate-and-format, lint, test, build-container, functional-tests |
| Virtual E2E | `virtual-e2e.yaml` | PR / push to main | Single-node virtual cluster E2E test |
| Release | `release.yaml` | push to main / tags | Multi-arch container build + push to GHCR |
| Chart Push | `chart-push.yml` | push to main / tags | Package and push Helm chart |

### CI job details (`ci.yaml`)

1. **generate-and-format** — Runs `make generate` + `make fmt` and checks for
   uncommitted changes (verifies codegen is up-to-date).
2. **lint** — Runs `make lint` (golangci-lint v2.7.2).
3. **test** — Runs `make test-coverage` + uploads coverage to Coveralls.
4. **build-container** — Builds container image (PR only, not on push to main).
5. **functional-tests** — Runs `make e2e-tests` on `[sriov]` self-hosted
   runners. Depends on all other jobs passing.

---

## Recommended Pre-Push Sequences

### Minimal (any change)

```bash
make check           # assert-fmt + vet + lint
make test            # unit tests with envtest
```

### API / generated-code changes

```bash
# 1. Regenerate
make generate        # deepcopy + CRDs + mocks

# 2. Format
make fmt

# 3. Verify
make check           # assert-fmt + vet + lint

# 4. Test
make test
```

### Full (before submitting a PR)

```bash
make all             # check + test + build
```

---

## Important Notes

- **envtest is required** — Tests will fail without `KUBEBUILDER_ASSETS`. Always
  use `make test` or set up envtest manually before running `go test`.
- The `generate-and-format` CI check verifies that `make generate && make fmt`
  produces no diff — always run these before pushing.
- Container images are **not built from the root Makefile**. Use
  `make -f deployments/container/Makefile centos9`.
- **Go version** is pinned in `common.mk` (`GOLANG_VERSION ?= 1.26`). CI uses
  `GO_VERSION: "1.26.x"` in workflow env vars.
