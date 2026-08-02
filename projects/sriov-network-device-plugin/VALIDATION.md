# SR-IOV Network Device Plugin — Validation

Pre-push verification, build, lint, and test commands for the
`k8snetworkplumbingwg/sriov-network-device-plugin` repository. All commands are
run from the repository root via `make`.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Build binary | `make build` |
| Run linter | `make lint` |
| Run unit tests | `make test` |
| Run tests with race detector | `make test-race` |
| Run coverage tests | `make test-coverage` |
| Build + lint + test | `make all` |
| Fix lint issues | `make lint-fix` |
| Regenerate mocks | `make generate-mocks` |
| Update dependencies | `make deps-update` |
| Build Docker image | `make image` |
| Clean build artifacts | `make clean` |

---

## Build

### Binary

```bash
make build
```

Builds the `sriovdp` binary to `build/sriovdp`. The build always uses
`-tags no_openssl` (set via `GO_TAGS` in the Makefile). For static builds, set
`STATIC=1`:

```bash
make build STATIC=1
```

This adds `CGO_ENABLED=0`, `-extldflags "-static"`, and `-a` flags.

### Docker Image

```bash
make image
```

Builds a multi-stage Docker image:
1. **Builder** — `golang:1.25-alpine`, compiles `sriovdp` binary.
2. **DDP builder** — `golang:1.20-alpine3.16`, compiles `ddptool` (pinned Go
   version — do **not** bump).
3. **Final** — `alpine:3`, installs `hwdata-pci`, copies binaries and
   entrypoint.

Proxy support:

```bash
make image HTTP_PROXY=http://proxy:8080 HTTPS_PROXY=http://proxy:8080
```

---

## Linting

### golangci-lint

```bash
make lint
```

Uses golangci-lint v2.7.2 (installed automatically to `bin/golangci-lint`).
Configuration is in `.golangci.yml` (v2 format).

**Enabled linters** (notable):

| Linter | Purpose |
|--------|---------|
| `errcheck` | Unchecked error returns |
| `govet` | Go vet analysis |
| `staticcheck` | Advanced static analysis |
| `gosec` | Security issues (except G304 — file path from variable) |
| `gocyclo` | Cyclomatic complexity (max 15) |
| `funlen` | Function length (max 100 lines / 50 statements) |
| `lll` | Line length (max 140 characters) |
| `mnd` | Magic numbers in arguments, cases, conditions, returns |
| `dupl` | Code duplication (threshold 100 tokens) |
| `ginkgolinter` | Ginkgo/Gomega best practices, forbids focused containers |
| `depguard` | Denies `logrus` imports |
| `misspell` | US English spelling |

**Formatters** (run via `make lint-fix`):

| Formatter | Purpose |
|-----------|---------|
| `gofmt` | Standard Go formatting |
| `goimports` | Import sorting and removal of unused imports |
| `gci` | Import grouping: stdlib → external → project-internal |

**Exclusions**:
- Generated code uses `lax` exclusion mode.
- Test files (`_test.go`) exclude: `dupl`, `goconst`, `lll`, `gosec`.
- Directories excluded: `.github/`, `deployments/`, `docs/`.
- Specific files excluded: `pkg/utils/testing.go`, `pkg/resources/testing.go`.

### Shell and Dockerfile linting (CI only)

| Check | CI tool | Notes |
|-------|---------|-------|
| ShellCheck | `ludeeus/action-shellcheck@master` | Excludes vendor dir, suppresses SC3037 |
| Hadolint | `hadolint/hadolint-action@v3.3.0` | Ignores DL3018 (Alpine apk pinning) |

These are not available as Makefile targets — they run only in CI.

---

## Testing

### Unit Tests

```bash
make test
```

Runs `go test -timeout 15s` on all packages except mocks. The test timeout is
configurable via `TIMEOUT` variable:

```bash
make test TIMEOUT=30
```

### Tests with Race Detector

```bash
make test-race
```

Runs tests with `-race` flag. This is what CI runs.

**Prerequisite**: The `hwdata` package must be installed on the system (provides
PCI device ID database used by `ghw`):

```bash
# Ubuntu/Debian
sudo apt-get install hwdata

# Alpine
apk add hwdata-pci
```

### Coverage

```bash
make test-coverage
```

Generates coverage profile to `test/coverage/cover.out` with `atomic` coverage
mode. CI uploads results to Coveralls.

### Running Specific Tests

Use Go test directly with the build tag:

