---
name: kubernetes-pre-push
description: Run a structured pre-push verification checklist for Kubernetes contributions — lint, codegen, OpenAPI, tests, and regeneration.
---

# Kubernetes Pre-Push Command

Follow the `kubernetes-pre-push` skill from this plugin.

Use the text after the command name as the target scope. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

If no scope was provided, discover the changed packages automatically from `git diff` against the upstream base branch.

Read and follow:
- `skills/kubernetes-pre-push/SKILL.md`
- `projects/kubernetes/VALIDATION.md`
- `projects/kubernetes/CODING.md`
- `projects/kubernetes/REVIEWING.md`

Execute the full Discover → Analyze → Verify → Report workflow. Report a clear pass/fail verdict at the end.
