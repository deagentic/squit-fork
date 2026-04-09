# ADR-0001: Refactor SQL queries to use parameterization in BigQuery

**Status:** accepted
**Deciders:** Deacero Agentic Team
**Date:** 2026-04-09
**Technical Story:** Security hardening and static analysis fixes (Bandit)

---

## Context and Problem Statement

The `squit` application interacts heavily with BigQuery. Several classes, specifically `ProgressTracker` and `VectorSearch`, construct SQL queries (`INSERT`, `UPDATE`, `SELECT`) using Python f-strings, effectively concatenating raw variables into the query strings. Additionally, a custom `_json_to_sql` method was being used to manually escape single quotes for JSON payloads. 

How can we eliminate the risk of SQL injection vulnerabilities while ensuring that complex types like JSON are safely transmitted to BigQuery?

---

## Decision Drivers

- **Security:** Need to eliminate high and medium severity vulnerabilities flagged by Bandit (`B608:hardcoded_sql_expressions`).
- **Reliability:** Manual escaping of strings (like `.replace("'", "\\'")`) is error-prone and can lead to malformed queries.
- **Maintainability:** Using standard BigQuery library features makes the code cleaner and easier for the team to read.

---

## Considered Options

- **Option 1: Continue using f-strings but improve manual sanitization methods.** (e.g., writing a more robust `escape_string` function).
- **Option 2: Use parameterized queries provided by the Google Cloud BigQuery client library.**

---

## Decision Outcome

**Chosen option:** "Option 2: Use parameterized queries provided by the Google Cloud BigQuery client library", because it delegates the responsibility of sanitization, type casting, and escaping directly to the underlying driver, which is the industry standard for preventing SQL injection.

We replaced f-string variables with standard BigQuery parameters (`@run_id`, `@status`) and leveraged `bigquery.ScalarQueryParameter` combined with `bigquery.QueryJobConfig`. We also removed the manual `_json_to_sql` method and instead relied on BigQuery's `PARSE_JSON(@param)` function combined with a parameterized JSON string.

### Positive Consequences

- Mitigated SQL injection risks across the `ProgressTracker` class.
- Cleared Bandit `B608` warnings for the refactored code.
- Removed custom, brittle escaping logic.

### Negative Consequences

- The code is slightly more verbose due to the setup of `bigquery.ScalarQueryParameter` lists and `QueryJobConfig` objects for every query.

---

## Links

- Google Cloud Documentation: [Parameterized queries in BigQuery](https://cloud.google.com/bigquery/docs/parameterized-queries)
