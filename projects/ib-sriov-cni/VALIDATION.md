# ib-sriov-cni — Validation

Pre-push verification, build commands, and test sequences for the
`k8snetworkplumbingwg/ib-sriov-cni` repository. All commands must be run from
the repository root.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Build binaries | `make build` |
| Run linter | `make lint` |
| Run unit tests | `make test` |
| Run tests with coverage | `make test-coverage` |
| Run Dockerfile lint | `make hadolint` |
| Run shell script lint | `make shellcheck` |
| Build container image | `make image` |
| Test container image | `make test-image` |
| Full suite (lint + build + coverage) | `make all` |
| Full checks (lint + hadolint + shellcheck + test + image) | `make tests` |
| Update dependencies | `make deps-update` |

---

## Build

### Binaries

```bash
make build
```

Builds two binaries into `build/`:

| Binary | Source | Purpose |
|--------|--------|---------|
| `ib-sriov` | `cmd/ib-sriov-cni/` | CNI plugin binary |
| `thin_entrypoint` | `cmd/thin_entrypoint/` | Container entrypoint to install binary |

Build settings:

- `CGO_ENABLED=0` (static binary, no C dependencies)
- `-tags no_openssl` (required build tag)
- Linker flags inject `version`, `commit`, and `date`

### Container image

```bash
make image
```

Uses `docker` by default. Override with `IMAGE_BUILDER=podman`. Supports
proxy via `HTTP_PROXY` / `HTTPS_PROXY` environment variables:

```bash
make image HTTP_PROXY=http://proxy:8080
```

The Dockerfile is a multi-stage build: `golang:1.26` builder →
`gcr.io/distroless/static-debian13` final image.

---

## Linting

### Go linting

```bash
make lint
```

Runs `golangci-lint v2.7.2` with the `.golangci.yml` config (v2 format).
The linter binary is automatically downloaded to `bin/golangci-lint` on
first run.

**Key linter settings:**

- `gocyclo`: max complexity 15
- `funlen`: max 100 lines / 50 statements
- `lll`: max line length 140
- `dupl`: threshold 100
- `depguard`: blocks `github.com/sirupsen/logrus`
- Test files: `mnd`, `gosec`, `dupl`, `lll`, `goconst`, `errcheck` relaxed
- Formatters: `gofmt` + `goimports` with local prefix
  `github.com/k8snetworkplumbingwg/ib-sriov-cni`
- Excluded paths: `.github/`, `deployment/`, `docs/`, `images/`

**Timeout**: 5 minutes for lint, 10 minutes configured in `.golangci.yml`.

### Dockerfile linting

```bash
make hadolint
```

Runs hadolint v2.12.1-beta against the `Dockerfile`. The binary is
automatically downloaded to `bin/hadolint`.

### Shell script linting

```bash
make shellcheck
```

Runs shellcheck v0.11.0 against `images/*.sh`. The binary is automatically
downloaded to `bin/shellcheck`.

---

## Testing

### Unit tests

```bash
make test
```

Runs `go test` with a 15-second timeout against all test packages. Uses
Ginkgo v2 + Gomega framework.

Test variants:

| Target | Description |
|--------|-------------|
| `make test` | Default test run |
| `make test-race` | Tests with Go race detector |
| `make test-short` | Short tests only |
| `make test-verbose` | Verbose output with coverage |
| `make test-bench` | Benchmarks only |

### Test coverage

```bash
make test-coverage
```

Generates coverage report at `ib-sriov-cni.cover`. Upload to Coveralls
with:

```bash
make upload-coverage
```

### Image test

```bash
make test-image
```

Builds the container image, then runs `images/image_test.sh` which:
1. Runs the image with `--no-sleep` and a temporary output directory.
2. Verifies the `ib-sriov` binary was copied to the output directory.
3. Verifies the binary is non-empty.

---

## CI Pipeline

### Workflows

