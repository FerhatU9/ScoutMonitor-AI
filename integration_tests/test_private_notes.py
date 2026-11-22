"""Cross-organization protection for private scouting notes.

All tests use temporary PostgreSQL CI data, never real scouting reports.
"""

import os
import unittest
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from api.main import app
from api.security import Identity, require_identity

ORG_A = UUID("33333333-3333-4333-8333-333333333333")
ORG_B = UUID("44444444-4444-4444-8444-444444444444")
PLAYER = 99999941
ISSUER = "https://identity.example.test"


@unittest.skipUnless(
    os.getenv("SCOUTMONITOR_RUN_DB_TESTS") == "1",
    "Private note integration tests require the disposable PostgreSQL CI database",
)
class TestPrivateNoteIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        admin_url = make_url(os.getenv("SCOUTMONITOR_DATABASE_URL", ""))
        runtime_url = make_url(os.getenv("SCOUTMONITOR_PRIVATE_DATABASE_URL", ""))
        if admin_url.database != "scoutmonitor_ci" or runtime_url.database != "scoutmonitor_ci":
            raise RuntimeError("Private note integration tests refuse non-CI databases")
        if runtime_url.username in ("postgres", admin_url.username):
            raise RuntimeError("RLS tests require an independent, restricted database role")

        def parameters(url):
            return {
                "host": url.host, "port": url.port, "dbname": url.database,
                "user": url.username, "password": url.password,
            }

        cls.admin = parameters(admin_url)
        cls.runtime = parameters(runtime_url)
        with psycopg.connect(**cls.admin) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO organizations (org_id, name) VALUES "
                    "(%s, 'Private Notes A'), (%s, 'Private Notes B')",
                    (ORG_A, ORG_B),
                )
                cursor.execute(
                    "INSERT INTO identity_users (issuer, subject) VALUES "
                    "(%s, 'notes-scout'), (%s, 'notes-reviewer')",
                    (ISSUER, ISSUER),
                )
                cursor.execute(
                    """
                    INSERT INTO organization_memberships (org_id, user_id, role)
                    SELECT %s, user_id, 'scout'
                    FROM identity_users WHERE issuer = %s AND subject = 'notes-scout'
                    UNION ALL
                    SELECT %s, user_id, 'reviewer'
                    FROM identity_users WHERE issuer = %s AND subject = 'notes-reviewer'
                    """,
                    (ORG_A, ISSUER, ORG_B, ISSUER),
                )
                cursor.execute(
                    "INSERT INTO players (player_id, name) VALUES (%s, 'Private Note Test Player')",
                    (PLAYER,),
                )
                cursor.execute(
                    """
                    INSERT INTO organization_scouting_notes
                      (org_id, player_id, author_user_id, title, body)
                    SELECT %s, %s, user_id, 'Other club confidential',
                           'Only Club B may read this'
                    FROM identity_users WHERE issuer = %s AND subject = 'notes-reviewer'
                    """,
                    (ORG_B, PLAYER, ISSUER),
                )

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        with psycopg.connect(**cls.admin) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM organization_scouting_notes WHERE org_id IN (%s, %s)",
                    (ORG_A, ORG_B),
                )
                cursor.execute(
                    "DELETE FROM organization_memberships WHERE org_id IN (%s, %s)",
                    (ORG_A, ORG_B),
                )
                cursor.execute(
                    "DELETE FROM organizations WHERE org_id IN (%s, %s)",
                    (ORG_A, ORG_B),
                )
                cursor.execute(
                    "DELETE FROM identity_users WHERE issuer = %s "
                    "AND subject IN ('notes-scout', 'notes-reviewer')",
                    (ISSUER,),
                )
                cursor.execute("DELETE FROM players WHERE player_id = %s", (PLAYER,))

    def setUp(self):
        self.client = TestClient(app)
        self.as_user("notes-scout")
        with psycopg.connect(**self.admin) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM organization_scouting_notes WHERE org_id = %s",
                    (ORG_A,),
                )

    def tearDown(self):
        app.dependency_overrides.clear()

    def as_user(self, subject):
        app.dependency_overrides[require_identity] = lambda: Identity(
            issuer=ISSUER, subject=subject
        )

    def test_scout_cannot_read_other_club_notes(self):
        result = self.client.get(f"/api/v1/organizations/{ORG_B}/notes")
        self.assertEqual(result.status_code, 404)
        self.assertNotIn("confidential", result.text.lower())

    def test_scout_cannot_add_note_to_other_club(self):
        result = self.client.post(
            f"/api/v1/organizations/{ORG_B}/notes",
            json={"player_id": PLAYER, "title": "Unauthorized", "body": "Rejected"},
        )
        self.assertEqual(result.status_code, 404)

    def test_scout_can_create_and_read_private_note(self):
        result = self.client.post(
            f"/api/v1/organizations/{ORG_A}/notes",
            json={"player_id": PLAYER, "title": "Player summary", "body": "Good positioning"},
        )
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.json()["title"], "Player summary")
        listing = self.client.get(f"/api/v1/organizations/{ORG_A}/notes")
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(len(listing.json()["notes"]), 1)
        self.assertNotIn("Other club confidential", listing.text)

    def test_reviewer_can_read_own_club(self):
        self.as_user("notes-reviewer")
        result = self.client.get(f"/api/v1/organizations/{ORG_B}/notes")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["notes"][0]["title"], "Other club confidential")

    def test_reviewer_cannot_create_notes(self):
        self.as_user("notes-reviewer")
        result = self.client.post(
            f"/api/v1/organizations/{ORG_B}/notes",
            json={"player_id": PLAYER, "title": "Unauthorized", "body": "Rejected"},
        )
        self.assertEqual(result.status_code, 403)

    def test_unknown_player_returns_404(self):
        result = self.client.post(
            f"/api/v1/organizations/{ORG_A}/notes",
            json={"player_id": 99999998, "title": "Missing", "body": "No player"},
        )
        self.assertEqual(result.status_code, 404)

    def test_postgres_rls_denies_rows_without_verified_context(self):
        with psycopg.connect(**self.runtime) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM organization_scouting_notes")
                self.assertEqual(cursor.fetchone()[0], 0)

    def test_postgres_rls_limits_rows_to_selected_club(self):
        with psycopg.connect(**self.admin) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO organization_scouting_notes
                      (org_id, player_id, author_user_id, title, body)
                    SELECT %s, %s, user_id, 'Club A note', 'Private data'
                    FROM identity_users WHERE issuer = %s AND subject = 'notes-scout'
                    """,
                    (ORG_A, PLAYER, ISSUER),
                )

        with psycopg.connect(**self.runtime) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT set_config('scoutmonitor.org_id', %s, true),
                           set_config('scoutmonitor.user_id', (
                               SELECT user_id::text FROM identity_users
                               WHERE issuer = %s AND subject = 'notes-scout'
                           ), true)
                    """,
                    (str(ORG_A), ISSUER),
                )
                # No WHERE clause: actual PostgreSQL row security hides Club B.
                cursor.execute("SELECT title FROM organization_scouting_notes")
                self.assertEqual([r[0] for r in cursor.fetchall()], ["Club A note"])


if __name__ == "__main__":
    unittest.main()
