# Review Perspectives Reference

## File-to-Perspective Mapping

| Changed file pattern | Review perspective |
|---|---|
| `.go` (non-test) | Go |
| `.py` (non-test) | Python |
| `.ts`, `.tsx`, `.js`, `.jsx`, `.css`, `.html` | Frontend |
| `.sql`, migrations, or code importing DB drivers | Database |
| `.yaml`/`.yml` in `k8s/`, `deploy/`, `helm/`, `charts/` | Kubernetes |
| Code importing `netlink`, `sysfs`, `cgroup`, `unix.Syscall` | Linux Systems |
| `*_test.go`, `*.test.ts`, `*.spec.ts`, `*_test.py` | Test |
| API handler, route, or middleware files | API |
| `Dockerfile`, `Containerfile`, `.dockerignore` | Dockerfile |
| `.sh`, `.bash`, `Makefile` | Shell & Build Script |
| `.tf`, `.tfvars`, `terragrunt.hcl` | Terraform / IaC |
| `go.mod`, `go.sum`, `package.json`, `*lock*`, `requirements.txt`, `pyproject.toml` | Dependency |
| `CHANGELOG.md`, `RELEASE_NOTES.md`, `docs/` | Documentation |
| Changes spanning 2+ packages/services without integration tests | Integration & E2E Test |
| **All code** (always apply) | **Security**, **Performance** |

---

## Go

- Idiomatic patterns and stdlib usage (`io`, `context`, `errors`, `slices`, `maps`)
- Error handling: wrapping with `%w`, `errors.Is`/`As`, sentinel errors, custom types
- Concurrency: goroutine lifecycles, channel ownership, sync primitives, `errgroup`
- Interface design: small interfaces, accept interfaces return structs, embedding
- Performance: allocation reduction, `strings.Builder`, slice pre-allocation, `sync.Pool`
- Package naming, circular dependency avoidance, internal packages
- Module hygiene: unnecessary deps, `replace` directives
- Race detection: if new goroutines or shared state are introduced, flag missing `-race` in CI

## Python

- Type hints on function signatures; avoid `Any` escape hatches
- Async patterns: proper `async`/`await`, no blocking in async context
- Error handling: specific exception types, context managers for resources
- Dependency management: pinned versions, no unused deps
- Security: `eval()`/`exec()`, `pickle` of untrusted data, SQL injection in ORMs
- Performance: generators for large datasets, `__slots__` for data classes
- Style: f-strings, `pathlib`, dataclasses/Pydantic for structured data
- Testing: `pytest` fixtures, parametrize, proper mocking

## Frontend

- React hooks: deps arrays, cleanup, justified `memo`/`useMemo`/`useCallback`
- Component design: single responsibility, prop drilling avoidance, composition
- State: local vs global, unnecessary re-renders, derived state
- TypeScript: strict typing, no `any`, proper generics, discriminated unions
- Accessibility: ARIA attributes, keyboard navigation, screen reader, focus management
- Performance: bundle size, lazy loading, virtualization for long lists
- Error handling: error boundaries, loading/empty/fallback states
- Security: XSS via `dangerouslySetInnerHTML`, user content sanitization

## Security (always apply)

- SQL/command/path traversal injection
- Hardcoded credentials or secrets in code/config
- Broken auth/authz: missing RBAC, IDOR, JWT validation gaps
- Sensitive data exposure: logging secrets, error message leaks, stack traces in responses
- Insecure crypto: MD5/SHA1 for passwords, weak keys, predictable randomness
- SSRF, CSRF, XSS in web handlers
- Unsafe deserialization of untrusted input
- Missing input validation at system boundaries (HTTP handlers, CLI args, env vars)
- Container/K8s: privileged pods, host networking, missing seccomp/AppArmor
- Dependency vulnerabilities: known CVEs
- TOCTOU race conditions

## Kubernetes

- Reconcile loop correctness, status subresource updates, conditions
- CRD design: validation, defaulting, conversion webhooks, CEL rules
- RBAC: least-privilege Role/ClusterRole, kubebuilder markers
- Finalizer patterns: cleanup, race conditions, deletion timestamp
- Watch/cache efficiency: field selectors, label selectors, index functions
- Leader election and HA patterns
- Health probes: readiness vs liveness semantics, startup probes
- Scheduler framework: PreFilter, Filter, Score, Reserve, Permit, Bind
- DRA: ResourceClaim lifecycle, ResourceClass design
- client-go: informers, listers, work queues, shared informer factory

## Linux Systems

- sysfs/procfs access: error handling for missing files, ENODEV, EACCES
- Netlink: message parsing, attribute handling, multicast groups, NLA alignment
- `vishvananda/netlink`: Handle vs default, namespace-aware operations
- cgroup v2: hierarchy management, controller delegation, `subtree_control`
- Namespace operations: `setns`, `unshare`, cleanup, `runtime.LockOSThread()`
- FD lifecycle: leaks, CLOEXEC flags, `/proc/self/fd`
- eBPF: verifier constraints, map types, BTF, CO-RE patterns
- Syscall wrappers: errno handling, platform-specific behavior

