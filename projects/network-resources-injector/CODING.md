# Network Resources Injector — Coding

Coding conventions, architecture patterns, and common pitfalls for contributing
to the `k8snetworkplumbingwg/network-resources-injector` repository.

---

## Repository Layout

| Directory | Purpose |
|-----------|---------|
| `cmd/webhook/` | Main webhook server entry point — HTTP/TLS server, certificate watching, control loop |
| `cmd/installer/` | Self-installer binary for webhook configuration registration |
| `pkg/webhook/` | Core admission webhook logic — mutating handler, JSON patch generation, TLS config/utils |
| `pkg/types/` | Shared type definitions (`JSONPatchOperation`) and constants (downward API paths, hugepage paths) |
| `pkg/controlswitches/` | Feature flags — CLI-based and ConfigMap-driven runtime control switches |
| `pkg/userdefinedinjections/` | User-defined injection rules parsed from a ConfigMap |
| `pkg/tools/` | Network Attachment Definition (NAD) cache using informers |
| `pkg/installer/` | Installer logic for self-registering the `MutatingWebhookConfiguration` |
| `scripts/` | Build, test, E2E setup/teardown, image build, and webhook deployment helpers |
| `test/e2e/` | End-to-end tests (hugepages, node selector, resource name, user-defined injections, control switches) |
| `test/util/` | E2E test utility functions |
| `deployments/` | Kubernetes manifests — RBAC (`auth.yaml`), PDB, Deployment, Service, `MutatingWebhookConfiguration` |
| `docs/` | Installation documentation |

---

## Architecture: Mutating Admission Webhook

NRI is a **Kubernetes Mutating Admission Webhook** that intercepts pod creation
requests and injects network-related resources. The core flow is:

1. **Kubernetes API server** sends an `AdmissionReview` request to the `/mutate`
   endpoint.
2. **`MutateHandler`** (`pkg/webhook/webhook.go`) deserializes the request,
   extracts the pod spec, and determines what mutations are needed.
3. The handler reads `k8s.v1.cni.cncf.io/networks` annotations to identify
   requested Network Attachment Definitions (NADs).
4. For each NAD, NRI:
   - Looks up the NAD (via cache or API) to find associated resource names.
   - Injects resource requests/limits into the first container.
   - Optionally injects hugepage requests as downward API volumes.
   - Optionally injects node selector labels from the NAD.
   - Applies user-defined custom injections from a ConfigMap.
5. The handler returns a JSON patch response to the API server.

### Key Components

| Component | Role |
|-----------|------|
| `MutateHandler` | Main HTTP handler — orchestrates the full mutation flow |
| `NetAttachDefCache` | In-memory cache of NADs populated via informers (avoids API calls per pod) |
| `ControlSwitches` | Feature toggles — set via CLI flags at startup, overridable at runtime via a ConfigMap |
| `UserDefinedInjections` | Custom JSON patches defined in a ConfigMap, applied to every pod |
| `tlsKeypairReloader` | Hot-reloads TLS certificates when files change (via fsnotify) |

### Global State Pattern

NRI uses **package-level variables** in `pkg/webhook/` to hold shared state:

```go
var (
    clientset             kubernetes.Interface
    nadCache              netcache.NetAttachDefCacheService
    userDefinedInjections *userdefinedinjections.UserDefinedInjections
    controlSwitches       *controlswitches.ControlSwitches
)
```

These are set once at startup via `Set*()` functions called from `main()`.
This is the established pattern — do not refactor to dependency injection
without a broader design discussion.

---

## Coding Conventions

### Logging

NRI uses **`github.com/golang/glog`** (not klog, not zerolog):

```go
glog.Infof("message: %v", value)
glog.Errorf("error: %v", err)
glog.Warningf("warning: %s", msg)
glog.V(2).Infof("verbose debug: %v", event)  // verbosity levels
glog.Fatalf("fatal: %v", err)                 // exits the process
```

Do **not** use `fmt.Printf`, `log.Printf`, or `klog` for runtime logging.

### Error Handling

- Use `github.com/pkg/errors` for wrapping: `errors.Wrap(err, "context")`,
  `errors.Errorf("message: %v", val)`, `errors.New("message")`.
