# PostgreSQL migrations

Alembic provides the versioned schema for **new, empty** ScoutMonitor AI databases.

| Revision | Scope |
|---|---|
| `0001` | Players, observations, alerts, and AI report review |
| `0002` | Organizations, verified identities, memberships, and watchlists |
| `0003` | Organization-owned human-authored notes and row-level security |

**Do not apply these migrations to a legacy database created using `docs/schema.sql`.** The migration environment refuses non-Alembic tables, and schema adoption requires a separately reviewed backup and transition plan.

The migration environment also requires `SCOUTMONITOR_MIGRATION_DATABASE` to match the exact database name. Automatic downgrades are disabled to reduce the chance of data loss.

For setup commands and restricted-role requirements, read [Database migrations](../../docs/database.md). CI runs the full migration chain against disposable PostgreSQL 18 instances.
