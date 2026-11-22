"""OIDC access-token checks run without network calls or real credentials."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from api.main import app


class TestOrganizationAuthentication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_key = cls.private_key.public_key()

    def setUp(self):
        self.client = TestClient(app)
        self.issuer = "https://identity.example.test"
        self.audience = "scoutmonitor-api"

    def token(self, **claims):
        now = datetime.now(timezone.utc)
        fields = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": "subject-1",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        }
        fields.update(claims)
        return jwt.encode(fields, self.private_key, algorithm="RS256")

    def request(self, token=None, configured=True):
        settings = {
            "OIDC_ISSUER": self.issuer if configured else "",
            "OIDC_AUDIENCE": self.audience if configured else "",
            "OIDC_JWKS_URL": self.issuer + "/.well-known/jwks.json" if configured else "",
        }
        with patch.dict(os.environ, settings), patch("api.security._client") as client:
            client.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(
                key=self.public_key
            )
            headers = {"Authorization": "Bearer " + token} if token is not None else {}
            return self.client.get(
                "/api/v1/organizations/11111111-1111-1111-1111-111111111111/watchlist",
                headers=headers,
            )

    def test_anonymous_cannot_access_watchlist(self):
        self.assertEqual(self.request().status_code, 401)

    def test_unconfigured_oidc_fails_closed(self):
        self.assertEqual(self.request(self.token(), configured=False).status_code, 503)

    def test_wrong_audience_rejected(self):
        self.assertEqual(self.request(self.token(aud="different-app")).status_code, 401)

    def test_wrong_issuer_rejected(self):
        self.assertEqual(
            self.request(self.token(iss="https://attacker.example.test")).status_code, 401
        )

    def test_expired_token_rejected(self):
        old_time = datetime.now(timezone.utc) - timedelta(minutes=2)
        self.assertEqual(self.request(self.token(exp=old_time)).status_code, 401)

    def test_missing_subject_rejected(self):
        now = datetime.now(timezone.utc)
        fields = {
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": now + timedelta(minutes=10),
        }
        self.assertEqual(self.request(jwt.encode(fields, self.private_key, algorithm="RS256")).status_code, 401)

    def test_unsigned_token_rejected(self):
        now = datetime.now(timezone.utc)
        token = jwt.encode(
            {"iss": self.issuer, "aud": self.audience, "sub": "subject-1",
             "iat": now, "exp": now + timedelta(minutes=10)},
            key="", algorithm="none",
        )
        self.assertEqual(self.request(token).status_code, 401)


if __name__ == "__main__":
    unittest.main()
