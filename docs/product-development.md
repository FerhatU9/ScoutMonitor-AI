# ScoutMonitor AI — Product Development Roadmap

## Product outcome

Deliver a secure, reliable, **customer-usable football scouting and performance monitoring service**. A scout should be able to sign in, join an organization, search players, compare verified statistics, maintain a private watchlist, generate an evidence-backed AI report, review it, and revisit the organization's report history **without installing development tools**.

This roadmap describes both the implemented baseline and unfinished work. A green test run is necessary but not proof of commercial readiness.

## Working agreement: guided product development

ScoutMonitor AI will be built **with the developer actively operating the technologies**, not by presenting batches of finished modules as substitutes for learning.

For each feature, the mentor and developer will:

1. Inspect the current behavior and select one concrete customer-facing outcome.
2. Explain the chosen tool, what it solves, and which existing components it connects.
3. Implement through the real local development environment with exact file paths and actionable instructions.
4. Run the application and validate the workflow visually and through automated tests.
5. Resolve defects, verify security and data handling, and document the result.
6. Move on only when acceptance criteria are met; avoid repeating completed steps.

Do not add classroom exercises or unnecessary frameworks. Avoid broad unverified rewrites, artificial commits, and naming such as "initial", "portfolio version", "starter", "draft release", or "polish" in visible project materials. Genuine technical names, release versions, and factual descriptions of draft AI reports remain appropriate.

## Verified baseline

The repository currently includes:

- A local Streamlit dashboard and LangGraph/Gemini structured scouting workflow with human review.
- PostgreSQL persistence, missing-statistics handling, and duplicate-record controls.
- A FastAPI service with read-only synthetic player browsing and comparisons.
- PostgreSQL migrations 0001–0003 on newly created, empty Alembic-managed databases.
- OIDC token verification, organization memberships, protected watchlists, and organization-private **human-authored** scouting notes.
- Automated Python and isolated PostgreSQL checks (**41 API/data/security tests and 24 database integration tests** in the latest verified GitHub Actions run). The runtime dependency-import check also passed.

**Not yet verified:** an end-to-end hosted customer journey, actual customer identity-provider setup, complete organization isolation of legacy AI reports and source data, commercial football-data rights, operational recovery, or payment functionality.

**Important protection:** existing local PostgreSQL databases created outside Alembic must not be stamped, migrated, or overwritten without a separate backup and reviewed adoption procedure.

## Delivery sequence and acceptance criteria

### 1. Reproducible development and honest verification

- **Tools:** Docker Compose (planned for repeatable local setup), FastAPI, PostgreSQL 18, Alembic, unittest/pytest, Playwright later.
- Establish a documented, clean local environment without modifying existing reports.
- Add a database readiness check separate from process liveness.
- Use integration tests that exercise the API, database, and failures; report real test coverage rather than just test counts.
- Validate the Streamlit report-generation, approval, and historical monitoring journey using isolated synthetic data.
- Add structured logging and a consistent configuration layer with safe secret handling.

**Done when:** a developer can check out the project, start its services, create synthetic data, execute one complete report workflow, and rerun automated checks without secret-sharing or manual schema intervention.

### 2. Professional customer-facing interface

- **Tools:** Next.js, TypeScript, Tailwind CSS, FastAPI.
- Create an application shell with navigation, player profiles, comparison views, watchlists, scouting-note screens, and report review queue.
- Use only synthetic data until customer authorization and licensed data are ready.
- Connect each real page to a tested API; do not treat static mockups as functioning features.
- Ensure responsive layout, accessibility, loading/error states, and understandable data-source labels.

**Done when:** a user can browse and compare fictional players, use a protected organization workflow, and understand the origin and completeness of each metric through a working browser interface.

### 3. Managed identity and complete organization isolation

- **Tools:** managed OIDC identity service, PostgreSQL RLS where appropriate, Pydantic/FastAPI validation.
- Configure an actual trusted identity provider with safe development accounts.
- Add invitation and membership administration, explicit organization selection, session protections, and audit events.
- Model organization ownership for **new** AI reports and associated private data; do not expose legacy global reports to customers.
- Test forbidden access across organizations, direct object references, inactive memberships, privilege escalation, and database-role boundaries.

**Done when:** two independent test organizations can operate simultaneously without accessing or changing each other's notes, reports, or permissions. A security review confirms intended boundaries.

### 4. Evidence-based scouting and AI reliability

- **Tools:** LangGraph, Google Gemini (replaceable through a model adapter), structured validation, LangSmith/OpenTelemetry as justified.
- Connect the verified reporting workflow to organization-owned records.
- Distinguish genuine zeroes from missing, stale, or unknown statistics.
- Track source, observation date, transformation logic, evidence references, and model usage/cost.
- Evaluate factual correctness, unsupported narrative statements, report quality, provider outages, and human approval decisions on repeatable cases.
- Add useful player comparisons, monitoring alerts, and history charts.

**Done when:** reports are evidence-traceable, reject unsupported facts, remain private to the correct organization, and work reliably through review and retrieval.

### 5. Data licensing and resilient collection

- **Tools:** provider-specific HTTP clients, scheduled tasks or n8n as an explicit automation layer, and a durable job queue only when failure/retry requirements justify it.
- Select licensed football-data sources with explicit commercial rights.
- Test ingestion retries, pagination, rate limits, idempotency, data freshness, and provenance.
- n8n may schedule work or deliver notifications; the main agent remains in LangGraph.
- Keep scheduled publishing and customer notifications inactive until deliberately enabled; never bypass human approval.

**Done when:** authorized source data arrives on schedule, can be traced and corrected, and does not silently fabricate unavailable metrics.

### 6. Operations and secure cloud delivery

- **Tools:** Docker, managed PostgreSQL, cloud container hosting, GitHub Actions, OpenTelemetry, error tracking.
- Package API and interface; implement least-privilege credentials, migrations, backups, restore drills, health checks, rate limits, and safe error handling.
- Measure latency, reliability, and infrastructure/LLM costs.
- Test deployment, rollback, incident recovery, privacy processes, and retention/deletion.
- Do not expose the legacy Streamlit dashboard directly as a multi-tenant public service.

**Done when:** external pilot users can log in, complete core tasks safely, and the operator can monitor and recover the service.

### 7. Commercial launch

- **Tools:** subscription entitlements and Stripe only after billing requirements are defined.
- Conduct usability pilots with real scouts; verify product value and pricing.
- Complete commercial data licensing, contract terms, privacy notices, security review, support, and customer onboarding.
- Add subscription billing, account lifecycle and support processes.
- Set a clear release checklist with measured acceptance thresholds.

**Done when:** an external customer can subscribe, use supported workflows, receive support, and trust the product's privacy, accuracy, and availability.

## Current focus

**Next working milestone:** run ScoutMonitor AI locally through a reproducible application/API/database development setup, prove a complete synthetic-data scouting/review journey, and identify the first customer-facing Next.js page to connect to real endpoints.

Starting with this working vertical slice is more useful than introducing multiple frameworks without a product workflow. Keep the existing local reports untouched.

## GitHub and naming quality

- Maintain the public project identity as **ScoutMonitor AI** in repository descriptions, README, UI, and key docs.
- Keep filenames descriptive and professional; technical modules may have different functional names.
- Use reviewed branches, honest implementation details, and CI checks; do not inflate commit counts.
- Never rewrite published Git history purely to change visible commit messages without a deliberate backup and local-clone synchronization plan.
- Do not commit secrets, licensed data exports, or synthetic statistics described as real.
