# Shell / Build / CI — Refactoring Checklist

Covers `.sh`, `.bash`, `Makefile`, `Dockerfile`, `Containerfile`, and CI pipeline configs.

---

## Shell Scripts

- Start with `set -euo pipefail` for safety.
- Quote all variable expansions: `"$var"`, not `$var`.
- Use `#!/bin/bash` shebang when using bash-specific features.
- Add error handling: check command return codes, use `trap cleanup EXIT`.
- Pass ShellCheck: address SC2086 (double-quote), SC2046 (quote command substitution), SC2034 (unused variables).

## Makefiles

- Declare `.PHONY` for all non-file targets.
- Use variables for repeated values (compiler flags, paths, versions).
- Add help target that documents available targets.
- Order targets logically: build, test, lint, clean, deploy.

## Dockerfiles

- Use multi-stage builds to separate build dependencies from runtime.
- Pin base image tags or digests — never use `latest`.
- Run as non-root `USER` in the final stage.
- Minimize layers: combine related `RUN` commands.
- Clean up package caches in the same layer as the install.
- Use `.dockerignore` to exclude unnecessary files.

## CI Pipelines

- Cache dependencies between builds (Go modules, npm packages, pip packages).
- Run lint, test, and build in parallel where possible.
- Use matrix builds for multi-platform or multi-version testing.
- Pin action versions in GitHub Actions.
