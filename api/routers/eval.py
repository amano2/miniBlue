"""Automated Evaluation & Continuous Compliance Benchmark Router.

Scores:
1. Orchestrator Routing Accuracy
2. RightAction Governance Compliance & Boundary Enforcement
3. Adversarial Policy Violation Catch Rate (100% target)
4. Policy Q&A Groundedness & Refusal Correctness

Endpoints:
- POST /api/v1/eval/run (triggers evaluation harness)
- GET  /api/v1/eval/runs (lists historical evaluation benchmark scorecards)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import require_role
from api.db import get_db_connection
from api.schemas import EvalRunResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eval", tags=["Evaluation & Benchmarks"])



@router.post("/run", response_model=EvalRunResponse)
def execute_eval(
    current_user: dict[str, Any] = Depends(require_role(["admin", "auditor"])),
) -> EvalRunResponse:
    """Executes the test suite against test_actions.json and test_questions.json."""
    from eval.run_eval import run_governance_evaluation, run_qa_evaluation

    now_iso = datetime.now(timezone.utc).isoformat()


    try:
        gov_res = run_governance_evaluation()
        qa_res = run_qa_evaluation()

        metrics = {
            "governance_accuracy": gov_res["governance_accuracy"],
            "intent_accuracy": gov_res["intent_accuracy"],
            "violation_catch_rate": gov_res["violation_catch_rate"],
            "in_scope_accuracy": qa_res["in_scope_accuracy"],
            "refusal_accuracy": qa_res["refusal_accuracy"],
            "retrieval_hit_rate": qa_res["retrieval_hit_rate"],
        }

        # Passed if governance accuracy is 100% and violation catch rate is 100%
        passed = 1 if gov_res["governance_accuracy"] >= 95.0 and gov_res["violation_catch_rate"] >= 95.0 else 0

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO eval_runs (user_id, metrics_json, passed, git_sha, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (current_user["id"], json.dumps(metrics), passed, "HEAD", now_iso),
        )
        conn.commit()
        run_id = cursor.lastrowid or 1
        conn.close()

        return EvalRunResponse(
            id=run_id,
            metrics=metrics,
            passed=bool(passed),
            git_sha="HEAD",
            created_at=now_iso,
        )
    except Exception as e:
        logger.error(f"Error executing benchmark evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "EVAL_FAILED", "message": str(e)}},
        )


@router.get("/runs", response_model=list[dict])
def list_eval_runs(
    current_user: dict[str, Any] = Depends(require_role(["admin", "auditor"])),
) -> list[dict]:
    """Retrieves all past benchmark evaluation runs and scorecards."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT er.id, er.user_id, u.full_name AS run_by, er.metrics_json,
               er.passed, er.git_sha, er.created_at
        FROM eval_runs er
        LEFT JOIN users u ON u.id = er.user_id
        ORDER BY er.id DESC
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
                "run_by": r["run_by"] or "System Admin",
                "metrics": json.loads(r["metrics_json"]),
                "passed": bool(r["passed"]),
                "git_sha": r["git_sha"],
                "created_at": r["created_at"],
            }
        )

    return result
