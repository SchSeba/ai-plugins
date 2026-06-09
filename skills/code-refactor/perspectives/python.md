# Python — Refactoring Checklist

Covers **Python Backend** (non-test `.py` files) and **Python Testing** (`_test.py`, `test_*.py`, `conftest.py` files).

---

## Python Backend

### Type Hints

- Annotate ALL function signatures: parameters and return types.
- Avoid `Any` unless truly necessary — prefer `Union`, `Optional`, `Protocol`.
- Use `TypedDict` for dictionary shapes.
- Use `Protocol` for structural typing (duck-typing with type safety).
- Use `dataclasses` or Pydantic models for structured data — avoid raw dicts.

### Error Handling

- Use specific exception types — never bare `except:` or `except Exception:` without re-raising.
- Use context managers (`with` statements) for all resource management.
- Create custom exception classes for domain-specific errors.
- Chain exceptions with `raise NewError(...) from original_error`.

### Async Patterns

- If the project uses async: `async`/`await` consistently. No blocking calls in async contexts.
- Use `asyncio.gather()` for concurrent operations.
- Use `async with` for async context managers.

### Function Design

- Single responsibility. Functions > 50 lines should be decomposed.
- Use keyword-only arguments for functions with > 3 parameters.
- Use `*args` and `**kwargs` sparingly — prefer explicit parameters.

### Documentation

- Docstrings on all public functions, classes, and modules.
- Use the project's existing docstring style (Google, NumPy, or Sphinx).
- Include parameter descriptions, return types, and raised exceptions.

### Dependency Injection

- Pass dependencies as constructor or function parameters.
- Use `Protocol` classes for dependency interfaces.
- For FastAPI: use `Depends()` for DI.
- For Django: use service layer pattern with injected repositories.

---

## Python Testing

- Use `pytest` with fixtures. `@pytest.mark.parametrize` for data-driven tests.
- Test async code with `pytest-asyncio`.
- Fixtures in `conftest.py` for shared setup.
- Mock external dependencies; test internal logic directly.
- Test edge cases: empty inputs, None values, type errors, boundary conditions.
