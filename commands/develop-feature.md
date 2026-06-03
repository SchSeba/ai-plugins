---
name: develop-feature
description: Plan, implement, and review a feature request, bug fix, or change specification.
---

# Develop Feature Command

Follow the `develop-feature` skill from this plugin.

Use the text after the command name as the feature request. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

If no request was provided, ask the user for the missing feature, bug fix, or change description before proceeding.

Read and follow:
- `skills/develop-feature/SKILL.md`
- `skills/review-engine/SKILL.md`
- `skills/review-engine/review-perspectives.md`

Execute the full Plan -> Code -> Review loop. Save the plan, implement the change, run verification, and iterate until the review returns `APPROVED` or the skill reaches its maximum iteration count.
