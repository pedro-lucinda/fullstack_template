from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JOSEError
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

# Module-level JWKS cache. Populated lazily on first use and refreshed
# on-demand if a token references a `kid` we don't recognize (e.g. after
# Auth0 rotates its signing keys) — see `_get_signing_key`.
_jwks_cache: dict[str, Any] | None = None


class CurrentUser(BaseModel):
    """The authenticated user, derived from a validated Auth0 JWT."""

    sub: str
    email: str | None = None
    permissions: list[str] = []


async def _fetch_jwks() -> dict[str, Any]:
    """Fetch Auth0's JSON Web Key Set (JWKS) used to verify token signatures."""
    async with httpx.AsyncClient(timeout=5.0) as http_client:
        response = await http_client.get(settings.auth0_jwks_url)
        response.raise_for_status()
        return response.json()


def _find_key(jwks: dict[str, Any], kid: str | None) -> dict[str, Any] | None:
    return next((key for key in jwks.get("keys", []) if key.get("kid") == kid), None)


async def _get_signing_key(token: str) -> dict[str, Any]:
    """Resolve the JWKS signing key matching the token's `kid` header.

    Uses a process-wide cache to avoid fetching the JWKS on every request, but
    transparently refreshes it once if the `kid` isn't found — this keeps
    verification working across Auth0 key rotations without a restart.
    """
    global _jwks_cache

    kid = jwt.get_unverified_header(token).get("kid")

    if _jwks_cache is None:
        _jwks_cache = await _fetch_jwks()

    key = _find_key(_jwks_cache, kid)
    if key is None:
        _jwks_cache = await _fetch_jwks()
        key = _find_key(_jwks_cache, kid)

    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find an appropriate signing key",
        )
    return key


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
        signing_key = await _get_signing_key(token)
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
