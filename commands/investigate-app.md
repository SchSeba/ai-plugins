---
name: investigate-app
description: Investigate a running production application for bugs, performance issues, stability problems, and optimization opportunities by analyzing pod logs and Jaeger traces.
---

# Investigate App Command

Follow the `investigate-app` skill from this plugin.

Use the text after the command name as the input. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

Parse the input for:
- **kubectl log commands** — one or more `kubectl logs ...` commands (required)
- **`--jaeger <endpoint>`** — Jaeger UI endpoint for trace analysis (optional)
- **`--services <service-list>`** — comma-separated service names in Jaeger (optional)

Read and follow:
- `skills/investigate-app/SKILL.md`
- `skills/investigate-app/analysis-perspectives.md`

If the input does not contain at least one kubectl logs command, ask the user how to access the application's pod logs before proceeding.
