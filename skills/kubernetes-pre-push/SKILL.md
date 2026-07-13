---
name: kubernetes-pre-push
description: Run a structured pre-push verification checklist for Kubernetes contributions. Discovers which verifiers, codegen scripts, and test commands apply based on what files changed, then executes them in dependency order. Use when preparing to push a Kubernetes commit, running pre-push checks, or verifying K8s changes before submitting a PR.
---

# Kubernetes Pre-Push

A structured verification workflow for Kubernetes repository contributions.
Analyzes the changed files in your working tree, determines which verification
steps apply, and executes them in the correct dependency order — regenerating
code before verifying, running focused tests before broad integration suites.

## When to Use

- Before pushing commits to a Kubernetes fork or upstream branch.
- After regenerating code and wanting to verify everything is consistent.
- When preparing a PR against `kubernetes/kubernetes` and need confidence that CI will pass.

## Arguments

- `$ARGUMENTS` — Optional. Specific packages or directories to check (e.g., `./pkg/apis/resource/...`). If omitted, the skill discovers changed files from `git diff` against the upstream base branch and determines the scope automatically.

---

## Workflow

### Step 1: Discover the Environment

1. **Locate the Kubernetes repository root.**
   - Look for `hack/verify-codegen.sh`, `hack/verify-golangci-lint.sh`, and `staging/` as signals.
   - If the current directory is not a Kubernetes checkout, ask the user for the path.

2. **Read project conventions.**
   - Check for `AGENTS.md`, `CONTRIBUTING.md`, or `README.md` at the repo root.
   - Note any project-specific verification requirements.

3. **Determine the base branch.**
   - Default to `master`. If the user specifies a different base, use that.
   - Run `git merge-base HEAD <base>` to find the common ancestor.

**Completion criterion:** You know the repo root, the base branch, and the merge-base commit.

### Step 2: Analyze Changed Files

1. **Get the diff stat** against the merge-base.
   - Collect the list of changed files.

2. **Classify each changed file** into one or more categories:

   | Category | File patterns |
   |----------|--------------|
   | API types | `pkg/apis/*/types.go`, `staging/src/k8s.io/api/*/types.go` |
   | API validation | `pkg/apis/*/validation/` |
   | Generated code | `**/zz_generated*`, `**/generated.pb.go`, `**/*_generated.go` |
   | OpenAPI | `api/openapi-spec/`, `pkg/generated/openapi/` |
   | Staging modules | `staging/src/k8s.io/*/` |
   | client-go | `staging/src/k8s.io/client-go/` |
   | Scheduler plugins | `pkg/scheduler/framework/plugins/` |
   | Integration tests | `test/integration/` |
   | E2E tests | `test/e2e/`, `test/e2e_*/` |
   | Go source (other) | `*.go` not matching above |
   | Non-Go files | Everything else |

