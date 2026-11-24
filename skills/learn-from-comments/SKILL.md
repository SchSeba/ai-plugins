---
name: learn-from-comments
description: Retrospective for completed Local Review threads and verified changes. Use when asked to learn from local comments or publish the lessons to ai-plugins.
---

# Learn from comments

1. Identify the reviewed Git worktree and branch before changing directories. Use the canonical Git repository name for the project, or the worktree name for a repository without a remote. Resolve any ambiguity before choosing a project. Read completed threads through the Local Review MCP tool `list_review_history` with the absolute worktree root and any review scope supplied by the user. Keep the returned scope for rereads. Honor any selection of threads. If the tool is unavailable or there is no completed evidence, report that outcome.
2. Follow **Derive durable lessons** in the [retrospective skill](../retrospective/SKILL.md), using the local threads as evidence and the final reviewed changes as the code to verify. Read the reviewed checkout's instructions and the existing guidance under `projects/<project>/`. Consider follow-ups in order. Confirm that each lesson holds in the code and reflects the review, beyond what the saved reply summary claims. Report the lessons or explain why none qualify.
3. For an explicit publication request with a qualifying lesson, clone [SchSeba/ai-plugins](https://github.com/SchSeba/ai-plugins) into a fresh temporary directory and start a topic branch from the remote default branch. Read that clone's instructions and current project guidance. Follow **Update guidance** in the retrospective, limiting edits to `projects/<project>/` and omitting private details, secrets, excerpts, and raw comments. Keep the reviewed checkout and its Git state intact. If the guidance already covers the lessons, finish without a commit.
4. Follow **Validate and publish** in the retrospective's manual mode for the temporary clone. Confirm that the diff contains only public-safe project guidance. Publish to the ai-plugins default branch through a PR from the topic branch. Report the PR URL and validation results, or retain the patch and report its path and the specific blocker.
