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

## Dev-Task Review Variants

When used inside the bytebot dev-task engine, two specialized review modes are available:

| Variant | File | When |
|---------|------|------|
| Review Own PR | [review-own-pr.md](review-own-pr.md) | Reviewing changes the agent itself produced (own_pr / issue origin) |
| Review External PR | [review-external-pr.md](review-external-pr.md) | Reviewing a PR authored by someone else (external_pr origin) |

Both variants use the reusable review workflow in [../review-engine/SKILL.md](../review-engine/SKILL.md) and the perspective criteria in [../review-engine/review-perspectives.md](../review-engine/review-perspectives.md).

If another skill needs the same review phase, reuse `review-engine` instead of duplicating the workflow.