3. **Determine which verification steps are needed** based on the categories present. See the [Verification Step Reference](#verification-step-reference) below.

**Completion criterion:** You have a classified file list and know exactly which verification steps to run.

### Step 3: Run the Always-Required Checks

These checks apply to every push, regardless of what changed.

#### 3.1: Focused Go Tests

Run tests for the packages that were directly modified.

- Discover the changed Go packages from the diff.
- Run `go test` against those specific packages.
- If a user provided `$ARGUMENTS` with explicit packages, use those instead.

#### 3.2: Lint

Run the linter scoped to the changed packages.

- Discover the lint script at `hack/verify-golangci-lint.sh`.
- Pass only the changed package paths to scope the run.
- If scoping is not supported, run the full lint.

#### 3.3: Codegen Verification

- Run `hack/verify-codegen.sh`.
- This script expects a **clean worktree** (no uncommitted changes to generated files). If it fails because generated files are stale, proceed to Step 4 to regenerate, then re-run this verifier.

#### 3.4: OpenAPI Spec Verification

- Run `hack/verify-openapi-spec.sh`.
- Same clean-worktree requirement as codegen verification.

**Completion criterion:** All four checks pass, or you have identified which ones failed and why.

### Step 4: Regenerate (If Verifiers Failed or API Types Changed)

Run this step if:
- Any verifier from Step 3 reported stale generated files, OR
- Changed files include API types, generated code, or OpenAPI specs.

Execute regeneration in this order:

1. **Regenerate code** — run `hack/update-codegen.sh`.
   - For targeted regeneration when only specific generators are needed, the script supports passing generator names as arguments (e.g., `protobuf`, `deepcopy`, `conversions`, `validation`, `openapi`, `applyconfigs`).
   - If unsure which generators to target, run the full script without arguments.

2. **Regenerate OpenAPI snapshots** — run `hack/update-openapi-spec.sh`.
   - This script requires `etcd` on PATH. Check `third_party/etcd/` for a local copy — prepend it to PATH if present.

3. **Regenerate API compatibility data** — run `hack/update-generated-api-compatibility-data.sh`.
   - This script may require `protoc` on PATH. Check `third_party/protoc/` for a local copy — prepend it to PATH if present.

4. **Re-run the verifiers** from Step 3 (3.3 and 3.4 at minimum) to confirm regeneration resolved the failures.

**Completion criterion:** All verifiers pass after regeneration.

### Step 5: Run Conditional Checks

Run these only when the corresponding file categories were changed.

#### 5.1: API Descriptions Verification

**When:** Changed files include API type definitions (`types.go` with doc comments).

- Run `hack/verify-description.sh`.

#### 5.2: API Compatibility Test

**When:** Changed files include API types or generated protobuf/JSON fixtures.

- Run `go test k8s.io/api` with the compatibility test pattern.
- Requires `protoc` on PATH — check `third_party/protoc/` for a local copy.

#### 5.3: Client-Go API Diff

**When:** Changed files are under `staging/src/k8s.io/client-go/`, or applyconfigurations, or any public Go API in staging modules.

- Run `hack/apidiff.sh` comparing against the base branch for the affected staging modules.
- If the diff reports undocumented incompatible changes, inform the user that `staging/src/k8s.io/client-go/CHANGELOG.md` needs updating.

#### 5.4: Integration Tests

**When:** Changed files include integration test code, or the user explicitly requests integration tests.

- Integration tests require `etcd`. Check `third_party/etcd/` — if present, prepend to PATH. Otherwise, run `hack/install-etcd.sh` first.
- Run `go test` for the affected integration test packages with `etcd` on PATH.
- For targeted test runs, the user can specify a test name pattern (e.g., `-run 'TestDRA/all/SharedConsumableCapacity$'`).

**Completion criterion:** All applicable conditional checks pass.

### Step 6: Final Summary

Present the results to the user:

```text
## Pre-Push Verification Summary

### Changed Files
- {count} files changed across {count} packages

### Categories Detected
- {list of categories from Step 2}

### Checks Executed
| Check | Result | Notes |
|-------|--------|-------|
| Focused Go tests | ✅/❌ | {packages tested} |
| Lint | ✅/❌ | {scope} |
| Codegen verification | ✅/❌ | |
| OpenAPI spec verification | ✅/❌ | |
| API descriptions | ✅/⏭️ | {skipped if not applicable} |
| API compatibility | ✅/⏭️ | |
| Client-go API diff | ✅/⏭️ | |
| Integration tests | ✅/⏭️ | |

### Regeneration
- {whether regeneration was needed and what was regenerated}

### Issues Found
- {list of unresolved issues, if any}

### Verdict
✅ Ready to push / ❌ Issues need attention
```

**Completion criterion:** The summary is presented and all passing checks are confirmed.

---

## Verification Step Reference

Quick reference for which steps to run based on changed file categories:

| Changed category | Always-required | Conditional steps |
|-----------------|----------------|-------------------|
| Any Go source | Tests, Lint, Codegen, OpenAPI | — |
| API types | Tests, Lint, Codegen, OpenAPI | Regenerate, Descriptions, API compat |
| Generated code | Tests, Lint, Codegen, OpenAPI | Regenerate (if stale) |
| Staging modules | Tests, Lint, Codegen, OpenAPI | API diff (if client-go) |
| client-go | Tests, Lint, Codegen, OpenAPI | API diff, CHANGELOG check |
| Integration tests | Tests, Lint, Codegen, OpenAPI | Integration test run |
| E2E tests | Tests, Lint, Codegen, OpenAPI | — (E2E runs in CI) |
| Non-Go files | — | Depends on file type |

---

## Guidelines

- **Order matters.** Regenerate before verifying. Verify before testing. Focused tests before integration tests. This saves time by catching issues early.
- **Clean worktree for verifiers.** The `verify-codegen.sh` and `verify-openapi-spec.sh` scripts expect no uncommitted generated file changes. If they fail due to staleness, regenerate first, commit the generated files, then re-run.
- **etcd and protoc from third_party.** The Kubernetes repo bundles `etcd` and `protoc` under `third_party/`. Always check there before asking the user to install them system-wide. Prepend to PATH rather than installing globally.
- **Scope when possible.** Scoped lint and test runs are dramatically faster than full-repo runs. Always pass only the affected packages.
- **Release notes are manual.** There is no automated release-note verifier. Remind the user to ensure their PR body contains a fenced `` ```release-note `` block.
- **Integration tests are optional locally.** They require `etcd` and take significant time. Offer to run them but do not block the push verdict on them unless the user explicitly requests it.
- **E2E tests run in CI only.** Do not attempt to run E2E tests locally — they require a full cluster. Note any E2E test file changes in the summary so the user knows CI will exercise them.
- **Do not hardcode package paths.** Discover changed packages from `git diff`. The examples in this skill's description are illustrative — always derive the actual paths from the working tree.
