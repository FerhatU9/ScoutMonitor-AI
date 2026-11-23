# Continuous integration workflows

- `code-quality.yml` validates Python syntax, the synthetic-data API, security checks, and isolated PostgreSQL migrations. It also checks installation of the complete Python runtime dependency set.
- `website.yml` verifies the GitHub Pages site's HTML/JavaScript assets and confirms the published player CSV exactly matches the 20 fictional source records.

GitHub Pages itself deploys the static website from `main` → `/docs`. **The static site is not the Python API or customer application.**

Workflow credentials in the database job are temporary CI-only values. Real football-data and model API credentials must not be stored in source control.
