"""Action Logs & Governance Ledger Router.

Endpoints:
- GET /api/v1/actions (lists actions with RBAC: employee sees own, manager/admin/auditor sees all)
- GET /api/v1/actions/{id} (detailed governance receipt with cryptographic proof)
"""

from __future__ import annotations

import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.auth import get_current_user
from api.db import get_db_connection
from api.schemas import ActionLogOut, CitationChunk, ReviewEventOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actions", tags=["Governance Actions"])


@router.get("", response_model=list[ActionLogOut])
def list_actions(
    decision: str | None = Query(None, description="Filter by governance decision: APPROVE, FLAG_FOR_REVIEW, BLOCK"),
    action_type: str | None = Query(None, description="Filter by action type: leave, reimbursement"),
    review_status: str | None = Query(None, description="Filter by review status: pending, approved_exception, rejected"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[ActionLogOut]:
    """Retrieves governed actions with strict RBAC:

    - Employees see only their own submitted requests.
    - Managers, Admins, and Auditors can inspect the organization-wide ledger.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT a.id, a.entry_type, a.ref_action_id, a.session_id, a.requester_id,
               u.full_name AS requester_name, u.employee_id,
               a.timestamp, a.intent, a.action_type, a.payload_json,
               a.decision, a.reason, a.cited_rule, a.prev_hash, a.entry_hash, a.review_status
        FROM action_logs a
        LEFT JOIN users u ON u.id = a.requester_id
        WHERE 1=1
    """
    params: list[Any] = []

    # RBAC filter: Employees only see their own requests
    if current_user["role"] == "employee":
        query += " AND (a.requester_id = ? OR a.requester_id IS NULL)"
        params.append(current_user["id"])

    if decision:
        query += " AND a.decision = ?"
        params.append(decision.upper())

    if action_type:
        query += " AND a.action_type = ?"
        params.append(action_type.lower())

    if review_status:
        query += " AND a.review_status = ?"
        params.append(review_status.lower())

    query += " ORDER BY a.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results: list[ActionLogOut] = []
    for r in rows:
        payload = {}
        if r["payload_json"]:
            try:
                payload = json.loads(r["payload_json"])
            except Exception:
                payload = {"raw": r["payload_json"]}

        results.append(
            ActionLogOut(
                id=r["id"],
                entry_type=r["entry_type"],
                ref_action_id=r["ref_action_id"],
                session_id=r["session_id"],
                requester_id=r["requester_id"],
                requester_name=r["requester_name"] or "Alex Mercer (Employee)",
                employee_id=r["employee_id"] or "EMP-001",
                timestamp=r["timestamp"],
                intent=r["intent"],
                action_type=r["action_type"],
                payload=payload,
                decision=r["decision"],
                reason=r["reason"],
                cited_rule=r["cited_rule"],
                prev_hash=r["prev_hash"],
                entry_hash=r["entry_hash"],
                review_status=r["review_status"],
            )
        )

    return results


@router.get("/{action_id}", response_model=dict)
def get_action_detail(
    action_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Retrieves full details of a specific governed action, including hash proof and review history."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT a.id, a.entry_type, a.ref_action_id, a.session_id, a.requester_id,
               u.full_name AS requester_name, u.employee_id, u.email AS requester_email,
               a.timestamp, a.intent, a.action_type, a.payload_json,
               a.decision, a.reason, a.cited_rule, a.prev_hash, a.entry_hash, a.review_status
        FROM action_logs a
        LEFT JOIN users u ON u.id = a.requester_id
        WHERE a.id = ?
        """,
        (action_id,),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ACTION_NOT_FOUND", "message": f"Action #{action_id} not found."}},
        )

    # RBAC check: Employee cannot access other users' actions
    if current_user["role"] == "employee" and row["requester_id"] and row["requester_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Cannot inspect another employee's action."}},
        )

    # Get review events for this action
    cursor.execute(
        """
        SELECT re.id, re.action_log_id, re.reviewer_id, u.full_name AS reviewer_name,
               re.action, re.notes, re.created_at
        FROM review_events re
        JOIN users u ON u.id = re.reviewer_id
        WHERE re.action_log_id = ?
        ORDER BY re.created_at ASC
        """,
        (action_id,),
    )
    review_events = [
        {
            "id": re["id"],
            "action_log_id": re["action_log_id"],
            "reviewer_id": re["reviewer_id"],
            "reviewer_name": re["reviewer_name"],
            "action": re["action"],
            "notes": re["notes"],
            "created_at": re["created_at"],
        }
        for re in cursor.fetchall()
    ]

    conn.close()

    payload = {}
    if row["payload_json"]:
        try:
            payload = json.loads(row["payload_json"])
        except Exception:
            payload = {"raw": row["payload_json"]}

    return {
        "action": {
            "id": row["id"],
            "entry_type": row["entry_type"],
            "ref_action_id": row["ref_action_id"],
            "session_id": row["session_id"],
            "requester_id": row["requester_id"],
            "requester_name": row["requester_name"],
            "employee_id": row["employee_id"],
            "requester_email": row["requester_email"],
            "timestamp": row["timestamp"],
            "intent": row["intent"],
            "action_type": row["action_type"],
            "payload": payload,
            "decision": row["decision"],
            "reason": row["reason"],
            "cited_rule": row["cited_rule"],
            "prev_hash": row["prev_hash"],
            "entry_hash": row["entry_hash"],
            "review_status": row["review_status"],
        },
        "review_events": review_events,
    }
