# SR-IOV Network Metrics Exporter — Validation

Pre-push verification, build, lint, and test commands for the
`k8snetworkplumbingwg/sriov-network-metrics-exporter` repository. All commands
should be run from the repository root.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Build binary | `make build` |
| Run unit tests | `make test` |
| Run tests with coverage | `make test-coverage` |
| Lint (golangci-lint v2) | `make lint` (or `make go-lint`) |
| Build container image | `make image-build` |
| Push container image | `make image-push` |
| Full build + image + test | `make all` |
| Clean build artifacts | `make clean` |

---

## Build

### Binary Build

```bash
make build
```

This runs:

```bash
cd cmd && CGO_ENABLED=0 go build -ldflags '-s -w' -tags no_openssl -v -o build/sriov-exporter
```

Key flags:

- `CGO_ENABLED=0` — static binary (no C dependencies)
- `-tags no_openssl` — avoids OpenSSL linking
- `-ldflags '-s -w'` — strips debug symbols and DWARF info

The output binary is placed at `build/sriov-exporter`.

### Container Image Build

```bash
make image-build
```

Uses Docker (or the builder specified by `IMAGE_BUILDER`) with a multi-stage
Dockerfile:

- **Builder**: `golang:1.26-alpine` — installs build deps, runs `make build`
- **Runtime**: `alpine:3.24` — copies binary, adds CA certificates

Configurable variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `IMAGE_REGISTRY` | `ghcr.io/k8snetworkplumbingwg/` | Container registry |
| `IMAGE_VERSION` | `latest` | Image tag |
| `IMAGE_NAME` | `$(IMAGE_REGISTRY)sriov-network-metrics-exporter:$(IMAGE_VERSION)` | Full image name |
| `IMAGE_BUILDER` | `docker` | Container build tool |

Proxy support: set `HTTP_PROXY` / `HTTPS_PROXY` env vars to pass build args.

---

## Linting

### golangci-lint

```bash
make lint
# or equivalently:
make go-lint
```

This installs and runs **golangci-lint v2.7.2** with a 5-minute timeout.

The `.golangci.yml` configuration (v2 format) enables an extensive set of
linters:

| Category | Linters |
|----------|---------|
| **Error handling** | errcheck, rowserrcheck |
| **Code quality** | govet, staticcheck, ineffassign, unused, unconvert, unparam |
| **Style** | goconst, gocritic, goprintffuncname, nakedret, whitespace |
| **Complexity** | funlen (100 lines / 50 stmts), gocyclo (≥15), dupl (threshold 100) |
| **Security** | gosec |
| **Formatting** | gofmt, goimports (local prefix: `github.com/k8snetworkplumbingwg/sriov-network-metrics-exporter`) |
| **Misc** | bodyclose, copyloopvar, dogsled, exhaustive, lll (140 chars), misspell, mnd, prealloc |

### Test file exclusions

The following linters are **disabled for test files** (`*_test.go`):

- dupl, funlen, goconst, mnd, errcheck, lll, gocritic, staticcheck, unconvert

### Lint Report

```bash
make go-lint-report
```

Writes full colored lint output to `golangci-lint.txt`.

---

## Testing

### Unit Tests

```bash
make test
```

Runs:

```bash
go test ./... -count=1
```

- `-count=1` disables test caching.
- Tests use **Ginkgo v2 + Gomega**.
- Tests mock filesystem access via `fstest.MapFS` — no real sysfs needed.
- CI installs `hwdata` package before running tests (`sudo apt-get install hwdata -y`).

### Test Coverage

```bash
make test-coverage
```

Runs:

```bash
go test ./... -coverprofile cover.out
go tool cover -func cover.out
```

Generates `cover.out` and prints per-function coverage to stdout.

### Running Specific Tests

To run tests for a single package:

```bash
go test ./collectors/ -count=1
go test ./pkg/utils/ -count=1
go test ./pkg/vfstats/ -count=1
go test ./cmd/ -count=1
```

To run a specific Ginkgo test by name:

```bash
go test ./collectors/ -count=1 -run "TestCollectors" -v -ginkgo.focus="should return"
```

---

## CI Pipeline

The CI workflow (`.github/workflows/build-test-lint.yml`) runs on every push
and pull request.

### Jobs and Dependencies

```
build (matrix: amd64/arm64/ppc64le/s390x) ──► test ──► (done)
                                           └─► test-coverage
build-image (multi-arch Docker buildx)
golangci (golangci-lint-action v9, v2.7.2)
hadolint (Dockerfile lint, ignores DL3018)
go-check (go mod tidy + go mod vendor consistency)
```

### Go Version

CI uses Go `1.25.x` across all jobs (build matrix, test, test-coverage,
golangci, go-check).

### go-check Job

The `go-check` job verifies module consistency:

```bash
# Must not produce diffs
go mod tidy && git diff --exit-code
go mod vendor && git diff --exit-code
```

**Important**: The vendor directory is **not tracked in git**. The `go-check`
job generates it as untracked files and verifies it matches `go.mod`/`go.sum`.
Do **not** commit `vendor/` files.

### Other Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `codeql.yml` | push to master, PRs | CodeQL security analysis |
| `image-push-master.yml` | push to master | Multi-arch image push to GHCR |
| `image-push-release.yml` | release tags | Release image push to GHCR |

---

## Recommended Pre-Push Sequences

### Minimal (any change)

```bash
make lint
make test
```

### After Dependency Changes

```bash
go mod tidy
make lint
make test
# Verify no unexpected changes
git diff go.mod go.sum
```

### Full (before submitting a PR)

```bash
make lint
make build
make test
make test-coverage
make image-build
```

### Verifying Module Consistency (matches CI go-check)

```bash
go mod tidy && git diff --exit-code
```

---

## PATH and Tool Requirements

| Tool | Install Method | Required By |
|------|----------------|-------------|
| Go 1.25+ | System / `actions/setup-go` | All build and test targets |
| golangci-lint v2.7.2 | Auto-installed by `make lint` via `go install` | `make lint` |
| Docker (or podman) | System | `make image-build` |
| hwdata | `apt-get install hwdata` | Unit tests (CI installs this) |

---

## Important Notes

- **No `go build` without tags** — Always use `make build` or pass
  `-tags no_openssl` manually. Building without this tag will fail.
- **No vendor directory in git** — The repo uses Go modules without vendoring.
  CI checks consistency but does not expect `vendor/` to be committed.
- **CGO_ENABLED=0 is required** — The Alpine-based container image requires a
  statically linked binary.
- **golangci-lint version pinned in two places** — The Makefile
  (`GOLANGCI_LINT_VER`) and the CI workflow (`golangci-lint-action` `version:`
  parameter) must stay in sync when upgrading.
- **Test caching is disabled** — `make test` uses `-count=1` to ensure fresh
  runs every time.
