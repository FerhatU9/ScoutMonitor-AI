# API service

The FastAPI application starts at `api/main.py` and provides two different types of routes.

**Public demonstration routes** read only bundled fictional player records. They support health checks, CSV validation, player browsing, and two-player comparisons. They do not expose PostgreSQL customer data or invoke Gemini.

**Protected organization routes** use a trusted OpenID Connect token and database membership checks. Organization watchlists are defined in `api/organizations.py`; human-authored private scouting notes are defined in `api/private_notes.py`. Private notes require a separately configured restricted PostgreSQL database role.

The token verifier is in `api/security.py`. A token is not proof of an organization role: authorization comes from active membership records in PostgreSQL.

The legacy Streamlit report-review workflow is not tenant-isolated and must not be exposed through these API routes. No public user registration or customer-hosted login is provided yet.

See [API reference](../docs/api.md), [authentication](../docs/authentication.md), and [private notes](../docs/private-notes.md).
