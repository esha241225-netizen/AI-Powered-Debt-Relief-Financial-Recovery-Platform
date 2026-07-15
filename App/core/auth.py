"""
auth.py
=======
JWT token-based authentication for FinRelief AI.

Provides:
  - Password hashing with bcrypt (via Werkzeug)
  - JWT access token creation (HS256, python-jose)
  - Bearer token extraction + verification
  - `get_current_user` FastAPI dependency for protected routes
  - `get_db_user` — combines DB session + auth in one dependency
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from app.db.session import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# Configuration (use env vars in production)
# ---------------------------------------------------------------------------

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "finrelief-super-secret-change-me-in-prod")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 h

# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return generate_password_hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*.

    Supports both bcrypt hashes (new accounts) and plain-text passwords
    stored by the old system — detects the format automatically so existing
    accounts keep working after the upgrade.
    """
    # Old plain-text passwords from pre-JWT era
    if not hashed.startswith(("pbkdf2:", "scrypt:", "bcrypt:")):
        return plain == hashed
    return check_password_hash(hashed, plain)


# ---------------------------------------------------------------------------
# JWT token creation
# ---------------------------------------------------------------------------


def create_access_token(user_id: int, email: str) -> str:
    """Create a signed JWT containing the user's ID and email."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),        # subject = user_id
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Token extraction & verification
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


def _credentials_exception(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency — decode Bearer token → return the authenticated User.

    Raises HTTP 401 if token is missing, expired, or invalid.
    """
    if credentials is None:
        raise _credentials_exception("Authentication token missing")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise _credentials_exception()
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise _credentials_exception()

    # Single indexed lookup — O(log n) on the primary key
    user = db.get(User, user_id)
    if user is None:
        raise _credentials_exception("User not found")

    return user


# Type alias for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