```bash
# Single package
go test -tags no_openssl ./pkg/devices/...

# Specific test
go test -tags no_openssl ./pkg/factory/ -run "TestFactory" -v

# With Ginkgo focus (for local debugging only — never commit)
go test -tags no_openssl ./pkg/resources/ -ginkgo.focus "Allocate"
```

### Verbose Mode

```bash
make test-verbose
```

Runs tests with `-v` flag for detailed output.

---

## Mock Generation

```bash
make generate-mocks
```

Regenerates mocks for all interfaces using mockery (installed automatically to
`bin/mockery`):

| Source directory | Output directory |
|-----------------|------------------|
| `pkg/types/` | `pkg/types/mocks/` |
| `pkg/utils/` | `pkg/utils/mocks/` |
| `pkg/cdi/` | `pkg/cdi/mocks/` |

Run this after changing any interface in these packages, or tests relying on
mocks will fail.

---

## Dependency Management

### Update dependencies

```bash
make deps-update
```

Runs `go mod tidy`. Do **not** commit vendor directory files — the repo uses
Go modules without vendoring.

### CI consistency check

CI runs two verification steps:

```bash
# Check go.mod/go.sum consistency
go mod tidy && git diff --exit-code

# Check vendor reproducibility
go mod vendor && git diff --exit-code
```

Even though vendor is not tracked, CI verifies that `go mod vendor` produces a
clean diff (i.e., go.mod/go.sum are consistent with the code).

---

## CI Pipeline

### Workflow: `build-test-lint.yml`

Triggered on push and pull_request:

| Job | Description | Dependencies |
|-----|-------------|-------------|
| `build` | `make build` | — |
| `test` | `make test-race` (with `hwdata`) | `build` |
| `test-coverage` | `make test-coverage` + Coveralls | `build` |
| `golangci` | `make lint` | — |
| `shellcheck` | ShellCheck on all shell scripts | — |
| `hadolint` | Hadolint on `images/Dockerfile` | — |
| `go-check` | `go mod tidy` + `go mod vendor` diff check | — |
| `sriov-operator-e2e-test` | E2E via sriov-network-operator (self-hosted `sriov` runners) | `build`, `test` |

All Go jobs use `go-version: 1.25.x`.

### Other workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `codeql.yml` | Push/PR | CodeQL security analysis |
| `image-push-master.yml` | Push to master | Publish image to ghcr.io |
| `image-push-release.yml` | Release tags | Publish release image |

---

## Recommended Pre-Push Sequences

### Minimal (any change)

```bash
make lint
make test
```

### After interface changes

```bash
make generate-mocks
make lint
make test-race
```

### After dependency changes

```bash
make deps-update        # go mod tidy
make lint
make test
# Verify CI will pass:
go mod vendor && git diff --exit-code
# Clean up untracked vendor
rm -rf vendor/
```

### Full (before submitting a PR)

```bash
make all                # lint + build + test
make test-race          # race detector
make test-coverage      # coverage
make image              # Docker build
```

---

## Go Version References

When bumping the Go version, update these files:

| File | What to change |
|------|---------------|
| `go.mod` | `go X.XX.X` directive |
| `images/Dockerfile` | `FROM golang:X.XX-alpine AS builder` (line 1 only — **not** the DDP builder on line 16) |
| `.github/workflows/build-test-lint.yml` | 5 occurrences of `go-version: X.XX.x` (build, test, test-coverage, golangci, go-check) |

**Do not** change the DDP builder stage (`golang:1.20-alpine3.16`) — it is
intentionally pinned for ddptool compatibility.

---

## Important Notes

- **No `go test ./...` directly** — Always use `make test` or pass
  `-tags no_openssl` if running `go test` directly.
- **hwdata required** — Tests depend on `hwdata` for PCI device ID database.
  Install it before running tests locally.
- **E2E tests are remote** — The `sriov-operator-e2e-test` job runs on
  self-hosted runners with SR-IOV hardware. These tests are frequently flaky
  due to infrastructure issues — `podman build` exit code 125 is a container
  runtime error, not a code issue.
- **Vendor not tracked** — Do not stage or commit `vendor/` files. CI validates
  consistency, but the directory is not in git.
- **golangci-lint Go compatibility** — When bumping Go versions, verify the
  pinned golangci-lint version supports the new Go. For example, golangci-lint
  v2.7.2 does not support Go 1.26 — use v2.12.2 or newer.
