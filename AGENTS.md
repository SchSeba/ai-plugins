# AGENTS.md

Repository conventions and rules for AI agents working in the `ai-plugins` repository.

## Repository Overview

This repository contains a curated collection of markdown-based skills and commands for AI coding agents. Skills provide step-by-step instructions for workflows like code review, feature development, Jira integration, and PR comment resolution. Commands are lightweight entry points that route user input to the appropriate skill.

The plugin is designed to work with Claude Code, Cursor, and any agent that supports MCP servers.

## Directory Layout

```
ai-plugins/
├── AGENTS.md              # This file — conventions and rules
├── README.md              # Project README with skills/commands catalog
├── .mcp.json              # MCP server configuration
├── .claude-plugin/        # Claude Code plugin registration
├── .cursor-plugin/        # Cursor IDE plugin registration
├── skills/                # Skill definitions (one directory per skill)
│   └── <skill-name>/
│       └── SKILL.md       # Main skill file (required)
└── commands/              # Command entry points (one file per command)
    └── <skill-name>.md
```

## Skill Conventions

### File Structure

- Each skill lives in `skills/<skill-name>/SKILL.md`.
- The directory name is `kebab-case` and matches the `name` field in the YAML frontmatter.
- Supporting files (reference docs, examples, scripts) can be placed alongside `SKILL.md`.

### Frontmatter Format

Every `SKILL.md` must start with YAML frontmatter:

```yaml
---
name: <skill-name>
description: <What it does>. Use when <specific triggers>.
---
```

- `name` — must match the directory name exactly.
- `description` — the only thing the agent sees when choosing which skill to load. First sentence states the capability, second sentence lists trigger phrases. Max 1024 characters.

### Cross-Skill Referencing

- Reference other skills using relative paths: `../review-engine/SKILL.md`.
- The `review-engine` skill is the shared review workflow — reuse it instead of duplicating review logic.

## Command Conventions

- Commands live in `commands/<skill-name>.md`.
- Same YAML frontmatter pattern (`name`, `description`).
- Commands route to their skill with a `Read and follow:` section pointing to `skills/<skill-name>/SKILL.md`.
- Commands parse `$ARGUMENTS` from user input.

## Plugin Registration

- `.claude-plugin/plugin.json` defines the plugin metadata, skills directory, commands directory, and MCP servers.
- `.cursor-plugin/` provides Cursor IDE integration.
- `.mcp.json` configures MCP servers (currently GitHub MCP).

---

## Rules

The following rules are **mandatory** for all AI agents working in this repository.

### Rule 1: README Maintenance (Blocking)

Every new skill and command **MUST** be added to `README.md`. This is a **blocking requirement** — a PR that adds a skill or command without updating `README.md` **MUST NOT** be merged.

When adding a new skill:
1. Add a row to the **Available Skills** table in alphabetical order.
2. Add a row to the **Commands** table in alphabetical order (if the skill has a command).
3. Add a dedicated section for the skill under the skills table (in alphabetical order) with description and usage examples.
4. Update the directory tree in the **Project Structure** section to include the new files.
5. Add the skill to the **Table of Contents**.

The format for each table row is:

```markdown
<!-- Skills table -->
| [<skill-name>](#<skill-name>) | <short description> | [`skills/<skill-name>/`](skills/<skill-name>/) |

<!-- Commands table -->
| <skill-name> | <short description> | [`commands/<skill-name>.md`](commands/<skill-name>.md) |
```

**Do not skip this step.** The README is the canonical catalog of all skills and commands in this repository. If you forget, the reviewer will send you back.

### Rule 2: Use write-a-skill for New Skills

When creating a new skill, **ALWAYS** read and follow `skills/write-a-skill/SKILL.md` first.

This skill provides the complete workflow:
1. Gather requirements from the user (including invocation design and branching).
2. Create the skill directory and `SKILL.md` with proper frontmatter.
3. Write the body using the information hierarchy — steps on top, reference below, disclosed reference behind context pointers.
4. Write a description that front-loads a leading word and lists one trigger per branch.
5. Create the matching command file in `commands/`.
6. Update `README.md` with the new entries.
7. Run the review checklist — including checks for no-ops, duplication, completion criteria, and progressive disclosure.

The skill also includes a `GLOSSARY.md` with the domain vocabulary for skill authoring (predictability, leading words, information hierarchy, failure modes, etc.).

Do not create skills ad-hoc. The `write-a-skill` skill ensures consistency and predictability across all skills in this repository.

### Rule 3: No Hardcoded Commands

Skills **MUST NOT** hardcode specific make targets, CLI commands, or tool invocations as defaults.

- **Do**: Instruct the agent to discover the correct commands by reading `AGENTS.md`, `Makefile`, or equivalent project configuration files.
- **Don't**: Write instructions like "Run `make lint test build-all`" or "Execute `go test ./...`".
- **Exception**: Negative examples (what NOT to do) are acceptable for clarity.

Even "example" commands in parentheses bias the agent toward using those specific targets instead of discovering the right ones from the project.
