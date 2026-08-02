---
name: explain-pr
description: Explain a pull request in plain language — summarise purpose, key changes, technical details, impact, and what to test. Use when the user asks to explain a PR, summarise a pull request, understand what a PR does, or describe changes in a merge request.
---

# Explain PR

Produce a structured, plain-language explanation of the current pull request so reviewers and teammates can understand _what_ changed, _why_, and _what to watch for_ — without reading every line of diff.

## Workflow

### Step 1: Read Project Guidelines (MANDATORY — Do This FIRST)

Before any analysis, read the project's best-practices, contribution guidelines, and any previously learned knowledge:

1. **Read `.ai-rules/`** — If the target project has an `.ai-rules/` directory, read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain previously learned knowledge about this project — coding conventions, validation commands, and review patterns discovered during past sessions. **This is the highest-priority source** because it reflects confirmed, project-specific knowledge.
2. **Read `projects/<project-name>/`** — If this plugin repository has a `projects/<project-name>/` directory (where `<project-name>` matches the target project's repo name), read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain knowledge shared across all skills in this plugin, discovered during past sessions with this project.
3. **Read `AGENTS.md`** — This is the primary source of project conventions, architecture rules, and agent-specific instructions. If this file exists, its rules override any defaults in this skill.
4. **Read `CONTRIBUTING.md`** — Contribution workflow, PR format, commit conventions.
5. **Read `CLAUDE.md`** or equivalent — Additional AI-agent instructions the project maintainers have set.
6. **Read `Makefile` / build scripts** — Understand the build, test, and lint commands available.
7. **Read linting configs** — `.golangci.yml`, `.eslintrc`, `pyproject.toml`, `rustfmt.toml`, etc.

> **Rule:** If any of these files exist and contain instructions, you MUST follow them. Project-specific conventions always take precedence over the generic guidelines in this skill.

### Step 2: Gather Context

Collect PR metadata and diff content. Use whichever sources are available — prefer richer data when possible.

**PR metadata (preferred):** Use the GitHub MCP server or repository management tools to fetch:
- Title, body / description
- Labels, base branch → head branch
- Linked issues or references mentioned in the body

If PR metadata tools are unavailable (e.g. working inside a plain worktree), fall back to:
- `git log` between the merge-base and HEAD for commit messages
- Branch name for hints about purpose

**Completion criterion:** You have the PR title, description (or commit messages), and know the base/head branches.

### Step 3: Understand the Diff

Run a diff between the base branch and the PR head.

1. List changed files with their status (added / modified / deleted / renamed).
2. Classify files into categories: production code, tests, configuration, documentation, CI/build, dependencies.
3. Note the approximate size — number of files changed and lines added/removed.
4. Read the full diff content to understand the substance of the changes.

**Completion criterion:** You can describe every changed file's role and the overall scope of the diff.

### Step 4: Produce the Explanation

Write a structured explanation with the following sections. Keep language accessible — aim for a teammate who knows the project but has not seen this PR yet.

#### 1. Overview
- One or two sentences: what is the main purpose of this PR?
- What problem does it solve, or what feature does it add?

#### 2. Key Changes
Group changes into whichever categories apply:
- **Features** — new capabilities or behaviours
- **Fixes** — bugs or regressions addressed
- **Refactors** — structural improvements without behaviour change
- **Breaking changes** — anything that alters public API, config format, or external behaviour

For each item, give a brief plain-language description. Reference file paths where helpful.

#### 3. Technical Details
- Architecture or design decisions (e.g. new abstractions, patterns chosen)
- Dependencies added, removed, or bumped
- Configuration or environment changes
- Migration steps (if any)

Omit this section if the PR is simple enough that Key Changes covers everything.

#### 4. Impact
- Which subsystems, services, or modules are affected?
- Potential side effects or edge cases
- Performance implications (if discernible from the diff)

#### 5. Testing
- What should a reviewer verify manually?
- What should CI cover?
- Are there new or modified tests? Summarise their coverage briefly.

### Step 5: Present — Do Not Publish

Display the explanation to the user in the conversation. **Do NOT post it as a GitHub comment, review, or PR description unless the user explicitly asks.**

**Completion criterion:** The explanation is displayed in the conversation and covers all five sections (omitting Technical Details only if genuinely unnecessary).

## Guidelines

- **Facts over speculation.** Derive every claim from the diff or PR metadata. When you must infer intent (e.g. "this likely fixes…"), label it clearly as an assumption.
- **Plain language first.** Avoid jargon when a simpler phrase works. Define acronyms on first use if they are not obvious in context.
- **Proportional depth.** A 5-file typo fix needs a two-sentence explanation, not five sections. Scale the output to match the PR's complexity.
- **Respect the user's ask.** If the user provides extra context or asks to focus on a specific aspect, adapt the explanation accordingly.
