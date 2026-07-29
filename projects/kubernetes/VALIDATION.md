# Kubernetes — Validation

Pre-push verification, code generation, and test commands for the
`kubernetes/kubernetes` repository. All scripts live under `hack/` and **must be
run from the repository root**.

---

## Quick Reference

| Action | Script |
|--------|--------|
| Run **all** verifiers | `hack/verify-all.sh` (or `make verify`) |
| Run **all** generators | `hack/update-all.sh` (or `make update`) |
| Lint | `hack/verify-golangci-lint.sh` |
| Codegen | `hack/verify-codegen.sh` / `hack/update-codegen.sh` |
| OpenAPI spec | `hack/verify-openapi-spec.sh` / `hack/update-openapi-spec.sh` |
| Boilerplate headers | `hack/verify-boilerplate.sh` |
| API compatibility | `hack/update-generated-api-compatibility-data.sh` |
| API diff (client-go) | `hack/apidiff.sh` |

---

## Verifiers (`hack/verify-*.sh`)

Verifiers are **read-only** checks. They exit non-zero when something is wrong
but never modify the tree. CI runs all of them via `make verify`.

### Always-run verifiers

These apply to virtually every change and should be part of every pre-push run.

| Script | What it checks |
|--------|----------------|
| `hack/verify-golangci-lint.sh [pkgs…]` | Go linting. Accepts optional package list for focused runs. Equivalent: `make lint` |
| `hack/verify-gofmt.sh` | Go formatting (`gofmt -s`) |
| `hack/verify-boilerplate.sh` | Copyright / license header on every source file |
| `hack/verify-imports.sh` | Import grouping and ordering |
| `hack/verify-import-aliases.sh` | Enforced import alias conventions (see `hack/.import-aliases`) |
| `hack/verify-import-boss.sh` | Import restrictions between packages |
| `hack/verify-description.sh` | API field descriptions in `types.go` |
| `hack/verify-fieldname-docs.sh` | Field-name documentation consistency |
| `hack/verify-codegen.sh` | All generated code is up-to-date (deepcopy, conversions, defaults, openapi, applyconfiguration, protobuf, validation) |
| `hack/verify-openapi-spec.sh` | OpenAPI spec snapshots match generated output |

### Conditional verifiers

Run these when the listed trigger conditions apply.

| Script | When to run | Notes |
|--------|-------------|-------|
| `hack/verify-featuregates.sh` | Changed feature gates | |
| `hack/verify-generated-docs.sh` | Changed CLI flags or docs | |
| `hack/verify-generated-stable-metrics.sh` | Changed metrics | |
| `hack/verify-golangci-lint-config.sh` | Changed lint config | |
| `hack/verify-golangci-lint-pr-hints.sh` | Lint hint validation | |
| `hack/verify-govulncheck.sh` | Dependency changes | Checks for known Go vulnerabilities |
| `hack/verify-cli-conventions.sh` | Changed kubectl / CLI code | |
| `hack/verify-conformance-requirements.sh` | Conformance test changes | |
| `hack/verify-conformance-yaml.sh` | Conformance test changes | |
| `hack/verify-deadcode-elimination.sh` | Build changes | |
| `hack/verify-e2e-images.sh` | E2E test image references | |
| `hack/verify-e2e-test-ownership.sh` | E2E test ownership labels | |
| `hack/verify-external-dependencies-version.sh` | Dependency bumps | |
| `hack/verify-file-sizes.sh` | Large file additions | |
| `hack/verify-flags-underscore.py` | CLI flag naming (no underscores) | |
| `hack/verify-go-apidocs.sh` | Go API documentation | |
| `hack/verify-api-groups.sh` | API group registration | |
| `hack/verify-internal-modules.sh` | Internal module structure | |

---

## Generators (`hack/update-*.sh`)

Generators **modify the tree** — they regenerate code, specs, or docs.
After running a generator, re-run the matching verifier to confirm the tree is
clean.

### Core generators

| Script | What it generates | Typical trigger |
|--------|-------------------|-----------------|
| `hack/update-codegen.sh` | deepcopy, conversions, defaults, openapi, applyconfiguration, protobuf, validation | Any API type change |
| `hack/update-openapi-spec.sh` | OpenAPI JSON/protobuf snapshots | API changes. **Needs etcd on PATH** |
| `hack/update-generated-api-compatibility-data.sh` | API compatibility test fixtures | API changes. **Needs protoc on PATH** |
| `hack/update-gofmt.sh` | Applies `gofmt -s` | Formatting issues |
| `hack/update-import-aliases.sh` | Fixes import aliases | Import alias violations |

### Targeted codegen

`hack/update-codegen.sh` accepts target arguments for faster partial generation:

