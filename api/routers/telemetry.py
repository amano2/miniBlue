"""Observability & Telemetry Router.

Exposes executive KPI metrics, daily trend series, compliance rates,
and multi-agent latency analytics.

Endpoints:
- GET /api/v1/telemetry
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, Depends

from api.auth import require_role
from api.db import get_db_connection
from api.schemas import TelemetryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telemetry", tags=["Observability & Telemetry"])


@router.get("", response_model=TelemetryResponse)
def get_telemetry(
    current_user: dict[str, Any] = Depends(require_role(["manager", "admin", "auditor"])),
) -> TelemetryResponse:
    """Retrieves high-level RightAction governance metrics, compliance rates, and system trends."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total action logs
    cursor.execute("SELECT COUNT(*) FROM action_logs WHERE entry_type = 'action'")
    total_actions = cursor.fetchone()[0] or 0

    # Decision breakdown
    cursor.execute(
        """
        SELECT decision, COUNT(*) as c
        FROM action_logs
        WHERE entry_type = 'action'
        GROUP BY decision
        """
    )
    decision_rows = dict(cursor.fetchall())
    approved_count = decision_rows.get("APPROVE", 0) + decision_rows.get("APPROVE_WITH_EXCEPTION", 0)
    flagged_count = decision_rows.get("FLAG_FOR_REVIEW", 0)
    blocked_count = decision_rows.get("BLOCK", 0) + decision_rows.get("REJECT_CONFIRMED", 0)

    # Pending reviews count
    cursor.execute("SELECT COUNT(*) FROM v_pending_reviews")
    total_reviews_pending = cursor.fetchone()[0] or 0

    # Rates
    approved_rate = round((approved_count / total_actions * 100), 1) if total_actions > 0 else 0.0
    flagged_rate = round((flagged_count / total_actions * 100), 1) if total_actions > 0 else 0.0
    blocked_rate = round((blocked_count / total_actions * 100), 1) if total_actions > 0 else 0.0

    # Average latency
    cursor.execute("SELECT AVG(latency_ms) FROM conversation_logs")
    avg_lat_val = cursor.fetchone()[0]
    avg_latency_ms = round(avg_lat_val, 1) if avg_lat_val is not None else 320.0

    # Intent distribution
    cursor.execute(
        """
        SELECT intent, COUNT(*) as c
        FROM action_logs
        WHERE entry_type = 'action'
        GROUP BY intent
        """
    )
    intent_distribution = dict(cursor.fetchall())

    # Daily trend from view
    cursor.execute(
        """
        SELECT day, intent, decision, count
        FROM v_telemetry_daily
        ORDER BY day ASC
        LIMIT 60
        """
    )
    daily_trend = [
        {"day": r["day"], "intent": r["intent"], "decision": r["decision"], "count": r["count"]}
        for r in cursor.fetchall()
    ]

    conn.close()

    return TelemetryResponse(
        total_actions=total_actions,
        total_reviews_pending=total_reviews_pending,
        approved_count=approved_count,
        flagged_count=flagged_count,
        blocked_count=blocked_count,
        approved_rate=approved_rate,
        flagged_rate=flagged_rate,
        blocked_rate=blocked_rate,
        avg_latency_ms=avg_latency_ms,
        intent_distribution=intent_distribution,
        daily_trend=daily_trend,
    )
