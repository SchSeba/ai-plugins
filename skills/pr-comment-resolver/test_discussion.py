"""Offline behavioral regressions for the actual resolver collector and evidence gates."""
import copy
import json
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace

import discussion as d


FIXTURE = json.loads(Path(__file__).with_name("discussion-cases.json").read_text())


def comment(identity):
    """Build a sanitized API comment including nullable location context."""
    return dict(id=identity, url="https://example.invalid/comment/" + identity,
                body="Review request", author=None, authorAssociation="NONE",
                createdAt="2026-01-01T00:00:00Z", updatedAt="2026-01-01T00:00:00Z",
                path="api.go", line=None, startLine=None, originalLine=4,
                originalStartLine=None, diffHunk="@@ api @@", commit={"oid": "head"},
                originalCommit={"oid": "old"}, state="COMMENTED",
                submittedAt="2026-01-01T00:00:00Z")


def thread(identity):
    """Build authoritative state independently of line age."""
    return dict(id=identity, isResolved=False, isOutdated=True, path="api.go",
                line=None, startLine=None, originalLine=4, originalStartLine=None,
                diffSide="RIGHT", startDiffSide=None, resolvedBy=None)


def page(nodes, total=None, more=False, cursor=None):
    """Construct explicit connection coverage metadata."""
    return dict(nodes=nodes, totalCount=len(nodes) if total is None else total,
                pageInfo=dict(hasNextPage=more, endCursor=cursor))


class Source:
    """Inject separate stream/thread/cursor pages with a recorded call inventory."""

    def __init__(self, pages=None):
        """Initialize an empty discussion at a stable revision."""
        self.pages = pages or {}
        self.calls = []
        self.meta = dict(id="PR", url="https://example.invalid/pr/1",
                         headRefOid="head", baseRefOid="base")

    def __call__(self, stream, cursor=None, thread=None):
        """Return detached pages as a real JSON transport would."""
        self.calls.append((stream, cursor, thread))
        value = self.meta if stream == "metadata" else self.pages.get(
            (stream, cursor, thread), page([]))
        if isinstance(value, Exception):
            raise value
        return copy.deepcopy(value)


