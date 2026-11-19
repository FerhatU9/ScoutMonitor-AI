# ScoutMonitor AI

## AI-Powered Football Performance Monitoring & Scouting

ScoutMonitor AI is a football intelligence application built with Python, LangGraph, PostgreSQL, and Streamlit.

The project combines football performance monitoring, AI-assisted scouting reports, automatic factual validation, and human review.

### Current Capabilities

- **Player Performance Monitoring:** Track football player statistics and identify changes between snapshots.
- **AI Scouting Reports:** Generate evidence-based scouting report previews.
- **LangGraph Workflows:** Organize data retrieval, analysis, and report preparation.
- **PostgreSQL Database:** Store and retrieve football statistics, alerts, and scouting reports.
- **Human Review:** Require approval or rejection before reports are finalized.
- **Data Validation:** Verify report facts against stored data and handle missing statistics without assuming they are zero.
- **Streamlit Dashboard:** Inspect players, monitor statistics, and review AI-generated reports.
- **Automated Testing:** Six automated tests for synthetic player-data validation; additional integration and operational checks have been performed manually.

### Project Scope

The application has been demonstrated locally using stored football statistics. The public repository contains fictional demonstration data rather than provider API exports.

Core functionality has been tested locally. Further work is required for reproducible deployment, broader testing, and production readiness.

This repository documents a locally demonstrated engineering prototype, not a commercially deployed service.

## Local Installation (Windows)

### Requirements

- Python 3.11 or newer with compatible dependencies
- PostgreSQL 18 (the included schema was exported from PostgreSQL 18)
- Git
- A Google Gemini API key
- A Sportmonks API token for features requiring live football data

### 1. Clone the Repository

```powershell
git clone https://github.com/FerhatU9/ScoutMonitor-AI.git
cd ScoutMonitor-AI
```

### 2. Install Python Dependencies

Create a virtual environment:

```powershell
py -m venv .venv
```

Install the required packages:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Open `.env` and enter your PostgreSQL password and your own Google Gemini API key. The example points to a separate fictional demonstration database. `GEMINI_MODEL` specifies the AI model used for reports. A Sportmonks token is needed only for optional live football-data ingestion, not for viewing the fictional demo records.

Never upload `.env` or real credentials to GitHub.

### 4. Set Up PostgreSQL

For the safe fictional demonstration, create a **separate empty PostgreSQL database** called `scoutmonitor_portfolio_test`, matching `.env.example`. With PostgreSQL 18 installed in its default Windows location, run the following from the repository root in PowerShell:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\createdb.exe" -h localhost -p 5432 -U postgres scoutmonitor_portfolio_test
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5432 -U postgres -d scoutmonitor_portfolio_test -v ON_ERROR_STOP=1 -f docs/schema.sql
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5432 -U postgres -d scoutmonitor_portfolio_test -v ON_ERROR_STOP=1 -f docs/demo_seed.sql
```

The demonstration contains four fictional players and illustrates complete, partial, unreported, and uncollected statistics, plus historical snapshots. The seed intentionally refuses to run in any database except `scoutmonitor_portfolio_test`. The SQL schema is a PostgreSQL dump and should be restored using `psql`.

**Do not seed your existing `scoutmonitor_db` development database.** If you use your own authorized live data, configure a separate database and ingestion workflow.

### 5. Run the Streamlit Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run scripts/review_dashboard.py --server.port 8502
```

Open:

http://localhost:8502

### 6. Run Automated Tests

Install development dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run the six synthetic player-data validation tests (not full API/database integration tests):

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

### Repository Structure

| Location | Purpose |
|---|---|
| `scoutmonitor/` | Reusable player-data validation |
| `scripts/review_dashboard.py` | Streamlit application entry point |
| `scripts/scout_structured_graph.py` | Structured AI reporting and validation workflow |
| `scripts/scout_monitoring_graph.py` | Shared monitoring nodes and conditional routing |
| `scripts/` | Football-data integrations, database utilities and manual checks |
| `tests/` | Automated validation tests |
| `docs/` | Architecture, PostgreSQL schema and demonstration setup |
| `data/` | Fictional CSV records used in validation tests |

### Data Sources

The project uses synthetic football demonstration data for local validation. Sportmonks integration is included for supported football-data workflows.

Synthetic information must not be represented as real player performance data.

### Current Limitations

This is a locally demonstrated AI engineering project. Broader testing, reproducible deployment verification, and production security improvements are still required.

### Demonstration and Data Sources

The principal application is `scripts/review_dashboard.py`, with its AI report workflow in `scripts/scout_structured_graph.py`. The dashboard uses a local PostgreSQL instance; an AI report also requires your own Gemini API key. No hosted public dashboard or production authentication is provided, so do not expose the local Streamlit service to the internet.

The repository includes original application code, fictional test data, and optional integration scripts. No downloaded Sportmonks API dataset or StatsBomb event dataset is distributed. Only use third-party football data under the applicable license and access terms.
