---
name: pr-review
description: Review a pull request from four engineering perspectives — developer, quality engineer, security engineer, and DevOps. Use when the user asks for a thorough PR review, a multi-perspective review, a full PR analysis, or wants developer/QA/security/DevOps review of a pull request.
---

# PR Review Command

This command reviews a pull request using the existing `code-review review-pr` workflow, then presents the findings grouped into four engineering perspectives.

Use the text after the command name as the PR link or number. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

If no PR link or number was provided, ask the user for the pull request URL before proceeding.

## Execution

1. **Run the `code-review review-pr` workflow.** Read and follow these files in order:
   - `skills/code-review/SKILL.md` — route to `review-pr`
   - `skills/code-review/review-pr.md` — the full PR review workflow
   - `skills/review-engine/SKILL.md` — the shared review engine
   - `skills/review-engine/review-perspectives.md` — perspective criteria

   Complete all steps (setup, PR context, size assessment, orchestrated review, CI status, save review). Do NOT skip any step.

2. **Regroup the findings into four perspectives.** After the review engine produces aggregated findings, classify each finding into one or more of these presentation perspectives based on its category:

   | Perspective | Source categories (from review-perspectives.md) |
   |---|---|
   | **Developer Review** | Go, Python, Frontend, Performance, API, Documentation, Dependency — code quality, maintainability, scalability, coding standards |
   | **Quality Engineer Review** | Test, Integration & E2E Test — test coverage, edge cases, potential bugs, regression risk |
   | **Security Engineer Review** | Security — vulnerabilities, data handling, OWASP compliance |
   | **DevOps Review** | Dockerfile, Shell & Build Script, Terraform / IaC, Kubernetes — CI/CD integration, infrastructure changes, monitoring needs |

   Findings that span multiple perspectives appear under each relevant one. Findings that don't clearly map go under Developer Review.

3. **Render the report** using four sequential sections instead of the default flat format. Each section acts as a self-contained review from that engineering role:

   ```
   ## PR Review: <PR title>

   **Verdict**: APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION

   **Summary**: 2–3 sentence overall assessment.

   ---

   ### 1. Developer Review
   Code quality, maintainability, performance, scalability, and coding standards.

   #### [{severity}] {title}
   **File**: `path/to/file.ext` (lines N–M)
   **Category**: {category}

   {Detailed explanation of the issue.}

   **How to fix:**
   {code snippet showing the corrected code}

   **Developer Verdict**: {pass/fail summary}

   ---

   ### 2. Quality Engineer Review
   Test coverage, edge cases, potential bugs, and regression risk.

   (same finding format)

   **QE Verdict**: {pass/fail summary}

   ---

   ### 3. Security Engineer Review
   Vulnerabilities, data handling, and OWASP compliance.

   (same finding format)

   **Security Verdict**: {pass/fail summary}

   ---

   ### 4. DevOps Review
   CI/CD integration, infrastructure changes, and monitoring needs.

   (same finding format)

   **DevOps Verdict**: {pass/fail summary}

   ---

   ### What's Good
   - {praise for well-written aspects across all perspectives}

   ### Stats
   - Files reviewed: N
   - Findings: N critical, N high, N medium, N low, N info
   - Developer: N | QE: N | Security: N | DevOps: N
   ```

## Rules

- **Every finding MUST include a fix** — both a clear explanation and a code snippet showing corrected code.
- **Empty perspectives are fine.** If a perspective has no findings, state that explicitly (e.g., "No security issues found.") rather than omitting the section.
- **Verdict comes from the review engine** — follow its severity-based verdict rules. A single critical or high finding in any perspective triggers REQUEST_CHANGES.
- **Interactive finding presentation** still applies — follow the optional interactive flow from `review-engine/SKILL.md` for publishing findings to GitHub.
