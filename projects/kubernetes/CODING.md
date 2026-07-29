# Kubernetes — Coding

Coding conventions, architecture patterns, and common pitfalls for contributing
to the `kubernetes/kubernetes` repository.

---

## Repository Layout

| Directory | Purpose |
|-----------|---------|
| `cmd/` | Binary entry points (kube-apiserver, kubelet, kubectl, etc.) |
| `pkg/` | Core library code — internal to the Kubernetes binary |
| `staging/src/k8s.io/` | Published client libraries (client-go, apimachinery, api, etc.) |
| `plugin/` | Plugin implementations (admission, auth) |
| `test/` | Integration and E2E tests |
| `hack/` | Build, codegen, and verification scripts |
| `api/` | OpenAPI and Swagger definitions |
| `vendor/` | Vendored dependencies (managed by `hack/update-vendor.sh`) |
| `third_party/` | Third-party tools (etcd, protoc — installed by `hack/install-*.sh`) |

---

## API Types

### Where types live

- **Internal types**: `pkg/apis/<group>/types.go`
- **Versioned types**: `staging/src/k8s.io/api/<group>/<version>/types.go`
- **Validation**: `pkg/apis/<group>/validation/validation.go`
- **Registry / strategy**: `pkg/registry/<group>/<resource>/strategy.go`
- **Apply configurations**: auto-generated in `staging/src/k8s.io/client-go/applyconfigurations/`

### API change workflow

1. Edit the versioned types in `staging/src/k8s.io/api/`.
2. Add/update validation in `pkg/apis/<group>/validation/`.
3. Run `hack/update-codegen.sh` to regenerate deepcopy, conversions, defaults,
   openapi, applyconfiguration, and protobuf code.
4. Run `hack/update-openapi-spec.sh` (needs etcd on PATH).
5. Run `hack/update-generated-api-compatibility-data.sh` (needs protoc on PATH).
6. Run verifiers to confirm everything is consistent.

### Field comments

API field comments become the OpenAPI descriptions. They must:

- Start with the field name.
- Use complete sentences.
- Include `+optional` marker for optional fields.
- Include appropriate markers: `+listType=`, `+mapType=`, `+structType=`,
  `+featureGate=`, etc.

---

## Code Generation

Kubernetes uses extensive code generation. **Never hand-edit generated files.**

| Marker | Generated output |
|--------|------------------|
| `+k8s:deepcopy-gen` | `zz_generated.deepcopy.go` |
| `+k8s:conversion-gen` | `zz_generated.conversion.go` |
| `+k8s:defaulter-gen` | `zz_generated.defaults.go` |
| `+k8s:openapi-gen` | OpenAPI definitions |
| `+k8s:applyconfiguration-gen` | Apply configuration types |
| `+k8s:protobuf-gen` | Protobuf serialization |
| `+k8s:validation-gen` | Declarative validation |

Generated files are prefixed with `zz_generated.` — do not edit these.

---

## Feature Gates

New features must be gated behind a feature gate:

1. Define the gate in `pkg/features/kube_features.go` (or the appropriate
   staging module).
2. Use `featureGate.Enabled(features.MyFeature)` in runtime code.
3. Add `+featureGate=MyFeature` markers on gated API fields.
4. Run `hack/update-featuregates.sh` and `hack/verify-featuregates.sh`.

Feature gate lifecycle: `Alpha → Beta → GA → Deprecated → Removed`.

---

## Boilerplate

Every source file must start with the Apache 2.0 license boilerplate.
The expected header is in `hack/boilerplate/`. Verify with:

```bash
hack/verify-boilerplate.sh
```

---

## Import Conventions

- Import aliases are enforced via `hack/.import-aliases`.
- Import ordering: stdlib → external → k8s.io → internal.
- Run `hack/verify-imports.sh` and `hack/verify-import-aliases.sh` to check.

---

## Logging

Kubernetes uses **structured logging** via `klog`:

```go
klog.InfoS("message", "key", value)
klog.ErrorS(err, "message", "key", value)
```

Do **not** use `fmt.Printf` or `log.Printf` for runtime logging.

Contextual logging (`klog.FromContext`) is preferred in new code.

---

## Testing Patterns

### Unit tests

- Tests live alongside the code: `foo_test.go` next to `foo.go`.
- Use the `testing` package standard patterns.
- Table-driven tests are strongly preferred.

### Integration tests

- Live in `test/integration/`.
- Require etcd (install via `hack/install-etcd.sh`).
- Use `kubeadm`-style test helpers to spin up API servers.

### E2E tests

- Live in `test/e2e/` (and `test/e2e_dra/`, `test/e2e_node/`, etc.).
- Use the Ginkgo + Gomega framework.
- Follow the `framework.NewDefaultFramework()` pattern.
- E2E test ownership labels are enforced by `hack/verify-e2e-test-ownership.sh`.

---

## Common Pitfalls

1. **Forgetting to run codegen** — Any change to API types requires
   `hack/update-codegen.sh`. The `verify-codegen.sh` check will catch this in CI.
2. **Stale OpenAPI spec** — After API changes, also run
   `hack/update-openapi-spec.sh` or the verifier will fail.
3. **Missing boilerplate** — New files without the license header fail
   `verify-boilerplate.sh`.
4. **Editing generated files** — Files prefixed with `zz_generated.` are
   auto-generated. Edit the source types and re-run codegen instead.
5. **Dirty worktree before verify** — `verify-codegen.sh` and
   `verify-openapi-spec.sh` expect a clean `git status`. Commit or stash
   unrelated changes first.
6. **Missing PATH for etcd/protoc** — Several scripts and tests need
   `third_party/etcd` or `third_party/protoc` on PATH.
7. **Import alias violations** — The repo enforces specific aliases for k8s.io
   packages. Check `hack/.import-aliases`.
