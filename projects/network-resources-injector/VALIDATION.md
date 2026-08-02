# Network Resources Injector — Validation

Pre-push verification, build, lint, and test commands for the
`k8snetworkplumbingwg/network-resources-injector` repository. All commands
**must be run from the repository root**.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Build binaries | `make` (default target) or `scripts/build.sh` |
| Lint | `make lint` |
| Unit tests | `make test` or `scripts/test.sh` |
| Build Docker image | `make image` or `scripts/build-image.sh` |
| E2E tests | `make e2e` |
| E2E cleanup | `make e2e-clean` |
| Update dependencies | `make deps-update` |
| Vendor dependencies | `make vendor` |

---

## Build

### Default Build (`make`)

Runs `scripts/build.sh`, which builds two binaries into `bin/`:

```bash
make
```

The build script sets:
- `CGO_ENABLED=0` — static binaries, no C dependencies.
- `-ldflags "-s -w"` — stripped symbols for smaller binaries.
- `-tags no_openssl` — avoids OpenSSL/CGO linking from the cfssl dependency.

**Output binaries:**
- `bin/webhook` — the main admission webhook server.
- `bin/installer` — the webhook configuration installer.

### Docker Image (`make image`)

Builds a multi-stage Docker image:

```bash
make image
```

- **Builder stage**: `golang:<version>-alpine` with `build-base` and `bash`.
- **Runtime stage**: `alpine:<version>`, runs as `USER 1001` (non-root).
- Copies `bin/webhook` and `bin/installer` to `/usr/bin/`.
- Default `CMD`: `["webhook"]`.

The `CONTAINER_ENGINE` environment variable controls the container runtime
(defaults to `docker`):

```bash
CONTAINER_ENGINE=podman make image
```

---

## Linting

### golangci-lint (`make lint`)

```bash
make lint
```

- Uses golangci-lint **v2** (version controlled via `GOLANGCI_LINT_VER` in the
  Makefile, currently `v2.7.2`).
- Auto-installs to `bin/golangci-lint` on first run.
- Configuration in `.golangci.yml` (v2 format).
- Default timeout: `10m` (override with `GOLANGCI_LINT_TIMEOUT`).
- Cache directory: `build/.cache`.

**Key linters enabled:**

| Linter | Purpose |
|--------|---------|
| `govet` | Go vet checks |
| `staticcheck` | Comprehensive static analysis |
| `unused` | Unused code detection |
| `ineffassign` | Ineffectual assignments |
| `bodyclose` | HTTP response body close checks |
| `errname` | Error naming conventions |
| `misspell` | Spelling (US locale) |
| `goconst` | Repeated string constants |
| `depguard` | Blocks `github.com/sirupsen/logrus` |
| `asciicheck` | Non-ASCII identifier detection |
| `bidichk` | Dangerous unicode sequences |

**Formatters enforced:**
- `gofmt` — standard Go formatting.
- `goimports` — import grouping with local prefix
  `github.com/k8snetworkplumbingwg/network-resources-injector`.

**Exclusions:**
- `test/` directory paths are excluded from lint.
- Test files (`_test.go`) have relaxed rules for `errcheck`, `gosec`, `dupl`,
  `lll`, `goconst`, `funlen`.
- Generated code uses `lax` exclusion.

### Build Tag Awareness

The linter runs with build tags `unittests` (configured in `.golangci.yml`
under `run.build-tags`). This ensures lint covers test-only code paths.

---

## Testing

### Unit Tests (`make test`)

```bash
make test
```

Runs `scripts/test.sh`, which executes:

```bash
go test --tags=unittests -race -coverprofile="$filePath" "./pkg/..."
```

Key flags:
- `--tags=unittests` — required build tag for unit tests.
- `-race` — race detector enabled.
- `-coverprofile` — generates a coverage profile in `/tmp/go-cover.<timestamp>.tmp`.
- After tests, `go tool cover -html=...` opens coverage in a browser (can be
  ignored in CI).

