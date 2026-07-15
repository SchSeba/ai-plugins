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
   | Vendor / go.mod | `vendor/`, `go.mod`, `go.sum` |
   | CLI commands | `cmd/`, `pkg/**/options/`, `staging/src/k8s.io/kubectl/` |
   | Docs / descriptions | `**/doc.go`, `**/types.go` (doc comments), `docs/` |
   | Metrics | `**/metrics.go`, `staging/src/k8s.io/component-base/metrics/` |
   | Feature gates | `pkg/features/`, `staging/src/k8s.io/apiserver/pkg/features/` |
   | Shell scripts | `*.sh` |
   | Test files | `*_test.go` |
   | Mock files | `**/mocks/`, `**/*_mock.go` |
   | Go source (other) | `*.go` not matching above |
   | Non-Go files | Everything else |

3. **Determine which verification steps are needed** based on the categories present. See the [Verification Step Reference](#verification-step-reference) below.

**Completion criterion:** You have a classified file list and know exactly which verification steps to run.

### Step 3: Run the Always-Required Checks

These checks apply to every push, regardless of what changed.

#### 3.1: Boilerplate Verification

- Run `hack/verify-boilerplate.sh`.
- Ensures all files have the correct license/copyright headers.

#### 3.2: Go Formatting

- Run `hack/verify-gofmt.sh`.
- If it fails, run `hack/update-gofmt.sh` to auto-fix, then re-verify.

#### 3.3: Focused Go Tests

Run tests for the packages that were directly modified.

- Discover the changed Go packages from the diff.
- Run `go test` against those specific packages.
- If a user provided `$ARGUMENTS` with explicit packages, use those instead.

#### 3.4: Lint

Run the linter scoped to the changed packages.

- Discover the lint script at `hack/verify-golangci-lint.sh`.
- Pass only the changed package paths to scope the run.
- If scoping is not supported, run the full lint.

#### 3.5: Codegen Verification

- Run `hack/verify-codegen.sh`.
- This script expects a **clean worktree** (no uncommitted changes to generated files). If it fails because generated files are stale, proceed to Step 4 to regenerate, then re-run this verifier.

#### 3.6: OpenAPI Spec Verification

- Run `hack/verify-openapi-spec.sh`.
- Same clean-worktree requirement as codegen verification.

#### 3.7: Spelling

- Run `hack/verify-spelling.sh`.
- Catches typos in code comments and documentation.

**Completion criterion:** All always-required checks pass, or you have identified which ones failed and why.

### Step 4: Regenerate (If Verifiers Failed or API Types Changed)

Run this step if:
- Any verifier from Step 3 reported stale generated files, OR
- Changed files include API types, generated code, or OpenAPI specs.

Execute regeneration in this order:

1. **Fix Go formatting** — run `hack/update-gofmt.sh`.
   - Always safe to run; auto-corrects formatting.

2. **Regenerate code** — run `hack/update-codegen.sh`.
   - For targeted regeneration when only specific generators are needed, the script supports passing generator names as arguments (e.g., `protobuf`, `deepcopy`, `conversions`, `validation`, `openapi`, `applyconfigs`, `swagger`).
   - If unsure which generators to target, run the full script without arguments.
   - Commonly useful targeted set for API work:
     ```
     hack/update-codegen.sh protobuf deepcopy conversions validation openapi applyconfigs
     ```

3. **Regenerate OpenAPI snapshots** — run `hack/update-openapi-spec.sh`.
   - This script requires `etcd` on PATH. Check `third_party/etcd/` for a local copy — prepend it to PATH if present.

4. **Regenerate API compatibility data** — run `hack/update-generated-api-compatibility-data.sh`.
   - This script may require `protoc` on PATH. Check `third_party/protoc/` for a local copy — prepend it to PATH if present.

5. **Regenerate docs** (if CLI/flag changes) — run `hack/update-generated-docs.sh`.

6. **Regenerate stable metrics** (if metrics changes) — run `hack/update-generated-stable-metrics.sh`.

7. **Regenerate mocks** (if mock interfaces changed) — run `hack/update-mocks.sh`.

8. **Update vendor** (if `go.mod` changed) — run `hack/update-vendor.sh`.

9. **Update feature gates** (if feature gate definitions changed) — run `hack/update-featuregates.sh`.

10. **Re-run the verifiers** from Step 3 (at minimum 3.5 and 3.6) to confirm regeneration resolved the failures.

**Completion criterion:** All verifiers pass after regeneration.

### Step 5: Run Conditional Checks

Run these only when the corresponding file categories were changed.

#### 5.1: API Descriptions Verification

**When:** Changed files include API type definitions (`types.go` with doc comments).

- Run `hack/verify-description.sh`.

#### 5.2: API Groups Verification

**When:** New API groups or resources are added.

- Run `hack/verify-api-groups.sh`.

#### 5.3: Prerelease Lifecycle Tags

**When:** Changed files include API types (lifecycle annotations, alpha/beta markers).

- Run `hack/verify-prerelease-lifecycle-tags.sh`.

#### 5.4: API Compatibility Test

**When:** Changed files include API types or generated protobuf/JSON fixtures.

- Run `go test k8s.io/api` with the compatibility test pattern.
- Requires `protoc` on PATH — check `third_party/protoc/` for a local copy.

#### 5.5: Client-Go API Diff

**When:** Changed files are under `staging/src/k8s.io/client-go/`, or applyconfigurations, or any public Go API in staging modules.

- Run `hack/apidiff.sh` comparing against the base branch for the affected staging modules.
- If the diff reports undocumented incompatible changes, inform the user that `staging/src/k8s.io/client-go/CHANGELOG.md` needs updating.

#### 5.6: Generated Docs Verification

**When:** Changed files include CLI commands, flags, or kubectl code.

- Run `hack/verify-generated-docs.sh`.
- If it fails, run `hack/update-generated-docs.sh`, then re-verify.

#### 5.7: Structured Logging Verification

**When:** Changed Go files contain log statements (`klog.`, `logger.`).

- Run `hack/verify-structured-logging.sh`.

#### 5.8: Generated Stable Metrics Verification

**When:** Changed files include metrics definitions or `component-base/metrics`.

- Run `hack/verify-generated-stable-metrics.sh`.
- If it fails, run `hack/update-generated-stable-metrics.sh`, then re-verify.

#### 5.9: Vendor Verification

**When:** Changed files include `go.mod`, `go.sum`, or `vendor/`.

- Run `hack/verify-vendor.sh`.
- If it fails, run `hack/update-vendor.sh`, then re-verify.

#### 5.10: Feature Gates Verification

**When:** Changed files include feature gate definitions.

- Run `hack/verify-featuregates.sh`.
- If it fails, run `hack/update-featuregates.sh`, then re-verify.

#### 5.11: Flags Underscore Verification

**When:** Changed files add or modify command-line flags.

- Run `hack/verify-flags-underscore.py` (note: Python script, not shell).
- Ensures flag names use hyphens, not underscores.

#### 5.12: Import Verification

**When:** Changed Go source files.

- Run `hack/verify-import-aliases.sh` — checks import alias conventions.
- Run `hack/verify-imports.sh` — checks for forbidden imports.

#### 5.13: Shellcheck

**When:** Changed files include shell scripts (`*.sh`).

- Run `hack/verify-shellcheck.sh`.

#### 5.14: Ginkgo Focus Verification

**When:** Changed test files use Ginkgo framework.

- Run `hack/verify-ginkgo-focus.sh` (if it exists in the repo).
- Catches leftover `FIt`, `FDescribe`, `FContext` focused specs that would skip other tests.

#### 5.15: Mock Verification

**When:** Changed files include mock interfaces or mock definitions.

- Run `hack/verify-mocks.sh`.
- If it fails, run `hack/update-mocks.sh`, then re-verify.

#### 5.16: Integration Tests

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
| Boilerplate (license headers) | ✅/❌ | |
| Go formatting (gofmt) | ✅/❌ | |
| Focused Go tests | ✅/❌ | {packages tested} |
| Lint | ✅/❌ | {scope} |
| Codegen verification | ✅/❌ | |
| OpenAPI spec verification | ✅/❌ | |
| Spelling | ✅/❌ | |
| API descriptions | ✅/⏭️ | {skipped if not applicable} |
| API groups | ✅/⏭️ | |
| Prerelease lifecycle tags | ✅/⏭️ | |
| API compatibility | ✅/⏭️ | |
| Client-go API diff | ✅/⏭️ | |
| Generated docs | ✅/⏭️ | |
| Structured logging | ✅/⏭️ | |
| Stable metrics | ✅/⏭️ | |
| Vendor | ✅/⏭️ | |
| Feature gates | ✅/⏭️ | |
| Flags underscore | ✅/⏭️ | |
| Import verification | ✅/⏭️ | |
| Shellcheck | ✅/⏭️ | |
| Ginkgo focus | ✅/⏭️ | |
| Mock verification | ✅/⏭️ | |
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
| Any Go source | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Imports |
| API types | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Regenerate, Descriptions, API groups, Lifecycle tags, API compat |
| Generated code | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Regenerate (if stale) |
| Staging modules | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | API diff (if client-go) |
| client-go | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | API diff, CHANGELOG check |
| Vendor / go.mod | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Vendor verification |
| CLI commands | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Generated docs, Flags underscore |
| Docs / descriptions | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Descriptions |
| Metrics | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Stable metrics |
| Feature gates | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Feature gates verification |
| Shell scripts | Boilerplate, Spelling | Shellcheck |
| Test files | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Ginkgo focus, Structured logging |
| Mock files | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Mock verification |
| Integration tests | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | Integration test run |
| E2E tests | Boilerplate, Gofmt, Tests, Lint, Codegen, OpenAPI, Spelling | — (E2E runs in CI) |
| Non-Go files | Boilerplate, Spelling | Depends on file type |

---

## Complete Script Reference

All `verify-*` and `update-*` scripts available in the Kubernetes `hack/` directory. The agent should check for the existence of these scripts at the repo root — not all scripts may be present in every Kubernetes version.

### Verifiers (`hack/verify-*.sh`)

| Script | Purpose | When to run |
|--------|---------|-------------|
| `verify-boilerplate.sh` | License/copyright headers | Always |
| `verify-gofmt.sh` | Go source formatting | Always (Go changes) |
| `verify-golangci-lint.sh` | Go linter | Always (Go changes) |
| `verify-codegen.sh` | Generated code freshness | Always |
| `verify-openapi-spec.sh` | OpenAPI spec freshness | Always |
| `verify-spelling.sh` | Spelling in comments/docs | Always |
| `verify-description.sh` | API field descriptions | API types changed |
| `verify-api-groups.sh` | API group registration | New API groups/resources |
| `verify-prerelease-lifecycle-tags.sh` | Alpha/beta lifecycle tags | API types changed |
| `verify-generated-docs.sh` | CLI/kubectl docs | CLI commands/flags changed |
| `verify-generated-stable-metrics.sh` | Stable metrics definitions | Metrics code changed |
| `verify-vendor.sh` | Vendor directory consistency | go.mod/vendor changed |
| `verify-featuregates.sh` | Feature gate definitions | Feature gates changed |
| `verify-flags-underscore.py` | Flag naming (hyphens not underscores) | Command flags changed |
| `verify-import-aliases.sh` | Import alias conventions | Go files changed |
| `verify-imports.sh` | Forbidden import checks | Go files changed |
| `verify-structured-logging.sh` | Structured logging compliance | Log statements changed |
| `verify-shellcheck.sh` | Shell script linting | Shell scripts changed |
| `verify-mocks.sh` | Mock freshness | Mock interfaces changed |
| `verify-typecheck.sh` | Cross-platform type checking | Go files changed |
| `verify-no-vendor-cycles.sh` | Vendor dependency cycles | Vendor changed |
| `verify-vendor-licenses.sh` | Vendor license compliance | Vendor changed |
| `verify-golangci-lint-config.sh` | Lint config consistency | Lint config changed |
| `verify-conformance-yaml.sh` | Conformance test YAML | Conformance tests changed |
| `verify-e2e-test-ownership.sh` | E2E test ownership labels | E2E tests changed |
| `verify-test-code.sh` | Test code conventions | Test files changed |
| `verify-test-featuregates.sh` | Test feature gate usage | Test files changed |
| `verify-prometheus-imports.sh` | Prometheus import conventions | Metrics imports changed |
| `verify-publishing-bot.sh` | Publishing bot config | Staging repos changed |
| `verify-staging-meta-files.sh` | Staging module metadata | Staging modules changed |
| `verify-internal-modules.sh` | Internal module consistency | Internal modules changed |
| `verify-readonly-packages.sh` | Read-only package protection | Protected packages changed |
| `verify-owners-fmt.sh` | OWNERS file formatting | OWNERS files changed |
| `verify-pkg-names.sh` | Package naming conventions | New packages added |
| `verify-cli-conventions.sh` | CLI flag/command conventions | CLI code changed |

### Generators (`hack/update-*.sh`)

| Script | Purpose | When to run |
|--------|---------|-------------|
| `update-codegen.sh` | Regenerate all generated code | API types/generated files stale |
| `update-openapi-spec.sh` | Regenerate OpenAPI specs (needs etcd) | OpenAPI specs stale |
| `update-generated-api-compatibility-data.sh` | Regenerate API compat fixtures (needs protoc) | API types changed |
| `update-gofmt.sh` | Auto-fix Go formatting | gofmt verification failed |
| `update-generated-docs.sh` | Regenerate CLI docs | CLI docs stale |
| `update-generated-stable-metrics.sh` | Regenerate stable metrics | Metrics defs stale |
| `update-vendor.sh` | Update vendor directory | go.mod changed |
| `update-mocks.sh` | Regenerate mock files | Mock interfaces changed |
| `update-featuregates.sh` | Regenerate feature gate lists | Feature gates changed |
| `update-golangci-lint-config.sh` | Regenerate lint config | Lint config stale |
| `update-conformance-yaml.sh` | Regenerate conformance YAML | Conformance tests changed |
| `update-import-aliases.sh` | Update import alias config | Import aliases changed |
| `update-internal-modules.sh` | Update internal module refs | Internal modules changed |
| `update-owners-fmt.sh` | Format OWNERS files | OWNERS files changed |
| `update-translations.sh` | Update translation files | User-facing strings changed |
| `update-all.sh` | Run ALL update scripts | Full regeneration needed |

### Other Useful Scripts

| Script | Purpose |
|--------|---------|
| `install-etcd.sh` | Install etcd for integration tests |
| `apidiff.sh` | Check API compatibility diff against a base branch |
| `verify-all.sh` | Run ALL verify scripts (slow, comprehensive) |

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
- **Check script existence.** Not all scripts exist in every Kubernetes version. Before running a script, verify it exists at the expected path. Skip gracefully if absent and note it in the summary.
- **update-all.sh as a fallback.** If many verifiers fail or you are unsure which generators to run, `hack/update-all.sh` runs every update script. It is slow but comprehensive.
- **Python scripts.** Some verifiers are Python scripts (e.g., `verify-flags-underscore.py`). Ensure Python is available before running them.
