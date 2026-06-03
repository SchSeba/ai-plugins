---
name: jira-cli
description: Run Jira task and epic lookup workflows through the jira-cli skill.
---

# Jira CLI Command

Follow the `jira-cli` skill from this plugin.

Use the text after the command name as the skill input. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

Supported workflows:
- `get_my_tasks [PROJECT] [LIMIT]`
- `get_my_epics [VERSION] [PROJECT] [LIMIT]`

Read and follow:
- `skills/jira-cli/SKILL.md`

If the user did not provide a subcommand, ask which Jira workflow they want to run and suggest the supported options above.
