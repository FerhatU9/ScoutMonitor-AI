"""Integration checks for organization membership and watchlist isolation.

Uses only the disposable CI database scoutmonitor_ci.
"""

import os
import unittest
from uuid import UUID

import psycopg
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from api.main import app
from api.security import Identity, require_identity


ORG_A = UUID("11111111-1111-4111-8111-111111111111")
ORG_B = UUID("22222222-2222-4222-8222-222222222222")
PLAYER_A = 99999921
PLAYER_B = 99999922
ISSUER = "https://identity.example.test"


@unittest.skipUnless(
    os.getenv("SCOUTMONITOR_RUN_DB_TESTS") == "1",
    "Organization integration requires the disposable CI database",
)
class TestOrganizationIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.getenv("SCOUTMONITOR_DATABASE_URL", "")
        settings = make_url(url)
        if settings.database != "scoutmonitor_ci":
            raise RuntimeError("Organization tests refuse non-CI databases")
        cls.conn_params = {
            "host": settings.host, "port": settings.port, "dbname": settings.database,
            "user": settings.username, "password": settings.password,
        }
        with psycopg.connect(**cls.conn_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO organizations (org_id, name) VALUES (%s, 'Club A'), (%s, 'Club B')",
                    (ORG_A, ORG_B),
                )
                cursor.execute(
                    "INSERT INTO identity_users (issuer, subject) VALUES (%s, 'user-a'), (%s, 'user-b')",
                    (ISSUER, ISSUER),
                )
                cursor.execute(
                    """
                    INSERT INTO organization_memberships (org_id, user_id, role)
                    SELECT %s, user_id, 'scout' FROM identity_users WHERE issuer = %s AND subject = 'user-a'
                    UNION ALL
                    SELECT %s, user_id, 'reviewer' FROM identity_users WHERE issuer = %s AND subject = 'user-b'
                    """,
                    (ORG_A, ISSUER, ORG_B, ISSUER),
                )
                cursor.execute(
                    "INSERT INTO players (player_id, name, team_id) VALUES (%s, 'CI Player A', 85), (%s, 'CI Player B', 85)",
                    (PLAYER_A, PLAYER_B),
                )
                cursor.execute(
                    """
                    INSERT INTO organization_watchlist (org_id, player_id, created_by_user_id)
                    SELECT %s, %s, user_id FROM identity_users
                    WHERE issuer = %s AND subject = 'user-b'
                    """,
                    (ORG_B, PLAYER_B, ISSUER),
                )

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        with psycopg.connect(**cls.conn_params) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM organization_watchlist WHERE org_id IN (%s, %s)",
                    (ORG_A, ORG_B),
                )
                cursor.execute(
                    "DELETE FROM organization_memberships WHERE org_id IN (%s, %s)",
                    (ORG_A, ORG_B),
                )
                cursor.execute("DELETE FROM organizations WHERE org_id IN (%s, %s)", (ORG_A, ORG_B))
                cursor.execute("DELETE FROM identity_users WHERE issuer = %s AND subject IN ('user-a', 'user-b')", (ISSUER,))
                cursor.execute("DELETE FROM players WHERE player_id IN (%s, %s)", (PLAYER_A, PLAYER_B))

    def setUp(self):
        self.client = TestClient(app)
        self.authenticate("user-a")

    def tearDown(self):
        app.dependency_overrides.clear()

    def authenticate(self, subject):
        app.dependency_overrides[require_identity] = lambda: Identity(
            issuer=ISSUER, subject=subject
        )

    def test_nonmember_cannot_read_other_organization(self):
        response = self.client.get(f"/api/v1/organizations/{ORG_B}/watchlist")
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("CI Player B", response.text)

    def test_member_sees_only_own_watchlist(self):
        response = self.client.get(f"/api/v1/organizations/{ORG_A}/watchlist")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["players"], [])

    def test_scout_can_add_player_for_own_organization(self):
        response = self.client.post(
            f"/api/v1/organizations/{ORG_A}/watchlist",
            json={"player_id": PLAYER_A},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual([x["player_id"] for x in response.json()["players"]], [PLAYER_A])
        with psycopg.connect(**self.conn_params) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM organization_watchlist WHERE org_id = %s AND player_id = %s",
                    (ORG_A, PLAYER_A),
                )

    def test_nonmember_cannot_write_other_organization(self):
        response = self.client.post(
            f"/api/v1/organizations/{ORG_B}/watchlist",
            json={"player_id": PLAYER_A},
        )
        self.assertEqual(response.status_code, 404)

    def test_reviewer_cannot_write(self):
        self.authenticate("user-b")
        response = self.client.post(
            f"/api/v1/organizations/{ORG_B}/watchlist",
            json={"player_id": PLAYER_A},
        )
        self.assertEqual(response.status_code, 403)

    def test_reviewer_can_read_own_watchlist(self):
        self.authenticate("user-b")
        response = self.client.get(f"/api/v1/organizations/{ORG_B}/watchlist")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([x["player_id"] for x in response.json()["players"]], [PLAYER_B])

    def test_nonexistent_player_cannot_be_added(self):
        response = self.client.post(
            f"/api/v1/organizations/{ORG_A}/watchlist",
            json={"player_id": 99999999},
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_player_id_rejected(self):
        response = self.client.post(
            f"/api/v1/organizations/{ORG_A}/watchlist",
            json={"player_id": -7},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
