# PostgreSQL integration tests

These tests exercise data persistence, report review rules, organization membership controls, and private-note isolation against disposable PostgreSQL 18 instances.

- `test_database.py` tests migration revisions, statistics integrity, report submission, and review constraints.
- `test_organizations.py` verifies organization membership and watchlist permissions.
- `test_private_notes.py` checks isolation at both the API and restricted PostgreSQL role levels.

Integration tests must **never run against a personal or production database**. The suite is enabled only when `SCOUTMONITOR_RUN_DB_TESTS=1` and refuses any database name except `scoutmonitor_ci`. CI provisions temporary database credentials and creates a restricted application account for row-level-security checks.

See [database setup and safety](../docs/database.md) and the [GitHub Actions workflow](../.github/workflows/code-quality.yml).
