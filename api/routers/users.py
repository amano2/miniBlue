"""User Administration Router.

Endpoints:
- GET   /api/v1/users (list enterprise users)
- POST  /api/v1/users (create new user)
- PATCH /api/v1/users/{user_id} (update role, active status, department)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth import hash_password, require_role
from api.db import get_db_connection
from api.schemas import UserOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Administration"])


class CreateUserRequest(BaseModel):
    employee_id: str
    email: str
    full_name: str
    password: str = Field(..., min_length=6)
    role: str = Field("employee", description="employee | manager | admin | auditor")
    department: str | None = None


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    role: str | None = None
    department: str | None = None
    is_active: bool | None = None


@router.get("", response_model=list[UserOut])
def list_users(
    current_user: dict[str, Any] = Depends(require_role(["admin", "auditor"])),
) -> list[UserOut]:
    """Lists all enterprise employees and their assigned governance roles."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, employee_id, email, full_name, role, department, is_active, last_login_at
        FROM users
        ORDER BY id ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        UserOut(
            id=r["id"],
            employee_id=r["employee_id"],
            email=r["email"],
            full_name=r["full_name"],
            role=r["role"],
            department=r["department"],
            is_active=bool(r["is_active"]),
            last_login_at=r["last_login_at"],
        )
        for r in rows
    ]


@router.post("", response_model=UserOut)
def create_user(
    payload: CreateUserRequest,
    current_user: dict[str, Any] = Depends(require_role(["admin"])),
) -> UserOut:
    """Provisions a new employee account with RBAC assignment."""
    now_iso = datetime.now(timezone.utc).isoformat()
    hashed = hash_password(payload.password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (employee_id, email, full_name, password_hash, role, department, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (payload.employee_id, payload.email.lower().strip(), payload.full_name, hashed, payload.role, payload.department, now_iso),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return UserOut(
            id=user_id,
            employee_id=payload.employee_id,
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role,
            department=payload.department,
            is_active=True,
        )
    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "USER_CREATION_FAILED", "message": f"Email or employee_id already exists: {e}"}},
        )


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UpdateUserRequest,
    current_user: dict[str, Any] = Depends(require_role(["admin"])),
) -> UserOut:
    """Updates an employee's role, department, or active status."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, employee_id, email, full_name, role, department, is_active, last_login_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "USER_NOT_FOUND", "message": f"User #{user_id} not found."}},
        )

    updates = []
    params = []
    if payload.full_name is not None:
        updates.append("full_name = ?")
        params.append(payload.full_name)
    if payload.role is not None:
        updates.append("role = ?")
        params.append(payload.role)
    if payload.department is not None:
        updates.append("department = ?")
        params.append(payload.department)
    if payload.is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if payload.is_active else 0)

    if updates:
        params.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    cursor.execute("SELECT id, employee_id, email, full_name, role, department, is_active, last_login_at FROM users WHERE id = ?", (user_id,))
    updated = cursor.fetchone()
    conn.close()

    return UserOut(
        id=updated["id"],
        employee_id=updated["employee_id"],
        email=updated["email"],
        full_name=updated["full_name"],
        role=updated["role"],
        department=updated["department"],
        is_active=bool(updated["is_active"]),
        last_login_at=updated["last_login_at"],
    )