class DiscussionTests(unittest.TestCase):
    """Exercise collection coverage and conservative recommendation behavior."""

    def snapshot(self):
        """Collect a realistic multi-comment sequence."""
        comments = []
        for item in FIXTURE["sequence"]:
            value = comment(item["id"])
            value.update(item)
            comments.append(value)
        return d.collect_discussion(Source({
            ("threads", None, None): page([thread("T")]),
            ("thread_comments", None, "T"): page(comments),
            ("comments", None, None): page([comment("general")]),
            ("reviews", None, None): page([comment("review")]),
        }))

    def evidence(self, snapshot):
        """Record concrete inspection prerequisites pinned to the tested content."""
        return dict(head="head", base="base", content="digest",
                    discussion=d.fingerprint(snapshot["threads"][0]),
                    file="api.go", symbol_or_hunk="Allocate", diff="+ reject empty",
                    expected_behavior="empty rejected", inspection="traced update caller",
                    focused_observation="update returned validation error",
                    checks=[dict(command="focused regression", status="passed", content="digest")])

    def test_empty(self):
        """Empty endpoints still need terminal audited pages."""
        result = d.collect_discussion(Source())
        self.assertTrue(result["complete"])
        self.assertEqual(result["totals"]["threads"], 0)
        self.assertEqual(len(result["audit"]), 3)
        self.assertEqual(result["before"], result["after"])

    def test_independent_pagination(self):
        """Exact, short and empty continuing pages never imply exhaustion."""
        for first_size in (0, 1, 100):
            with self.subTest(first_size=first_size):
                initial = [thread("T" + str(i)) for i in range(first_size)]
                pages = {
                    ("threads", None, None): page(initial, first_size + 1, True, "outer"),
                    ("threads", "outer", None): page([thread("last")], first_size + 1),
                    ("thread_comments", None, "last"): page([comment("a")], 2, True, "nested"),
                    ("thread_comments", "nested", "last"): page([comment("b")], 2),
                }
                for stream in ("comments", "reviews"):
                    pages[(stream, None, None)] = page([comment(stream + "1")], 2, True, stream)
                    pages[(stream, stream, None)] = page([comment(stream + "2")], 2)
                source = Source(pages)
                result = d.collect_discussion(source)
                self.assertTrue(result["complete"], result["gaps"])
                self.assertEqual(result["totals"]["thread_comments"], 2)
                self.assertIn(("thread_comments", "nested", "last"), source.calls)
                self.assertEqual(result["totals"]["reviews"], 2)

    def test_failures_preserve_partial_and_name_gap(self):
        """Coverage errors cannot silently turn a partial inventory into a success."""
        failures = [
            ValueError("rate limited"), None, {}, {"truncated": True},
            {"errors": ["partial"]}, page([], 1),
            dict(nodes=[], totalCount=0, pageInfo={"hasNextPage": False}),
            page([thread("first")], 2),  # duplicate across pages
            page([], 2, True, "next"),  # repeated cursor
            page([], 3),  # changed total
        ]
        for failure in failures:
            with self.subTest(failure=failure):
                result = d.collect_discussion(Source({
                    ("threads", None, None): page([thread("first")], 2, True, "next"),
                    ("threads", "next", None): failure,
                }))
                self.assertFalse(result["complete"])
                self.assertEqual(result["threads"][0]["id"], "first")
                self.assertEqual(result["gaps"][0]["stream"], "threads")
                self.assertEqual(result["gaps"][0]["cursor"], "next")

    def test_missing_state_and_context(self):
        """Missing authoritative fields stay unknown; nullable locations are retained."""
        for stream in ("threads", "thread_comments", "comments", "reviews"):
            source = Source({("threads", None, None): page([thread("T")])})
            key = (stream, None, "T" if stream == "thread_comments" else None)
            source.pages[key] = page([{"id": "missing"}])
            result = d.collect_discussion(source)
            self.assertFalse(result["complete"])
        result = self.snapshot()
        self.assertTrue(result["complete"])
        self.assertIsNone(result["threads"][0]["comments"][0]["line"])

    def test_required_thread_context(self):
        """Every requested context key is required even on an empty thread."""
        for key in d.THREAD_SCHEMA:
            with self.subTest(missing=key):
                record = thread("T")
                del record[key]
                result = d.collect_discussion(Source({("threads", None, None): page([record])}))
                self.assertFalse(result["complete"])
                self.assertTrue(any(key in gap["reason"] or key == "id"
                                    for gap in result["gaps"]))
                if key != "id":
                    self.assertEqual(result["threads"][0]["comments"], [])

    def test_malformed_source_fields(self):
        """Unusable links, bodies, identities, dates and revisions name explicit gaps."""
        cases = dict(url=[None, 7, "", "/relative", "https://bad link"],
                     body=[None, {}, 7], author=[False, {}, {"login": 7}],
                     authorAssociation=[None, 7], createdAt=[None, 7, "yesterday"],
                     updatedAt=["2026-01-01", []], path=[None, 7],
                     line=[True, "4", -1], diffHunk=[None, []],
                     commit=[{}, {"oid": 7}, "head"],
                     originalCommit=[{"oid": None}], state=[None, 7],
                     submittedAt=[7, "yesterday"])
        for stream, schema in (("thread_comments", d.INLINE_SCHEMA),
                               ("comments", d.COMMENT_SCHEMA), ("reviews", d.REVIEW_SCHEMA)):
            for key, values in cases.items():
                if key not in schema:
                    continue
                for value in values:
                    with self.subTest(stream=stream, key=key, value=value):
                        record = comment("C")
                        record[key] = value
                        source = Source({("threads", None, None): page([thread("T")]),
                            (stream, None, "T" if stream == "thread_comments" else None): page([record])})
                        result = d.collect_discussion(source)
                        self.assertFalse(result["complete"])
                        self.assertTrue(any(g["stream"] == stream and key in g["reason"]
                                            for g in result["gaps"]))
                        stored = (result["threads"][0]["comments"] if stream == "thread_comments"
                                  else result[stream])
                        self.assertEqual(stored[0], record)

    def test_metadata_types_and_nullable_context(self):
        """Invalid PR revisions stay incomplete; documented nullable context is valid."""
        for key in d.METADATA_SCHEMA:
            for value in (None, True, 7, {}, ""):
                with self.subTest(key=key, value=value):
                    source = Source()
                    source.meta[key] = value
                    result = d.collect_discussion(source)
                    self.assertFalse(result["complete"])
                    self.assertEqual(result["before"], source.meta)
                    self.assertTrue(any(key in g["reason"] for g in result["gaps"]))
        record = comment("C")
        record.update(author=None, commit=None, originalCommit=None, submittedAt=None, body="")
        result = d.collect_discussion(Source({
            ("threads", None, None): page([thread("T")]),
            ("thread_comments", None, "T"): page([record]),
            ("reviews", None, None): page([record])}))
        self.assertTrue(result["complete"], result["gaps"])

    def test_state_refresh_and_rebase(self):
        """Follow-ups, reopen transitions and head/base changes invalidate evidence."""
        old = self.snapshot()
        current = copy.deepcopy(old)
        old["threads"][0]["isResolved"] = True
        changes = d.correlate(old, current)
        self.assertTrue(changes[0]["reopened"])
        self.assertTrue(changes[0]["outdated"])
        self.assertFalse(d.correlate(None, current)[0]["reopened"])
        for key in ("headRefOid", "baseRefOid"):
            changed = copy.deepcopy(current)
            changed["after"][key] = "rebased"
            self.assertTrue(d.correlate(current, changed)[0]["evidence_invalidated"])
        source = Source()
        original = source.__call__
        def moving(stream, cursor=None, thread=None):
            """Model a rebase during retrieval."""
            value = original(stream, cursor, thread)
            if stream == "metadata" and len(source.calls) > 1:
                value["headRefOid"] = "new"
            return value
        self.assertFalse(d.collect_discussion(moving)["complete"])

    def test_roles_and_grouping(self):
        """Identity never discards bots, contributor claims or distinct same-line concerns."""
        records = self.snapshot()["threads"][0]["comments"]
        self.assertIn("unverified", d.comment_role(records[1], "contributor"))
        self.assertIn("substance", d.comment_role(records[3], "contributor"))
        self.assertIn("needs-assessment", d.comment_role(comment("deleted"), "contributor"))
        groups = d.group_concerns(records, [
            dict(ids=["request", "followup"], rationale="same validation concern")])
        self.assertEqual(len(groups), 3)
        self.assertEqual([s["url"] for s in groups[0]["sources"]],
                         [records[0]["url"], records[2]["url"]])
        for ids in (["request", "request"], ["missing"]):
            with self.assertRaises(ValueError):
                d.group_concerns(records, [dict(ids=ids, rationale="same")])

    def test_evidence_guards(self):
        """Done, old checks, incomplete collection and later feedback never qualify alone."""
        snapshot = self.snapshot()
        evidence = self.evidence(snapshot)
        good = d.guarded_report(snapshot, snapshot, "T", evidence, "digest")
        self.assertTrue(good["eligible"], good["reasons"])
        self.assertIsNone(good["reply"])  # Even valid prerequisites cannot invent claims.
        for status in ("failed", "blocked", "pending"):
            invalid = copy.deepcopy(evidence)
            invalid["checks"][0]["status"] = status
            self.assertFalse(d.guarded_report(snapshot, snapshot, "T", invalid, "digest")["eligible"])
        for key in evidence:
            invalid = copy.deepcopy(evidence)
            del invalid[key]
            self.assertFalse(d.guarded_report(snapshot, snapshot, "T", invalid, "digest")["eligible"], key)
        for stream in ("threads", "comments", "reviews"):
            changed = copy.deepcopy(snapshot)
            changed[stream].append(thread("new") if stream == "threads" else comment("new"))
            report = d.guarded_report(snapshot, changed, "T", evidence, "digest")
            self.assertFalse(report["eligible"])
            self.assertTrue(report["open_explanation"])
        incomplete = copy.deepcopy(snapshot)
        incomplete["complete"] = False
        self.assertFalse(d.guarded_report(incomplete, snapshot, "T", evidence, "digest")["eligible"])
        self.assertFalse(d.guarded_report(snapshot, snapshot, "T", None, "digest")["eligible"])
        self.assertFalse(d.guarded_report(snapshot, snapshot, "T", evidence, "edited")["eligible"])
        self.assertFalse(d.guarded_report(snapshot, snapshot, "absent", evidence, "digest")["eligible"])

    def test_transport_rejects_bad_envelopes(self):
        """Malformed/truncated JSON, partial GraphQL, null data and transport errors fail closed."""
        for output in ('{', '[]', '{"errors":["denied"],"data":{}}', '{"data":null}', '{}'):
            with self.subTest(output=output):
                def run(*args, **kwargs):
                    """Return a bounded synthetic gh response."""
                    return SimpleNamespace(returncode=0, stdout=output)
                with self.assertRaises(ValueError):
                    d.GhReader("owner", "repo", 1, run=run)("metadata")
        for failure in (OSError("missing"), subprocess.TimeoutExpired("gh", 60)):
            def run(*args, **kwargs):
                """Simulate unavailable transport."""
                raise failure
            with self.assertRaises(ValueError):
                d.GhReader("owner", "repo", 1, run=run)("metadata")

    def test_adapter_query_and_identifier_safety(self):
        """The production adapter uses query-only argv with independent nested cursors."""
        calls = []
        def run(args, **kwargs):
            """Capture argv and supply a valid nested connection."""
            calls.append(args)
            return SimpleNamespace(returncode=0, stdout=json.dumps({"data": {"node": {"comments": page([])}}}))
        reader = d.GhReader("owner", "repo", 1, run=run)
        self.assertEqual(reader("thread_comments", 'cursor"', "T"), page([]))
        self.assertIn("query { node", calls[0][-1])
        self.assertIn('after: "cursor\\""', calls[0][-1])
        self.assertNotIn("mutation", calls[0][-1])
        for owner, repo, number in (("-x", "r", 1), ("o", "../r", 1), ("o", "r", 0)):
            with self.assertRaises(ValueError):
                d.GhReader(owner, repo, number)


if __name__ == "__main__":
    unittest.main()
