"""Authentication service for validating JWT tokens from AWS Cognito."""
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient

COGNITO_REGION = os.environ.get("AWS_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.environ.get("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID", "")

JWKS_URL = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com"
    f"/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"
)

_security = HTTPBearer()


class AuthenticationService:
    """Validates JWT tokens issued by AWS Cognito using JWKS key verification."""

    def __init__(self) -> None:
        """Initialize with a JWKS client pointed at the Cognito user pool endpoint."""
        self._jwks_client = PyJWKClient(JWKS_URL)
        self._client_id = COGNITO_CLIENT_ID

    def verify_token(self, token: str) -> dict:
        """Decode and verify a Cognito JWT bearer token, returning its claims.

        Fetches the matching signing key from Cognito's JWKS endpoint and
        validates the token signature, expiry, and audience claim.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self._client_id,
        )
        return payload


_auth_service = AuthenticationService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> dict:
    """FastAPI dependency that validates the bearer token from the Authorization header.

    Decodes and verifies the Cognito JWT, returning the authenticated user's
    claims. Raises HTTP 401 if the token is absent, invalid, or expired.
    """
    try:
        return _auth_service.verify_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
