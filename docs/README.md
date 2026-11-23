# ScoutMonitor AI documentation

The project has separate technical documentation for its current local application, public showcase, and developing multi-user backend.

| Guide | What it covers |
|---|---|
| [Architecture](architecture.md) | Existing application components, boundaries, and data flow |
| [API](api.md) | Public fictional-data and protected organization routes |
| [Authentication](authentication.md) | Trusted OIDC tokens and organization membership checks |
| [Database](database.md) | Alembic migration procedure and protection for legacy databases |
| [Private scouting notes](private-notes.md) | Restricted PostgreSQL role and organization isolation |
| [Public website](website.md) | GitHub Pages showcase and fictional player dataset |
| [Product roadmap](product-development.md) | Development milestones and acceptance criteria |
| [StatsBomb integration plan](statsbomb_plan.md) | Proposed data ingestion and licensing considerations |

The website files `index.html` and `assets/` are also in this directory for GitHub Pages publishing. Real customer login, hosted LangGraph/Gemini workflows, tenant-isolated AI reports, and commercial football-data redistribution are **not** implemented by the public website.
