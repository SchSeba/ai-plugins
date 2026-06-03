#!/usr/bin/env bash
# get_my_epics.sh — List epics assigned to the current user, optionally filtered by fix-version.
# Usage: get_my_epics.sh [VERSION] [PROJECT] [LIMIT]
#   VERSION - fixVersion filter (optional, e.g. "openshift-4.22")
#   PROJECT - Jira project key (optional, uses default from config)
#   LIMIT   - Max results to return (optional, default: 25, max: 100)

set -euo pipefail

VERSION="${1:-}"
PROJECT="${2:-}"
LIMIT="${3:-25}"

PROJECT_FLAG=""
if [[ -n "$PROJECT" ]]; then
  PROJECT_FLAG="-p ${PROJECT}"
fi

JQL="assignee = currentUser() AND status NOT IN (Closed, Done)"
if [[ -n "$VERSION" ]]; then
  JQL="${JQL} AND fixVersion = '${VERSION}'"
fi

exec jira epic list \
  ${PROJECT_FLAG} \
  --table \
  -q "${JQL}" \
  --order-by updated \
  --paginate "0:${LIMIT}" \
  --plain \
  --columns key,summary,status,priority,updated,labels
