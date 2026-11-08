"""Read-only GitHub discussion collection and conservative evidence gates (stdlib only)."""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


COMMENT = """id url body author { login __typename } authorAssociation createdAt updatedAt"""
INLINE = COMMENT + """ path line startLine originalLine originalStartLine diffHunk
 commit { oid } originalCommit { oid }"""
THREAD = """id isResolved isOutdated path line startLine originalLine originalStartLine
 diffSide startDiffSide resolvedBy { login }"""
PAGE = "totalCount pageInfo { hasNextPage endCursor }"


def stamp():
    """Return an explicit UTC retrieval timestamp."""
    return datetime.now(timezone.utc).isoformat()


def fingerprint(value):
    """Pin evidence to serialized content, including comments and resolution state."""
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class GhReader:
    """Authenticated gh GraphQL adapter; query-only, with independent connection cursors."""

    def __init__(self, owner, repo, number, run=subprocess.run):
        """Validate identifiers before constructing any subprocess arguments."""
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", owner):
            raise ValueError("invalid owner")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", repo) or repo in (".", ".."):
            raise ValueError("invalid repository")
        if not isinstance(number, int) or number < 1:
            raise ValueError("invalid PR number")
        self.owner, self.repo, self.number, self.run = owner, repo, number, run

    def __call__(self, stream, cursor=None, thread=None):
        """Fetch one bounded page; never use outer pagination for nested comments."""
        after = ", after: " + json.dumps(cursor) if cursor else ""
        args = "(first: 100" + after + ")"
        if stream == "metadata":
            selection = "id url headRefOid baseRefOid"
        elif stream == "threads":
            selection = "reviewThreads" + args + " { " + PAGE + " nodes { " + THREAD + " } }"
        elif stream == "comments":
            selection = "comments" + args + " { " + PAGE + " nodes { " + COMMENT + " } }"
        elif stream == "reviews":
            selection = "reviews" + args + " { " + PAGE + " nodes { " + COMMENT + " state submittedAt commit { oid } } }"
        elif stream == "thread_comments":
            query = "query { node(id: " + json.dumps(thread) + ") { ... on PullRequestReviewThread { comments" + args + " { " + PAGE + " nodes { " + INLINE + " } } } } }"
            return self._request(query, ["node", "comments"])
        else:
            raise ValueError("unknown stream")
        query = ("query { repository(owner: " + json.dumps(self.owner) + ", name: "
                 + json.dumps(self.repo) + ") { pullRequest(number: " + str(self.number)
                 + ") { " + selection + " } } }")
        path = ["repository", "pullRequest"]
        if stream != "metadata":
            path.append({"threads": "reviewThreads"}.get(stream, stream))
        return self._request(query, path)

    def _request(self, query, path):
        """Reject partial GraphQL and transport errors without echoing credentials/content."""
        try:
            result = self.run(["gh", "api", "graphql", "-f", "query=" + query],
                              capture_output=True, text=True, timeout=60, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError("transport unavailable or timed out") from exc
        if result.returncode:
            raise ValueError("gh request failed; inspect authentication, permission and rate limits")
        try:
            payload = json.loads(result.stdout)
            if not isinstance(payload, dict):
                raise ValueError("malformed GraphQL envelope")
            if payload.get("errors"):
                raise ValueError("partial GraphQL errors")
            value = payload["data"]
            for key in path:
                value = value[key]
            if not isinstance(value, dict):
                raise ValueError("null or malformed response")
            return value
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ValueError("malformed/truncated JSON or missing connection") from exc


def nonempty(value):
    """Require a usable string identity rather than truthiness."""
    return isinstance(value, str) and bool(value.strip())


def source_url(value):
    """Require an absolute HTTP source link."""
    return nonempty(value) and bool(re.fullmatch(r"https?://[^/\s]+(?:/[^\s]*)?", value))


def timestamp(value):
    """Validate GitHub timestamp strings with explicit timezone context."""
    if not nonempty(value):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def nullable(check):
    """Allow documented nulls without allowing absent fields."""
    return lambda value: value is None or check(value)


def actor(value):
    """Deleted actors may be null; present actors require usable identity and type."""
    return value is None or (isinstance(value, dict)
        and nonempty(value.get("login")) and nonempty(value.get("__typename")))


def commit(value):
    """Unavailable commits may be null; present commits require a revision string."""
    return value is None or (isinstance(value, dict) and nonempty(value.get("oid")))


LOCATION = {key: nullable(lambda v: type(v) is int and v > 0)
            for key in ("line", "startLine", "originalLine", "originalStartLine")}
COMMENT_SCHEMA = dict(id=nonempty, url=source_url, body=lambda v: isinstance(v, str),
    author=actor, authorAssociation=nonempty, createdAt=timestamp, updatedAt=timestamp)
INLINE_SCHEMA = dict(COMMENT_SCHEMA, **LOCATION, path=nonempty,
                     diffHunk=lambda v: isinstance(v, str), commit=commit, originalCommit=commit)
THREAD_SCHEMA = dict(LOCATION, id=nonempty, isResolved=lambda v: type(v) is bool,
    isOutdated=lambda v: type(v) is bool, path=nonempty,
    diffSide=lambda v: v in ("LEFT", "RIGHT"),
    startDiffSide=nullable(lambda v: v in ("LEFT", "RIGHT")),
    resolvedBy=lambda v: v is None or (isinstance(v, dict) and nonempty(v.get("login"))))
REVIEW_SCHEMA = dict(COMMENT_SCHEMA, state=nonempty, submittedAt=nullable(timestamp), commit=commit)
METADATA_SCHEMA = dict(id=nonempty, url=source_url, headRefOid=nonempty, baseRefOid=nonempty)


def invalid_fields(value, schema):
    """Report missing and malformed fields while retaining the original evidence."""
    if not isinstance(value, dict):
        return ["record"]
    return [key for key, check in schema.items() if key not in value or not check(value[key])]


def collect_discussion(fetch_page, source="injected"):
    """Collect each connection to its terminal cursor, retaining partial data and gaps."""
    result = dict(schema_version=1, source=source, started_at=stamp(),
                  before=None, after=None, threads=[], comments=[], reviews=[],
                  audit=[], gaps=[], complete=False)

    def gap(stream, thread, cursor, reason):
        """Name the exact failed connection and resume position."""
        result["gaps"].append(dict(stream=stream, thread=thread, cursor=cursor, reason=reason))

    def metadata(label):
        """Require explicit PR identity and revision context."""
        try:
            value = fetch_page("metadata")
            result[label] = value
            invalid = invalid_fields(value, METADATA_SCHEMA)
            if invalid:
                gap("metadata", None, None, label + ": invalid/missing " + ", ".join(invalid))
        except Exception as exc:
            gap("metadata", None, None, str(exc))

    def connection(stream, thread=None):
        """Validate coverage independently of page length; duplicate IDs fail closed."""
        nodes, ids, cursors, cursor, total = [], set(), set(), None, None
        while True:
            try:
                page = fetch_page(stream, cursor, thread)
                if not isinstance(page, dict) or page.get("errors") or page.get("truncated"):
                    raise ValueError("partial, truncated or malformed page")
                count, info, batch = page["totalCount"], page["pageInfo"], page["nodes"]
                if type(count) is not int or count < 0 or not isinstance(batch, list):
                    raise ValueError("invalid count/nodes")
                if type(info["hasNextPage"]) is not bool or "endCursor" not in info:
                    raise ValueError("missing page metadata")
                if total is not None and total != count:
                    raise ValueError("total changed during retrieval")
                total = count
                for node in batch:
                    if not isinstance(node, dict) or not nonempty(node.get("id")):
                        raise ValueError("invalid/missing node identity")
                    if node["id"] in ids:
                        raise ValueError("duplicate node ID; collection unstable")
                    ids.add(node["id"])
                    nodes.append(node)
                result["audit"].append(dict(stream=stream, thread=thread, cursor=cursor,
                    end_cursor=info["endCursor"], has_next=info["hasNextPage"],
                    total=total, received=len(batch), unique=len(ids), retrieved_at=stamp()))
                if not info["hasNextPage"]:
                    if len(ids) != total:
                        raise ValueError("terminal count mismatch")
                    break
                next_cursor = info["endCursor"]
                if not isinstance(next_cursor, str) or not next_cursor or next_cursor in cursors:
                    raise ValueError("missing/repeated/nonadvancing cursor")
                cursors.add(next_cursor)
                cursor = next_cursor
            except Exception as exc:
                gap(stream, thread, cursor, str(exc))
                break
        return nodes

    def validate(record, schema, stream, thread=None):
        """Name invalid fields and source identity without dropping partial records."""
        invalid = invalid_fields(record, schema)
        if invalid:
            gap(stream, thread, None, record["id"] + ": invalid/missing " + ", ".join(invalid))

    metadata("before")
    result["threads"] = connection("threads")
    for thread in result["threads"]:
        thread["comments"] = connection("thread_comments", thread["id"])
        validate(thread, THREAD_SCHEMA, "threads", thread["id"])
        for comment in thread["comments"]:
            validate(comment, INLINE_SCHEMA, "thread_comments", thread["id"])
    result["comments"] = connection("comments")
    result["reviews"] = connection("reviews")
    for stream in ("comments", "reviews"):
        for comment in result[stream]:
            validate(comment, REVIEW_SCHEMA if stream == "reviews" else COMMENT_SCHEMA, stream)
    metadata("after")
    if result["before"] != result["after"]:
        gap("metadata", None, None, "identity/head/base changed; recollect at stable revision")
    result["finished_at"] = stamp()
    result["complete"] = not result["gaps"]
    result["totals"] = dict(threads=len(result["threads"]),
        thread_comments=sum(len(t["comments"]) for t in result["threads"]),
        resolved=sum(t.get("isResolved") is True for t in result["threads"]),
        comments=len(result["comments"]), reviews=len(result["reviews"]))
    return result


def correlate(previous, current):
    """Compare authoritative snapshots; never invent reopen history without prior state."""
    old = {t["id"]: t for t in (previous or {}).get("threads", [])}
    changes = []
    revision_changed = (previous or {}).get("after") != current.get("after")
    for thread in current["threads"]:
        prior = old.get(thread["id"])
        changes.append(dict(id=thread["id"], resolved=thread.get("isResolved"),
            outdated=thread.get("isOutdated"),
            reopened=bool(prior and prior.get("isResolved") is True
                          and thread.get("isResolved") is False),
            evidence_invalidated=revision_changed or prior != thread,
            urls=[c.get("url") for c in thread["comments"]]))
    return changes


def comment_role(comment, pr_author):
    """Identity hints only; content relevance and reviewer authority require human assessment."""
    author = comment.get("author") or {}
    if author.get("__typename") == "Bot":
        return "bot-needs-substance-assessment"
    if author.get("login") == pr_author:
        return "contributor-unverified-claim"
    return "reviewer-or-participant-needs-assessment"


def group_concerns(records, associations):
    """Group only explicitly justified associations, retaining every source identity/link."""
    by_id = {r["id"]: r for r in records}
    used, groups = set(), []
    for association in associations:
        ids = association.get("ids", [])
        if not association.get("rationale") or not ids or len(set(ids)) != len(ids) or any(i not in by_id or i in used for i in ids):
            raise ValueError("invalid or overlapping concern association")
        used.update(ids)
        groups.append(dict(rationale=association["rationale"], sources=[by_id[i] for i in ids]))
    groups.extend(dict(rationale="independent concern", sources=[r])
                  for r in records if r["id"] not in used)
    return groups


def guarded_report(snapshot, refreshed, thread_id, evidence, content_digest):
    """Enforce prerequisites on agent-inspected evidence; this does not prove semantic correctness."""
    reasons = []
    thread = next((t for t in refreshed["threads"] if t["id"] == thread_id), None)
    if not snapshot["complete"] or not refreshed["complete"]:
        reasons.append("discussion incomplete; retrieve named gaps")
    if snapshot["after"] != refreshed["after"] or snapshot["threads"] != refreshed["threads"] or snapshot["comments"] != refreshed["comments"] or snapshot["reviews"] != refreshed["reviews"]:
        reasons.append("discussion/revision changed; reassess latest feedback")
    if not thread or thread.get("isResolved") is not False:
        reasons.append("thread absent, resolved or unknown")
    evidence = evidence or {}
    expected = dict(head=(refreshed.get("after") or {}).get("headRefOid"),
                    base=(refreshed.get("after") or {}).get("baseRefOid"),
                    discussion=fingerprint(thread), content=content_digest)
    if any(not value or evidence.get(key) != value for key, value in expected.items()):
        reasons.append("missing or stale revision/content/thread evidence")
    for key in ("file", "symbol_or_hunk", "diff", "expected_behavior", "inspection", "focused_observation"):
        if not evidence.get(key):
            reasons.append("missing " + key)
    checks = evidence.get("checks", [])
    if not checks or any(not c.get("command") or c.get("status") != "passed"
                         or c.get("content") != content_digest for c in checks):
        reasons.append("validation absent, failed, blocked or stale")
    urls = [c.get("url") for c in (thread or {}).get("comments", [])]
    # Do not synthesize a semantic claim from booleans, roles, timestamps or keyword matches.
    return dict(eligible=not reasons, reasons=reasons, sources=urls,
                reply=None, open_explanation="; ".join(reasons) if reasons else None)


def main():
    """Save the full artifact and print a bounded summary; incomplete collection exits nonzero."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("owner")
    parser.add_argument("repo")
    parser.add_argument("number", type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        reader = GhReader(args.owner, args.repo, args.number)
    except ValueError as exc:
        parser.error(str(exc))
    result = collect_discussion(reader, source="gh GraphQL")
    # Exclusive creation prevents an accidental overwrite of earlier audit evidence.
    with args.output.open("x", encoding="utf-8") as artifact:
        json.dump(result, artifact, indent=2)
    print(json.dumps(dict(complete=result["complete"], totals=result["totals"],
                          gap_count=len(result["gaps"]), artifact=str(args.output))))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
