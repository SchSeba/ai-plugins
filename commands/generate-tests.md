---
name: generate-tests
description: Generate comprehensive test suites for specified code, discovering project testing conventions automatically. Use when asked to add tests, create test files, improve test coverage, or generate unit/integration tests.
---

# Generate Tests Command

Use the text after the command name as the target file, component, or module to generate tests for. If your command runtime exposes `$ARGUMENTS`, treat it as that same value.

If no target was provided, ask the user which file, component, or module they want tests for before proceeding.

## Workflow

### Step 1 — Read project guidelines and discover the testing setup (MANDATORY — Do this FIRST)

Before writing any test code, read the project's conventions and discover how it runs tests:

1. **Read `.ai-rules/`** — If the target project has an `.ai-rules/` directory, read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain previously learned knowledge about this project — coding conventions, validation commands, and review patterns discovered during past sessions. **This is the highest-priority source** because it reflects confirmed, project-specific knowledge.
2. **Read `projects/<project-name>/`** — If this plugin repository has a `projects/<project-name>/` directory (where `<project-name>` matches the target project's repo name), read all files in it (`CODING.md`, `VALIDATION.md`, `REVIEWING.md`). These contain knowledge shared across all skills in this plugin, discovered during past sessions with this project.
3. **Read `AGENTS.md`** — This is the primary source of project conventions, architecture rules, and agent-specific instructions. If this file exists, its rules override any defaults in this skill.
4. **Read `CONTRIBUTING.md`** — Contribution workflow, PR format, commit conventions.
5. **Read `CLAUDE.md`** or equivalent — Additional AI-agent instructions the project maintainers have set.
6. **Read `Makefile` / build scripts** — Understand the build, test, and lint commands available.
7. **Read testing and linting configs** — Discover the testing framework, assertion library, and test runner from dependency/config files in the project.

> **Rule:** If any of these files exist and contain instructions, you MUST follow them. Project-specific conventions always take precedence over the generic guidelines in this skill.

8. **Identify the test framework** — Determine which testing framework and assertion library the project (or the specific package you are targeting) uses. Examine existing test files for import statements, test function signatures, and assertion patterns. You MUST use the same framework and style for the tests you generate.
9. **Study existing test patterns** — Find existing test files in the project and study their naming conventions, directory structure, import style, assertion library, and setup/teardown approach.

> **CodeGraph-first rule:** If CodeGraph MCP is configured and available, prefer `codegraph_explore` to discover the target's structure and dependencies. If the `.codegraph/` directory is missing, run `codegraph init` in the project root first. If CodeGraph is not available, **inform the user** and fall back to manual exploration.

Do **not** assume any specific testing framework or tool. Discover it from the project files.

### Step 2 — Analyze the target

1. Read the target file or component specified in `$ARGUMENTS`.
2. Identify all testable units: exported functions, methods, classes, API endpoints, state transitions, and significant branches.
3. Map external dependencies that will need mocking (network calls, databases, file I/O, third-party services).
4. Note edge cases: boundary values, empty/nil inputs, error paths, concurrency concerns, and permission checks.

### Step 3 — Plan the test suite

Outline the tests before writing code:

1. **Unit tests** — one or more tests per public function/method, covering the happy path, error cases, and edge cases.
2. **Integration tests** — tests for interactions between components, if applicable.
3. **Edge-case tests** — boundary values, empty inputs, malformed data, timeout/retry behavior.

Group related tests logically (by function, by feature, or by scenario) following the project's existing grouping pattern.

### Step 4 — Generate test files

Create test files following the project's naming and directory conventions discovered in Step 1.

For each test:

1. **Arrange** — set up test data, mocks, and preconditions.
2. **Act** — call the function or trigger the behavior under test.
3. **Assert** — verify the result matches expectations.

Follow these guidelines:

- Use **descriptive test names** that explain the scenario and expected outcome.
- Follow the **Arrange-Act-Assert** (AAA) pattern for clarity.
- **Group related tests** using the project's grouping mechanism (test suites, describe blocks, sub-tests, or equivalent).
- **Mock external dependencies** — do not make real network calls, database queries, or file system changes in unit tests.
- **Reuse existing test utilities** — check for test helpers, fixtures, factories, or shared mocks already in the project before creating new ones.
- Add necessary **setup and teardown** logic to keep tests isolated.
- Aim for **80%+ code coverage** on critical paths (business logic, error handling, security-sensitive code).
- Adapt to the project's testing framework and conventions — use the patterns discovered in Step 1, not defaults from other projects.

### Step 5 — Verify

1. Run the project's test command (discovered in Step 1) to confirm all new tests pass.
2. Review test output for failures, skipped tests, or unexpected warnings.
3. If any tests fail, fix them and re-run until the suite is green.
4. Check coverage if the project has a coverage tool — identify any remaining gaps in critical paths and add missing tests.

### Step 6 — Summary

Present a summary to the user:

- Number of test files created or updated.
- Number of test cases added, grouped by type (unit, integration, edge case).
- Coverage delta (if measurable).
- Any areas that could not be tested automatically and why (e.g., requires hardware, manual UI interaction, or external service).
