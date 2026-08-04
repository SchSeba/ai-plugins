# SR-IOV CNI — Validation

Pre-push verification, build, lint, and test commands for the
`k8snetworkplumbingwg/sriov-cni` repository. All commands are run from the
repository root.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Format code | `make fmt` |
| Lint | `make lint` |
| Build binary | `make build` |
| Unit tests | `make test` |
| Unit tests (race detector) | `make test-race` |
| Unit tests (coverage) | `make test-coverage` |
| Integration tests | `sudo make test-integration` |
| Merge coverage reports | `make merge-test-coverage` |
| Generate mocks | `make mock-generate` |
| Build container image | `make image` |
| Full validation | `make all` (= `fmt` + `lint` + `build`) |
| Update dependencies | `make deps-update` |
| Clean build artifacts | `make clean` |

---

## Makefile Targets (Detail)

### `make fmt`

Runs `go fmt ./...` on all source files. Quick formatting check.

### `make lint`

Runs **golangci-lint v2** (version pinned in Makefile via
`GOLANGCI_LINT_VERSION`). The linter binary is auto-installed to `bin/`
on first run.

The `.golangci.yml` config enables 25+ linters including:

| Category | Linters |
|----------|---------|
| Correctness | `govet`, `staticcheck`, `errcheck`, `ineffassign`, `unused` |
| Security | `gosec`, `bidichk` |
| Style | `gocritic`, `misspell`, `nakedret`, `whitespace`, `asciicheck` |
| Performance | `prealloc`, `makezero`, `unconvert` |
| Duplication | `dupl` (threshold: 100), `goconst` |
| Dependencies | `depguard` (denies `github.com/sirupsen/logrus`) |

Formatters: `gofmt` and `goimports` (with local prefix
`github.com/k8snetworkplumbingwg/sriov-cni`).

Exclusions:
- `vendor/`, `.github/`, `docs/`, `images/` directories are excluded
- Test files (`_test.go`) relax `mnd`, `gosec`, `dupl`, `lll`, `goconst`
- Standard error handling and comment presets are excluded

### `make vet`

Runs `go vet ./...`. Separate from lint — useful for a quick check.

### `make build`

Builds the `sriov` binary to `build/sriov`:

```bash
CGO_ENABLED=0 go build -tags no_openssl -o build/sriov ./cmd/sriov/
```

Key flags:
- `CGO_ENABLED=0` — static binary, no C dependencies
- `-tags no_openssl` — avoids OpenSSL dependency
- Output: `build/sriov`

### `make test`

Runs unit tests (excludes mock packages):

```bash
go test -timeout 30s $(go list ./... | grep -v ".*/mocks")
```

### `make test-race`

Same as `make test` with `-race` flag for race condition detection.

### `make test-coverage`

Runs unit tests with coverage:

```bash
go test -timeout 30s -cover -covermode=atomic \
  -coverprofile=test/coverage/cover-unit.out ./...
```

Output: `test/coverage/cover-unit.out`

### `make test-integration`

Runs integration tests using the `bash_unit` framework. **Requires `sudo`**
for network namespace operations:

```bash
sudo make test-integration
```

The integration tests:
1. Auto-download `bash_unit` to `bin/bash_unit`
2. Build a mocked version of the CNI binary (`test/integration/sriov_mocked.go`)
3. Create a fake sysfs filesystem and mock netlink library
4. Execute shell-based test cases in `test/integration/test_*.sh`
5. Generate coverage to `test/coverage/cover-integration.out`

Set `INT_TEST_SKIP_CLEANUP=true` to preserve test artifacts for debugging.

### `make merge-test-coverage`

Merges unit and integration coverage reports:

```bash
gocovmerge test/coverage/cover-unit.out test/coverage/cover-integration.out \
  > test/coverage/cover.out
```

### `make mock-generate`

Regenerates mock files using **mockery v2** (auto-installed to `bin/`):

```bash
mockery --recursive=true --name=NetlinkManager --output=./pkg/utils/mocks/ \
  --filename=netlink_manager_mock.go --exported --dir pkg/utils
mockery --recursive=true --name=pciUtils --output=./pkg/sriov/mocks/ \
  --filename=pci_utils_mock.go --exported --dir pkg/sriov
```

Run this after changing any interface definition.

### `make image`

Builds the container image using Docker (or `IMAGE_BUILDER=podman`):

```bash
docker build -t ghcr.io/k8snetworkplumbingwg/sriov-cni -f Dockerfile .
```

The Dockerfile is a multi-stage build:
- **Builder**: `golang:1.25-alpine` — runs `make clean && make build`
- **Runtime**: `alpine:3` — copies `build/sriov` and `images/entrypoint.sh`

