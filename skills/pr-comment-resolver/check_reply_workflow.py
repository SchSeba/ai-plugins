"""Check the PR comment resolver's documented reply acceptance scenarios."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / "skills/pr-comment-resolver/SKILL.md"
SCENARIOS_PATH = ROOT / "skills/pr-comment-resolver/reply-workflow-scenarios.md"
README_PATH = ROOT / "README.md"

ALLOWED_FIXTURE_REPLY = (
    "Added a nil-request guard that returns ErrMissingRequest before reading req.User."
)


def reply_matches_fixture(reply: str, diff: str) -> bool:
    """Accept only the documented reply supported by the nil-request diff."""
    if reply.strip() != ALLOWED_FIXTURE_REPLY:
        return False

    claims = ("nil-request guard", "errmissingrequest", "before reading req.user")
    diff_positions = (
        diff.find("if req == nil"),
        diff.find("return ErrMissingRequest"),
        diff.find("return process(req.User)"),
    )
    return (
        all(claim in reply.casefold() for claim in claims)
        and all(position >= 0 for position in diff_positions)
        and diff_positions[0] < diff_positions[1] < diff_positions[2]
    )


def main() -> int:
    """Run documentation coverage and diff-to-reply acceptance checks."""
    skill = SKILL_PATH.read_text(encoding="utf-8")
    scenarios = SCENARIOS_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")

    diff_match = re.search(r"Applied diff:\s*~~~diff\n(.*?)\n~~~", scenarios, re.DOTALL)
    reply_match = re.search(r"eligible concise reply is: “([^”]+)”", scenarios)
    diff = diff_match.group(1) if diff_match else ""
    reply = reply_match.group(1) if reply_match else ""

    checks = [
        ("positive diff fixture and reply are present", bool(diff_match and reply_match)),
        (
            "nil guard returns before req.User is read",
            reply_matches_fixture(reply, diff),
        ),
        (
            "future-work placeholder reply is rejected",
            not reply_matches_fixture(
                "I will add a nil-request guard and update this draft later.", diff
            ),
        ),
        (
            "generic status reply is rejected",
            not reply_matches_fixture("This concern is being handled.", diff),
        ),
        (
            "unsupported test claim is rejected",
            not reply_matches_fixture(f"{reply} All tests passed.", diff),
        ),
        (
            "unrelated change reply is rejected",
            not reply_matches_fixture("Updated unrelated validation instructions.", diff),
        ),
        ("reply starts unset", "Start with the reply unset." in skill),
        (
            "related resolved or outdated history is reviewed before filtering",
            "before filtering anything out" in skill
            and "Include resolved and outdated inline threads where available" in skill,
        ),
        (
            "MCP pagination must reach an empty page or documented final page",
            "A source is complete only after every page for both endpoints in use has been retrieved" in skill
            and "request successive pages with `page`" in skill
            and "until an empty page confirms exhaustion" in skill
            and "do not infer exhaustion from a short page" in skill,
        ),
        (
            "GitHub CLI fallback confirms pagination exhaustion per endpoint",
            "continue to Source 2 for it" in skill
            and "GitHub CLI's documented pagination feature" in skill
            and "Verify that it follows every page and that no next page remains" in skill,
        ),
        (
            "exported history is accepted only with complete coverage",
            "contents or accompanying metadata establish that it includes every page of both inline review comments and general PR comments" in skill
            and "If coverage is partial or uncertain, history remains incomplete." in skill,
        ),
        (
            "incomplete pagination is surfaced before assessment or fixes",
            "mark history incomplete" in skill
            and "Do not make a validity disposition or propose a fix until the missing history or context is supplied." in skill,
        ),
        (
            "relevant history retains target, status, quote, and rationale",
            "original URL and ID, inline thread ID when available, active/resolved/outdated status, quote, and stated rationale" in skill,
        ),
        (
            "history informs but does not decide validity; expected behavior precedes fixes",
            "History informs the decision; it does not by itself accept or reject the request." in skill
            and "valid**, **invalid**, or **needs context**" in skill
            and "state the expected behavior and relevant regression cases" in skill,
        ),
        (
            "missing context is surfaced before a fix is proposed",
            "identify the missing evidence and ask the user" in skill
            and "do not assume or propose a change until the ambiguity is resolved" in skill,
        ),
        (
            "focused behavior evidence is required with applicable project checks",
            "Perform a focused behavior check against the stated expectation and regression cases." in skill
            and "Passing general project checks alone does not establish the expected behavior." in skill,
        ),
        (
            "draft requires final PR head-to-base evidence and checked validation",
            "final candidate PR change set shows a change" in skill
            and "Define that change set as the PR head compared with its base." in skill
            and "applicable validation is checked" in skill,
        ),
        (
            "approved corrections enter mapped commits without fixup commits",
            "integrate corrections only into the approved existing commits" in skill
            and "without creating fixup commits" in skill,
        ),
        (
            "rebases refresh evidence when relevant content or validation changes",
            "After every rebase, re-evaluate the evidence against the new final head-to-base change set." in skill
            and "If the rebase changes relevant content or validation state, invalidate the affected evidence and draft" in skill,
        ),
        (
            "absent resolutions remain unpublished",
            "No applied resolution to report" in skill
            and "leave reply text unset" in skill,
        ),
        (
            "later edits invalidate reply evidence",
            "Any later edit that changes the relevant diff or validation state invalidates"
            in skill,
        ),
        (
            "review and knowledge completion precede publication",
            "full review and knowledge persistence are complete" in skill,
        ),
        ("latest-push confirmation is required", "explicitly confirm" in skill),
        ("each exact reply receives separate approval", "separately approves" in skill),
        (
            "original comment and thread identity are retained",
            "original comment URL and ID" in skill
            and "inline review-thread ID" in skill,
        ),
        ("threads are not automatically resolved", "Do not resolve threads automatically." in skill),
        (
            "placeholder and unrelated-diff negatives are documented",
            "Pending or future-work text" in scenarios
            and "A diff for another concern" in scenarios
            and "An otherwise valid fixture reply gains" in scenarios,
        ),
        (
            "no-resolution, project-check failure, and focused-behavior failure cases are documented",
            "A reply claims a fix absent from the diff" in scenarios
            and "Applicable validation fails or is blocked" in scenarios
            and "a focused reproduction still reads `req.User` before rejecting nil" in scenarios
            and "no reply is eligible" in scenarios,
        ),
        (
            "history-informed accepting, declining, and missing-context cases are documented",
            "mark the current request valid because the old assumption changed" in scenarios
            and "Mark it invalid with the concrete reason" in scenarios
            and "mark the request needs context" in scenarios,
        ),
        (
            "later-page, API fallback, and incomplete-coverage cases are documented",
            "relevant rationale appears after the first page" in scenarios
            and "successive pages for each endpoint" in scenarios
            and "MCP returns the first page but cannot fetch or confirm later pages" in scenarios
            and "GitHub CLI's documented pagination feature succeeds" in scenarios
            and "Do not assign a valid/invalid disposition or propose a fix." in scenarios
            and "An export omits page metadata and its coverage cannot be established" in scenarios,
        ),
        (
            "positive behavior validation scenario is documented",
            "focused behavior evidence confirms the result" in scenarios
            and "subject to the existing final-diff and publication gates" in scenarios,
        ),
        (
            "declined and incomplete work cases are documented",
            "The user declines or skips" in scenarios
            and "implementation is incomplete" in scenarios,
        ),
        (
            "later-edit and stale-rebase scenarios are documented",
            "A later edit or revert" in scenarios
            and "A rebase changes the relevant content or validation state" in scenarios,
        ),
        (
            "approved mapped-commit integration remains eligible with a clean worktree",
            "An approved rebase integrates a fix into its mapped existing commits and the worktree is clean" in scenarios
            and "no fixup commit is created" in scenarios,
        ),
        (
            "README explains history-informed assessment and focused behavior checks",
            "Before filtering older discussion" in readme
            and "valid, invalid, or needs-context disposition" in readme
            and "focused behavior check" in readme,
        ),
        (
            "README requires full pagination and surfaces incomplete history",
            "paginates inline and general PR comments through all available pages" in readme
            and "reports the missing pages or endpoint" in readme
            and "every available page of inline review comments and general PR comments" in readme,
        ),
        (
            "README explains approved mapped-commit eligibility and evidence refresh",
            "corrections integrated into approved existing commits remain eligible with a clean worktree" in readme
            and "evidence is rechecked if relevant content or validation changes" in readme,
        ),
        (
            "cross-repository behavior is documented",
            "Target PR is kubernetes/kubernetes" in scenarios,
        ),
        (
            "API-field renames trace dependent references before proposing a fix",
            "For an API-field rename request, trace the field declaration and relevant references before proposing a fix:" in skill
            and "dependent functions and helpers, callers, tests and fixtures, and documentation" in skill
            and "include this impact in the expected behavior" in skill
            and "do not apply a blanket rename" in skill,
        ),
        (
            "API-field rename validation audits dependents and intentional old-name references",
            "compare the reference map recorded in Step 4 with the resulting change set" in skill
            and "A stale dependent reference or unexplained retained name means the expected behavior is unproven" in skill,
        ),
        (
            "coordinated API rename fixture updates dependent helper, caller, test, and documentation",
            "DisplayName" in scenarios
            and "DisplayLabel" in scenarios
            and "displayNameFor" in scenarios
            and "displayLabelFor" in scenarios
            and "accountSummary" in scenarios
            and "account_test.go" in scenarios
            and "API.md" in scenarios,
        ),
        (
            "intentional wire-format name is preserved with a compatibility reason",
            'json:"displayName"' in scenarios
            and "intentionally preserved to keep the existing wire format" in scenarios
            and "old field spelling remains as a documented JSON wire-format key" in scenarios,
        ),
        (
            "stale dependent references block reply eligibility",
            "dependent helper, caller, test, or documentation reference remains stale" in scenarios
            and "keep the reply ineligible until the dependency is corrected" in scenarios,
        ),
        (
            "README summarizes API rename dependency tracing and follow-up audit",
            "For API-field renames, it traces dependent functions, helpers, callers, tests, fixtures, and documentation" in readme
            and "then audits affected references after implementation" in readme,
        ),
        (
            "README identifies the repeatable acceptance check",
            "python3 skills/pr-comment-resolver/check_reply_workflow.py" in readme,
        ),
    ]

    # Documentation coverage checks complement the manual gate/state walkthrough.
    checks.extend([
        ("rebase review precedes execution and evidence refresh",
         skill.index("#### Separate approval before any rebase") < skill.index("#### Determine reply eligibility")
         and "complete candidate change set" in skill
         and "wait for separate explicit user rebase approval" in skill
         and "After an approved rebase" in skill),
        ("rebase corrections are uncommitted and no fixup commits are created",
         "Keep applied corrections as reviewable uncommitted changes while rebase approval is pending." in skill
         and "Do not create fixup commits" in skill
         and "temporary fixup commits intended for autosquash" in skill),
        ("every correction is mapped to an existing commit and ambiguous placement is clarified",
         "For every correction, identify the exact existing PR commit by SHA and subject" in skill
         and "If any destination is ambiguous, ask the user to clarify" in skill),
        ("rebase decisions and stale placement approval are explicit",
         all(phrase in skill for phrase in (
             "silence or blanket consent do not substitute",
             "Decline or skip leaves history unchanged",
             "operation, or commit-placement mapping invalidate approval"))),
        ("compatibility provenance is established before classification",
         skill.index("#### Establish production provenance") < skill.index("#### Classification rules")
         and "baseline revision, file/symbol evidence" in skill
         and "never assume absence" in skill),
        ("production contracts and PR-only removals are distinguished",
         "Preserve proven existing production contracts" in skill
         and "Fields introduced and removed within this unpublished PR" in skill
         and "protobuf-number reservation comment solely" in skill),
        ("wire-key fixture identifies production provenance",
         "Fixture production evidence" in scenarios
         and "prod-v1" in scenarios and "existing production JSON key" in scenarios),
        ("compatibility scenarios cover paired outcomes and unknown baseline",
         all(phrase in scenarios for phrase in (
             "An existing production field", "A field exists only",
             "PR adds two protobuf fields", "add no protobuf-number reservation",
             "production baseline or relevant history cannot be retrieved"))),
        ("rebase scenarios cover multi-commit placement, ambiguity, refusal, silence and stale mapping",
         all(phrase in scenarios for phrase in (
             "Corrections span multiple PR commits",
             "Ask the user to clarify its destination",
             "without creating fixup commits",
             "declines or skips the rebase",
             "user is silent",
             "commit-placement map changes after approval"))),
        ("README documents compatibility and reviewed commit placement gates",
         "Before compatibility handling" in readme
         and "maps every correction to an existing PR commit by SHA and subject" in readme
         and "never creates fixup commits" in readme
         and "Missing baseline evidence requires context" in readme),
    ])

    failures = 0
    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
        failures += not passed
    print(f"{len(checks) - failures}/{len(checks)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
