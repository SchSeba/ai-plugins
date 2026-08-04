# SR-IOV Network Operator — Validation

Pre-push verification, code generation, and test commands for the
`k8snetworkplumbingwg/sriov-network-operator` repository. All commands **must be
run from the repository root**.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Full build (generate + lint + build) | `make all` |
| Build all binaries | `make build` |
| Lint | `make lint` |
| Format (containerized) | `make fmt` |
| Format (local) | `make fmt-code` |
| Generate deepcopy + apply configs | `make generate` |
| Generate CRD manifests | `make manifests` |
| Verify CRD manifests up to date | `make check-manifests` |
| Verify go modules up to date | `make check-deps` |
| Update go modules | `make deps-update` |
| Generate mocks | `make mock-generate` |
| Unit tests (specific package) | `CLUSTER_TYPE=kubernetes make test-<dir>` / `CLUSTER_TYPE=openshift make test-<dir>` |
| E2E conformance (virtual K8s) | `make test-e2e-conformance-virtual-k8s-cluster-ci` |
| E2E conformance (virtual OCP) | `make test-e2e-conformance-virtual-ocp-cluster-ci` |
| Test bindata scripts | `make test-bindata-scripts` |

---

## Build Targets

### `make all`

Runs `generate` → `lint` → `build`. This is the primary "does everything
compile and pass lint?" check.

### `make build`

Builds all four binaries:

| Binary | Source | Build command |
|--------|--------|---------------|
| `manager` | `main.go` | `make manager` |
| `sriov-network-config-daemon` | `cmd/sriov-network-config-daemon/` | `make _build-sriov-network-config-daemon` |
| `webhook` | `cmd/webhook/` | `make _build-webhook` |
| `sriov-network-operator-config-cleanup` | `cmd/sriov-network-operator-config-cleanup/` | `make _build-sriov-network-operator-config-cleanup` |

Binaries are built with `CGO_ENABLED=0` and include version information via
`-ldflags` from `hack/build-go.sh`.

### `make image`

Builds all three container images using the configured `IMAGE_BUILDER` (default:
`docker`):

| Image | Dockerfile | Base |
|-------|-----------|------|
| Operator | `Dockerfile` | `quay.io/centos/centos:stream9` |
| Config Daemon | `Dockerfile.sriov-network-config-daemon` | `quay.io/centos/centos:stream9` |
| Webhook | `Dockerfile.webhook` | `quay.io/centos/centos:stream9` |

Override the builder: `IMAGE_BUILDER=podman make image`.

---

## Code Generation

### `make generate`

Runs `controller-gen` to regenerate:
- `zz_generated.deepcopy.go` in `api/v1/`
- Apply configuration types in `api/v1/applyconfiguration/`

Uses `controller-gen` with the boilerplate header from
`hack/boilerplate.go.txt`.

### `make manifests`

Runs `controller-gen` to regenerate CRD and webhook YAML in `config/crd/bases/`,
then copies CRDs to `deployment/sriov-network-operator-chart/crds/`.

### `make check-manifests`

Verifies that the `config/` folder is up to date by running `make manifests`
and checking for a clean `git diff`. **CI runs this check.**

### `make mock-generate`

Runs `go generate ./...` using `uber/mock/mockgen` to regenerate mock
implementations. Run this after modifying interfaces that have associated mocks.

---

## Formatting

### `make fmt`

Runs `gofmt -s` inside a container via `hack/go-fmt.sh`, then checks for a
clean `git diff`. This is used in CI. Requires `IMAGE_BUILDER` (docker/podman).

To run locally in CI mode (without the container): `IS_CONTAINER=yes make fmt`

### `make fmt-code`

Runs `go fmt ./...` directly on the host. Use this for quick local formatting.

---

## Linting

### `make lint`

Runs `golangci-lint` with a 10-minute timeout. The linter configuration
is in `.golangci.yml` (v2 format). The version is pinned in the `Makefile`.

**Enabled linters include**: asciicheck, bidichk, bodyclose, copyloopvar,
depguard, dogsled, errname, exhaustive, gocheckcompilerdirectives, goconst,
goprintffuncname, staticcheck, ineffassign, makezero, misspell, reassign,
unconvert, unused, whitespace.

**Enabled formatters**: gofmt, goimports (with local prefix for project imports).

**Excluded paths**: `vendor/`, `.github/`, `deployment/`, `doc/`, `bindata/`,
`pkg/client`.

**Test file exclusions**: mnd, gosec, dupl, lll, goconst are relaxed in
`_test.go` files.

---

## Dependency Management

### `make deps-update`

Runs `go mod tidy`. The project uses Go modules without vendoring.

### `make check-deps`

Runs `make deps-update` then verifies `go.mod` and `go.sum` are unchanged via
`git diff`. **CI runs this check.**

---

## Testing

### Unit Tests

Unit tests use Ginkgo v2 + Gomega and require the `CLUSTER_TYPE` environment
variable. The `test-%` Makefile pattern runs tests for any subdirectory:

```bash
# Test the pkg/ directory
CLUSTER_TYPE=kubernetes make test-pkg
CLUSTER_TYPE=openshift make test-pkg

# Test controllers
CLUSTER_TYPE=kubernetes make test-controllers
CLUSTER_TYPE=openshift make test-controllers

# Test cmd/
CLUSTER_TYPE=kubernetes make test-cmd
CLUSTER_TYPE=openshift make test-cmd

# Test api/
CLUSTER_TYPE=kubernetes make test-api
CLUSTER_TYPE=openshift make test-api
```

