# Automated Python tests

These tests verify input validation, API contract behavior, token verification, and missing-statistics handling without a live football-data provider.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

CI runs the test suite with Python 3.11 and 3.12. The suite uses the **fictional player dataset** in `data/fictional_players.csv`.

PostgreSQL integration tests live separately in `integration_tests/` and require an isolated `scoutmonitor_ci` database. A successful unit-test run does not establish that the complete production application is secure or deployable.
