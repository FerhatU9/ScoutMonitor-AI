"""Organization-scoped watchlist endpoints.

The trusted identity is verified from an external OIDC token.
Every database query is scoped to an active PostgreSQL membership.
These endpoints are not ready for public deployment without further hardening.
"""

import os
from pathlib import Path
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.engine import make_url

from api.security import Identity, require_identity

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])


class WatchlistEntry(BaseModel):
    player_id: int
    player_name: str


class WatchlistResponse(BaseModel):
    organization_id: UUID
    players: list[WatchlistEntry]


class AddWatchlistPlayer(BaseModel):
    player_id: int = Field(gt=0)


def _connection():
    url = os.getenv("SCOUTMONITOR_DATABASE_URL")
    if url:
        settings = make_url(url)
        if settings.drivername != "postgresql+psycopg":
            raise RuntimeError("Unsupported PostgreSQL driver")
        return psycopg.connect(
            host=settings.host, port=settings.port, dbname=settings.database,
            user=settings.username, password=settings.password, connect_timeout=10,
        )
    required = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    if any(not os.getenv(key) for key in required):
        raise RuntimeError("Database is not configured")
    return psycopg.connect(
        host=os.environ["DB_HOST"], port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], connect_timeout=10,
    )


def _membership(connection, organization_id: UUID, identity: Identity) -> tuple[int, str]:
    """Resolve permission from trusted identity AND active DB membership."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, m.role
            FROM organization_memberships m
            JOIN identity_users u ON u.user_id = m.user_id
            JOIN organizations o ON o.org_id = m.org_id
            WHERE m.org_id = %s AND u.issuer = %s AND u.subject = %s
              AND m.active = TRUE AND o.active = TRUE
            """,
            (organization_id, identity.issuer, identity.subject),
        )
        found = cursor.fetchone()
    if found is None:
        # Avoid disclosing whether an organization exists.
        raise HTTPException(status_code=404, detail="Organization not found")
    return found


@router.get("/{organization_id}/watchlist", response_model=WatchlistResponse)
def read_watchlist(
    organization_id: UUID,
    identity: Identity = Depends(require_identity),
) -> WatchlistResponse:
    try:
        with _connection() as connection:
            _membership(connection, organization_id, identity)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT p.player_id, p.name
                    FROM organization_watchlist w
                    JOIN players p ON p.player_id = w.player_id
                    WHERE w.org_id = %s
                    ORDER BY p.name, p.player_id
                    LIMIT 500
                    """,
                    (organization_id,),
                )
                rows = cursor.fetchall()
    except (psycopg.Error, RuntimeError):
        raise HTTPException(status_code=503, detail="Organization data unavailable") from None

    return WatchlistResponse(
        organization_id=organization_id,
        players=[WatchlistEntry(player_id=item[0], player_name=item[1]) for item in rows],
    )


@router.post("/{organization_id}/watchlist", response_model=WatchlistResponse, status_code=201)
def add_watchlist_player(
    organization_id: UUID,
    item: AddWatchlistPlayer,
    identity: Identity = Depends(require_identity),
) -> WatchlistResponse:
    try:
        with _connection() as connection:
            user_id, role = _membership(connection, organization_id, identity)
            if role not in ("owner", "admin", "scout"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM players WHERE player_id = %s", (item.player_id,)
                )
                if cursor.fetchone() is None:
                    raise HTTPException(status_code=404, detail="Player not found")
                cursor.execute(
                    """
                    INSERT INTO organization_watchlist
                      (org_id, player_id, created_by_user_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (org_id, player_id) DO NOTHING
                    """,
                    (organization_id, item.player_id, user_id),
                )
                cursor.execute(
                    """
                    SELECT p.player_id, p.name
                    FROM organization_watchlist w
                    JOIN players p ON p.player_id = w.player_id
                    WHERE w.org_id = %s
                    ORDER BY p.name, p.player_id
                    LIMIT 500
                    """,
                    (organization_id,),
                )
                rows = cursor.fetchall()
    except (psycopg.Error, RuntimeError):
        raise HTTPException(status_code=503, detail="Organization data unavailable") from None

    return WatchlistResponse(
        organization_id=organization_id,
        players=[WatchlistEntry(player_id=p[0], player_name=p[1]) for p in rows],
    )