- Do **not** use bare `fmt.Errorf` — the project consistently uses `pkg/errors`.
- Fatal errors in `main()` use `glog.Fatalf`.

### Import Ordering

The `.golangci.yml` enforces import ordering via `goimports` with local prefix:

```
github.com/k8snetworkplumbingwg/network-resources-injector
```

Standard ordering: stdlib → external → k8s.io → local project.

### Naming Conventions

- Package names are lowercase, single-word where possible (`webhook`, `cache`,
  `controlswitches`).
- The `cache` package uses the import alias `netcache` throughout the codebase
  to avoid collision with `k8s.io/client-go/tools/cache`.
- Type names use PascalCase: `ControlSwitches`, `UserDefinedInjections`,
  `NetAttachDefCache`.
- Constants use PascalCase: `DownwardAPIMountPath`, `Hugepages1GRequestPath`.

### Build Tags

- The build uses `-tags no_openssl` to avoid CGO/OpenSSL dependencies.
- Unit tests use `-tags unittests` (configured in `.golangci.yml` and
  `scripts/test.sh`).

### License Headers

Every source file must include the Apache 2.0 license boilerplate:

```go
// Copyright (c) <year> <organization>
//
// Licensed under the Apache License, Version 2.0 (the "License");
// ...
```

---

## Testing Patterns

### Unit Tests

- Use **Ginkgo v1** + **Gomega** framework (note: Ginkgo v1, not v2).
- Each package has a `*_suite_test.go` file that bootstraps the Ginkgo runner.
- Tests live alongside the code in the same package (white-box testing).
- Tests are run with the `unittests` build tag.

Example suite bootstrap:

```go
func TestWebhook(t *testing.T) {
    log.SetOutput(io.Discard)
    RegisterFailHandler(Fail)
    RunSpecs(t, "Webhook Suite")
}
```

### E2E Tests

- Live in `test/e2e/` — also use Ginkgo v1 + Gomega.
- Require a running Kubernetes cluster (KinD-based setup via
  `scripts/e2e_setup_cluster.sh`).
- Test areas: hugepage injection, node selector propagation, resource name
  injection, user-defined injections, control switches.
- Run with: `go test -timeout 60m -v ./test/e2e/...`
- E2E utilities in `test/util/` (hugepage availability checks, pod helpers).

### Test Coverage

Unit tests generate coverage profiles via `scripts/test.sh`:

```bash
go test --tags=unittests -race -coverprofile="$filePath" "./pkg/..."
```

---

## Common Pitfalls

1. **Forgetting the `no_openssl` build tag** — The build script uses
   `-tags no_openssl`. Without it, the cfssl dependency may try to link against
   OpenSSL and fail.

2. **Forgetting the `unittests` build tag** — Unit tests require
   `-tags unittests`. Running `go test ./pkg/...` without it will skip tests.

3. **Using the wrong Ginkgo version** — The project uses Ginkgo v1
   (`github.com/onsi/ginkgo`), not v2 (`github.com/onsi/ginkgo/v2`). Do not
   import from `ginkgo/v2` in existing test files.

4. **Cache import alias** — The `pkg/tools` package is named `cache` in Go but
   imported as `netcache` everywhere. Using the bare `cache` name will conflict
   with `k8s.io/client-go/tools/cache`.

5. **Modifying global state setters** — The `Set*()` functions in
   `pkg/webhook/` are called once at startup. Do not add concurrent-write
   patterns without synchronization.

6. **ConfigMap polling loop** — The main goroutine polls the control-switches
   ConfigMap every 30 seconds. Changes to this polling logic must consider
   API error handling — only `IsNotFound` errors should reset to defaults;
   other API errors should be logged and skipped.

7. **JSON patch ordering** — The order of JSON patch operations matters.
   Patches that create parent paths (e.g., adding annotations) must come
   before patches that modify children. The `appendAddAnnotPatch` function
   handles this — do not reorder patch generation.

8. **TLS certificate reloading** — Both cert and key files must be updated
   before `Reload()` triggers. The fsnotify watcher tracks both files and
   only reloads when both have been updated.
