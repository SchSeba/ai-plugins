---
name: code-refactor
description: Refactor and improve code quality across a project using parallel specialized sub-agents with a safety-first iterative approach.
---

# Code Refactor Command

Follow the `code-refactor` skill from this plugin.

Use the text after the command name as the refactoring scope. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

If no scope was provided, default to "full project" — comprehensive refactoring coverage of the entire codebase.

Read and follow:
- `skills/code-refactor/SKILL.md`
- `skills/code-refactor/refactor-perspectives.md` (index — maps file patterns to domain checklists)
- Domain-specific checklists under `skills/code-refactor/perspectives/*.md` — load on-demand based on which domains are present in the target project
- `skills/review-engine/SKILL.md`
- `skills/review-engine/review-perspectives.md`

Execute the full Analyze → Plan → Refactor → Verify loop. Save the analysis and plan, spawn specialized sub-agents, run verification, and iterate until all planned rounds are complete or the skill reaches its maximum iteration count.
