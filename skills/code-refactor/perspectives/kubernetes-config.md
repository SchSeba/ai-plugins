# Kubernetes / Config — Refactoring Checklist

Covers `.yaml`/`.yml` in `k8s/`, `deploy/`, `helm/`, `charts/`, and operator code.

---

## Manifests

- Use labels consistently: `app.kubernetes.io/name`, `app.kubernetes.io/version`, etc.
- Define resource requests and limits for all containers.
- Use liveness, readiness, and startup probes with appropriate thresholds.
- Use `SecurityContext`: non-root user, read-only root filesystem, drop all capabilities.

## Operator Code

- Reconcile loop correctness: handle requeue, errors, and edge cases.
- Update status subresource with conditions following the Kubernetes conventions.
- Implement finalizers correctly: check deletion timestamp, clean up, remove finalizer.
- RBAC: least-privilege roles. Use kubebuilder markers to generate RBAC rules.

## Helm Charts

- Parameterize all configurable values — do not hardcode in templates.
- Provide sensible defaults in `values.yaml`.
- Use `_helpers.tpl` for reusable template functions.
- Validate values with JSON schema (`values.schema.json`).
