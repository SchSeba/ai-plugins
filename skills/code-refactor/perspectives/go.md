# Go — Refactoring Checklist

Covers **Go Backend** (non-test `.go` files) and **Go Testing** (`_test.go` files).

---

## Go Backend

### Interfaces and Dependency Injection

- Define interfaces where they are **consumed**, not where they are implemented.
- Keep interfaces small: 1–3 methods. Prefer composition of small interfaces over large ones.
- Accept interfaces, return concrete structs.
- Pass dependencies as constructor parameters (constructor injection). Avoid global state, `init()` functions, and package-level variables for dependencies.
- Each struct that has external dependencies should accept them via a `New*()` constructor.
- Use `Option` or functional options pattern for optional configuration.

### Error Handling

- Wrap errors with context: `fmt.Errorf("component: operation: %w", err)`.
- Never discard errors. If an error is intentionally ignored, add a comment explaining why.
- Use sentinel errors (`var ErrNotFound = errors.New(...)`) for expected conditions.
- Use `errors.Is()` and `errors.As()` — never compare error strings.
- Create custom error types when callers need to inspect error details beyond identity.

### Function Design

- Single responsibility: each function does one thing.
- Functions > 50 lines should be decomposed into smaller, named helper functions.
- Keep the happy path un-indented. Use early returns for error cases.
- Avoid naked returns in functions longer than a few lines.

### Package Organization

- Packages should have a clear, single purpose described by their name.
- Avoid circular dependencies. Use interfaces at package boundaries if needed.
- Use `internal/` for packages that should not be imported externally.
- Group related types, constants, and functions in the same file.

### Concurrency

- Always manage goroutine lifecycle — never fire-and-forget.
- Use `errgroup` for concurrent operations that return errors.
- Use `context.Context` for cancellation and timeouts.
- Protect shared state with `sync.Mutex` or `sync.RWMutex`.
- Add `-race` flag to test commands if introducing concurrent code.

### Performance

- Pre-allocate slices and maps when the size is known or estimable.
- Use `strings.Builder` for string concatenation in loops.
- Use pointer receivers for large structs to avoid copying.
- Use `sync.Pool` for frequently allocated/released objects in hot paths.

### Documentation

- Every exported function, type, struct, and interface must have a Go-style docstring.
- Docstring format: `// FunctionName does X. It accepts Y and returns Z.`
- Comments explain **why**, not **what**. Only comment when the reason is non-obvious.
- Package-level comments in `doc.go` for packages with public APIs.

---

## Go Testing

### Framework and Structure

- Use the project's existing test framework. If migrating to GinkgoV2, follow the project's adoption pattern.
- Use `t.Run()` subtests for table-driven tests.
- Use `t.Helper()` in test helper functions so failures report the correct line.
- Use `t.Cleanup()` for teardown instead of `defer` when possible.
- Use `t.Parallel()` where tests are independent and safe to run concurrently.

### GinkgoV2 (when the project uses it)

- Use `Describe`/`Context`/`It` blocks for BDD-style test organization.
- Use `BeforeEach`/`AfterEach` for setup/teardown.
- Use `DeferCleanup()` for resource cleanup.
- Use `DescribeTable`/`Entry` for parameterized tests.
- Matchers: prefer Gomega matchers (`Expect(...).To(...)`) over raw assertions.

### Mocking

- Generate mocks from interfaces using the project's preferred tool (`mockgen` or `mockery`).
- **Discover the mock generation command** by reading the project's `Makefile`, `go:generate` directives, or build configuration. Do not hardcode or assume a specific mock command.
- If **no mock generation tool or command is found** in the project, flag this as a finding (e.g., "No mock framework configured — skipping mock generation") and **do not generate mocks**. Do not create hand-written mocks as a fallback.
- Mocks should live in a `mocks/` subdirectory or a `*_mock_test.go` file, following the project's existing convention.
- Mocks must match the real interface behavior — do not add methods that the real interface does not have.

### Coverage

- Every exported function should have at least one test.
- Test error paths explicitly — not just happy paths.
- Test edge cases: nil inputs, empty slices, zero values, boundary conditions.
- Test concurrent access if the code uses goroutines or shared state.

### Test Isolation

- No shared mutable state between tests.
- Each test creates its own fixtures and dependencies.
- Do not rely on test execution order.
- Avoid `time.Sleep` in tests — use channels, conditions, or `Eventually` (Gomega).
