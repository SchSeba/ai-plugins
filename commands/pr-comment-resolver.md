---
name: pr-comment-resolver
description: Resolve actionable pull request review comments one-by-one with explicit user approval.
---

# PR Comment Resolver Command

Follow the `pr-comment-resolver` skill from this plugin.

Use the text after the command name as the skill input. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

Expected input:

```text
[repo-folder(optional)] <pull-request-link>
```

Read and follow:
- `skills/pr-comment-resolver/SKILL.md`

If the user did not provide a pull request link, ask for it before proceeding.