| Workflow | File | Triggers |
|----------|------|----------|
| Build + test | `buildtest.yaml` | push, PR, weekly cron |
| Static analysis | `static-scan.yaml` | push, PR |
| CodeQL | `codeql.yml` | push to master, PR |
| Image push (master) | `image-push-master.yaml` | push to master |
| Image push (release) | `image-push-release.yaml` | release tags |

### buildtest.yaml jobs

| Job | Steps | Depends on |
|-----|-------|------------|
| **build** | `make build` (Go 1.26.x matrix) | — |
| **test** | `make test` | build |
| **image-test** | `make test-image` via Docker Buildx | — |
| **coverage** | `make test-coverage` + Coveralls | build |

### static-scan.yaml jobs

| Job | Steps |
|-----|-------|
| **golangci** | `make lint` (Go 1.26.x) |
| **shellcheck** | `make shellcheck` |
| **hadolint** | `make hadolint` |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GO_BUILD_OPTS` | `CGO_ENABLED=0` | Go build environment |
| `GO_TAGS` | `-tags no_openssl` | Go build tags |
| `IMAGE_BUILDER` | `docker` | Container build tool |
| `DOCKERFILE` | `./Dockerfile` | Dockerfile path |
| `TAG` | `k8snetworkplumbingwg/ib-sriov-cni` | Image tag |
| `IMAGE_BUILD_OPTS` | (empty) | Additional image build flags |
| `HTTP_PROXY` / `HTTPS_PROXY` | (empty) | Proxy for image builds |
| `VERSION` | `master` | Version string embedded in binary |
| `COMMIT` | git HEAD | Commit hash embedded in binary |
| `GOPATH` | `go env GOPATH` | Go workspace path |
| `GOLANGCI_LINT_CACHE` | `build/.cache` | Lint cache directory |
| `COVERAGE_MODE` | `count` | Coverage counting mode |

---

## Tool Requirements

| Tool | Version | Install method |
|------|---------|----------------|
| Go | 1.26.x | Manual / CI `setup-go` |
| golangci-lint | v2.7.2 | Auto-installed by Makefile via `go install` |
| hadolint | v2.12.1-beta | Auto-downloaded by Makefile |
| shellcheck | v0.11.0 | Auto-downloaded by Makefile |
| goveralls | latest | Auto-installed by Makefile via `go install` |
| Docker / Podman | — | Required for `make image` and `make test-image` |

All tools except Go and Docker/Podman are automatically downloaded to `bin/`
on first use.

---

## Recommended Pre-Push Sequences

### Minimal (any Go change)

```bash
make lint
make test
```

### Full verification

```bash
make all        # lint + build + test-coverage
make hadolint   # Dockerfile changes
make shellcheck # Shell script changes
```

### Complete (before submitting a PR)

```bash
make tests      # lint + hadolint + shellcheck + test + test-image
```

This is the most comprehensive local check. It runs:
1. `make lint` — golangci-lint
2. `make hadolint` — Dockerfile linting
3. `make shellcheck` — Shell script linting
4. `make test` — Unit tests
5. `make test-image` — Container image build and test

---

## Important Notes

- **No vendor directory** — The project uses Go modules. There is no
  `vendor/` directory and no `go mod vendor` step.
- **No Makefile target for mock generation** — Mocks in `pkg/types/mocks/`
  are generated by mockery (headers read `Code generated by mockery`), but
  there is no `make generate` or `make mocks` target. Mockery is run ad-hoc
  when interfaces change. Do not manually edit mock files.
- **Build tag required** — Always pass `-tags no_openssl`. The Makefile
  handles this automatically. If running `go test` or `go build` directly,
  add the tag manually.
- **No `go test ./...` directly** — Use `make test` to ensure correct
  timeout and package selection. Direct `go test` invocations skip the
  15-second timeout.
- **golangci-lint v2** — The `.golangci.yml` uses v2 format. Do not
  downgrade to v1 config syntax.
