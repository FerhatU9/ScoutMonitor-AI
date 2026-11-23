# ScoutMonitor AI — Public Website

The public website is a **static, interactive engineering showcase** for ScoutMonitor AI. It lives in `docs/index.html` and is designed to be published at:

**https://ferhatu9.github.io/ScoutMonitor-AI/**

The website includes:

- A responsive product overview and technical capability descriptions.
- A fictional player explorer with search, filters, sorting, and playing-time statistics.
- Two-player comparisons, with unreported metrics shown as unavailable (never zero).
- A browser-session shortlist. It is **not saved to customer accounts**.
- Direct links to the ScoutMonitor AI GitHub repository.

**Data:** The website loads `docs/assets/players.csv`, an exact copy of the 20 fictional records in `data/fictional_players.csv`. The data is not live football data; the website neither accesses a private database nor calls Gemini.

## Publish through GitHub Pages

GitHub Pages settings require an authorized repository administrator to enable publishing. For the existing repository:

1. Open `https://github.com/FerhatU9/ScoutMonitor-AI/settings/pages`.
2. Under **Build and deployment**, choose **Deploy from a branch** as the source.
3. Select branch **main** and folder **/docs**, then click **Save**.
4. When GitHub reports the site as published, open `https://ferhatu9.github.io/ScoutMonitor-AI/`.

If Pages already uses GitHub Actions, change its source to **Deploy from a branch** before selecting `main /docs`. GitHub may take a short period to publish after saving. The website cannot be considered publicly live until the URL loads.

## Development checks

- `node --check docs/assets/site.js` checks JavaScript syntax.
- `.github/workflows/website.yml` verifies page assets, the 20 fictional players, and consistency with the repository's original CSV.
- `.github/workflows/code-quality.yml` continues checking the Python and PostgreSQL application.

## Product boundary

GitHub Pages publishes static files only. It cannot run Python, LangGraph, PostgreSQL, customer sign-in, or Gemini report generation. These are separate application components, not falsely represented as live features on this showcase.

A fully working multi-user product will require a secure deployed API, licensed football data, identity-provider onboarding, organization-isolated reports, operational monitoring, and a separately deployed customer application.
