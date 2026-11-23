# API container only. The legacy Streamlit workflow remains local.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-api.txt ./
RUN python -m pip install --no-cache-dir -r requirements-api.txt

COPY api/ ./api/
COPY scoutmonitor/ ./scoutmonitor/
COPY data/fictional_players.csv ./data/fictional_players.csv
COPY db/migrations/ ./db/migrations/
COPY alembic.ini ./

# Do not run the web application or maintenance commands as root.
RUN groupadd --gid 10001 scoutmonitor \
    && useradd --uid 10001 --gid scoutmonitor --no-create-home --shell /usr/sbin/nologin scoutmonitor
USER scoutmonitor

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