**Scope**: Tests only `./pkg/...` (not `cmd/` or `test/`).

### E2E Tests (`make e2e`)

```bash
make e2e
```

This is a two-step process:
1. Sets up a KinD cluster with tools (`scripts/e2e_get_tools.sh` +
   `scripts/e2e_setup_cluster.sh`).
2. Runs E2E tests: `go test -timeout 40m -v ./test/e2e/...`

**Cleanup**: `make e2e-clean` tears down the cluster and removes artifacts.

**CI E2E** (`.github/workflows/e2e.yml`): Runs on `ubuntu-24.04` with a
60-minute timeout.

### SR-IOV Operator E2E Tests (CI only)

The `buildtest.yml` workflow includes an `sriov-operator-e2e-test` job that:
1. Builds an NRI container image.
2. Checks out the `sriov-network-operator` repo.
3. Runs the operator's E2E conformance tests against the locally built NRI
   image.

This runs on self-hosted `sriov` runners and is frequently flaky due to
hardware/infrastructure issues.

---

## CI Pipeline (`.github/workflows/`)

| Workflow | Triggers | Jobs |
|----------|----------|------|
| `buildtest.yml` | push, PR, daily cron | build + test, SR-IOV operator E2E |
| `e2e.yml` | PR | KinD-based E2E tests |
| `codeql.yml` | push to master, PR | CodeQL security analysis |
| `image-push-master.yml` | push to master | Publish container image |
| `image-push-release.yml` | release tags | Publish release container image |

### `buildtest.yml` Pipeline

```
Build (scripts/build.sh) → Unit Tests (scripts/test.sh)
                         ↓
              SR-IOV Operator E2E (needs: build)
```

---

## Dependency Management

### Update Dependencies

```bash
make deps-update    # runs: go mod tidy
```

### Vendor Dependencies

```bash
make vendor         # runs: go mod tidy && go mod vendor
```

**Note**: The repository does not track a `vendor/` directory in git. Vendoring
is optional for local builds.

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CONTAINER_ENGINE` | `docker` | Container runtime for `make image` (`docker` or `podman`) |
| `GOLANGCI_LINT_TIMEOUT` | `10m` | Override lint timeout |
| `GOLANGCI_LINT_CACHE` | `build/.cache` | Lint cache directory |
| `GOBIN` | `$PWD/bin` | Binary output directory (set by `scripts/build.sh`) |
| `CGO_ENABLED` | `0` | Disabled for static builds (set by `scripts/build.sh`) |

---

## Recommended Pre-Push Sequences

### Minimal (any change)

```bash
make lint
make test
make
```

This runs linting, unit tests, and builds the binaries. Covers the checks
enforced by the `buildtest.yml` CI pipeline.

### Full (before submitting a PR)

```bash
# 1. Lint
make lint

# 2. Unit tests
make test

# 3. Build
make

# 4. Build Docker image (validates Dockerfile)
make image

# 5. E2E tests (optional — requires KinD)
make e2e
make e2e-clean
```

### Dependency Changes

When modifying `go.mod`:

```bash
# 1. Tidy and verify
make deps-update

# 2. Lint + test + build
make lint
make test
make
```

---

## Important Notes

- **Build tags are mandatory**: Both the build (`no_openssl`) and tests
  (`unittests`) require specific build tags. Do not run `go build ./...` or
  `go test ./...` directly without them.
- **No `make all` target**: Unlike some sibling projects, NRI does not have a
  combined `make all`. Run `make lint`, `make test`, and `make` separately.
- **golangci-lint auto-installs**: The first `make lint` invocation downloads
  and installs golangci-lint to `bin/`. Subsequent runs use the cached binary.
- **Coverage HTML opens automatically**: `scripts/test.sh` runs
  `go tool cover -html=...` which may open a browser. This is harmless in CI
  (it fails silently) but expected locally.
- **Test scope is `./pkg/...` only**: Unit tests cover packages under `pkg/`.
  The `cmd/` directory and `test/e2e/` are not included in unit test runs.
