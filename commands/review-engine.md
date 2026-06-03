---
name: review-engine
description: Run the reusable low-level review engine directly on the current diff or on explicitly supplied review context.
---

# Review Engine Command

Follow the `review-engine` skill from this plugin.

Use the text after the command name as the review context. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

Read and follow:
- `skills/review-engine/SKILL.md`
- `skills/review-engine/review-perspectives.md`

Default behavior:
- If the user supplied specific review context, use it.
- Otherwise, review the current repository diff.

Prefer `/code-review` for normal pull request or local review workflows. Use this command when the user explicitly wants the shared review engine directly.
