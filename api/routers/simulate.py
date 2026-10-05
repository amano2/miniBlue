"""Policy Counterfactual Simulator Router.

Allows HR leadership to test prospective policy modifications against historical actions
and observe compliance shifts before committing changes to company handbooks.

Endpoints:
- POST /api/v1/simulate (executes simulation against historical actions)
- GET  /api/v1/simulate/runs (lists historical simulation runs)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import get_current_user, require_role
from api.db import get_db_connection, get_latest_chain_hash
from api.schemas import SimulateRequest, SimulateResponse
from src.simulator import simulate_policy_changes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulate", tags=["Policy Simulator"])


@router.post("", response_model=SimulateResponse)
def run_simulation(
    payload: SimulateRequest,
    current_user: dict[str, Any] = Depends(require_role(["admin"])),
) -> SimulateResponse:
    """Executes a what-if policy counterfactual simulation on in-memory copies of historical actions.

    Guarantees RightAction invariant: The live cryptographic hash chain is untouched,
    proven by verifying head hash before and after the run.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pre-simulation head hash
    head_before = get_latest_chain_hash()

    # Fetch historical actions
    cursor.execute(
        """
        SELECT id, timestamp, intent, action_type, payload_json, decision, reason, cited_rule
        FROM action_logs
        WHERE entry_type = 'action'
        ORDER BY id ASC
        """
    )
    rows = cursor.fetchall()
    historical_logs = [dict(r) for r in rows]

    # Run in-memory simulation
    sim_result = simulate_policy_changes(
        historical_logs=historical_logs,
        broadband_cap=payload.broadband_cap,
        ergonomic_cap=payload.ergonomic_cap,
        meal_per_diem_cap=payload.meal_cap,
        hotel_lodging_cap=payload.hotel_cap,
        sick_cert_threshold_days=float(payload.sick_notice_threshold),
    )

    # Post-simulation head hash check
    head_after = get_latest_chain_hash()
    if head_before != head_after:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "CHAIN_MUTATION_ERROR", "message": "Simulation corrupted the live hash chain!"}},
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    params_dict = payload.dict()
    before_dict = sim_result["baseline"]
    after_dict = sim_result["simulated"]
    shifts_list = sim_result["shift_details"]

    # Persist simulation run
    cursor.execute(
        """
        INSERT INTO simulation_runs (
            user_id, params_json, before_json, after_json, shifts_json, chain_head_hash, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            current_user["id"],
            json.dumps(params_dict),
            json.dumps(before_dict),
            json.dumps(after_dict),
            json.dumps(shifts_list),
            head_after,
            now_iso,
        ),
    )
    conn.commit()
    conn.close()

    return SimulateResponse(
        params=params_dict,
        before=before_dict,
        after=after_dict,
        shifts=shifts_list,
        total_evaluated=len(historical_logs),
        chain_head_hash=head_after,
        created_at=now_iso,
    )


@router.get("/runs", response_model=list[dict])
def get_simulation_runs(
    current_user: dict[str, Any] = Depends(require_role(["admin"])),
) -> list[dict]:
    """Retrieves audit trail of past simulation runs."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT sr.id, sr.user_id, u.full_name AS run_by, sr.params_json,
               sr.before_json, sr.after_json, sr.shifts_json, sr.chain_head_hash, sr.created_at
        FROM simulation_runs sr
        JOIN users u ON u.id = sr.user_id
        ORDER BY sr.id DESC
        LIMIT 20
        """
    )
    rows = cursor.fetchall()
    conn.close()

    result: list[dict] = []
    for r in rows:
        result.append(
            {
                "id": r["id"],
                "run_by": r["run_by"],
                "params": json.loads(r["params_json"]),
                "before": json.loads(r["before_json"]),
                "after": json.loads(r["after_json"]),
                "shifts_count": len(json.loads(r["shifts_json"])),
                "chain_head_hash": r["chain_head_hash"],
                "created_at": r["created_at"],
            }
        )

    return result
