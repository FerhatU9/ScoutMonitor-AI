# ScoutMonitor AI API

The FastAPI backend is an early, **read-only** foundation. It does not replace the working Streamlit dashboard, connect to a customer database, or provide user accounts.

## Start the API locally

From the repository root, after installing `requirements.txt`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` to inspect the interactive OpenAPI documentation.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness status for the API process only |
| `GET /api/v1/demo/validation` | Validate bundled fictional football data, returning counts |
| `GET /openapi.json` | Machine-readable API schema |
| `GET /docs` | Interactive API documentation |

The demonstration endpoint reads only `data/fictional_players.csv` in the repository and cannot accept a user-controlled file path. It does not expose records from PostgreSQL or any licensed football provider.


## Synthetic player catalog and comparison

These read-only endpoints use only the bundled fictional CSV; they do **not** query PostgreSQL or any external football-data provider.

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/demo/players` | List synthetic players with filters, sorting, and pagination |
| `GET /api/v1/demo/players/{player_id}` | Get a single fictional player's record |
| `GET /api/v1/demo/compare?first_id=SYN001&second_id=SYN002` | Compare two fictional players on recorded metrics |

The player list accepts:

- `league` — case-insensitive exact league name.
- `preferred_foot` — `left`, `right`, or `both`.
- `min_minutes` — minimum reported minutes, from 0 to 6000.
- `sort_by` — `player_id`, `minutes`, `progressive_passes_per90`, or `defensive_duel_win_pct`.
- `order` — `asc` or `desc`.
- `offset` — result position (0 or greater).
- `limit` — page size (1 to 100).

Missing metric values are returned as JSON `null`; they are not replaced with zero. Missing metrics sort last in either direction. Player comparisons return **second player minus first player**, not performance ratings or predictions. The metrics are synthetic demonstrations and should never be presented as real football analysis.

Example requests:

```text
GET http://127.0.0.1:8000/api/v1/demo/players?preferred_foot=left&sort_by=minutes&order=desc
GET http://127.0.0.1:8000/api/v1/demo/players/SYN006
GET http://127.0.0.1:8000/api/v1/demo/compare?first_id=SYN006&second_id=SYN007
```

This catalog is an early product foundation. Production player records, licensed datasets, account authorization, and organization-specific access are not implemented in these demo endpoints.

## Testing

Install `requirements-dev.txt` and run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The API tests do not require credentials or network access to Gemini, Sportmonks, or PostgreSQL.

## Important limitations

- A successful `/health` response does **not** establish database or external API readiness.
- There is no authentication, authorization, customer tenancy, persistence, or hosted deployment yet.
- Keep the service bound to `127.0.0.1` locally; do not expose it publicly without security controls.
- Next steps: API request logging, safe configuration handling, versioned DB migrations, organization-scoped authentication, and database integration tests.

## Protected organization watchlists

New routes require a valid externally issued OIDC access token **and** an active PostgreSQL membership in the requested organization.

| Endpoint | Required permission |
|---|---|
| `GET /api/v1/organizations/{organization_id}/watchlist` | Active organization member |
| `POST /api/v1/organizations/{organization_id}/watchlist` | Active owner, admin, or scout |

The POST body is `{"player_id": 990001}`. The referenced player must already exist in PostgreSQL. Other organizations' watchlists are never returned or modified. Reviewer accounts have read-only access. This implementation does **not** provide user registration, token issuance, role assignment, or public hosting.

See [Identity and Organization Access](authentication.md) for identity-provider configuration and safeguards.


## Private scouting notes

These endpoints require a trusted OIDC identity and an active organization membership:

- `GET /api/v1/organizations/{organization_id}/notes` — bounded read-only list, 1–100 notes per page
- `POST /api/v1/organizations/{organization_id}/notes` — creates a human-authored note; available to owner, admin, and scout

The notes are organization-owned and protected by a restricted PostgreSQL role with row-level security. Existing AI reports are **not** accessible through these endpoints. See [Private Scouting Notes](private-notes.md).
