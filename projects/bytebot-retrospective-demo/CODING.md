# ByteBot Retrospective Demo — Coding

Implementation conventions for `schsebabot/bytebot-retrospective-demo`.

## Runnable JSON examples

When adding or changing a runnable JSON example, include a matching checked-in
JSON Schema and a negative fixture. Validate the runnable example against the
schema in CI and assert that the negative fixture is rejected. Parsing JSON alone
does not verify the example's required settings.

For the connection example, keep `timeout_ms` required in
`examples/connection.schema.json`. Keep
`examples/invalid/connection-no-timeout.json` without that key and test that schema
validation rejects it. The accepted implementation in `test_examples.py` validates
`examples/connection.json` and asserts a `ValidationError` for the negative
fixture; `.github/workflows/examples.yml` runs that test in CI.

Before submitting a change, verify that the example and schema agree, the
negative fixture exercises the required-field rule, and CI runs both the valid
and invalid cases. Discover the current test invocation and dependencies from the
repository's workflow rather than assuming a JSON parse check is sufficient.

Source: [PR #1](https://github.com/schsebabot/bytebot-retrospective-demo/pull/1).
The repository owner's standing request and follow-up were verified in the final
diff at commit `85334dd5bf2f38373cf60dc01008d5c1ab852403`, including the schema,
missing-timeout fixture, rejection assertion, and CI wiring. Captured 2026-11-13.
