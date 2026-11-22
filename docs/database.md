# ScoutMonitor AI — Database Migrations

ScoutMonitor AI supports versioned PostgreSQL schema creation using Alembic.

**This is designed for NEW, EMPTY databases only.** The existing local database containing stored player observations, alerts, and approved reports remains unchanged. Do not run Alembic against an existing database created using `docs/schema.sql`.

## Why migrations?

Versioned migrations document the database structure and allow future changes to be reviewed and tested systematically. The first revision (`0001`) creates the existing core tables:

- `players`
- `player_season_stats`
- `player_stat_observations`
- `performance_alerts`
- `ai_reports`

It also creates constraints that protect report approval, prevent duplicate observations and reports, and reject invalid statistics.

## Prepare an isolated database

Create a **new empty PostgreSQL database** with a distinct name, such as `scoutmonitor_demo`. Do not use your existing `scoutmonitor_db` instance.

Install requirements from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For local use, copy `.env.example` to `.env` and fill in your own local database credentials. The `DB_NAME` setting must refer to the **new empty** database.

Before invoking Alembic, explicitly confirm the migration target database name in PowerShell:

```powershell
$env:SCOUTMONITOR_MIGRATION_DATABASE = "scoutmonitor_demo"
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
```

Alternatively, for CI, set `SCOUTMONITOR_DATABASE_URL` to a PostgreSQL connection string using the `postgresql+psycopg://` driver. `SCOUTMONITOR_MIGRATION_DATABASE` must still match the exact database name. Never put connection strings containing credentials into Git-tracked files.

## Safety protections

- Alembic refuses to start unless you explicitly confirm the exact target database name.
- Alembic refuses to migrate a database with existing manually created tables and no Alembic version history.
- The initial schema migration uses a transaction on PostgreSQL.
- No production or local application database is modified automatically by GitHub Actions.
- Automatic downgrade (table deletion) is deliberately disabled to protect records.
- Adoption/migration of an existing live database requires a separate, reviewed and backed-up procedure. **Do not run `alembic stamp` on a live database.**

If creating a new database from scratch through Alembic, do **not** run `docs/schema.sql` in the same database; both create the same tables.

## Automated integration tests

GitHub Actions launches a short-lived PostgreSQL 18 service named `scoutmonitor_ci`, applies the schema, reruns the migration to confirm idempotence, and runs separate database integration tests. All credentials in CI are disposable test-only values.

Tests cover schema revision, NULL preservation, report storage, approval, prevention of duplicate reviews, invalid report rejection, duplicate observations, and enforcement of approval constraints. Each test runs in a transaction and rolls back.

To run them in your own isolated test environment, use a database named exactly `scoutmonitor_ci` and explicitly set:

```powershell
$env:SCOUTMONITOR_RUN_DB_TESTS = "1"
$env:SCOUTMONITOR_MIGRATION_DATABASE = "scoutmonitor_ci"
```

Provide credentials through `SCOUTMONITOR_DATABASE_URL` locally. The integration test suite deliberately refuses other database names.

## Next steps

Once this baseline passes, future database changes should be implemented as new forward-only migration revisions, tested on disposable databases before any real-data rollout. Next priorities are integration tests for the data-ingestion workflow, authorization, and organization-level data separation.
