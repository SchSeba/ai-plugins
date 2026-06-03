---
name: code-review
description: Review local changes or a pull request using the shared multi-perspective review workflow.
---

# Code Review Command

Follow the `code-review` skill from this plugin.

Use the text after the command name as the input. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

Route the request like this:
- If no input was provided, review local changes in the current workspace.
- If the input looks like a GitHub pull request URL, run the pull request review workflow.
- Otherwise, treat the input as an optional project path and run the local review workflow there.

Read and follow:
- `skills/code-review/SKILL.md`
- `skills/code-review/review-change.md`
- `skills/code-review/review-pr.md`
- `skills/review-engine/SKILL.md`
- `skills/review-engine/review-perspectives.md`

If the input is ambiguous, ask one short clarifying question before proceeding.
