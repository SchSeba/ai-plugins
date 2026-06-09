# Refactoring Perspectives Reference

Technology-specific refactoring checklists for the `code-refactor` skill. Each domain has its own file under `perspectives/` containing the criteria a specialized sub-agent uses when refactoring files in that domain.

## File-to-Domain Mapping

| File pattern | Refactoring domain | Checklist |
|---|---|---|
| `.go` (non-test) | Go Backend | [perspectives/go.md](perspectives/go.md) |
| `_test.go` | Go Testing | [perspectives/go.md](perspectives/go.md) |
| `.ts`, `.tsx`, `.js`, `.jsx` | TypeScript / React Frontend | [perspectives/typescript-react.md](perspectives/typescript-react.md) |
| `.test.ts`, `.test.tsx`, `.spec.ts`, `.spec.tsx` | Frontend Testing | [perspectives/typescript-react.md](perspectives/typescript-react.md) |
| `.py` (non-test) | Python Backend | [perspectives/python.md](perspectives/python.md) |
| `_test.py`, `test_*.py`, `conftest.py` | Python Testing | [perspectives/python.md](perspectives/python.md) |
| `.rs` | Rust | [perspectives/rust.md](perspectives/rust.md) |
| `.sql`, migrations, code importing DB drivers / ORMs | Database | [perspectives/database.md](perspectives/database.md) |
| `.sh`, `.bash`, `Makefile`, `Dockerfile`, `Containerfile`, CI configs | Shell / Build / CI | [perspectives/shell-build-ci.md](perspectives/shell-build-ci.md) |
| `.yaml`/`.yml` in `k8s/`, `deploy/`, `helm/`, `charts/`, operator code | Kubernetes / Config | [perspectives/kubernetes-config.md](perspectives/kubernetes-config.md) |
| Code importing logging, metrics, or tracing libraries | Observability | [perspectives/observability.md](perspectives/observability.md) |

A file may belong to multiple domains. When that happens, assign it to the most specific domain (e.g., a Go file with database queries goes to "Database" for query refactoring and "Go Backend" for structural refactoring).

## Domain-to-Checklist Mapping

| Checklist file | Domains covered |
|---|---|
| [perspectives/go.md](perspectives/go.md) | Go Backend, Go Testing |
| [perspectives/typescript-react.md](perspectives/typescript-react.md) | TypeScript / React Frontend, Frontend Testing |
| [perspectives/python.md](perspectives/python.md) | Python Backend, Python Testing |
| [perspectives/rust.md](perspectives/rust.md) | Rust |
| [perspectives/database.md](perspectives/database.md) | Database |
| [perspectives/shell-build-ci.md](perspectives/shell-build-ci.md) | Shell / Build / CI |
| [perspectives/kubernetes-config.md](perspectives/kubernetes-config.md) | Kubernetes / Config |
| [perspectives/observability.md](perspectives/observability.md) | Observability |

## How to Use

When spawning a specialized sub-agent for a domain, **read only the checklist file(s) relevant to that domain** and pass the content to the sub-agent. This keeps each sub-agent's context focused and avoids loading unnecessary rules for unrelated technologies.
