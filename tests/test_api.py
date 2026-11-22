"""Read-only API tests; no database or external credentials required."""

import unittest

from fastapi.testclient import TestClient

from api.main import app


class TestPublicApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_status(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "ok", "service": "scoutmonitor-api"
        })

    def test_demo_validation(self):
        response = self.client.get("/api/v1/demo/validation")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "players": 20,
            "rows_with_missing_metrics": 2,
            "data_source": "synthetic_v1",
        })

    def test_openapi_documentation(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/api/v1/demo/validation", response.json()["paths"])

    def test_no_private_data_endpoints(self):
        response = self.client.get("/api/v1/players")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
