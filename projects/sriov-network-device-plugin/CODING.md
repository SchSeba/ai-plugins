# SR-IOV Network Device Plugin — Coding

Coding conventions, architecture patterns, and common pitfalls for contributing
to the `k8snetworkplumbingwg/sriov-network-device-plugin` repository.

---

## Repository Layout

| Directory | Purpose |
|-----------|---------|
| `cmd/sriovdp/` | Binary entry point — `main.go` (flags, signal handling) + `manager.go` (resource manager) |
| `pkg/types/` | Core type definitions, interfaces (`DeviceType`, `VdpaType`, selectors, device plugin API) |
| `pkg/types/mocks/` | Generated mocks for `pkg/types` interfaces (mockery) |
| `pkg/devices/` | Device discovery — PCI enumeration, network device, RDMA, vDPA, host device operations |
| `pkg/resources/` | Resource pool management — device selectors, gRPC device plugin server, pool stub |
| `pkg/netdevice/` | Network device provider — PCI net device, NAD utils, net resource pool |
| `pkg/accelerator/` | Accelerator device provider and resource pool |
| `pkg/auxnetdevice/` | Auxiliary network device (subfunctions) provider and resource pool |
| `pkg/factory/` | Factory pattern — creates device providers, resource pools, and info providers |
| `pkg/infoprovider/` | Device info providers — RDMA, UIO, VFIO, vDPA, vhost-net, generic, extra |
| `pkg/cdi/` | Container Device Interface (CDI) spec generation and management |
| `pkg/cdi/mocks/` | Generated mocks for CDI interfaces |
| `pkg/utils/` | Utilities — sysfs helpers, netlink, DDP profiles, sriovnet, vDPA, RDMA providers |
| `pkg/utils/mocks/` | Generated mocks for utility interfaces |
| `images/` | Container image — `Dockerfile` (multi-stage), `entrypoint.sh`, DDP tool source |
| `deployments/` | Kubernetes manifests — DaemonSet, ConfigMap, CRD examples, test pod specs |
| `docs/` | Documentation and design docs |
| `.github/workflows/` | CI pipeline — build, test, lint, image push, CodeQL |

---

## Architecture Overview

### Kubernetes Device Plugin Framework

The binary implements the Kubernetes Device Plugin API (`pluginapi.DevicePluginServer`
from `k8s.io/kubelet/pkg/apis/deviceplugin/v1beta1`). The main flow is:

1. **Configuration** — Read a JSON config from `/etc/pcidp/config.json` (or
   `--config-file` flag) defining resource pools with device selectors.
2. **Discovery** — Scan the host's PCI devices via sysfs and `ghw` library,
   matching devices against selectors (vendor/device IDs, drivers, PF names,
   link types, DDP profiles, pKeys).
3. **Resource pools** — Group discovered devices into pools, each exposed as a
   Kubernetes extended resource (e.g., `intel.com/sriov_net`).
4. **gRPC server** — One gRPC server per resource pool registers with kubelet and
   handles `Allocate`, `ListAndWatch`, and `GetDevicePluginOptions` RPCs.

### Device Type Hierarchy

Three device types with parallel provider/pool patterns:

| Type | Provider | Pool | Selector |
|------|----------|------|----------|
| `netDevice` | `netdevice.netDeviceProvider` | `netdevice.netResourcePool` | PCI vendor/device, driver, PF name, link type |
| `accelerator` | `accelerator.accelDeviceProvider` | `accelerator.accelResourcePool` | PCI vendor/device, driver |
| `auxNetDevice` | `auxnetdevice.auxNetDeviceProvider` | `auxnetdevice.auxNetResourcePool` | Auxiliary device name, driver |

### Factory Pattern

`pkg/factory/` creates all providers, pools, and info providers via a singleton
`resourceFactory`. The factory is the central dependency injection point — test
code can override it for isolation.

### Info Providers

Info providers expose device metadata to containers via environment variables or
CDI annotations:

| Provider | Data exposed |
|----------|-------------|
| `rdmaInfoProvider` | RDMA device paths |
| `uioInfoProvider` | UIO device nodes |
| `vfioInfoProvider` | VFIO group and device paths |
| `vdpaInfoProvider` | vDPA device paths (virtio or vhost) |
| `vhostNetInfoProvider` | vhost-net device path |
| `genericInfoProvider` | Generic device files, environment variables, mounts |
| `extraInfoProvider` | Additional user-specified device info |

---

## Coding Conventions

### Logging

The project uses **`glog`** (`github.com/golang/glog`) for logging — **not**
klog, zerolog, or logrus:

```go
glog.Infof("resource manager reading configs")
glog.Errorf("error getting resources from file %v", err)
glog.Fatalf("Exiting.. one or more invalid configuration(s) given")
```

- Use `glog.Infof` / `glog.Warningf` / `glog.Errorf` for runtime messages.
- Use `glog.Fatalf` only for unrecoverable startup failures.
- Verbosity levels are controlled via `-v` flag (entrypoint defaults to `-v 10`).
- **Do not** import `logrus` — it is explicitly denied in `.golangci.yml`
  depguard rules.

