# ScoutMonitor AI — Local Docker development

This setup creates a **separate**, Docker-managed PostgreSQL 18 volume and runs the synthetic-data FastAPI backend in a container. It does **not** import, migrate, or overwrite your existing Windows PostgreSQL reports. It is a development environment, not a publicly hosted or tenant-isolated product.

## Requirements

- Docker Desktop running Linux containers, with Docker Compose available.
- A local checkout of this repository on Windows.
- Port 8000 available on your machine; stop any previously running local Uvicorn process on that port.

## Run the API and database

Open PowerShell in the repository root:

1. Run `docker --version` and `docker compose version` to confirm Docker is installed.
2. If `.env` does not exist, create it with `Copy-Item .env.example .env`. If it already exists, **do not overwrite it**.
3. Add exactly one new line to your ignored local `.env` file:
   `SCOUTMONITOR_DOCKER_DB_PASSWORD=<your-own-long-random-password>`
   Replace the placeholder with a real locally generated password. Do not paste that password into a chat, commit, or screenshot. Do not use the password from your existing PostgreSQL database.
4. Start the containers:

   ```powershell
   docker compose up --build -d
   docker compose ps
   Invoke-RestMethod http://127.0.0.1:8000/health
   Invoke-RestMethod http://127.0.0.1:8000/api/v1/demo/validation
   ```

The health response should identify the `scoutmonitor-api` service. The validation endpoint should report **20 fictional players** and **two rows with unavailable metrics**. Open `http://127.0.0.1:8000/docs` to inspect the demo API. The API port is bound to your own computer; the database port is not published.

## Initialize the new container database deliberately

Only after the separate Docker PostgreSQL service is running, execute:

```powershell
docker compose run --rm migrate
```

This runs the guarded Alembic migrations against the specifically named `scoutmonitor_demo` database in the Docker environment. It is safe to rerun against this Alembic-managed database, but do not repoint the command to your existing local PostgreSQL installation.

The API currently serves fictional players from a bundled CSV, not this database. The organization-protected endpoints also require real OIDC configuration and restricted database access, which this local demonstration **does not provision**. Never expose these containers directly to the internet or use the PostgreSQL admin connection for production customer traffic.

## Inspect and stop

```powershell
docker compose logs --tail=100 api
docker compose down
```

`docker compose down` keeps the isolated database volume. **Do not run `docker compose down -v` unless you intend to permanently delete that Docker demonstration database volume.**

## What this milestone proves

- A new developer can build and start the Python API without configuring a local Python environment.
- PostgreSQL runs separately without interfering with local Windows databases.
- The API validates the bundled fictional data.
- New schemas can be initialized through guarded migrations.
- Container builds can be checked automatically in GitHub Actions.

This does **not** validate the full Gemini/LangGraph/Streamlit report workflow, real sign-in, tenant-owned AI reports, private-note runtime roles, or cloud readiness. Those remain separate product milestones.
