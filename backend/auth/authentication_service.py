"""Authentication service for validating AWS Cognito JWT tokens."""
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import JWTError, jwt


COGNITO_REGION = os.environ.get("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "")

_JWKS_URL = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com"
    f"/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)

_security = HTTPBearer()


async def _fetch_jwks() -> dict:
    """Fetch the JSON Web Key Set from AWS Cognito for token signature verification."""
    async with httpx.AsyncClient() as client:
        response = await client.get(_JWKS_URL)
        response.raise_for_status()
        return response.json()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> dict:
    """Validate the bearer token against Cognito and return the authenticated user's JWT claims.

    Raises HTTP 401 if the token is absent, expired, or fails signature verification.
    """
    token = credentials.credentials
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        jwks = await _fetch_jwks()
        header = jwt.get_unverified_header(token)
        signing_key = next(
            (key for key in jwks["keys"] if key["kid"] == header["kid"]),
            None,
        )
        if signing_key is None:
            raise invalid_credentials

        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
        )
        return claims
    except JWTError:
        raise invalid_credentials
