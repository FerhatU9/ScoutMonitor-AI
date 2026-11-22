# ScoutMonitor AI — Private Scouting Notes

ScoutMonitor AI supports **organization-private, human-authored player notes** as a foundation for secure customer scouting workflows.

These notes are deliberately separate from legacy AI-generated reports. Legacy `ai_reports` do not yet have organization ownership and must **not** be exposed through organization APIs.

## Access policy

| Membership | Read own organization's notes | Create notes |
|---|---|---|
| Owner | Yes | Yes |
| Administrator | Yes | Yes |
| Scout | Yes | Yes |
| Reviewer | Yes | No |
| Inactive member | No | No |
| Member of another organization | No | No |

The API first verifies the externally issued OIDC identity and checks the active membership in PostgreSQL. PostgreSQL then applies row-level security (RLS) on `organization_scouting_notes` using the current organization's and authenticated member's IDs, set **inside the database transaction**.

## HTTP endpoints

- `GET /api/v1/organizations/{organization_id}/notes?limit=25&offset=0` — read notes in the requested organization, with bounded pagination.
- `POST /api/v1/organizations/{organization_id}/notes` — create a human-authored note for a player already recorded in PostgreSQL.

Example JSON request:

```json
{
  "player_id": 990001,
  "title": "Positioning observations",
  "body": "The player maintained good defensive positioning during the observed sequence."
}
```

Notes contain a player reference, title (up to 150 characters), body (up to 5,000 characters), author ID, organization ID, and creation timestamp. The title and body cannot be empty after whitespace removal.

## Restricted database access

`SCOUTMONITOR_PRIVATE_DATABASE_URL` is **required** for the private-notes endpoints. It must use a dedicated, least-privilege PostgreSQL runtime account, not `postgres` or a database owner.

The account needs:

- `CONNECT` on the application database and `USAGE` on `public`.
- `SELECT` on `organizations`, `organization_memberships`, `identity_users`, and `players`.
- Only `SELECT` and `INSERT` on `organization_scouting_notes`.

The role should not have `SUPERUSER`, `BYPASSRLS`, table ownership, or DDL privileges. GitHub Actions demonstrates the permissions using a temporary `scoutmonitor_runtime` role and synthetic records.

**Important security boundary:** PostgreSQL session settings such as `scoutmonitor.org_id` are set by trusted API code, but they can be changed by a party with direct SQL execution access under that database role. The RLS policy is therefore an additional safeguard—not a replacement for protecting credentials, parameterizing SQL, restricting direct DB access, or enforcing authorization in the API. Do not claim that it protects against a compromised runtime role.

## Schema and migrations

Revision `0003` adds `organization_scouting_notes`, an index for organization queries, and forced RLS policies for selecting and inserting notes.

Migration instructions in [Database Migrations](database.md) apply **only to clean, Alembic-managed databases**. Do not apply these migrations to the existing legacy `scoutmonitor_db` without a separately reviewed backup and adoption plan.

## Automated tests

GitHub Actions uses PostgreSQL 18 with disposable credentials. Integration tests cover:

- Denying cross-organization reads and writes.
- Allowing scouts to create and retrieve private notes in their own organization.
- Reviewer read-only permissions.
- Rejecting unknown players.
- PostgreSQL RLS denying records without tenant context.
- PostgreSQL RLS restricting rows even when a query has no explicit organization WHERE clause.

Authentication and validation tests also cover missing access tokens and invalid request bodies.

## What's not yet covered

This feature does not provide tenant isolation for **legacy AI reports**, their source statistics, or the Streamlit dashboard. It does not include customer-facing registration, hosted identity-provider configuration, account recovery, auditing, or production security review.

**Next milestone:** create an explicitly organization-owned AI report model, connect it to the validated report workflow, and extend isolation tests to those records before enabling customer access.
