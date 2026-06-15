# Database — Refactoring Checklist

Covers `.sql` files, migrations, and code importing DB drivers or ORMs.

---

## Schema and Migrations

- Use migration files for all schema changes — never modify the database manually.
- Migrations must be reversible (include both up and down).
- Index columns used in WHERE clauses, JOIN conditions, and ORDER BY.
- Use appropriate column types and constraints (NOT NULL, UNIQUE, FOREIGN KEY).

## Query Patterns

- Parameterize all queries — never concatenate user input into SQL.
- Avoid N+1 queries: use JOINs, eager loading, or batch queries.
- Use transactions for operations that must be atomic.
- Add query timeout limits for long-running queries.

## ORM Usage

- Use the ORM's query builder for complex queries — avoid raw SQL unless necessary.
- Define model relationships explicitly.
- Use database-level constraints in addition to application-level validation.
- Index foreign key columns.

## Connection Management

- Use connection pooling. Configure pool size based on expected load.
- Handle connection errors gracefully with retries.
- Close connections and cursors properly — use context managers or deferred cleanup.
