# Rust — Refactoring Checklist

Covers all `.rs` source files.

---

## Ownership and Borrowing

- Prefer borrowing (`&T`) over cloning unless ownership transfer is necessary.
- Use `Cow<'_, str>` when a function may or may not need to allocate.
- Use `Arc`/`Rc` only when shared ownership is genuinely required.

## Error Handling

- `thiserror` for library errors. `anyhow` for application errors.
- Use the `?` operator for ergonomic error propagation.
- Create domain-specific error enums with `#[derive(thiserror::Error)]`.

## Crate Structure

- Use workspace `Cargo.toml` for multi-crate projects.
- Minimize public API surface — use `pub(crate)` for internal items.
- Feature flags for optional functionality.

## Testing

- `#[cfg(test)]` modules for unit tests in the same file.
- Integration tests in `tests/` directory.
- Use `proptest` or `quickcheck` for property-based testing where applicable.
- Test `Result` and `Option` paths explicitly.

## Documentation

- `///` doc comments on all public items.
- Include examples in doc comments (they are compiled and tested by `cargo test`).
- Module-level documentation with `//!`.
