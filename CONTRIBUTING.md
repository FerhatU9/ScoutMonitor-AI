# Contributing to ScoutMonitor AI

ScoutMonitor AI is publicly available source code for a football scouting application under development. Contributions should be small, verifiable and consistent with the implemented product. A passing CI workflow is not proof of commercial readiness.

## Branches and commits

- Start from an up-to-date `main` and use a focused branch, such as `feature/player-filters`, `fix/report-validation` or `docs/api-reference`.
- Make each commit describe a real change. Use a short action-oriented title: `Add player comparison filters`, `Test watchlist permissions`, `Document database recovery`.
- The repository name already provides the brand. Do not repeat `ScoutMonitor AI` in every commit message.
- Do not add cosmetic commits simply to populate GitHub's file listing, invent engineering milestones, or rewrite published history to change visible labels.
- Preserve established technical names and legitimate library, schema or model version identifiers.

## Changes and verification

1. Check the relevant implementation and documentation before editing.
2. Explain what is changing, its effect on users and any security or data-handling implications.
3. Include relevant validation and regression tests when changing behavior.
4. Run the tests for the affected components and review the diff before proposing a merge.
5. Open a pull request with the changed behavior, evidence of tests and remaining limitations.

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
git diff --check
```

PostgreSQL integration tests require the **isolated test database**, not the legacy local scouting database. Read [Database Migrations](docs/database.md) before running migrations or database tests. GitHub Actions runs isolated PostgreSQL integration tests automatically.

## Documentation follows verified milestones

Update documentation in the **same pull request** when a tested change alters functionality, setup, architecture, permissions or data handling.

| Change | Documentation |
| --- | --- |
| User-visible capability or setup | `README.md` |
| API contract, roles or response behavior | `docs/api.md`, and security guides when relevant |
| Component or data flow | `docs/architecture.md` |
| Schema or migration | `docs/database.md` and versioned migration files |
| Product milestone or next priorities | `docs/product-development.md` |

State what is actually implemented and verified. Keep planned work clearly separate. Do not overstate test coverage, data rights, authentication, tenant isolation or deployment status.

## Security and data protection

- Never commit `.env`, credentials, provider tokens, database dumps, private scouting reports or licensed datasets without redistribution rights.
- Use fictional data for demonstrations. Keep missing statistics unknown; do not silently convert them to zero.
- Existing local PostgreSQL databases may contain important reports: do not stamp, reset, or migrate them without a separately reviewed backup and adoption plan.
- The local Streamlit report workflow is not tenant-isolated. Do not expose it as a hosted multi-organization product.
- Report factual claims and identity/authorization boundaries honestly. AI-generated scouting reports require human approval.

## Review checklist

A pull request should make it clear what changed, how it was tested, whether any local data or credentials are affected, and which limitations remain. Merge when required checks pass and any necessary manual verification has been completed.
