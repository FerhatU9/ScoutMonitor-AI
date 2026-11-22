"""Verify externally issued OpenID Connect access tokens.

Identity comes from a trusted issuer. Organization roles come only from PostgreSQL.
This module never accepts a role, organization, or JWKS URL from the requester.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.error import URLError

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWKClientError
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Identity:
    issuer: str
    subject: str


@lru_cache(maxsize=4)
def _client(url: str) -> PyJWKClient:
    # JWKS location is server configuration, never a user-provided URL.
    return PyJWKClient(url, cache_keys=True, lifespan=300)


def require_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> Identity:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    issuer = os.getenv("OIDC_ISSUER", "").rstrip("/")
    audience = os.getenv("OIDC_AUDIENCE", "")
    jwks_url = os.getenv("OIDC_JWKS_URL", "")
    if not issuer.startswith("https://") or not audience or not jwks_url.startswith("https://"):
        # Fail closed if sign-in has not been configured on the server.
        raise HTTPException(status_code=503, detail="Identity provider not configured")

    try:
        signing_key = _client(jwks_url).get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            key=signing_key.key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience,
            leeway=30,
            options={"require": ["exp", "iat", "iss", "sub", "aud"]},
        )
        subject = claims["sub"]
        if not isinstance(subject, str) or not subject.strip():
            raise ValueError("Invalid identity subject")
    except (jwt.PyJWTError, PyJWKClientError, URLError, ValueError, TypeError, OSError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    return Identity(issuer=claims["iss"], subject=subject)
