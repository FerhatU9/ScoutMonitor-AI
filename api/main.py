"""Read-only HTTP endpoints for health and synthetic demonstration validation."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scoutmonitor.validation import DataValidationError, validate_players

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_DATA = PROJECT_ROOT / "data" / "fictional_players.csv"

app = FastAPI(
    title="ScoutMonitor AI API",
    description="Early API foundation. Does not expose private player records or generate AI reports.",
    version="0.1.0",
)


class HealthResponse(BaseModel):
    status: str
    service: str


class DemoValidationResponse(BaseModel):
    players: int
    rows_with_missing_metrics: int
    data_source: str


@app.get("/health", response_model=HealthResponse, tags=["Operations"])
def health() -> HealthResponse:
    """Liveness check; does not claim database or provider readiness."""
    return HealthResponse(status="ok", service="scoutmonitor-api")


@app.get("/api/v1/demo/validation", response_model=DemoValidationResponse, tags=["Demo"])
def validate_demo() -> DemoValidationResponse:
    """Validate the repository's fictional CSV; never read a user-supplied path."""
    try:
        result = validate_players(DEMO_DATA)
    except (DataValidationError, OSError):
        raise HTTPException(
            status_code=503, detail="Demonstration data unavailable or invalid"
        ) from None

    return DemoValidationResponse(**result, data_source="synthetic_v1")
