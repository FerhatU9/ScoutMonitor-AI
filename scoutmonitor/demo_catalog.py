"""Verified, read-only catalog of fictional football players."""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from scoutmonitor.validation import validate_players

SortField = Literal["player_id", "minutes", "progressive_passes_per90", "defensive_duel_win_pct"]
SortOrder = Literal["asc", "desc"]


@dataclass(frozen=True)
class DemoPlayer:
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


def _optional_float(value: str) -> float | None:
    return None if value == "" else float(value)


def load_demo_players(path: Path) -> list[DemoPlayer]:
    """Validate the entire CSV before returning any player data."""
    validate_players(path)
    with path.open(newline="", encoding="utf-8-sig") as source:
        return [
            DemoPlayer(
                player_id=row["player_id"],
                player_name=row["player_name"],
                age=int(row["age"]),
                position=row["position"],
                preferred_foot=row["preferred_foot"].lower(),
                league=row["league"],
                minutes=int(row["minutes"]),
                progressive_passes_per90=_optional_float(row["progressive_passes_per90"]),
                defensive_duel_win_pct=_optional_float(row["defensive_duel_win_pct"]),
                is_synthetic=True,
                source="synthetic_v1",
            )
            for row in csv.DictReader(source)
        ]


def filter_and_sort_players(
    players: list[DemoPlayer],
    *,
    league: str | None = None,
    preferred_foot: str | None = None,
    min_minutes: int = 0,
    sort_by: SortField = "player_id",
    order: SortOrder = "asc",
) -> list[DemoPlayer]:
    """Apply bounded filters; sort missing statistics last in either direction."""
    selected = [
        player for player in players
        if (league is None or player.league.casefold() == league.casefold())
        and (preferred_foot is None or player.preferred_foot == preferred_foot)
        and player.minutes >= min_minutes
    ]
    known = [player for player in selected if getattr(player, sort_by) is not None]
    missing = [player for player in selected if getattr(player, sort_by) is None]
    return sorted(
        known,
        key=lambda player: (getattr(player, sort_by), player.player_id),
        reverse=order == "desc",
    ) + sorted(missing, key=lambda player: player.player_id)


def metric_differences(first: DemoPlayer, second: DemoPlayer) -> dict[str, float | int | None]:
    """Second minus first, retaining null for any unreported metric."""
    return {
        "minutes": second.minutes - first.minutes,
        "progressive_passes_per90": (
            None if first.progressive_passes_per90 is None or second.progressive_passes_per90 is None
            else round(second.progressive_passes_per90 - first.progressive_passes_per90, 4)
        ),
        "defensive_duel_win_pct": (
            None if first.defensive_duel_win_pct is None or second.defensive_duel_win_pct is None
            else round(second.defensive_duel_win_pct - first.defensive_duel_win_pct, 4)
        ),
    }
