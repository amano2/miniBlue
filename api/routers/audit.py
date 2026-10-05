"""Cryptographic Audit & Tamper-Evident Ledger Router.

Endpoints:
- GET /api/v1/audit/verify (runs mathematical SHA-256 verification of the entire ledger)
- GET /api/v1/audit/export.csv (exports signed immutable audit ledger package)
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Any
from fastapi import APIRouter, Depends, Response, status

from api.auth import get_current_user, require_role
from api.db import get_db_connection, verify_entire_hash_chain
from api.schemas import AuditVerifyResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["Cryptographic Audit"])


@router.get("/verify", response_model=AuditVerifyResponse)
def verify_audit_ledger(
    current_user: dict[str, Any] = Depends(require_role(["admin", "auditor"])),
) -> AuditVerifyResponse:
    """Performs an end-to-end cryptographic hash verification across the entire action_logs chain.

    Recomputes SHA256(prev_hash | canonical_payload | decision | timestamp) for every block from genesis.
    Returns status, block count, and any broken link ID if tampering occurred.
    """
    res = verify_entire_hash_chain()
    return AuditVerifyResponse(
        valid=res["valid"],
        entries=res["entries"],
        first_broken_id=res.get("first_broken_id"),
        message=res["message"],
        head_hash=res.get("head_hash"),
    )


@router.get("/export.csv")
def export_audit_csv(
    current_user: dict[str, Any] = Depends(require_role(["admin", "auditor"])),
) -> Response:
    """Exports the complete immutable audit ledger in CSV format for third-party auditing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.id, a.entry_type, a.ref_action_id, a.timestamp, a.intent, a.action_type,
               a.payload_json, a.decision, a.reason, a.cited_rule, a.prev_hash, a.entry_hash,
               a.review_status, a.requester_id, u.full_name AS requester_name, u.employee_id
        FROM action_logs a
        LEFT JOIN users u ON u.id = a.requester_id
        ORDER BY a.id ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "entry_type",
            "ref_action_id",
            "timestamp",
            "employee_id",
            "requester_name",
            "intent",
            "action_type",
            "decision",
            "reason",
            "cited_rule",
            "prev_hash",
            "entry_hash",
            "review_status",
            "payload_json",
        ]
    )

    for r in rows:
        writer.writerow(
            [
                r["id"],
                r["entry_type"],
                r["ref_action_id"] or "",
                r["timestamp"],
                r["employee_id"] or "",
                r["requester_name"] or "",
                r["intent"],
                r["action_type"] or "",
                r["decision"],
                r["reason"],
                r["cited_rule"],
                r["prev_hash"],
                r["entry_hash"],
                r["review_status"],
                r["payload_json"],
            ]
        )

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="miniblue_cryptographic_audit_ledger.csv"'},
    )
