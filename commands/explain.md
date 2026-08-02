---
name: explain
description: Explain the current pull request in plain language for reviewers and teammates.
---

# Explain Command

Follow the `explain-pr` skill from this plugin.

Use the text after the command name as the input. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

Read and follow:
- `skills/explain-pr/SKILL.md`

If extra input is provided, pass it as additional context to the skill — the user may want the explanation focused on a specific aspect (e.g. "focus on the API changes" or "explain for a frontend engineer").

If the current workspace is not a git repository and no PR context is available, tell the user and ask them to run the command from inside a project with an active PR.
