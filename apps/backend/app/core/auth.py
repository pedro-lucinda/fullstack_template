from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JOSEError
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """The authenticated user, derived from a validated Auth0 JWT."""

    sub: str
    email: str | None = None
    permissions: list[str] = []


@lru_cache
def _get_jwks() -> dict:
    """Fetch and cache Auth0's JSON Web Key Set used to verify token signatures."""
    response = httpx.get(settings.auth0_jwks_url, timeout=5.0)
    response.raise_for_status()
    return response.json()


def _get_signing_key(token: str) -> dict:
    unverified_header = jwt.get_unverified_header(token)
    for key in _get_jwks().get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            return key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find an appropriate signing key",
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """FastAPI dependency that validates the Auth0 bearer token and returns the user.

    Verifies the JWT signature against Auth0's JWKS, and checks issuer/audience,
    following Auth0's recommended FastAPI integration pattern.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        signing_key = _get_signing_key(token)
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=[settings.auth0_algorithms],
            audience=settings.auth0_api_audience,
            issuer=settings.auth0_issuer,
        )
    except JOSEError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return CurrentUser(
        sub=payload["sub"],
        email=payload.get("email"),
        permissions=payload.get("permissions", []),
    )
