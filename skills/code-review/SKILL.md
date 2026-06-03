---
name: code-review
description: Review pull requests and local changes with reusable multi-perspective review workflows. Use when the user asks to review a PR, review local changes, review-pr, review-change, code review, or merge request review.
---

# Code Review

Multi-perspective code review with two commands:

| Command | Description |
|---------|-------------|
| `review-change [project-path]` | Review uncommitted or staged changes in the current or specified project |
| `review-pr <pr-url>` | Review a GitHub pull request |

## Command Routing

- `review-change` - follow [review-change.md](review-change.md)
- `review-pr` - follow [review-pr.md](review-pr.md)

Both commands use the reusable review workflow in [../review-engine/SKILL.md](../review-engine/SKILL.md) and the perspective criteria in [../review-engine/review-perspectives.md](../review-engine/review-perspectives.md).

If another skill needs the same review phase, reuse `review-engine` instead of duplicating the workflow.