The `test-%` pattern automatically:
- Sets up `envtest` (KUBEBUILDER_ASSETS)
- Excludes `/mock` and `/pkg/client` directories
- Generates a per-package coverage profile: `cover-<pkg>-<cluster-type>.out`

### Full Test Suite (as CI runs it)

```bash
# All unit tests for both platforms
CLUSTER_TYPE=kubernetes make test-pkg
CLUSTER_TYPE=openshift make test-pkg
CLUSTER_TYPE=kubernetes make test-cmd
CLUSTER_TYPE=openshift make test-cmd
CLUSTER_TYPE=kubernetes make test-api
CLUSTER_TYPE=openshift make test-api
CLUSTER_TYPE=kubernetes make test-controllers
CLUSTER_TYPE=openshift make test-controllers

# Bindata script tests
make test-bindata-scripts
```

### Test Coverage

```bash
# Run all unit tests (generates cover-*.out files), then merge
make merge-test-coverage
# Output: cover.out (merged), lcov.out (LCOV format for Coveralls)
```

### Shell Script Tests

```bash
make test-bindata-scripts
```

Requires `fakechroot`. Tests shell scripts embedded in `bindata/scripts/` via
`test/scripts/kargs_test.sh`.

### E2E / Conformance Tests

E2E tests require SR-IOV-capable hardware and a running cluster:

| Target | Environment |
|--------|-------------|
| `make test-e2e-conformance-virtual-k8s-cluster-ci` | Virtual K8s cluster (CI, auto-cleanup) |
| `make test-e2e-conformance-virtual-k8s-cluster` | Virtual K8s cluster (SKIP_DELETE=TRUE, keeps cluster) |
| `make test-e2e-conformance-virtual-ocp-cluster-ci` | Virtual OCP cluster (CI, auto-cleanup) |
| `make test-e2e-conformance-virtual-ocp-cluster` | Virtual OCP cluster (SKIP_DELETE=TRUE, keeps cluster) |
| `make test-e2e-conformance` | Conformance suite on existing cluster |
| `make test-e2e-validation-only` | Validation-only suite on existing cluster |

E2E tests run on self-hosted runners with `sriov` or `ocp` labels and are
frequently subject to infrastructure flakiness.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLUSTER_TYPE` | (none) | **Required for tests**: `kubernetes` or `openshift` |
| `IMAGE_BUILDER` | `docker` | Container runtime for image builds (`docker` or `podman`) |
| `OPERATOR_EXEC` | `oc` | CLI tool for cluster operations (`kubectl` or `oc`) |
| `NAMESPACE` | `openshift-sriov-network-operator` | Target namespace for deployment |
| `TESTPKGS` | `./...` | Override test package scope |
| `GOFLAGS` | (empty) | Extra Go build flags |
| `CGO_ENABLED` | `0` | CGO setting (disabled by default for static binaries) |

---

## CI Pipeline Jobs (`.github/workflows/test.yml`)

| Job | What it checks |
|-----|----------------|
| `build` | `IS_CONTAINER=yes make fmt` → `make all` (generate + lint + build) |
| `test` | Unit tests for pkg, cmd, api, controllers (both K8s and OpenShift) + bindata scripts |
| `modules` | `make check-deps` (go.mod/go.sum are up to date) |
| `manifests` | `make check-manifests` (config/ folder is up to date) |
| `golangci` | `make lint` |
| `shellcheck` | ShellCheck on all shell scripts (severity: error) |
| `hadolint` | Dockerfile linting on all three Dockerfiles |
| `test-coverage` | Same as `test` + coverage merge + Coveralls upload |
| `virtual-k8s-cluster` | E2E on self-hosted sriov runners (depends on build, test, golangci) |
| `virtual-ocp` | E2E on self-hosted ocp runners (depends on build, test, golangci) |

---

## Recommended Pre-Push Sequences

### Minimal (any code change)

```bash
make fmt-code
make lint
CLUSTER_TYPE=kubernetes make test-<changed-package>
```

### After API type changes

```bash
# 1. Regenerate
make generate
make manifests

# 2. Verify
make check-manifests
make lint

# 3. Test
CLUSTER_TYPE=kubernetes make test-api
CLUSTER_TYPE=kubernetes make test-controllers
CLUSTER_TYPE=openshift make test-controllers
```

### After interface changes (mocks)

```bash
make mock-generate
make lint
CLUSTER_TYPE=kubernetes make test-pkg
```

### Full (before submitting a PR)

```bash
make all                    # generate + lint + build
make check-manifests        # CRD manifests up to date
make check-deps             # go.mod/go.sum up to date

# Unit tests (both platforms)
CLUSTER_TYPE=kubernetes make test-pkg
CLUSTER_TYPE=openshift make test-pkg
CLUSTER_TYPE=kubernetes make test-cmd
CLUSTER_TYPE=openshift make test-cmd
CLUSTER_TYPE=kubernetes make test-api
CLUSTER_TYPE=openshift make test-api
CLUSTER_TYPE=kubernetes make test-controllers
CLUSTER_TYPE=openshift make test-controllers

# Script tests
make test-bindata-scripts
```

---

## Important Notes

- `make check-manifests` expects a **clean git status** for the `config/`
  directory. Run `make manifests` first if it fails.
- Unit tests require `envtest` which downloads etcd + apiserver binaries to
  `/tmp` on first run. This may take time on initial setup.
- The `fmt` target runs inside a container — use `fmt-code` for faster local
  formatting, or prefix with `IS_CONTAINER=yes` to run locally in CI mode.
- E2E tests on `sriov` runners are frequently flaky due to hardware and
  infrastructure issues — these are not indicative of code problems.
- There is **no vendor directory** — the project uses Go modules directly.
