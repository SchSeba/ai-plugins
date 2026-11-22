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
| `vendor/` | Vendored dependencies managed by the checkout's vendoring tooling |
| `third_party/` | Third-party tools such as etcd and protoc |

---

## Contribution authority

Follow the current [contributor PR guide](https://www.kubernetes.dev/docs/guide/pull-requests/),
[API changes process](https://github.com/kubernetes/community/blob/main/contributors/devel/sig-architecture/api_changes.md),
[API conventions](https://github.com/kubernetes/community/blob/main/contributors/devel/sig-architecture/api-conventions.md)
and [OWNERS guide](https://www.kubernetes.dev/docs/guide/owners/).
Route conceptual/API review separately from allocator/scheduler implementation
review and inspect ownership coverage for every affected path. See
[REVIEWING.md](REVIEWING.md) for trust/approvals, drafts/holds, release notes and
review-friendly commit organization. Associated tests belong with their logical
implementation. Generated artifacts can be separated for review. After a rebase,
compare the final diff to the updated base. Check that upstream test cases and
shared helpers still run through the intended callers. Recheck the commit
grouping, remove incidental churn and refresh the PR description.

The inventory below is checkout-dependent project knowledge. Discover actual
script interfaces and matching patterns in the target checkout. Historical PR
preferences are heuristics, not universal rules.

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
3. Discover applicable generators and supported targets from the checkout.
   Inspect source markers, internal conversions/defaulting, registry strategies
   and feature-gate handling as well as versioned types.
4. Regenerate affected code, OpenAPI and compatibility artifacts with the
   matching tools; inspect their prerequisites rather than assuming one script
   covers everything.
5. Run matching verifiers and focused behavior/regression tests; use
   [VALIDATION.md](VALIDATION.md) for the conditional discovery inventory.

### Evolving an existing API

- Trace a field from a manifest and an older typed client through serialization,
  defaulting, conversion and storage. A Go value can turn omission into a
  serialized zero. Check whether those states remain distinguishable before
  switching to a pointer, tightening validation or adding a union.
- Check every served version and the published Go types when splitting a
  struct used in multiple roles. Preserve existing JSON and protobuf field
  identities. Establish which representations shipped before adding a migration
  or reserving a number used only during review.
- Derive status list/map bounds from the largest valid input a producer can
  report. Specify keys, ordering and the meaning of absence where clients use
  them. Check that generated schemas and handwritten producers agree.

### Field comments

API field comments become the OpenAPI descriptions. They must:

- Start with the field name.
- Use complete sentences.
- Include `+optional` marker for optional fields.
- Include appropriate markers: `+listType=`, `+mapType=`, `+structType=`,
  `+featureGate=`, etc.
- Describe enduring behavior, contracts, or non-obvious rationale so the comment
  stands on its own. Omit review-conversation references and redundant assurances
  (for example, “consistent with the other fields”) unless specifically requested.
  Preserve useful semantics, such as whether allocations already in flight are included.

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

Many generated files are prefixed with `zz_generated.`; others include protobuf, apply configurations and OpenAPI artifacts. Inspect headers/source relationships and regenerate all affected outputs.

---

## Feature Gates

For a gated feature, use the KEP and neighboring versioned registrations to
confirm its stage, default and dependencies.

1. Define the gate in `pkg/features/kube_features.go` (or the appropriate
   staging module).
2. Use `featureGate.Enabled(features.MyFeature)` in runtime code.
3. Add `+featureGate=MyFeature` markers on gated API fields.
4. Discover the lifecycle inventory generator and verifier in the target
   checkout and refresh the affected artifacts.

Feature gate lifecycle: `Alpha → Beta → GA → Deprecated → Removed`.

For gated API fields, trace create and update through strategy preparation and
the REST validation path. Cover enabled and disabled writes, including an update
of an object already using the field when the gate is disabled. Removing a
gated union member can leave an invalid object. Follow the admission contract
before choosing between rejection and defaulting. For a tightened constraint,
test an unchanged stored value, a change within its validation boundary and a
repair. Inspect list/map semantics to find that boundary.

Follow retained fields into consumers. Determine which allocator or controller
can implement the enabled behavior and how an older or disabled implementation
handles inputs that depend on it. Keep unrelated paths close to the base.

---

## Shared state in schedulers and controllers

- Give each charge an identity, a lifetime and a source of truth. Decide which
  values follow live resource definitions and which belong to an allocation
  result. Trace two users of one resource through allocation, reconstruction
  from storage, release of either user and release of the last user.
- Where cached and in-flight state overlap, reconcile by allocation identity.
  A failed candidate must undo exactly its own reservations. Reuse the same
  state-building helper for production and tests where they consume the same
  inputs, so tests exercise that contract.
- Before arithmetic on informer-derived data, check the actual copy semantics
  of the type and its containers in the target revision. A value copy and a
  shared pointer to that value have different ownership. Ensure reconciliation
  leaves cached inputs available to other readers in their original state.
- When a map traversal can encounter both a fatal input error and a candidate
  that simply does not fit, preserve the contract's error precedence regardless
  of iteration order. Exercise both outcomes together. Keep any new indexing
  or scans proportional to demonstrated workload and feature use.

The [shared-capacity case study](SHARED_CAPACITY_REVIEW.md) shows how these
decisions changed during review of a DRA feature.

---

## Boilerplate

Use the applicable Apache 2.0 template from `hack/boilerplate/` for new
source files. Discover the matching check in the target checkout.

---

## Import Conventions

- Import aliases are enforced via `hack/.import-aliases`.
- Import ordering: stdlib → external → k8s.io → internal.
- Discover the checkout's import and alias checks when changing imports.

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
- Compare the complete relevant result, including an unexpectedly populated
  field. Inspect the suite's existing gate permutations before adding cases.

### Integration tests

- Live in `test/integration/`.
- Check how the target suite obtains etcd.
- Follow existing integration harness and API-server setup patterns in the affected suite.
- Isolate the limiting resource and assert the observable transition. For
  example, a scheduler test can keep another device free and check that a pod
  has no node assignment while the shared budget is exhausted, then verify it
  binds after release.

### E2E tests

- Live in `test/e2e/` (and `test/e2e_dra/`, `test/e2e_node/`, etc.).
- Use the Ginkgo + Gomega framework.
- Follow the `framework.NewDefaultFramework()` pattern.
- Check the suite's ownership labels with the repository's current verifier.

---

## Common Pitfalls

1. **Stale generated code** — Discover the generators and matching verifiers
   for the changed types in the target checkout.
2. **Stale OpenAPI spec** — Check whether the change affects schemas or
   descriptions and refresh the published artifacts.
3. **Missing boilerplate** — Match the expected license header for the file type.
4. **Editing generated files** — Files prefixed with `zz_generated.` are
   auto-generated. Edit the source types and re-run codegen instead.
5. **Verifier prerequisites** — Inspect current scripts for clean-tree and
   regeneration requirements. Preserve unrelated work and review side effects;
   never commit or stash blindly just to run a verifier.
6. **Missing PATH for etcd/protoc** — Several scripts and tests need
   `third_party/etcd` or `third_party/protoc` on PATH.
7. **Import alias violations** — The repo enforces specific aliases for k8s.io
   packages. Check `hack/.import-aliases`.
