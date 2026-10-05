"""Authentication, Password Hashing, JWT Tokens, and Role-Based Access Control (RBAC).

Implements FR-1 and TRD §4:
- Password hashing using bcrypt.
- JWT Access token (15 min) and Refresh token (7 days).
- Token rotation and revocation in refresh_tokens table.
- FastAPI dependencies: get_current_user, require_role.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from api.db import get_db_connection

# Secrets and configuration
SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "miniblue-super-secret-jwt-key-2026-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generates an encoded JWT access token with role and user claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Creates, stores, and returns an opaque random refresh token string."""
    token_str = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token_str.encode()).hexdigest()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, token_hash, expires_at, now_iso),
    )
    conn.commit()
    conn.close()
    return token_str


def verify_and_rotate_refresh_token(token_str: str) -> tuple[int, str]:
    """Validates refresh token, revokes it, and issues a new refresh token."""
    token_hash = hashlib.sha256(token_str.encode()).hexdigest()
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, expires_at, revoked_at
        FROM refresh_tokens
        WHERE token_hash = ?
        """,
        (token_hash,),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if row["revoked_at"] is not None:
        conn.close()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")

    if row["expires_at"] < now_iso:
        conn.close()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    user_id = row["user_id"]
    # Revoke old token
    cursor.execute("UPDATE refresh_tokens SET revoked_at = ? WHERE id = ?", (now_iso, row["id"]))
    conn.commit()
    conn.close()

    new_refresh_token = create_refresh_token(user_id)
    return user_id, new_refresh_token


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_bearer)) -> dict[str, Any]:
    """Dependency that extracts, decodes, and validates the JWT access token from Bearer header."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing subject or role claim",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials / invalid token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, employee_id, email, full_name, role, department, is_active
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated")

    return dict(user)


def get_optional_current_user(credentials: HTTPAuthorizationCredentials | None = Security(security_bearer)) -> dict[str, Any]:
    """Dependency that returns the current user if authenticated, or a default demo employee."""
    if not credentials:
        # Default fallback employee user
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, employee_id, email, full_name, role, department, is_active FROM users WHERE role = 'employee' LIMIT 1")
        user = cursor.fetchone()
        conn.close()
        if user:
            return dict(user)
        return {
            "id": 1,
            "employee_id": "EMP-001",
            "email": "employee@miniblue.dev",
            "full_name": "Alex Mercer (Employee)",
            "role": "employee",
            "department": "Engineering",
            "is_active": 1,
        }

    try:
        return get_current_user(credentials)
    except HTTPException:
        return {
            "id": 1,
            "employee_id": "EMP-001",
            "email": "employee@miniblue.dev",
            "full_name": "Alex Mercer (Employee)",
            "role": "employee",
            "department": "Engineering",
            "is_active": 1,
        }



def require_role(allowed_roles: list[str]) -> Callable:
    """Dependency factory enforcing Role-Based Access Control (RBAC)."""

    def role_checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: user role '{user_role}' is not in permitted roles {allowed_roles}",
            )
        return current_user

    return role_checker
