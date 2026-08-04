# rdma-cni — Validation

Pre-push verification, build, lint, and test commands for the
`k8snetworkplumbingwg/rdma-cni` repository. All commands should be run from the
repository root.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Build binary | `make build` |
| Run linter | `make lint` |
| Run unit tests | `make test` |
| Run tests with coverage | `make test-coverage` |
| Generate mocks | `make generate-mocks` (or `make generate`) |
| Build + lint + generate | `make all` |
| Build container image | `make image` |
| Clean build artifacts | `make clean` |

---

## Build

### Binary build

```bash
make build
```

Builds the `rdma` binary to `build/rdma`. Build options:

- `CGO_ENABLED=0` — static binary, no C dependencies.
- `-tags no_openssl` — excludes OpenSSL-dependent code.
- Cross-compilation: `TARGET_OS` and `TARGET_ARCH` env vars (defaults to host).

The binary embeds version info via ldflags: `-X main.version`, `-X main.commit`,
`-X main.date`.

### Container image

```bash
make image
```

Builds a multi-stage Docker image:
1. **Builder stage**: `golang:1.26-alpine` — installs `build-base`, runs
   `make clean && make build`.
2. **Runtime stage**: `alpine:3` — copies the binary and `images/entrypoint.sh`.

Proxy support: pass `HTTP_PROXY` and/or `HTTPS_PROXY` as make variables:

```bash
make image HTTP_PROXY=http://proxy:8080
```

Custom image builder: set `IMAGE_BUILDER` (defaults to `docker`):

```bash
make image IMAGE_BUILDER=podman
```

---

## Linting

### golangci-lint

```bash
make lint
```

Runs golangci-lint **v2.7.2** with the configuration in `.golangci.yml`.

### shellcheck

CI runs [shellcheck](https://github.com/koalaman/shellcheck) via
`ludeeus/action-shellcheck` on all shell scripts (primarily
`images/entrypoint.sh`).

### hadolint

CI runs [hadolint](https://github.com/hadolint/hadolint) on the `Dockerfile`
via `hadolint/hadolint-action`.

---

## Testing

### Unit tests

```bash
make test
```

Runs `go test` with a 30-second timeout on all packages except `vendor/` and
`mocks/`.

Test framework: Ginkgo v2 + Gomega with mockery v3 mocks.

### Test variants

| Target | Description |
|--------|-------------|
| `make test` | Standard unit tests |
| `make test-race` | Tests with race detector (`-race`) |
| `make test-short` | Only short tests (`-short`) |
| `make test-verbose` | Verbose mode with coverage reporting (`-v`) |
| `make test-bench` | Benchmarks only |

### Coverage

```bash
make test-coverage
```

Generates a coverage profile at `rdma-cni.cover`. CI uploads this to
[Coveralls](https://coveralls.io/) via `coverallsapp/github-action`.

---

## Code Generation

### Mock generation

```bash
make generate-mocks
# or
make generate
```

Uses **mockery v3** (v3.5.4) configured in `.mockery.yml`. Generates mocks for:

| Interface | Mock location |
|-----------|---------------|
| `cache.StateCache` | `pkg/cache/mocks/StateCache.go` |
| `rdma.Manager` | `pkg/rdma/mocks/RdmaManager.go` |
| `rdma.BasicOps` | `pkg/rdma/mocks/RdmaBasicOps.go` |

**Never hand-edit mock files** — always regenerate with `make generate-mocks`.

---

## CI Pipeline

### Workflows

| Workflow | File | Triggers | Jobs |
|----------|------|----------|------|
| Build & Test | `buildtest.yaml` | push, PR, weekly cron | build, test, coverage |
| Static Analysis | `static-scan.yaml` | push, PR | golangci-lint, shellcheck, hadolint |
| CodeQL | `codeql.yaml` | push to master, PR | CodeQL security analysis |
| Image Push (master) | `image-push-master.yaml` | push to master | Multi-arch image build & push |
| Image Push (release) | `image-push-release.yaml` | release tags | Multi-arch image build & push |

### CI Go version

All CI jobs use Go **1.26.x** (configured in workflow files).

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
make build
make test
```

### Full (before submitting a PR)

```bash
make all        # generate + lint + build
make test
make image      # verify container build
```

---

## Tool Requirements

| Tool | Version | Install method |
|------|---------|----------------|
| Go | 1.26.x | System install or `actions/setup-go` |
| golangci-lint | v2.7.2 | Auto-installed by `make lint` to `bin/` |
| mockery | v3.5.4 | Auto-installed by `make generate-mocks` to `bin/` |
| goveralls | v0.0.12 | Auto-installed by `make test-coverage` to `bin/` |
| Docker/Podman | any | System install (for `make image`) |
| shellcheck | any | CI only (`ludeeus/action-shellcheck`) |
| hadolint | any | CI only (`hadolint/hadolint-action`) |

All Go tools are installed to the local `bin/` directory (not global GOBIN)
via `go install` with pinned versions.

---

## Important Notes

- There is **no vendor directory** — the repo uses Go modules directly. Do not
  run `go mod vendor` or commit a `vendor/` directory.
- The `make all` target runs `generate + lint + build` (no tests). Run
  `make test` separately.
- The `PKGS` variable automatically excludes `vendor/` and `mocks/` directories
  from test runs.
- The `TIMEOUT` for tests defaults to 30 seconds. Override with
  `make test TIMEOUT=60`.
- There are no integration or E2E tests in this repository — only unit tests.
- The `make clean` target removes `build/`, `bin/`, and `test/` directories.
