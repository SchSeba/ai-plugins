# Kubernetes — Reviewing

Review patterns, common findings, and standards enforced during code review for
the `kubernetes/kubernetes` repository.

---

## Review Focus Areas

### API Changes

- **Backward compatibility**: New fields must be optional; removing or renaming
  fields is a breaking change.
- **Feature gate markers**: New alpha fields need `+featureGate=<Name>` markers.
- **Field comments**: Must start with the field name and use complete sentences.
  They become OpenAPI descriptions. Avoid inventing terminology — use the concept
  name consistently (e.g., say "a counter", not "a shared counter", unless the
  struct name literally is `SharedCounter`).
- **Validation coverage**: Every new field needs validation rules in
  `pkg/apis/<group>/validation/`.
- **Apply configurations**: Generated apply configs must include the new fields.
- **Protobuf tags**: New fields need correct protobuf field numbers (never reuse
  deleted numbers).
- **API compatibility**: `hack/update-generated-api-compatibility-data.sh` must
  be updated for type changes.
- **Pointer fields and `omitempty`**: Pointer fields with optional semantics
  **must** use `json:",omitempty"` to avoid serializing explicit `null` into JSON.
  This applies to all API versions (v1, v1beta1, v1beta2). If you see a pointer
  field without `omitempty`, that is a review finding.
- **Size limits on new list/slice fields**: Every new list or slice field in an
  API type needs a documented maximum-size constant and corresponding apiserver
  validation. The apiserver cannot trust the scheduler or any other client with
  write access — enforce bounds at the API layer.
- **Struct reuse across contexts**: If the same Go struct is used for fields with
  different semantics (e.g., the same `Counter` struct for both `sharedCounters`
  and `consumesCounters`), review whether OpenAPI-based validation can detect
  invalid combinations. If not, consider defining separate structs (this is a Go
  API break but not a Kubernetes REST API break if the wire encoding stays the
  same).
- **Validation tightening**: You cannot unconditionally tighten validation for
  existing fields. If a zero value was previously accepted, the new validation
  must only reject zero values under new conditions (e.g., a new field is set).
  Guard tightened validation behind the new feature or behind a check that the
  old object was also invalid — otherwise upgrades break existing objects.
- **Pointer field migration**: When changing a non-pointer `Quantity` (or
  similar) field to a `*Quantity` pointer for mutual-exclusivity semantics,
  there is a subtle backward-compat concern: existing stored objects may lack
  the field (implicit zero-value defaulting vs. explicit `nil`). Consult an API
  reviewer (e.g., @liggitt) before making this change, especially if the field
  was previously required by validation but defaulted implicitly.
- **Declarative validation markers**: Prefer `+k8s:optional`,
  `+k8s:zeroOrOneOfMember`, and other declarative validation tags when possible.
  Check whether the field type supports the tag (e.g., non-pointer structs like
  `resource.Quantity` cannot use `+k8s:optional`). When declarative validation
  cannot be used, add a source-code comment explaining why and keep the manual
  validation.
- **Feature gate gating in strategy**: The `dropDisabled*` pattern in strategy
  files must correctly handle three update scenarios: (1) keep fields when the
  feature is enabled, (2) drop fields when the feature is disabled, (3) keep
  fields that already exist in the old object even when the feature is disabled.
  Do not strip empty entries from lists/maps that the user explicitly sent — let
  the API return a validation error rather than silently discarding input.

### Generated Code

- All `zz_generated.*` files must be regenerated, not hand-edited.
- The diff for generated files should be consistent with the source type changes.
- If codegen output looks wrong, the reviewer should check the source markers.

### Go Code Quality

- **Structured logging**: `klog.InfoS` / `klog.ErrorS`, not `fmt.Printf`.
- **Error handling**: Errors must be wrapped with context, not swallowed.
- **Import ordering**: stdlib → external → k8s.io → internal.
- **Import aliases**: Must match `hack/.import-aliases`.
- **Boilerplate**: Every file needs the Apache 2.0 license header. Use
  `Copyright The Kubernetes Authors.` — not the year-specific variant.
- **No `init()` functions** unless absolutely necessary (registration patterns).
- **Context propagation**: Functions should accept and pass `context.Context`.
- **Avoid bespoke test helpers**: Use standard Go/Kubernetes patterns. For
  example, use `new(resource.MustParse("1"))` instead of defining custom helpers
  like `mustParseQuantityPtr`. Custom helpers add cognitive overhead for
  reviewers and obscure what the test actually does.
- **Function ordering**: Prefer top-down order in files — higher-level functions
  before the helpers they call (e.g., `dropDisabledFields` before
  `featureInUse`).
- **Naming consistency**: Use current field/struct names in test cases and
  comments, not former names. If a field was renamed (e.g., `capacity-key` →
  `capacity-name`), update all references including test case names.

### Testing

- **Unit test coverage**: New logic must have table-driven unit tests.
- **Tests in the same commit as code**: Unit tests and validation tests must be
  in the same commit as the code they test. Do not defer tests to a later commit
  — reviewers will send you back.
- **Strategy test shape**: For strategy `dropDisabled*` changes, follow the
  standard pattern:
  - **Create**: 2 cases — (1) feature enabled keeps new fields, (2) feature
    disabled strips new fields.
  - **Update**: 3 cases — (1) feature enabled keeps new fields, (2) feature
    disabled strips new fields, (3) feature disabled but existing object has
    fields → keep them (backward compatibility).