### `make all`

Full pre-push validation: `fmt` → `lint` → `build`.

Note: `make all` does **not** include tests. Run tests separately.

---

## CI Workflows

### `buildtest.yml` — Build & Test

Runs on every push and PR:

| Job | What it does |
|-----|-------------|
| `build-test` | Matrix build (amd64, arm64, ppc64le, s390x) + unit tests + integration tests |
| `coverage` | Unit + integration coverage, uploads to Coveralls |
| `sriov-operator-e2e-test` | Builds sriov-cni image, runs sriov-network-operator E2E suite (self-hosted `sriov` runners) |

Unit tests and integration tests both run with `sudo` (required for namespace
operations).

### `static-scan.yml` — Static Analysis

Runs on every push and PR:

| Job | What it does |
|-----|-------------|
| `golangci` | `make lint` |
| `shellcheck` | ShellCheck on all shell scripts |
| `hadolint` | Dockerfile linting |

### Other workflows

| Workflow | Trigger |
|----------|---------|
| `codeql.yml` | CodeQL security analysis on push/PR |
| `image-push-master.yml` | Push image on merge to master |
| `image-push-release.yml` | Push image on release tags |

---

## Environment Variables & Flags

| Variable | Default | Purpose |
|----------|---------|---------|
| `CGO_ENABLED` | `0` | Disable CGO for static binary |
| `GO_TAGS` | `-tags no_openssl` | Required build tag |
| `GO_LDFLAGS` | (empty) | Additional linker flags |
| `IMAGE_BUILDER` | `docker` | Container builder (`docker` or `podman`) |
| `TAG` | `ghcr.io/k8snetworkplumbingwg/sriov-cni` | Container image tag |
| `DOCKERFILE` | `./Dockerfile` | Dockerfile path |
| `HTTP_PROXY` / `HTTPS_PROXY` | (unset) | Proxy settings for Docker build |
| `INT_TEST_SKIP_CLEANUP` | (unset) | Set `true` to preserve integration test artifacts |
| `GOCOVERDIR` | (unset) | Directory for Go binary coverage instrumentation |

---

## PATH / Tool Requirements

| Tool | Version | Install method |
|------|---------|----------------|
| Go | 1.25.x+ | System install or `actions/setup-go` |
| golangci-lint | v2.7.2 | Auto-installed by `make lint` to `bin/` |
| mockery | v2.50.2 | Auto-installed by `make mock-generate` to `bin/` |
| bash_unit | v2.3.2 | Auto-downloaded by `make test-integration` to `bin/` |
| gocovmerge | latest | Auto-installed by `make merge-test-coverage` to `bin/` |
| Docker/Podman | any | Required for `make image` |
| ShellCheck | any | Required for CI static scan (not in Makefile) |
| Hadolint | any | Required for CI Dockerfile lint (not in Makefile) |

All Go tools are installed to `bin/` within the repo root via `GOBIN=$(BINDIR)`.
No global tool installation is needed.

---

## Recommended Pre-Push Sequences

### Minimal (any Go change)

```bash
make fmt
make lint
make test
make build
```

### Full (before submitting a PR)

```bash
# 1. Format and lint
make fmt
make lint

# 2. Build
make build

# 3. Unit tests with race detector
make test-race

# 4. Integration tests (requires sudo)
sudo make test-integration

# 5. Container image build
make image
```

### After interface changes

```bash
# 1. Regenerate mocks
make mock-generate

# 2. Run full validation
make all
make test
sudo make test-integration
```

### Coverage report

```bash
make test-coverage
sudo make test-integration
make merge-test-coverage
# Combined report: test/coverage/cover.out
```

---

## Important Notes

- **`sudo` requirement**: Unit tests and integration tests both need `sudo`
  for network namespace operations. CI runs them as
  `sudo env "PATH=$PATH" make test-race`.

- **No vendor directory**: The repo uses Go modules without vendoring. Do not
  commit a `vendor/` directory.

- **Integration tests need `bash_unit`**: Auto-downloaded on first run. If the
  download fails, the tests will fail.

- **E2E tests are external**: The sriov-network-operator E2E suite runs in CI
  on self-hosted `sriov` runners. These cannot be run locally without SR-IOV
  hardware.

- **`make all` ≠ full validation**: `make all` runs `fmt` + `lint` + `build`
  but does **not** run tests. Always run `make test` separately.

- **Coverage merging**: Unit and integration coverage are separate. Use
  `make merge-test-coverage` to combine them after running both.
