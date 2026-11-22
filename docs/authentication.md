# ScoutMonitor AI — Identity and Organization Access

This is the **first secured, database-backed multi-user foundation**. It is not a complete hosted sign-up system. ScoutMonitor AI does not store customer passwords.

## How access works

1. A trusted external OpenID Connect (OIDC) identity provider authenticates the user.
2. The client sends a signed **access token** using the HTTP `Authorization: Bearer <token>` header.
3. ScoutMonitor AI verifies the token's **RS256 signature**, issuer, audience, expiry, issued-at time, and subject using the configured JWKS endpoint.
4. The API looks up the token's verified `issuer` and `subject` in the application's PostgreSQL `identity_users` table.
5. Authorization uses the **active organization membership and role stored in PostgreSQL**, never the user's token claims.
6. Watchlist queries are scoped to the requested organization ID only.

Tokens without a valid signature, identity claims, or correct audience are rejected. Missing OIDC configuration disables authenticated endpoints. There is no fallback or test token in the production application.

## Roles

| Role | Read organization watchlist | Add to watchlist |
|---|---|---|
| owner | Yes | Yes |
| admin | Yes | Yes |
| scout | Yes | Yes |
| reviewer | Yes | No |

Memberships and organizations must both be active. Unrecognized or inactive memberships return 404 so callers cannot determine whether another organization exists.

## Server configuration

Set these **in your private environment**, never in GitHub:

```dotenv
OIDC_ISSUER=https://identity-provider.example
OIDC_AUDIENCE=scoutmonitor-api
OIDC_JWKS_URL=https://identity-provider.example/.well-known/jwks.json
```

These are illustrative placeholders, not a working identity provider. Use your chosen provider's documented issuer, API audience, and trusted JWKS URL. Only HTTPS issuer/JWKS URLs are accepted. Use a **signed access token** intended for this API—not a browser ID token for another audience. The API does not accept an issuer or JWKS URL supplied by the HTTP client.

Database credentials use `SCOUTMONITOR_DATABASE_URL` or the existing `DB_*` variables. The database must be an **Alembic-managed, newly created** schema upgraded to revision `0002`. Existing manually created databases must not be stamped or migrated without a separately reviewed, backed-up adoption plan.

## Schema

Migration `0002` adds:

- `organizations`: organization identifier, name, active state
- `identity_users`: trusted issuer/subject pair (no password storage)
- `organization_memberships`: per-user, per-organization role and active state
- `organization_watchlist`: organization-scoped player references and ownership trail

The pre-existing `players`, `ai_reports`, and other operational tables are **not yet tenant-partitioned**. The protected API currently supports only organization watchlists. Do not add private organization reports or broad database listing endpoints until organization ownership and policy checks are enforced on each data path.

## Protected API

| Endpoint | Access |
|---|---|
| `GET /api/v1/organizations/{organization_id}/watchlist` | Any active member of the organization |
| `POST /api/v1/organizations/{organization_id}/watchlist` | Active owner, admin, or scout |

Example request body for the POST endpoint:

```json
{"player_id": 990001}
```

This works only when the player already exists in the application's PostgreSQL `players` table. Duplicate additions are safely ignored. The response includes a maximum of 500 watchlist players; production paging will be added later.

### Member onboarding

There is **no public signup or membership-management endpoint yet**. A trusted administrator must provision an identity user, organization, and membership through a controlled database procedure before the watchlist endpoints can be used. Do not use an unauthenticated API to create privileged memberships.

## Security boundaries and next milestones

This feature includes authentication checks, membership-based access, permission restrictions, and cross-organization integration tests. It does **not** yet provide:

- Hosted sign-in screens, invitation flows, or account recovery
- Managed customer onboarding or auditing of membership changes
- Database row-level security across the legacy reporting tables
- Production-grade rate limits, web application firewall, observability, or incident response
- A tenancy and authorization penetration test
- Customer deployment or commercially licensed sports-data distribution

Before public hosting, add these protections and evaluate the full authentication and authorization design. Until then, keep the protected backend on a trusted development environment.

## Testing

The unit suite exercises token rejection without contacting an identity provider. The PostgreSQL CI job uses a disposable database and dependency-injected **test identities only** to validate organization isolation, role restrictions, and watchlist operations.

See [Database Migrations](database.md) and [API Reference](api.md) for related infrastructure.
