"""Human-in-the-Loop (HITL) Manager Review Inbox Router.

Endpoints:
- GET  /api/v1/reviews/pending (queue of flagged actions requiring human judgment)
- POST /api/v1/reviews/resolve (resolve review ticket via cryptographically logged resolution)
"""

from __future__ import annotations

import json
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import get_current_user, require_role
from api.db import get_db_connection, resolve_action_review
from api.schemas import ReviewResolutionRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["HITL Reviews"])


@router.get("/pending", response_model=list[dict])
def get_pending_reviews(
    current_user: dict[str, Any] = Depends(require_role(["manager", "admin"])),
) -> list[dict]:
    """Retrieves all compliance-flagged actions awaiting Manager or HRBP review."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, entry_type, ref_action_id, session_id, requester_id,
               requester_name, requester_email, employee_id,
               timestamp, intent, action_type, payload_json,
               decision, reason, cited_rule, prev_hash, entry_hash, review_status
        FROM v_pending_reviews
        ORDER BY id ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    results: list[dict] = []
    for r in rows:
        payload = {}
        if r["payload_json"]:
            try:
                payload = json.loads(r["payload_json"])
            except Exception:
                payload = {"raw": r["payload_json"]}

        results.append(
            {
                "id": r["id"],
                "requester_id": r["requester_id"],
                "requester_name": r["requester_name"] or "Alex Mercer (Employee)",
                "requester_email": r["requester_email"] or "employee@miniblue.dev",
                "employee_id": r["employee_id"] or "EMP-001",
                "timestamp": r["timestamp"],
                "intent": r["intent"],
                "action_type": r["action_type"],
                "payload": payload,
                "decision": r["decision"],
                "reason": r["reason"],
                "cited_rule": r["cited_rule"],
                "entry_hash": r["entry_hash"],
                "review_status": r["review_status"],
            }
        )

    return results


@router.post("/resolve", response_model=dict)
def resolve_review(
    payload: ReviewResolutionRequest,
    current_user: dict[str, Any] = Depends(require_role(["manager", "admin"])),
) -> dict:
    """Submits a manager resolution (Approve with Exception or Reject/Confirm Block).

    Maintains RightAction tamper-evident invariant: does not mutate historical hashed fields;
    appends a review_resolution hash block and logs an entry in review_events.
    """
    action_id = payload.action_id or payload.log_id
    if not action_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": {"code": "MISSING_ACTION_ID", "message": "action_id is required."}},
        )

    notes = (payload.note or payload.notes or "").strip()
    if not notes:
        notes = f"Resolution approved by {current_user['full_name']} ({current_user['role']})."

    try:
        res = resolve_action_review(
            action_id=action_id,
            reviewer_id=current_user["id"],
            resolution=payload.resolution,
            notes=notes,
        )
        return res
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": str(e)}},
        )
    except Exception as e:
        logger.error(f"Error resolving review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "RESOLUTION_FAILED", "message": str(e)}},
        )
