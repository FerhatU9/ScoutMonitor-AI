"""Organization-private scouting note API.

Notes are human-authored, not AI reports. The API enforces a verified identity,
active organization membership, and a restricted PostgreSQL connection with
row-level security. Never connect as a database owner or superuser.
"""

import os
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.engine import make_url

from api.security import Identity, require_identity

router = APIRouter(prefix="/api/v1/organizations", tags=["Private scouting notes"])


class NoteCreate(BaseModel):
    player_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=150)
    body: str = Field(min_length=1, max_length=5000)


class NoteView(BaseModel):
    note_id: UUID
    player_id: int
    player_name: str
    title: str
    body: str


class NotePage(BaseModel):
    organization_id: UUID
    notes: list[NoteView]
    limit: int
    offset: int


def _private_connection():
    """Require a dedicated least-privilege connection, not the legacy DB_* URL."""
    raw_url = os.getenv("SCOUTMONITOR_PRIVATE_DATABASE_URL")
    if not raw_url:
        raise RuntimeError("Restricted organization database connection not configured")
    url = make_url(raw_url)
    if url.drivername != "postgresql+psycopg":
        raise RuntimeError("Only PostgreSQL psycopg connections are supported")
    if not url.username or url.username in ("postgres", "scoutmonitor_owner"):
        raise RuntimeError("Organization API must not connect using a database owner")
    return psycopg.connect(
        host=url.host, port=url.port, dbname=url.database,
        user=url.username, password=url.password, connect_timeout=10,
    )


def _authorize(connection, organization_id: UUID, identity: Identity) -> tuple[int, str]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, m.role
            FROM organization_memberships m
            JOIN identity_users u ON u.user_id = m.user_id
            JOIN organizations o ON o.org_id = m.org_id
            WHERE m.org_id = %s
              AND u.issuer = %s AND u.subject = %s
              AND m.active AND o.active
            """,
            (organization_id, identity.issuer, identity.subject),
        )
        membership = cursor.fetchone()
        if membership is None:
            raise HTTPException(status_code=404, detail="Organization not found")

        user_id, role = membership
        # True = transaction-local. Never persist identity across connections.
        cursor.execute(
            """
            SELECT
              set_config('scoutmonitor.org_id', %s, true),
              set_config('scoutmonitor.user_id', %s, true)
            """,
            (str(organization_id), str(user_id)),
        )
    return user_id, role


def _list_notes(connection, organization_id: UUID, limit: int, offset: int):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT n.note_id, n.player_id, p.name, n.title, n.body
            FROM organization_scouting_notes n
            JOIN players p ON p.player_id = n.player_id
            WHERE n.org_id = %s
            ORDER BY n.created_at DESC, n.note_id DESC
            LIMIT %s OFFSET %s
            """,
            (organization_id, limit, offset),
        )
        return [
            NoteView(
                note_id=row[0], player_id=row[1], player_name=row[2],
                title=row[3], body=row[4]
            )
            for row in cursor.fetchall()
        ]


@router.get("/{organization_id}/notes", response_model=NotePage)
def list_private_notes(
    organization_id: UUID,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
    identity: Identity = Depends(require_identity),
) -> NotePage:
    try:
        with _private_connection() as connection:
            _authorize(connection, organization_id, identity)
            notes = _list_notes(connection, organization_id, limit, offset)
        return NotePage(
            organization_id=organization_id, notes=notes,
            limit=limit, offset=offset,
        )
    except (psycopg.Error, RuntimeError, ValueError):
        raise HTTPException(status_code=503, detail="Scouting notes unavailable") from None


@router.post("/{organization_id}/notes", response_model=NoteView, status_code=201)
def create_private_note(
    organization_id: UUID,
    note: NoteCreate,
    identity: Identity = Depends(require_identity),
) -> NoteView:
    title = note.title.strip()
    body = note.body.strip()
    if not title or not body:
        raise HTTPException(status_code=422, detail="Title and body must not be blank")

    try:
        with _private_connection() as connection:
            user_id, role = _authorize(connection, organization_id, identity)
            if role not in ("owner", "admin", "scout"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT name FROM players WHERE player_id = %s",
                    (note.player_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="Player not found")
                player_name = row[0]
                cursor.execute(
                    """
                    INSERT INTO organization_scouting_notes
                        (org_id, player_id, author_user_id, title, body)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING note_id
                    """,
                    (organization_id, note.player_id, user_id, title, body),
                )
                note_id = cursor.fetchone()[0]
        return NoteView(
            note_id=note_id, player_id=note.player_id,
            player_name=player_name, title=title, body=body,
        )
    except (psycopg.Error, RuntimeError, ValueError):
        raise HTTPException(status_code=503, detail="Scouting notes unavailable") from None
