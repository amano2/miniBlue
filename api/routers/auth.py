"""Authentication Router for miniBlue Enterprise Platform.

Endpoints:
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- GET  /api/v1/auth/me
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_and_rotate_refresh_token,
    verify_password,
)
from api.db import get_db_connection
from api.schemas import LoginRequest, RefreshRequest, TokenResponse, UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    """Authenticates a user with email + password and issues access & refresh tokens."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, employee_id, email, full_name, password_hash, role, is_active, failed_logins, locked_until
        FROM users WHERE email = ? COLLATE NOCASE
        """,
        (payload.email.strip(),),
    )
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}},
        )

    if not user["is_active"]:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "ACCOUNT_DISABLED", "message": "This account has been disabled."}},
        )

    # Check lockout
    now_iso = datetime.now(timezone.utc).isoformat()
    if user["locked_until"] and user["locked_until"] > now_iso:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "ACCOUNT_LOCKED", "message": "Account temporarily locked due to failed attempts."}},
        )

    # Verify password
    if not verify_password(payload.password, user["password_hash"]):
        failed = user["failed_logins"] + 1
        lock_until = None
        if failed >= 5:
            # 15 min lock
            lock_until = (datetime.now(timezone.utc).timestamp() + 900)
            lock_until_iso = datetime.fromtimestamp(lock_until, timezone.utc).isoformat()
            cursor.execute("UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?", (failed, lock_until_iso, user["id"]))
        else:
            cursor.execute("UPDATE users SET failed_logins = ? WHERE id = ?", (failed, user["id"]))
        conn.commit()
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}},
        )

    # Successful login: reset failed logins, set last_login_at
    cursor.execute("UPDATE users SET failed_logins = 0, locked_until = NULL, last_login_at = ? WHERE id = ?", (now_iso, user["id"]))
    conn.commit()
    conn.close()

    # Create tokens
    access_token = create_access_token(
        data={
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
            "name": user["full_name"],
            "emp_id": user["employee_id"],
        }
    )
    refresh_token = create_refresh_token(user["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=900,
        role=user["role"],
        full_name=user["full_name"],
        email=user["email"],
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest) -> TokenResponse:
    """Rotates refresh token and returns a fresh access token."""
    user_id, new_refresh_token = verify_and_rotate_refresh_token(payload.refresh_token)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, employee_id, email, full_name, role, is_active FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_USER", "message": "User no longer active."}},
        )

    access_token = create_access_token(
        data={
            "sub": str(user["id"]),
            "email": user["email"],
            "role": user["role"],
            "name": user["full_name"],
            "emp_id": user["employee_id"],
        }
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=900,
        role=user["role"],
        full_name=user["full_name"],
        email=user["email"],
    )


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)) -> UserOut:
    """Returns the authenticated user's profile and active role."""
    return UserOut(
        id=current_user["id"],
        employee_id=current_user["employee_id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        role=current_user["role"],
        department=current_user.get("department"),
        is_active=bool(current_user["is_active"]),
        last_login_at=current_user.get("last_login_at"),
    )
