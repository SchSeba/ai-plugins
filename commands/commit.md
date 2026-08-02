---
name: commit
description: Commit staged changes with a conventional-commit message. Use when committing, creating a commit, or saving changes.
---

# Commit Command

Create a well-formatted git commit using conventional commit format.

Use the text after the command name as an optional hint for the commit message. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

## Workflow

### 1. Read Project Guidelines (MANDATORY — Do This FIRST)

Before any work, read the project's best-practices, contribution guidelines, and any previously learned knowledge:

1. **Read `.ai-rules/`** — If the target project has an `.ai-rules/` directory, read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain previously learned knowledge about this project — coding conventions, validation commands, and review patterns discovered during past sessions. **This is the highest-priority source** because it reflects confirmed, project-specific knowledge.
2. **Read `projects/<project-name>/`** — If this plugin repository has a `projects/<project-name>/` directory (where `<project-name>` matches the target project's repo name), read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain knowledge shared across all skills in this plugin, discovered during past sessions with this project.
3. **Read `AGENTS.md`** — This is the primary source of project conventions, architecture rules, and agent-specific instructions. If this file exists, its rules override any defaults in this skill.
4. **Read `CONTRIBUTING.md`** — Contribution workflow, PR format, commit conventions.
5. **Read `CLAUDE.md`** or equivalent — Additional AI-agent instructions the project maintainers have set.
6. **Read `Makefile` / build scripts** — Understand the build, test, and lint commands available.
7. **Read linting configs** — `.golangci.yml`, `.eslintrc`, `pyproject.toml`, `rustfmt.toml`, etc.

> **Rule:** If any of these files exist and contain instructions, you MUST follow them. Project-specific conventions always take precedence over the generic guidelines in this skill.

### 2. Pre-commit checks

Unless the user passed `--no-verify`:
- Run whatever lint, format, and test checks the project defines based on the guidelines discovered in Step 1. Do **not** assume specific targets — use the ones you found.
- If any check fails, report the failure and stop. Do not commit broken code.

### 3. Stage files

- Check for staged files with `git diff --cached --name-only`.
- If nothing is staged, show the list of modified files and ask the user what to stage — how many commits they would like, and which files belong in each commit.

### 4. Analyze the diff

- Read the staged diff with `git diff --cached`.
- Identify the logical change: what was added, modified, or removed and why.

### 5. Detect multiple logical changes

- If the staged diff contains multiple distinct, unrelated changes (e.g., a bug fix and a new feature), suggest splitting into separate commits.
- List the distinct changes and ask the user whether to proceed as one commit or split.
- Each independent commit must compile on its own and contain a single logical change.

### 6. Build the commit message

Format: `<type>(<optional scope>): <subject>`

**Rules:**
- Present tense, imperative mood ("add feature" not "added feature").
- First line under 72 characters.
- Scope is optional — use when the change is clearly scoped to a module, package, or component.
- If the `$ARGUMENTS` hint is provided, use it to guide the message but still base it on the actual diff.

### 7. Confirm and commit

- Present the proposed commit message to the user.
- Wait for confirmation before running `git commit`.
- If the user suggests edits, incorporate them and re-confirm.
