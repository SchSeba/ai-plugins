---
name: jira-cli
description: Interact with Jira using the jira-cli tool. Query issues, epics, sprints, and manage tasks. Use when the user mentions Jira, tickets, epics, sprints, or asks about their assigned work items.
---

# Jira CLI

Interact with Jira via [jira-cli](https://github.com/ankitpokhrel/jira-cli).

## Prerequisites

- `jira` CLI installed and configured (`jira init` already run)
- `JIRA_API_TOKEN` exported in the shell
- Default project configured in `~/.config/.jira/.config.yml`

## Available Commands

### get_my_tasks

List open tasks assigned to the current user, ordered by most recently updated.

```bash
scripts/get_my_tasks.sh [PROJECT] [LIMIT]
```

- `PROJECT` — optional, override the default project (e.g. `OCPBUGS`)
- `LIMIT` — optional, max results per page (default: 25, max: 100)

Output: plain table with columns KEY, SUMMARY, STATUS, PRIORITY, UPDATED.

### get_my_epics

List epics assigned to the current user, optionally filtered by fix-version.

```bash
scripts/get_my_epics.sh [VERSION] [PROJECT] [LIMIT]
```

- `VERSION` — optional, filter by fixVersion (e.g. `openshift-4.22`)
- `PROJECT` — optional, override the default project
- `LIMIT` — optional, max results per page (default: 25, max: 100)

Output: plain table with columns KEY, SUMMARY, STATUS, PRIORITY, UPDATED, LABELS.

## Key jira-cli Patterns

| Action | Command |
|--------|---------|
| Current user | `jira me` |
| List issues (plain) | `jira issue list --plain --no-headers` |
| List epics (plain) | `jira epic list --table --plain --no-headers` |
| Filter by assignee | `-a$(jira me)` |
| Filter by project | `-p PROJECT` |
| Filter by status (exclude) | `-s~Done -s~Closed` |
| Order by field | `--order-by updated` |
| Paginate | `--paginate <from>:<limit>` |
| Raw JQL | `-q "fixVersion = 'openshift-4.22'"` |
| Select columns | `--columns key,summary,status,priority,updated` |

## JQL Tips

For complex filtering not covered by flags, use raw JQL with `-q`:

```bash
jira issue list -q "assignee = currentUser() AND fixVersion = 'openshift-4.22' AND status NOT IN (Closed, Done)" --plain
```

The `-q` flag runs JQL within the project context (project is auto-prepended unless you override with `-p`).
