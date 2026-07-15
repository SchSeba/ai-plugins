# ai-plugins

A collection of AI agent skills and slash commands for day-to-day software development. These plugins supercharge your AI coding assistant with structured workflows for feature development, code review, PR comment resolution, and Jira integration.

Built on the open [Agent Skills](https://agentskills.io) standard — works with **Claude Code**, **Cursor**, and any editor that supports the standard.

## Table of Contents

- [Installation](#installation)
  - [Claude Code](#claude-code)
  - [Cursor](#cursor)
- [Updating](#updating)
  - [Claude Code](#claude-code-1)
  - [Cursor](#cursor-1)
- [Available Skills](#available-skills)
  - [develop-feature](#develop-feature)
  - [code-review](#code-review)
  - [review-engine](#review-engine)
  - [pr-comment-resolver](#pr-comment-resolver)
  - [jira-cli](#jira-cli)
  - [kubernetes-pre-push](#kubernetes-pre-push)
  - [write-a-skill](#write-a-skill)
- [Project Structure](#project-structure)
- [MCP Servers](#mcp-servers)
  - [GitHub MCP Server](#github-mcp-server)
  - [CodeGraph MCP Server](#codegraph-mcp-server)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Claude Code

**Option A — Plugin Marketplace (recommended)**

Run these slash commands inside a Claude Code session:

1. Add the marketplace:

```
/plugin marketplace add SchSeba/ai-plugins
```

2. Install the plugin:

```
/plugin install ai-plugins@ai-plugins
```

> The install syntax is `<plugin-name>@<marketplace-name>`. Both are `ai-plugins` in this case — the plugin name comes from `plugin.json` and the marketplace name from the GitHub repo name.

Claude Code will prompt you to choose an installation scope:

| Scope | Effect | When to use |
|-------|--------|-------------|
| **User** | Available in all your projects | You want these skills everywhere (recommended) |
| **Project** | Shared with collaborators via `.claude/plugins.json` | Team-wide adoption for a specific project |
| **Local** | Per-user, per-repo (not committed) | Personal testing in a single repo |

Once installed, the skills are namespaced under the plugin name. For example:

```
/ai-plugins:develop-feature Add JWT authentication
/ai-plugins:code-review review-pr https://github.com/owner/repo/pull/42
```

**Option B — Skills Directory**

Clone the repo into your Claude skills directory for auto-loading without the marketplace:

```bash
git clone https://github.com/SchSeba/ai-plugins.git ~/.claude/skills/ai-plugins
```

Skills loaded this way are available directly (without namespacing):

```
/develop-feature Add JWT authentication
```

**Option C — Plugin Directory (development/testing only)**

For local development or testing changes to the plugin:

```bash
git clone https://github.com/SchSeba/ai-plugins.git
claude --plugin-dir ./ai-plugins
```

### Cursor

**Option A — Remote Rule from GitHub (recommended)**

1. Open **Cursor Settings** → **Rules**
2. Click **Add Rule** → select **Remote Rule (GitHub)**
3. Enter the repository URL: `https://github.com/SchSeba/ai-plugins`

Cursor will pull the skills and commands automatically.

**Option B — Copy skills to your project**

```bash
git clone https://github.com/SchSeba/ai-plugins.git

# Project-level (available in this project only):
cp -r ai-plugins/skills/* .cursor/skills/
cp -r ai-plugins/commands/* .cursor/commands/

# User-level (available across all projects):
cp -r ai-plugins/skills/* ~/.cursor/skills/
cp -r ai-plugins/commands/* ~/.cursor/commands/
```

## Updating

After the plugin is installed, here's how to pull the latest skill updates for each installation method.

### Claude Code

**Option A — Plugin Marketplace**

Run this slash command inside a Claude Code session:

```
/plugin update ai-plugins@ai-plugins
```

**Option B — Skills Directory**

Pull the latest changes from the repository:

```bash
cd ~/.claude/skills/ai-plugins && git pull
```

**Option C — Plugin Directory**

Pull the latest changes in the cloned directory:

```bash
cd ./ai-plugins && git pull
```

### Cursor

**Option A — Remote Rule from GitHub**

No action needed — Cursor automatically re-fetches the latest skills from GitHub on each session.

**Option B — Copy skills to your project**

Pull the latest changes and re-copy the files:

```bash
cd ai-plugins && git pull

# Project-level:
cp -r skills/* .cursor/skills/
cp -r commands/* .cursor/commands/

# Or user-level:
cp -r skills/* ~/.cursor/skills/
cp -r commands/* ~/.cursor/commands/
```

> **Note:** Updates take effect immediately on the next Claude Code or Cursor session — no restart required.

## Available Skills

| Skill | Description | Command |
|-------|-------------|---------|
| [develop-feature](#develop-feature) | Plan → Code → Review → Validate workflow with multi-subagent investigation and user approval | `/develop-feature` |
| [code-review](#code-review) | Multi-perspective code review for PRs and local changes | `/code-review` |
| [review-engine](#review-engine) | Reusable review engine (shared by other skills) | `/review-engine` |
| [pr-comment-resolver](#pr-comment-resolver) | Resolve PR review comments one-by-one with user approval | `/pr-comment-resolver` |
| [jira-cli](#jira-cli) | Query Jira tasks and epics | `/jira-cli` |
| [kubernetes-pre-push](#kubernetes-pre-push) | Structured pre-push verification checklist for Kubernetes contributions | `/kubernetes-pre-push` |
| [write-a-skill](#write-a-skill) | Create new agent skills with proper structure, conventions, and registration | `/write-a-skill` |

---

### develop-feature

A four-phase development workflow: **Plan → Code → Review → Validate** with multi-subagent investigation, mandatory user approval, and automated iteration until the review passes.

The planning phase spawns parallel specialist sub-agents to investigate the codebase, then presents a structured plan for user approval. After approval, the agent writes production-grade code with tests, reviews its own work with multi-perspective review, and runs a final validation phase. If the review finds issues, it loops back to coding — up to 3 iterations.

```
+----------+     +----------+     +----------+     +----------+
|   PLAN   | --> |   CODE   | --> |  REVIEW  | --> | VALIDATE |
+----------+     +----------+     +----------+     +----------+
     |                ^                |
     |                |    changes     |
  user must           |   requested    |
  approve             +----------------+
```

**Usage:**

```
/develop-feature Add user authentication with JWT tokens
```

```
/develop-feature Fix the race condition in the connection pool cleanup
```

```
/develop-feature Refactor the payment service to use the strategy pattern
```

---

### code-review

Multi-perspective code review that spawns parallel specialist reviewers (security, performance, language-specific, testing, etc.) and aggregates their findings into a single verdict.

Supports two modes:

| Command | Description |
|---------|-------------|
| `review-pr <pr-url>` | Review a GitHub pull request |
| `review-change [project-path]` | Review uncommitted or staged local changes |

**Usage:**

```
/code-review review-pr https://github.com/owner/repo/pull/42
```

```
/code-review review-change
```

```
/code-review review-change ./services/auth
```

---

### review-engine

The shared low-level review engine used by `code-review` and `develop-feature`. It handles diff analysis, file categorization, parallel reviewer spawning, finding aggregation, and verdict rendering.

You typically don't call this directly — it's invoked automatically by the other skills. Use it directly when you want the raw review engine on an arbitrary diff.

**Usage:**

```
/review-engine
```

```
/review-engine Review the changes in the last 3 commits
```

---

### pr-comment-resolver

Interactively resolves PR review comments one at a time. For each comment, the agent shows the code, the reviewer's feedback, and a suggested fix — then waits for your approval before applying it.

**Usage:**

```
/pr-comment-resolver https://github.com/owner/repo/pull/42
```

```
/pr-comment-resolver my-project https://github.com/owner/repo/pull/42
```

**Workflow:**

1. Fetches all unresolved review comments from the PR
2. Filters to actionable comments (skips resolved threads and pure praise)
3. Shows a numbered summary of all actionable comments
4. Presents each comment one-by-one with the code snippet, reviewer feedback, and suggested fix
5. Waits for your approval (`yes` / `no` / `skip`) before applying each change
6. Runs validation after each approved change
7. Shows a final summary of addressed vs. skipped comments

---

### jira-cli

Query your Jira tasks and epics using the [jira-cli](https://github.com/ankitpokhrel/jira-cli) tool.

**Prerequisites:**

- `jira` CLI installed and configured (`jira init` already run)
- `JIRA_API_TOKEN` exported in the shell

**Usage:**

```
/jira-cli get_my_tasks
```

```
/jira-cli get_my_tasks MYPROJ 10
```

```
/jira-cli get_my_epics openshift-4.22
```

```
/jira-cli get_my_epics openshift-4.22 OCPBUGS 50
```

| Subcommand | Arguments | Description |
|------------|-----------|-------------|
| `get_my_tasks` | `[PROJECT] [LIMIT]` | List open tasks assigned to you, ordered by last updated |
| `get_my_epics` | `[VERSION] [PROJECT] [LIMIT]` | List your epics, optionally filtered by fix-version |

---

### kubernetes-pre-push

A structured pre-push verification workflow for Kubernetes repository contributions. Analyzes the changed files in your working tree, determines which verification steps apply (lint, codegen, OpenAPI, API descriptions, integration tests, client-go API diff), and executes them in the correct dependency order — regenerating code before verifying, running focused tests before broad integration suites.

**Usage:**

```
/kubernetes-pre-push
```

```
/kubernetes-pre-push ./pkg/apis/resource/... ./pkg/scheduler/framework/plugins/dynamicresources/...
```

**Workflow:**

1. Discovers the Kubernetes repo root and base branch
2. Analyzes changed files and classifies them (API types, generated code, staging modules, etc.)
3. Runs always-required checks: focused Go tests, lint, codegen verification, OpenAPI verification
4. Regenerates code if verifiers fail or API types changed (codegen, OpenAPI snapshots, API compatibility data)
5. Runs conditional checks based on what changed: API descriptions, API compatibility, client-go API diff, integration tests
6. Presents a pass/fail summary with a clear push verdict

---

### write-a-skill

Step-by-step workflow for creating a new skill in this repository. Guides you through requirements gathering, directory creation, writing the skill body with proper information hierarchy, crafting the description, creating the command file, registering in README.md, and running the review checklist.

Integrates best practices from [mattpocock's writing-great-skills](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-great-skills/SKILL.md) — including completion criteria, leading words, progressive disclosure, and failure mode awareness.

**Usage:**

```
/write-a-skill Create a skill for database migration management
```

```
/write-a-skill
```

Includes a [`GLOSSARY.md`](skills/write-a-skill/GLOSSARY.md) with domain vocabulary for skill authoring (predictability, leading words, information hierarchy, failure modes, etc.).

## Project Structure

```
ai-plugins/
├── AGENTS.md                 # Repository conventions and rules for AI agents
├── README.md                 # This file
├── .claude-plugin/           # Claude Code plugin manifest
│   ├── marketplace.json
│   └── plugin.json
├── .cursor-plugin/           # Cursor plugin manifest
│   └── plugin.json
├── .mcp.json                 # MCP server configuration (GitHub, CodeGraph)
├── commands/                 # Slash command definitions
│   ├── code-review.md
│   ├── develop-feature.md
│   ├── jira-cli.md
│   ├── kubernetes-pre-push.md
│   ├── pr-comment-resolver.md
│   ├── review-engine.md
│   └── write-a-skill.md
└── skills/                   # Skill implementations
    ├── code-review/
    │   ├── SKILL.md
    │   ├── review-change.md
    │   └── review-pr.md
    ├── develop-feature/
    │   └── SKILL.md
    ├── jira-cli/
    │   ├── SKILL.md
    │   └── scripts/
    ├── kubernetes-pre-push/
    │   └── SKILL.md
    ├── pr-comment-resolver/
    │   └── SKILL.md
    ├── review-engine/
    │   ├── SKILL.md
    │   └── review-perspectives.md
    └── write-a-skill/
        ├── SKILL.md
        └── GLOSSARY.md
```

**How it works:**

- **Skills** (`skills/<name>/SKILL.md`) contain the detailed agent instructions — the workflow steps, criteria, and guidelines that teach the AI how to perform a task.
- **Commands** (`commands/<name>.md`) are the user-facing slash commands that route to the appropriate skill.
- **Plugin manifests** (`.claude-plugin/` and `.cursor-plugin/`) register the skills, commands, and MCP servers with the respective editors.

## MCP Servers

The repository includes pre-configured MCP servers in `.mcp.json` for GitHub and CodeGraph integration.

### GitHub MCP Server

The [GitHub MCP server](https://github.com/github/github-mcp-server) gives skills access to GitHub APIs for fetching PR data, review comments, and more.

**Setup:**

1. Export your GitHub token:
   ```bash
   export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
   ```

2. The config uses `podman` by default. If you use Docker, update `.mcp.json`:
   ```json
   {
     "github": {
       "command": "docker",
       "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
       "env": {
         "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
       }
     }
   }
   ```

### CodeGraph MCP Server

[CodeGraph](https://github.com/colbymchenry/codegraph) provides semantic code intelligence — it builds a graph of your codebase's symbols, call paths, and relationships, enabling AI agents to explore code structure in a single tool call instead of slow grep/find/read loops.

**Prerequisites:**

Install CodeGraph from its repository:

```bash
# Install via Go
go install github.com/colbymchenry/codegraph@latest

# Or clone and build from source
git clone https://github.com/colbymchenry/codegraph.git
cd codegraph
go install .
```

Ensure the `codegraph` binary is available on your `PATH`.

**Setup:**

The `.mcp.json` already includes the CodeGraph server configuration:

```json
{
  "codegraph": {
    "command": "codegraph",
    "args": ["serve", "--mcp"]
  }
}
```

**First-time use in a project:**

Before using CodeGraph in a project, you need to initialize the code graph:

```bash
cd /path/to/your/project
codegraph init
```

This creates a `.codegraph/` directory with the indexed code graph. All code-related skills in this plugin will automatically detect and use CodeGraph when available, and will run `codegraph init` if the `.codegraph/` directory is missing.

## Contributing

Skills are plain Markdown files — no executable code required. To add a new skill:

1. Read and follow the [`write-a-skill`](skills/write-a-skill/SKILL.md) skill for the complete workflow
2. Create `skills/<your-skill>/SKILL.md` with YAML frontmatter (`name`, `description`) and the skill workflow in Markdown
3. Create a matching `commands/<your-skill>.md` that routes to your skill
4. **Add the new skill and command to this README** — both the Skills table and the dedicated section, in alphabetical order
5. Follow the existing patterns — see any skill directory for reference

## License

[MIT](https://opensource.org/licenses/MIT)
