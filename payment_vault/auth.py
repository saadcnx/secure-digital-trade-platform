import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ISSUER = os.getenv("JWT_ISSUER", "global-trade-platform-demo")
DEMO_API_KEY = os.getenv("DEMO_API_KEY")

if not JWT_SECRET or not DEMO_API_KEY:
    raise RuntimeError("JWT_SECRET and DEMO_API_KEY must be set in .env")

bearer_scheme = HTTPBearer(auto_error=False)


def issue_demo_jwt(x_demo_api_key: str | None = Header(default=None)) -> dict:
    if not x_demo_api_key or not secrets.compare_digest(
        x_demo_api_key, DEMO_API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing demo API key",
        )

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "local-demo-client",
        "iss": JWT_ISSUER,
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "scope": "payment:tokenize",
    }

    encoded = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {
        "access_token": encoded,
        "token_type": "bearer",
        "expires_in_seconds": 900,
        "warning": "Local educational demo token; not a production identity system.",
    }


def require_payment_jwt(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer JWT required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=["HS256"],
            issuer=JWT_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired JWT",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if claims.get("scope") != "payment:tokenize":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="JWT does not have payment:tokenize scope",
        )

    return claims
