"""
routers/auth.py
===============
JWT authentication endpoints for FinRelief AI.

Public endpoints (no token required):
  POST /auth/register  — create account (password is bcrypt-hashed)
  POST /auth/login     — verify credentials, return JWT

Protected endpoints (Bearer token required):
  GET  /auth/me        — return current user's profile
  POST /auth/refresh   — issue a fresh token for a still-valid token
  POST /auth/logout    — client-side logout hint (stateless JWT)
  PUT  /auth/change-password — change password (re-hashes)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    CurrentUser,
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.schemas.api import LoginRequest, LoginResponse, MeResponse
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# POST /auth/register  (public)
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates a user with a bcrypt-hashed password and returns a JWT token immediately.",
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> dict:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),  # bcrypt hash
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.user_id, user.email)
    return {
        "message": "Account created successfully",
        "user": user,
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
    }


# ---------------------------------------------------------------------------
# POST /auth/login  (public)
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login and receive a JWT access token",
    description=(
        "Validates email/password, returns a signed JWT. "
        "Send the token as `Authorization: Bearer <token>` on all protected routes."
    ),
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    # Single indexed lookup on email — efficient per-session query
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(user.user_id, user.email)
    return {
        "message": "Login successful",
        "user": user,
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
    }


# ---------------------------------------------------------------------------
# GET /auth/me  (protected)
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get the current authenticated user's profile",
)
def me(current_user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    profile = (
        db.query(FinancialProfile)
        .filter(FinancialProfile.user_id == current_user.user_id)
        .first()
    )
    return {"user": current_user, "financial_profile": profile}


# ---------------------------------------------------------------------------
# POST /auth/refresh  (protected)
# ---------------------------------------------------------------------------

@router.post(
    "/refresh",
    summary="Refresh JWT — issue a new token for a still-valid session",
)
def refresh(current_user: CurrentUser) -> dict:
    """Issue a new JWT. Client should call this before expiry to stay logged in."""
    token = create_access_token(current_user.user_id, current_user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
    }


# ---------------------------------------------------------------------------
# PUT /auth/change-password  (protected)
# ---------------------------------------------------------------------------

class _ChangePasswordPayload:
    pass

from pydantic import BaseModel, Field

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


@router.put(
    "/change-password",
    summary="Change the authenticated user's password",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> dict:
    if not verify_password(payload.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.password = hash_password(payload.new_password)
    db.commit()
    # Issue a fresh token after password change
    token = create_access_token(current_user.user_id, current_user.email)
    return {
        "message": "Password changed successfully",
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
    }


# ---------------------------------------------------------------------------
# POST /auth/logout  (protected, informational)
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    summary="Logout (client-side token invalidation)",
    description="JWT is stateless — the client must discard the token. This endpoint is for audit/UX.",
)
def logout(current_user: CurrentUser) -> dict:
    return {"message": f"Goodbye, {current_user.name}. Please discard your token."}