- **Feature-gate gating tests**: Must cover the three update scenarios above.
- **Validation test coverage**: When reusing a validator function in a new
  context, add at least one failure case to confirm the validator is actually
  called (exhaustive coverage belongs in the validator's own tests).
- **Integration tests**: API/scheduler changes need integration test coverage.
- **E2E tests**: Feature-level changes need E2E tests in the appropriate suite.
- **Test ownership labels**: E2E tests must have correct ownership annotations.
- **No `go test ./...`**: Run only the relevant packages to keep CI fast.

### Client-go / Staging Changes

- **API diff check**: `hack/apidiff.sh -base master staging/src/k8s.io/client-go`
  must be clean, or `CHANGELOG.md` must document incompatible changes.
- **No breaking changes** to published Go APIs without deprecation.
- **Apply configuration consistency**: Generated apply configs should reflect
  API type changes exactly.
- **Unavoidable Go API breaks from Kubernetes API changes**: When a Kubernetes
  API change inevitably breaks the Go client API (e.g., splitting a struct into
  two), prefer extending
  `hack/apidiff-changelog/api-changes-allowlist` in a **separate PR** rather
  than documenting in `CHANGELOG.md`. The background: Kubernetes API changes
  that break Go types are expected and typically should not be documented as
  client-go changelog entries.
- **Staging module placement for new features**: New alpha-level features belong
  in the `experimental` staging module, not `incubating`. Only promote to
  `incubating` when the feature reaches beta.

### Commit Structure

- **Self-contained commits**: Each commit should be self-contained — code changes
  and their corresponding tests belong in the same commit.
- **Generated code in codegen commits**: `zz_generated.validations.*` files and
  other generated artifacts belong in the codegen/regeneration commit, not in the
  manual API change commit.
- **Squash related manual changes**: All manual API-related changes (types,
  validation, strategy) should be squashed into a single commit so the reviewer
  can see the full picture in one diff without navigating across files.
- **Commit-by-commit review**: PR descriptions should suggest commit-by-commit
  review and use KEP-prefixed commit messages (e.g.,
  `KEP-5941: Add shared consumable capacity API types`).
- **Rebase hygiene**: Rebases can accidentally scatter tests and generated code
  across wrong commits. After each rebase, verify via `git log --all --oneline`
  that tests, validation, and strategy code are still in the same commit as the
  code they test. This is specifically enforced during API review — reviewers
  may refuse to LGTM until the commit history is clean.

---

## Common Review Findings

| Finding | What to check |
|---------|---------------|
| Missing codegen | `zz_generated.*` files not updated after type change |
| Stale OpenAPI spec | `api/openapi-spec/` not regenerated |
| Missing boilerplate | New file lacks Apache 2.0 header |
| Hand-edited generated file | Changes in `zz_generated.*` not matching codegen output |
| Missing validation | New API field has no validation rules |
| Missing feature gate | Alpha feature exposed without gate |
| Broken import aliases | Import uses wrong alias for k8s.io package |
| Missing test | New behavior has no unit/integration test |
| Unstructured logging | Uses `fmt.Printf` or `klog.Infof` instead of `klog.InfoS` |
| Missing CHANGELOG entry | Incompatible client-go change without documentation |
| Dirty worktree artifacts | PR includes unrelated formatting or whitespace changes |
| `null` in JSON output | Missing `omitempty` on pointer field — causes explicit `null` serialization |
| Missing size limit | New list/slice field has no max-size constant or apiserver validation |
| Tests in wrong commit | Unit/validation tests split from the code commit they test |
| Bespoke test helper | Custom helper instead of standard pattern (e.g., `new(resource.MustParse())`) |
| Stale field name in test | Test case uses former field name instead of current name |
| Validation tightened unconditionally | Existing zero-value behavior broken by new stricter validation |
| Struct reuse hiding invalid combos | Same struct used for different API fields — OpenAPI cannot detect forbidden combinations |
| Alpha code in wrong staging module | New alpha feature in `incubating` instead of `experimental` |
| Feature-gate drop missing keepExisting | Strategy `dropDisabled*` doesn't preserve fields already present in old objects |
| Rebase scattered tests | Test commits ended up in wrong commits after a rebase — re-verify test placement after every rebase |

---

## PR Checklist (Reviewer Perspective)

1. Does the PR have a fenced `` ```release-note `` block?
2. Are all `verify-*` checks passing? (boilerplate, gofmt, codegen, openapi, imports)
3. Are generated files regenerated, not hand-edited?
4. Do new API fields have validation, feature gates (if alpha), and descriptions?
5. Are there adequate tests (unit, integration, E2E as appropriate)?
6. Are unit tests in the same commit as the code they test?
7. Does `hack/apidiff.sh` report clean for staging changes?
8. Is the commit message clear and follows Kubernetes conventions?
9. Are there no unrelated changes mixed into the PR?
10. Do new pointer fields use `omitempty` in their JSON tags?
11. Do new list fields have size-limit constants and apiserver validation?
12. Are `dropDisabled*` strategy changes tested with create(2) + update(3) cases?

---

## Reviewer Preferences

- **Small, focused PRs** are preferred over large omnibus changes.
- **Separate codegen commits** from manual code changes (makes review easier).
- **API changes** often require a KEP (Kubernetes Enhancement Proposal) reference.
- **Sig-label** must match the affected area (e.g., `sig/scheduling`, `sig/node`).
- **Squash manual API changes** into one commit — reviewers don't want to navigate
  across many files to find the full set of related manual changes.
- **Top-down function order** — define higher-level functions before their helpers.
- **Standard patterns over custom helpers** — use well-known idioms that every
  reviewer recognizes instead of project-local shortcuts.
- **Explain declarative-validation limitations** — when a tag cannot be used, add
  a source-code comment so the next API reviewer understands why manual validation
  exists.
