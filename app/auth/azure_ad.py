# app/auth/azure_ad.py
import os
import time
import httpx
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel

TENANT_ID = os.environ["AZURE_TENANT_ID"]
ISSUER = os.environ["AZURE_ISSUER"]
AUDIENCE = os.environ["AZURE_AUDIENCE"]

OIDC_WELLKNOWN = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"

_cached = {"jwks_uri": None, "ts": 0}

class UserContext(BaseModel):
    oid: str
    upn: str | None = None
    name: str | None = None
    groups: list[str] = []

async def _get_jwks_uri() -> str:
    # cache 1h
    if _cached["jwks_uri"] and (time.time() - _cached["ts"] < 3600):
        return _cached["jwks_uri"]

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(OIDC_WELLKNOWN)
        r.raise_for_status()
        jwks_uri = r.json()["jwks_uri"]
        _cached.update({"jwks_uri": jwks_uri, "ts": time.time()})
        return jwks_uri

async def validate_bearer_token(token: str) -> UserContext:
    jwks_uri = await _get_jwks_uri()
    jwk_client = PyJWKClient(jwks_uri)
    signing_key = jwk_client.get_signing_key_from_jwt(token).key

    claims = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        audience=AUDIENCE,
        issuer=ISSUER,
        options={"require": ["exp", "iat", "iss", "aud"]},
    )

    return UserContext(
        oid=claims.get("oid") or claims.get("sub"),
        upn=claims.get("preferred_username"),
        name=claims.get("name"),
        groups=claims.get("groups", []) or [],
    )