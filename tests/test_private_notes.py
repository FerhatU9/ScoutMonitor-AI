"""Scouting-note API request validation without a database or real credentials."""

import unittest
from fastapi.testclient import TestClient
from api.main import app

ORG = "11111111-1111-4111-8111-111111111111"


class TestPrivateNotesRequests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_anonymous_cannot_read_notes(self):
        self.assertEqual(
            self.client.get(f"/api/v1/organizations/{ORG}/notes").status_code, 401
        )

    def test_anonymous_cannot_create_notes(self):
        self.assertEqual(
            self.client.post(
                f"/api/v1/organizations/{ORG}/notes",
                json={"player_id": 1, "title": "Note", "body": "Evidence"},
            ).status_code,
            401,
        )

    def test_invalid_note_rejected(self):
        self.assertEqual(
            self.client.post(
                f"/api/v1/organizations/{ORG}/notes",
                json={"player_id": -1, "title": "Note", "body": "Evidence"},
            ).status_code,
            422,
        )

    def test_unbounded_paging_rejected(self):
        self.assertEqual(
            self.client.get(f"/api/v1/organizations/{ORG}/notes?limit=101").status_code,
            422,
        )


if __name__ == "__main__":
    unittest.main()
