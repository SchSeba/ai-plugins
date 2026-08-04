---
name: develop-feature
description: Implement and review a feature using an approved plan. Run plan-feature first if no plan exists.
---

# Develop Feature Command

This command first runs `plan-feature` to produce an implementation plan, then executes `develop-feature` for implementation, review, and validation.

Use the text after the command name as the feature request. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

If no request was provided, ask the user for the missing feature, bug fix, or change description before proceeding.

## Step 1: Plan

If a plan file already exists at `docs/plans/{feature-name}-plan.md`, skip to Step 2.

Otherwise, read and follow:
- `skills/plan-feature/SKILL.md`

Wait for user approval of the plan before proceeding.

## Step 2: Implement, Review, Validate

Read and follow:
- `skills/develop-feature/SKILL.md`
- `skills/review-engine/SKILL.md`
- `skills/review-engine/review-perspectives.md`

Execute the Code -> Review -> Validate loop. Iterate until the review returns `APPROVED` or the skill reaches its maximum iteration count.
