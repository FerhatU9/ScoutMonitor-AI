# ScoutMonitor AI — Product Development Plan

## Product goal

Make ScoutMonitor AI a reliable, secure football monitoring service usable by different users or organizations. The current Streamlit and PostgreSQL application is a locally demonstrated prototype. This plan defines work still needed before any commercial launch; it does not claim those features are already available.

## Engineering principles

- Preserve verified evidence: missing statistics must remain unknown, not zero.
- Treat AI-generated analysis as a draft until validated and approved.
- Keep private keys and licensed provider data out of source control.
- Prefer automated tests and small reviewed changes over cosmetic commits.
- Keep source-data attribution and access rights explicit.

## Phase 1 — Reliability and reproducibility

1. Run Python syntax checks and the synthetic-data unit tests on every pull request.
2. Expand tests to monitoring change detection, report validation, duplicate prevention, and approval decisions.
3. Add integration tests that run against an isolated PostgreSQL test database.
4. Replace manual schema setup with versioned database migrations (Alembic).
5. Build a Docker-based local development environment and document a clean setup.

**Completion criteria:** clean checkout, documented setup, reliable automated tests, and repeatable database migrations.

## Phase 2 — Application backend and identity

1. Introduce FastAPI for versioned, documented application endpoints.
2. Implement user authentication with a managed identity provider or vetted library.
3. Design organization and user roles, including reviewer/admin permissions.
4. Ensure every database query enforces organization ownership; add cross-organization isolation tests.
5. Add rate limits, secure session management, audit logs, and structured error handling.

**Completion criteria:** authorized users can safely access only their permitted data and actions.

## Phase 3 — Data collection and AI quality

1. Establish and document licensed, permissioned football data sources.
2. Build resilient scheduled ingestion with retry/backoff, idempotency, and provenance.
3. Track player snapshots and distinguish missing, stale, and verified statistics.
4. Evaluate factual correctness, narrative relevance, and AI cost with repeatable test datasets.
5. Track model/provider failures and provide safe fallback behavior.
6. Build player-to-player comparisons that explicitly show comparable metrics and data gaps.

**Completion criteria:** repeatable ingestion and measurable evidence quality before reports reach reviewers.

## Phase 4 — Usable hosted application

1. Move to a multi-user web UI with onboarding, player search, watchlists, comparison screens, and approval queues.
2. Deploy application and managed PostgreSQL in an appropriate cloud environment.
3. Add backups, restore drills, monitoring, alerts, encrypted secrets, and operational logs.
4. Add privacy documentation, retention/deletion workflows, support process, and published limitations.

**Completion criteria:** invited users can operate the system end-to-end without local installation.

## Phase 5 — Commercial release

1. Confirm sports-data licensing permits the intended hosted and paying-user workflows.
2. Complete a security review including authorization and tenancy separation.
3. Run pilot users, measure reliability and usefulness, and fix observed failures.
4. Establish billing, subscription entitlement checks, customer terms, privacy policy, and support procedures.
5. Define service levels and operating costs before paid launch.

**Completion criteria:** secure, legally usable, monitored service tested with real external users and a repeatable support process.

## Suggested technologies

| Component | Recommendation | Purpose |
|---|---|---|
| Web/API backend | FastAPI and Pydantic | Validated, documented service endpoints |
| Database | PostgreSQL with SQLAlchemy and Alembic | Reliable persistence and schema migrations |
| Web interface | Start with Streamlit; consider Next.js later | Faster early iteration, stronger multi-user product UI later |
| Identity | Managed authentication provider | Sign-in, sessions, password and account security |
| Agent workflow | Keep LangGraph and Google Gemini | Existing report orchestration and AI generation |
| Background jobs | A scheduler plus a durable queue when needed | Resilient ingestion and report preparation |
| Containers | Docker and Compose | Reproducible local and deployment environments |
| Testing | unittest/pytest, integration tests and GitHub Actions | Continuous quality checks |
| Monitoring | Structured logs and OpenTelemetry | Diagnostics, latency, failures and AI costs |
| Cloud | Managed container service and managed PostgreSQL | Hosting without self-managing servers |

## GitHub contribution policy

Use descriptive commits for actual changes, for example:

- `ci: validate Python source and unit tests`
- `test: cover missing football statistics`
- `feat: implement organization-scoped player queries`
- `fix: prevent duplicate report submission`
- `docs: explain local database setup`

Create branches for cohesive features, run tests, review in pull requests, and merge into `main` when checks pass. The goal is a truthful, maintainable project history, **not** a large number of artificial commits.

## Scope boundaries

The current repository does **not** provide a multi-user SaaS product, production authentication, billing, guaranteed real-time licensed data, or a public hosted service. These are proposed future milestones.