## Performance (always apply)

- Memory allocations in hot paths (escape analysis, heap vs stack)
- Slice/map pre-allocation when size is known
- String concatenation in loops (`strings.Builder`, `bytes.Buffer`)
- Unnecessary copying of large structs (use pointer receivers)
- DB query efficiency: N+1 queries, missing indexes, full table scans
- Connection pooling: HTTP clients, DB connections, gRPC channels
- Caching: `singleflight` for stampede protection, TTL eviction
- Context timeouts on all external calls
- Streaming vs buffering for large payloads (`io.Reader` pipelines)
- Regex: compile once, not per-call

## Test

- Coverage: are new/changed code paths tested?
- Table-driven tests with `t.Run()` subtests
- Edge cases: nil inputs, empty slices, zero values, boundaries
- Error path testing: not just happy paths
- Isolation: no shared mutable state, `t.Cleanup()`
- Mock quality: mocks match real interface behavior
- Flaky indicators: `time.Sleep`, race conditions, order-dependent
- Benchmarks for performance-critical paths
- **Regression coverage**: bug-fix PRs must include a test for the previously-broken scenario
- **Edge case completeness**: for each changed function, identify 2-3 untested edge cases (empty/nil inputs, overflow, concurrent access, permission boundaries, first-use vs steady-state)

## API

- REST conventions: HTTP methods, status codes, resource naming
- Backwards compatibility: no breaking changes without versioning
- Error responses: consistent format, appropriate codes, no internal details
- Input validation: request body, query params, path params
- Pagination: consistent pattern, proper defaults and limits
- Auth/authz: middleware applied, scope checks
- Idempotency: PUT/DELETE idempotent, POST with idempotency keys

## Dockerfile

- Multi-stage builds: build deps excluded from final image
- Layer caching: frequently-changing steps placed last
- Base image: pinned tag/digest (not `latest`), minimal base (`distroless`, `alpine`)
- Security: non-root `USER`, secrets mounted not passed via build args
- `.dockerignore`: excludes `.git`, `node_modules`, test files
- `HEALTHCHECK` defined for production images
- Package cache cleanup in same layer as install
- No unnecessary tools or debug utilities in final image

## Shell & Build Script

- Safety: `set -euo pipefail`
- Quoting: all variable expansions properly quoted (`"$var"`)
- Portability: bash features require `#!/bin/bash` shebang
- Error handling: command failures checked, cleanup traps (`trap cleanup EXIT`)
- Shellcheck compliance: SC2086, SC2046, SC2034
- Makefile: `.PHONY` targets, correct dependencies
- No hardcoded credentials or tokens

## Terraform / IaC

- Remote state configured with locks enabled
- Module design: reusable, properly parameterized
- Security: `sensitive = true` for secrets, least-privilege IAM
- Plan safety: no unexpected destroys or replacements
- Resource naming: consistent conventions, `name_prefix` for uniqueness
- Provider versions pinned via `required_providers`
- Variable validation blocks
- Outputs defined for downstream consumers

## Dependency

- **New deps**: well-maintained? Necessary, or can stdlib handle it?
- **License compatibility**: flag GPL in non-GPL projects
- **Major version bumps**: breaking changes accounted for?
- **Removed deps**: all usage also removed from codebase?
- **Security**: known CVEs in dependencies
- **Bloat**: small utility pulling large dependency tree?
- **Go-specific**: unnecessary `replace` directives, appropriate `go` version
- **JS-specific**: `dependencies` vs `devDependencies` classification, lockfile consistency

## Documentation

Apply when public APIs, CLI commands, or configuration options change. Skip when no public-facing interfaces changed.

- Exported symbol changes: godoc / JSDoc / docstring updated?
- CLI flag changes: usage help / README updated?
- Config changes: example configs and docs updated?
- API endpoint changes: OpenAPI spec / README updated?
- README accuracy after this PR
- Changelog entry: especially for breaking changes, new features, security fixes, deprecations
- Flag missing docs as **medium-severity** (additive) or **high-severity** (breaking)

## Integration & E2E Test

Apply when changes span 2+ packages, services, or layers.

- **Cross-component coverage**: multi-layer changes need integration tests with real dependencies (not just mocked unit tests)
- **E2E for new user flows**: new API endpoints consumed by frontend need end-to-end tests
- **Contract consistency**: API response shape changes must update AND test all consumers together
- **State lifecycle across boundaries**: when Service A creates state that Service B reads, test with real data
- **Patterns to flag**: handler tests mocking the service layer for new endpoints, service tests mocking repositories for complex queries, frontend tests with hardcoded API shapes
- **Recommendation threshold**: if the PR touches 2+ layers (handler, service, repository, model, frontend) with NO integration/e2e tests, flag as **high-severity**
