# ScoutMonitor AI

**Evidence-driven football performance monitoring and AI-assisted scouting**

[![Code quality](https://github.com/FerhatU9/ScoutMonitor-AI/actions/workflows/code-quality.yml/badge.svg)](https://github.com/FerhatU9/ScoutMonitor-AI/actions/workflows/code-quality.yml)

ScoutMonitor AI combines football statistics, historical monitoring, AI-generated scouting reports, factual validation, and human approval in a Python application. It demonstrates a review-first workflow: **the system prepares the analysis; a person decides whether to approve it.**

**Project status:** Local AI scouting dashboard plus a developing FastAPI backend. Organization memberships, restricted watchlists and private scouting notes are implemented, but customer sign-in, tenant-isolated AI reports, hosted deployment, and paid features are not available.

## What it does

| Capability | What is implemented |
|---|---|
| Player monitoring | Read stored performance snapshots and evaluate changes over time |
| Missing-data integrity | Distinguish complete, partial, not-reported, and not-collected statistics without inventing zeros |
| AI scouting reports | Use LangGraph and Google Gemini to draft structured reports from stored evidence |
| Factual verification | Check five structured report fields against database records; flag mismatches for review |
| Human decisions | Approve or reject pending reports and inspect reviewed-report history |
| Database persistence | Store player observations, alerts, and report/review records in PostgreSQL |
| Streamlit dashboard | View monitoring information, generate report drafts, and review results locally |
| FastAPI service | Synthetic player browsing and comparisons; protected organization watchlists and human-authored scouting notes |
| Continuous testing | Run **41 API/data/security tests** and **24 PostgreSQL integration tests** through GitHub Actions |

The automated tests cover synthetic-data validation and the read-only API. Other features have been demonstrated locally but do not yet have complete integration-test coverage.

## How it works

~~~mermaid
flowchart LR
    A[Football statistics] --> B[(PostgreSQL)]
    B --> C[LangGraph monitoring]
    C --> D[Gemini report draft]
    D --> E[Factual validation]
    E --> F[Human approval]
    F --> G[(Reviewed report history)]
    B --> H[Streamlit dashboard]
    H --> C
~~~

The Streamlit dashboard runs the existing reporting and review workflow. The FastAPI service is a separate, read-only foundation; it does **not** expose private database records or replace the dashboard.

For the component-level design, see [System Architecture](docs/architecture.md).

For branching, testing, review and documentation standards, see [Contributing](CONTRIBUTING.md).

## Technology

| Layer | Technology |
|---|---|
| Application and data processing | Python, Pandas, Pydantic |
| Agent orchestration | LangGraph, LangChain Core |
| Language model | Google Gemini |
| Web interface | Streamlit |
| Read-only HTTP API | FastAPI, Uvicorn |
| Database | PostgreSQL, psycopg, SQLAlchemy, Alembic |
| Identity verification | OpenID Connect, PyJWT |
| Quality checks | unittest, pytest, GitHub Actions |

## Repository guide

| Path | Purpose |
|---|---|
| `api/main.py` | FastAPI application and read-only endpoints |
| `scoutmonitor/validation.py` | Reusable synthetic-data validation |
| `scoutmonitor/demo_catalog.py` | Safe synthetic player catalog and metric comparisons |
| `scripts/monitor_logic.py` | Historical monitoring rules and truthful source labels |
| `scripts/review_dashboard.py` | Streamlit dashboard |
| `scripts/scout_structured_graph.py` | AI report generation and factual checks |
| `scripts/scout_monitoring_graph.py` | Historical monitoring workflow |
| `scripts/` | Ingestion, storage, monitoring, and manual diagnostic utilities |
| `tests/` | Automated validation and API tests |
| `data/fictional_players.csv` | Synthetic player data for repeatable tests |
| `docs/schema.sql` | PostgreSQL schema export for reference |
| `db/migrations/` | Safe, versioned schema creation for new databases |
| `docs/database.md` | Database migration guide and protection rules |
| `api/security.py` | Signed OIDC access-token verification |
| `api/organizations.py` | Organization-scoped watchlist APIs and database permission checks |
| `docs/authentication.md` | Identity-provider setup and organization authorization design |
| `api/private_notes.py` | Protected, organization-private scouting notes |
| `docs/private-notes.md` | Scouting-note permissions and database security |
| `docs/demo_seed.sql` | Four fictional demonstration players and snapshot states |
| `docs/api.md` | API endpoints and usage |
| `docs/product-development.md` | Staged roadmap toward a secure multi-user product |

## Local setup (Windows)

**Requirements:** Python 3.11 or 3.12, PostgreSQL 18 for the included schema dump, and Git. Generate your own Gemini API key for AI reports. A Sportmonks token is needed only for optional provider-backed ingestion.

### 1. Clone and install

~~~powershell
git clone https://github.com/FerhatU9/ScoutMonitor-AI.git
cd ScoutMonitor-AI
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

### 2. Run the read-only API (no external credentials required)

~~~powershell
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
~~~

Open the interactive documentation at **http://127.0.0.1:8000/docs**.

| Endpoint | Result |
|---|---|
| `GET /health` | API process liveness; not a database readiness guarantee |
| `GET /api/v1/demo/validation` | Counts from the fictional CSV dataset |
| `GET /api/v1/demo/players` | Browse fictional players with filters and pagination |
| `GET /api/v1/demo/players/{player_id}` | Read one fictional player's record |
| `GET /api/v1/demo/compare` | Compare two fictional players, preserving unknown metrics |
| `GET /openapi.json` | OpenAPI specification |

See [API documentation](docs/api.md) for details. The API is not designed to be exposed publicly yet.

### 3. Configure the dashboard and database

Copy the template and edit the **local** `.env` file:

~~~powershell
Copy-Item .env.example .env
~~~

Set your PostgreSQL password and Gemini credentials in `.env`. Do not commit that file. The example configuration uses the isolated database `scoutmonitor_demo`.

Create an **empty, isolated** demonstration database, apply the versioned migrations, then load the fictional records. From the repository root, with PostgreSQL 18 installed at the default Windows path:

~~~powershell
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -h localhost -p 5432 -U postgres scoutmonitor_demo
$env:SCOUTMONITOR_MIGRATION_DATABASE = "scoutmonitor_demo"
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5432 -U postgres -d scoutmonitor_demo -v ON_ERROR_STOP=1 -f docs/demo_seed.sql
~~~

**Safety:** Use an entirely new, empty database. Alembic refuses to adopt a database with manually created tables, and the fictional seed only permits `scoutmonitor_demo`. **Never stamp or migrate your existing local report database without a separately reviewed backup and adoption plan.** `docs/schema.sql` is a legacy reference export; do not run it alongside Alembic.

### 4. Start the Streamlit dashboard

~~~powershell
.\.venv\Scripts\python.exe -m streamlit run scripts/review_dashboard.py --server.port 8502
~~~

Open **http://localhost:8502**. The dashboard requires its configured PostgreSQL database; generating a report also requires a valid Gemini key and a supported model. Some reporting actions require stored player statistics beyond the bundled fictional examples.

## Testing

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
~~~

The suite includes **41 API, data-validation, authentication, and provenance tests** plus **24 PostgreSQL integration tests** that run against a disposable CI database. GitHub Actions checks Python syntax, runs the API/data suite on Python 3.11 and 3.12, verifies PostgreSQL migrations, selected report-storage workflows, roles and note isolation, and checks full runtime dependency installation on Python 3.12. Real identity-provider integration, the full Streamlit-to-AI workflow, and external football-data ingestion still need independent verification.

## Database migrations

New, **empty** PostgreSQL databases can be initialized with a guarded Alembic migration. Existing databases containing reports or player information must **not** be stamped or migrated using this baseline. See [Database Migrations](docs/database.md) for the process, safety controls, and isolated PostgreSQL integration tests.

## Organization access

The backend now supports signed **OpenID Connect access tokens**, database-backed organization memberships, and organization-scoped player watchlists. Owners, administrators, and scouts can add players to their organization's watchlist; reviewers have read-only access. Membership permissions are checked against PostgreSQL rather than trusted from token roles. See [Identity and Organization Access](docs/authentication.md).

The application also provides [organization-private scouting notes](docs/private-notes.md) with PostgreSQL row-level security and a dedicated restricted database role. These notes are human-authored and separate from the existing AI reports.

This is a protected foundation, **not** a public signup or customer-hosted service. The legacy AI reporting tables and Streamlit dashboard are not yet tenant-isolated; public deployment awaits comprehensive authorization, data isolation, security hardening, and licensing.

## Data integrity and licensing

ScoutMonitor AI distinguishes:

- **COMPLETE** — required statistics are available
- **PARTIAL** — one or more required values are unavailable
- **NOT_REPORTED** — the provider did not report required statistics
- **NOT_COLLECTED** — no observation has been stored

Unknown values remain unknown; they are never silently treated as zero. Generated narratives require human review even when structured factual checks pass.

This repository includes **fictional football data**, not downloaded Sportmonks or StatsBomb datasets. Integrations that use real data must respect the relevant provider's access and redistribution terms.

## Development direction

ScoutMonitor AI is being developed toward a secure service that other users and organizations can access. Planned work includes database migrations, broader integration testing, authentication and role-based permissions, organization-level data separation, robust data ingestion, cloud deployment, monitoring, and commercial licensing review.

See [Product Development Plan](docs/product-development.md) for milestones, technology choices, acceptance criteria, and the guided build process.

**Current boundary:** The backend has token verification and limited organization-scoped resources, but no configured customer login or tenant separation for legacy AI reports and the Streamlit dashboard. There is no billing, publicly hosted service, or production guarantee. The source is public, but the application is not yet a commercial SaaS product.
