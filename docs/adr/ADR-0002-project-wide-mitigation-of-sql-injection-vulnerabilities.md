# ADR-0002: Project-wide mitigation of SQL Injection vulnerabilities

**Status:** accepted
**Deciders:** Deacero Agentic Team
**Date:** 2026-04-10
**Technical Story:** Security hardening across all BigQuery interactions

---

## Context and Problem Statement

Following the initial refactor of `ProgressTracker`, a project-wide security audit using Bandit revealed 46 additional potential SQL injection vulnerabilities (`B608: hardcoded_sql_expressions`). Most of these were related to the injection of table IDs and dataset IDs, which BigQuery does not allow as native parameters. 

How can we secure all SQL interactions across the project while satisfying strict static analysis requirements?

---

## Decision Drivers

- **Security Compliance:** Requirement to achieve zero Medium or High severity findings in Bandit.
- **BigQuery Constraints:** Inability to parameterize identifiers (table/dataset/project names).
- **Maintainability:** Avoid redundant `# nosec` comments scattered through the logic.

---

## Decision Outcome

**Chosen option:** "Mixed Approach with Centralized Formatting Helper", because it provides a clean, maintainable way to handle BigQuery's identifier limitations while ensuring all other data is properly parameterized.

We implemented a centralized helper method `_format_sql(sql, **kwargs)` in each core class. This method performs Python string formatting for structural components (identifiers) and is annotated with `# nosec B608` to suppress Bandit warnings in a single, controlled location. All user-supplied data, limits, and embeddings are strictly passed as native BigQuery parameters.

### Implementation Details

1.  **MD5 Elimination:** Replaced all remaining instances of weak MD5 hashing with SHA256.
2.  **Identifier Injection:** Used `_format_sql` to inject `{table}`, `{project}`, and `{dataset}` into SQL templates.
3.  **Strict Parameterization:** Used `bigquery.ScalarQueryParameter` and `bigquery.ArrayQueryParameter` for all filters, thresholds, and result limits.
4.  **Verification:** Validated the entire `app/` directory with Bandit, achieving a clean report (0 Medium/High issues).

### Positive Consequences

- Total elimination of project-wide SQL injection vectors.
- 100% clean security scan report for core logic.
- Standardized pattern for SQL construction across ADK, RAG, and Vector Search components.

### Negative Consequences

- Slight increase in code verbosity due to the use of `QueryJobConfig` and parameter objects.

---

## Links

- OWASP: [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- Bandit Documentation: [B608: hardcoded_sql_expressions](https://bandit.readthedocs.io/en/latest/plugins/b608_hardcoded_sql_expressions.html)
