#!/usr/bin/env bash
# get_my_tasks.sh — List open tasks assigned to the current user, newest updated first.
# Usage: get_my_tasks.sh [PROJECT] [LIMIT]
#   PROJECT - Jira project key (optional, uses default from config)
#   LIMIT   - Max results to return (optional, default: 25, max: 100)

set -euo pipefail

PROJECT="${1:-}"
LIMIT="${2:-25}"

PROJECT_FLAG=""
if [[ -n "$PROJECT" ]]; then
  PROJECT_FLAG="-p ${PROJECT}"
fi

ME=$(jira me)

exec jira issue list \
  ${PROJECT_FLAG} \
  -a"${ME}" \
  -s~Closed \
  -s~Done \
  --order-by updated \
  --paginate "0:${LIMIT}" \
  --plain \
  --columns key,summary,status,priority,updated
