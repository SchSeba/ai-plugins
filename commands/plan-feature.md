---
name: plan-feature
description: Produce a detailed implementation plan through multi-agent codebase investigation.
---

# Plan Feature Command

Follow the `plan-feature` skill from this plugin.

Use the text after the command name as the feature request. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

If no request was provided, ask the user for the missing feature, bug fix, or change description before proceeding.

Read and follow:
- `skills/plan-feature/SKILL.md`

Execute the full planning workflow: gather context, run multi-subagent investigation, and produce a detailed implementation plan at `docs/plans/{feature-name}-plan.md`.