```bash
# Single target
hack/update-codegen.sh swagger
hack/update-codegen.sh validation
hack/update-codegen.sh protobuf

# Common combo for API work
hack/update-codegen.sh protobuf deepcopy conversions validation openapi applyconfigs

# Full regeneration (no arguments)
hack/update-codegen.sh
```

### Other generators

| Script | What it generates |
|--------|-------------------|
| `hack/update-featuregates.sh` | Feature gate registration code |
| `hack/update-generated-docs.sh` | CLI reference documentation |
| `hack/update-generated-stable-metrics.sh` | Stable metrics list |
| `hack/update-golangci-lint-config.sh` | Regenerate lint config from template |
| `hack/update-go-apidocs.sh` | Go API documentation |
| `hack/update-conformance-yaml.sh` | Conformance test YAML |
| `hack/update-vendor.sh` | `go mod vendor` |
| `hack/update-vendor-licenses.sh` | Vendor license files |
| `hack/update-internal-modules.sh` | Internal module structure |
| `hack/update-kustomize.sh` | Kustomize manifests |
| `hack/update-mocks.sh` | Mock implementations |
| `hack/update-netparse-cve.sh` | Net-parse CVE data |
| `hack/update-owners-fmt.sh` | OWNERS file formatting |
| `hack/update-tools.sh` | Tool binaries |
| `hack/update-translations.sh` | i18n translation files |

---

## Testing

### Focused Go tests

Run only the packages you changed:

```bash
go test ./pkg/apis/resource/validation \
       ./pkg/registry/resource/resourceslice \
       ./staging/src/k8s.io/dynamic-resource-allocation/...
```

### Integration tests (require etcd)

```bash
# Install etcd (one-time)
hack/install-etcd.sh

# Run integration tests with etcd on PATH
PATH="$(pwd)/third_party/etcd:$PATH" go test ./test/integration/dra/...

# Targeted integration test
PATH="$(pwd)/third_party/etcd:$PATH" \
  go test ./test/integration/dra/all \
  -run 'TestDRA/all/SharedConsumableCapacity$' -count=1
```

### API compatibility tests (require protoc)

```bash
PATH="$(pwd)/third_party/protoc:$PATH" \
  go test k8s.io/api -run //HEAD -count=1
```

### E2E tests

E2E tests are typically run by CI, not locally. If needed:

```bash
hack/ginkgo-e2e.sh
```

---

## API Diff (client-go)

When changing public Go APIs in staging repos (especially `client-go`):

```bash
hack/apidiff.sh -base master staging/src/k8s.io/client-go
```

If it reports undocumented incompatible changes, update
`staging/src/k8s.io/client-go/CHANGELOG.md`.

---

## PATH Requirements

Several scripts need helper binaries on `PATH`:

| Binary | Install script | Used by |
|--------|----------------|---------|
| `etcd` | `hack/install-etcd.sh` | `update-openapi-spec.sh`, integration tests |
| `protoc` | `hack/install-protoc.sh` | `update-generated-api-compatibility-data.sh`, API compat tests |

Standard PATH augmentation:

```bash
export PATH="$(pwd)/third_party/etcd:$PATH"
export PATH="$(pwd)/third_party/protoc:$PATH"
```

---

## Recommended Pre-Push Sequences

### Minimal (any change)

```bash
hack/verify-boilerplate.sh
hack/verify-gofmt.sh
hack/verify-golangci-lint.sh [changed-packages…]
hack/verify-imports.sh
go test [changed-packages…]
```

### API / generated-code changes

```bash
# 1. Regenerate
hack/update-codegen.sh protobuf deepcopy conversions validation openapi applyconfigs
PATH="$(pwd)/third_party/etcd:$PATH" hack/update-openapi-spec.sh
PATH="$(pwd)/third_party/protoc:$PATH" hack/update-generated-api-compatibility-data.sh

# 2. Verify
hack/verify-codegen.sh
hack/verify-openapi-spec.sh
hack/verify-description.sh
hack/verify-boilerplate.sh
hack/verify-gofmt.sh
hack/verify-golangci-lint.sh [changed-packages…]

# 3. Test
go test [changed-packages…]
PATH="$(pwd)/third_party/protoc:$PATH" go test k8s.io/api -run //HEAD -count=1
PATH="$(pwd)/third_party/etcd:$PATH" go test ./test/integration/dra/...
```

### Full (before submitting a PR)

```bash
make verify
make update
make test
```

---

## Important Notes

- `verify-codegen.sh` and `verify-openapi-spec.sh` **expect a clean worktree**.
  If they fail because generated files are stale, run the matching `update-*`
  command first, then re-run the verifier.
- There is no dedicated local release-note verifier — ensure the PR body has a
  fenced `` ```release-note `` block manually.
- `hack/lint-dependencies.sh` checks for unwanted dependencies
  (see `hack/unwanted-dependencies.json`).