### Error Handling

- Return errors up the call chain with context:
  ```go
  return fmt.Errorf("error reading config file: %w", err)
  ```
- Do not silently ignore errors — the `errcheck` linter enforces this.
- Hardware discovery functions must handle missing/inaccessible sysfs paths
  gracefully since devices can disappear at runtime (hot-unplug, driver unbind).

### Import Ordering

Enforced by `gci` and `goimports` formatters in `.golangci.yml`:

1. Standard library
2. External packages
3. Project-internal (`github.com/k8snetworkplumbingwg/sriov-network-device-plugin`)

```go
import (
    "fmt"
    "os"

    "github.com/jaypipes/ghw"
    pluginapi "k8s.io/kubelet/pkg/apis/deviceplugin/v1beta1"

    "github.com/k8snetworkplumbingwg/sriov-network-device-plugin/pkg/types"
)
```

### Naming Conventions

- Interfaces in `pkg/types/types.go` — all core interfaces live here.
- Mock files in `<package>/mocks/` directories — generated by mockery.
- Test helper files named `testing.go` (e.g., `pkg/utils/testing.go`,
  `pkg/resources/testing.go`) — these are excluded from lint checks.
- Test suite bootstrap files: `<package>_suite_test.go`.

### Build Tags

The binary is always built with `-tags no_openssl` (set in `Makefile`
via `GO_TAGS`). Do not introduce OpenSSL dependencies.

---

## Testing Patterns

### Framework

All tests use **Ginkgo v2 + Gomega**:

```go
import (
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

var _ = Describe("MyComponent", func() {
    Context("when configured", func() {
        It("does the right thing", func() {
            Expect(result).To(Equal(expected))
        })
    })
})
```

Dot-imports for Ginkgo, Gomega, and `gomega/gstruct` are allowed (whitelisted
in `.golangci.yml` staticcheck configuration).

### Test Suite Structure

Each package with tests has a `*_suite_test.go` bootstrap:

```go
func TestResources(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Devices Suite")
}
```

### Mocking

- Mocks are generated by **mockery** from interfaces in `pkg/types/`, `pkg/utils/`,
  and `pkg/cdi/`.
- Regenerate mocks: `make generate-mocks`.
- Tests use both mockery-generated mocks and `stretchr/testify/mock`.
- The `ginkgolinter` is enabled with `forbid-focus-container: true` — never
  commit `FIt`, `FDescribe`, `FContext`, or `FWhen` blocks.

### Test Data

- `pkg/utils/testdata/` contains test fixture files for sysfs simulation.
- Helper functions in `pkg/utils/testing.go` and `pkg/resources/testing.go`
  set up test fixtures — these files are excluded from lint checks.

### What Tests Run In CI

- `make test-race` — unit tests with race detector (requires `hwdata` package).
- `make test-coverage` — coverage tests with Coveralls reporting.
- No local E2E tests — E2E tests run through the sriov-network-operator
  checkout on self-hosted `sriov` runners with real hardware.

---

## License Headers

Two license header styles are in use:

**Intel copyright (older files)**:
```
// Copyright 2018 Intel Corp. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
```

**NVIDIA SPDX (newer files)**:
```
/*
 * SPDX-FileCopyrightText: Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES.
 * SPDX-License-Identifier: Apache-2.0
 */
```

Both are Apache 2.0 licensed. Follow the style of surrounding files when adding
new ones.

---

## Common Pitfalls

1. **Missing `-tags no_openssl`** — The build requires this tag. Use `make build`,
   never `go build` directly without the tag.
2. **Nil pointer on hardware info** — `ghw` PCI device info and network device
   attributes can be nil (incomplete sysfs data). Always nil-check before
   dereferencing.
3. **Sysfs path assumptions** — Devices can disappear between discovery passes.
   Handle `ENOENT` / `EACCES` gracefully instead of crashing.
4. **Committing vendor/ files** — The vendor directory is **not** tracked in git.
   CI runs `go mod vendor && git diff --exit-code` to check consistency, but
   vendor files themselves must not be committed.
5. **Focused Ginkgo tests** — `FIt`, `FDescribe`, etc. are forbidden by the
   `ginkgolinter` — CI will fail if you leave them in.
6. **Mock generation** — After changing interfaces in `pkg/types/`, `pkg/utils/`,
   or `pkg/cdi/`, run `make generate-mocks` or tests will fail.
7. **DDP builder stage** — The Dockerfile has a second builder stage using
   `golang:1.20` for `ddptool`. Do **not** bump this Go version — it is
   intentionally pinned for ddptool compatibility.
8. **Logrus import** — Importing `github.com/sirupsen/logrus` is blocked by
   depguard rules in `.golangci.yml`.
9. **Magic numbers** — The `mnd` linter flags hardcoded numbers in arguments,
   cases, conditions, and returns. Use named constants instead.
10. **Long functions** — `funlen` enforces max 100 lines / 50 statements per
    function. Break up large functions.
