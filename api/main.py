"""Read-only HTTP endpoints for health and verified synthetic player records."""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from api.organizations import router as organizations_router
from api.private_notes import router as notes_router
from pydantic import BaseModel

from scoutmonitor.demo_catalog import (
    DemoPlayer,
    filter_and_sort_players,
    load_demo_players,
    metric_differences,
)
from scoutmonitor.validation import DataValidationError, validate_players

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEMO_DATA = PROJECT_ROOT / "data" / "fictional_players.csv"

app = FastAPI(
    title="ScoutMonitor AI API",
    description="Read-only synthetic-data API. No customer records, real football-provider data, or AI generation endpoints.",
    version="0.2.0",
)


app.include_router(organizations_router)
app.include_router(notes_router)


class HealthResponse(BaseModel):
    status: str
    service: str


class DemoValidationResponse(BaseModel):
    players: int
    rows_with_missing_metrics: int
    data_source: str


class DemoPlayerResponse(BaseModel):
    player_id: str
    player_name: str
    age: int
    position: str
    preferred_foot: str
    league: str
    minutes: int
    progressive_passes_per90: float | None
    defensive_duel_win_pct: float | None
    is_synthetic: bool
    source: str


class DemoPlayerPage(BaseModel):
    total: int
    offset: int
    limit: int
    data_source: str
    players: list[DemoPlayerResponse]


class MetricDifference(BaseModel):
    minutes: int
    progressive_passes_per90: float | None
    defensive_duel_win_pct: float | None


class DemoPlayerComparison(BaseModel):
    first: DemoPlayerResponse
    second: DemoPlayerResponse
    difference_second_minus_first: MetricDifference
    data_source: str


def _get_players() -> list[DemoPlayer]:
    try:
        return load_demo_players(DEMO_DATA)
    except (DataValidationError, OSError, ValueError):
        raise HTTPException(
            status_code=503, detail="Demonstration data unavailable or invalid"
        ) from None


def _find_player(players: list[DemoPlayer], player_id: str) -> DemoPlayer:
    player = next((item for item in players if item.player_id == player_id), None)
    if player is None:
        raise HTTPException(status_code=404, detail="Demo player not found")
    return player


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


@app.get("/api/v1/demo/players", response_model=DemoPlayerPage, tags=["Demo"])
def list_demo_players(
    league: str | None = Query(default=None, min_length=1, max_length=80),
    preferred_foot: Literal["left", "right", "both"] | None = None,
    min_minutes: int = Query(default=0, ge=0, le=6000),
    sort_by: Literal["player_id", "minutes", "progressive_passes_per90", "defensive_duel_win_pct"] = "player_id",
    order: Literal["asc", "desc"] = "asc",
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> DemoPlayerPage:
    """Browse verified synthetic football players with bounded pagination."""
    selected = filter_and_sort_players(
        _get_players(), league=league, preferred_foot=preferred_foot,
        min_minutes=min_minutes, sort_by=sort_by, order=order,
    )
    return DemoPlayerPage(
        total=len(selected), offset=offset, limit=limit,
        data_source="synthetic_v1",
        players=[
            DemoPlayerResponse.model_validate(player, from_attributes=True)
            for player in selected[offset:offset + limit]
        ],
    )


@app.get("/api/v1/demo/players/{player_id}", response_model=DemoPlayerResponse, tags=["Demo"])
def get_demo_player(player_id: str) -> DemoPlayerResponse:
    """Retrieve one verified fictional player by ID."""
    return DemoPlayerResponse.model_validate(_find_player(_get_players(), player_id), from_attributes=True)


@app.get("/api/v1/demo/compare", response_model=DemoPlayerComparison, tags=["Demo"])
def compare_demo_players(
    first_id: str = Query(min_length=1, max_length=32),
    second_id: str = Query(min_length=1, max_length=32),
) -> DemoPlayerComparison:
    """Compare two fictional players; unknown differences remain null."""
    if first_id == second_id:
        raise HTTPException(status_code=400, detail="Select two different demo players")
    players = _get_players()
    first = _find_player(players, first_id)
    second = _find_player(players, second_id)
    return DemoPlayerComparison(
        first=DemoPlayerResponse.model_validate(first, from_attributes=True),
        second=DemoPlayerResponse.model_validate(second, from_attributes=True),
        difference_second_minus_first=MetricDifference(**metric_differences(first, second)),
        data_source="synthetic_v1",
    )
