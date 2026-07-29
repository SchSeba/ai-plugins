---
name: kubernetes-pre-push
description: Run a structured pre-push verification checklist for Kubernetes contributions. Analyzes changed files, determines which verifiers and generators apply, and executes them in dependency order. Use when preparing to push a Kubernetes commit, running pre-push checks, or verifying changes before submitting a PR to kubernetes/kubernetes.
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

- `$ARGUMENTS` — Optional. Specific packages or directories to check. If omitted, the skill discovers changed files from `git diff` against the upstream base branch and determines the scope automatically.

---

## Project Knowledge

Read the Kubernetes project knowledge files **before** starting:

- `projects/kubernetes/VALIDATION.md` — all `hack/verify-*.sh` and `hack/update-*.sh` scripts, pre-push sequences, PATH requirements, test commands
- `projects/kubernetes/CODING.md` — coding conventions, API change workflows, code generation patterns
- `projects/kubernetes/REVIEWING.md` — review standards, common findings, PR checklist

These files are the authoritative reference. The workflow below delegates to
them for the exact commands and flags.

---

## Workflow

### Step 1: Discover the Environment

1. **Locate the Kubernetes repository root.** Look for `hack/verify-codegen.sh`,
   `hack/verify-golangci-lint.sh`, and `staging/` as signals.
2. **Determine the base branch.** Default to `master`. Run
   `git merge-base HEAD <base>` to find the common ancestor.

**Completion criterion:** You know the repo root, the base branch, and the merge-base commit.

### Step 2: Analyze Changed Files

1. Get the diff stat against the merge-base.
2. Classify each changed file into categories:
   - **API types** — `staging/src/k8s.io/api/`, `pkg/apis/`
   - **Generated code** — `zz_generated.*` files
   - **Validation** — `pkg/apis/*/validation/`
   - **Scheduler / plugins** — `pkg/scheduler/`
   - **Client-go / staging** — `staging/src/k8s.io/client-go/`
   - **Test code** — `test/integration/`, `test/e2e/`
   - **Feature gates** — `pkg/features/`
   - **Documentation** — API comments, CLI docs
   - **Other Go code** — everything else

**Completion criterion:** You have a categorized list of changed files and know which verification tracks apply.

### Step 3: Execute Verification

Refer to `projects/kubernetes/VALIDATION.md` for the exact commands.

Follow this dependency order:

1. **Regenerate first** (if API types or generated code changed):
   - `hack/update-codegen.sh` with appropriate targets
   - `hack/update-openapi-spec.sh` (needs etcd on PATH)
   - `hack/update-generated-api-compatibility-data.sh` (needs protoc on PATH)

2. **Verify** (always):
   - `hack/verify-boilerplate.sh`
   - `hack/verify-gofmt.sh`
   - `hack/verify-golangci-lint.sh` (scoped to changed packages)
   - `hack/verify-imports.sh`
   - `hack/verify-codegen.sh` (if API/generated files changed)
   - `hack/verify-openapi-spec.sh` (if API files changed)
   - `hack/verify-description.sh` (if API comments changed)
   - `hack/verify-featuregates.sh` (if feature gates changed)

3. **Test** (scoped):
   - `go test` on changed packages
   - API compatibility tests (if API types changed)
   - Integration tests (if integration test files changed)

4. **API diff** (if staging/client-go changed):
   - `hack/apidiff.sh -base master staging/src/k8s.io/client-go`

### Step 4: Report Results

Present a summary table:

| Step | Result | Notes |
|------|--------|-------|
| verify-boilerplate | ✅ / ❌ | |
| verify-gofmt | ✅ / ❌ | |
| ... | ... | ... |

If any step failed, explain what went wrong and suggest the fix (usually
running the matching `hack/update-*.sh` script).

**Completion criterion:** The user has a clear pass/fail verdict with actionable next steps for any failures.
