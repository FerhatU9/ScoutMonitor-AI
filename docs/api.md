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
