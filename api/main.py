"""FastAPI REST API layer for Enterprise Agentic HR Assistant & RightAction Governance.

Exposes `/chat`, `/actions`, `/reviews/pending`, `/reviews/resolve`, `/simulate`,
`/audit/verify`, and `/telemetry` endpoints.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from src.db import (
    get_all_action_logs,
    get_pending_reviews,
    resolve_review,
    verify_audit_hash_chain,
    get_telemetry_metrics,
)
from src.pipeline import process_message
from src.simulator import simulate_policy_changes

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BlueVerse Inspired | Enterprise Agentic HR & RightAction Governance API",
    description="Multi-agent orchestration, RightAction compliance gates, HITL manager queue, and tamper-evident auditing.",
    version="2.5.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Schema for chat requests."""

    session_id: str = Field(
        default="default-session",
        description="Unique session identifier for multi-turn conversational memory and repair.",
        example="session-emp-101",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="The employee message, question, leave request, or reimbursement claim.",
        example="I would like to apply for 3 days of annual leave starting next Monday.",
    )


class SourceChunk(BaseModel):
    """Schema for a retrieved source document chunk."""

    chunk_id: int | None = None
    doc_name: str | None = None
    source_file: str | None = None
    text: str | None = None
    score: float | None = None


class ChatResponse(BaseModel):
    """Schema for chat response payload with deep observability telemetry."""

    response: str
    agent_used: str
    intent: str
    confidence: float
    action_taken: str | None = None
    governance_decision: str | None = None
    rule_cited: str | None = None
    log_id: int | None = None
    latency_ms: float = 0.0
    sources: list[SourceChunk] = []
    refused: bool = False


class ReviewResolutionRequest(BaseModel):
    """Schema for manager HITL ticket resolution."""

    log_id: int
    manager_id: str = "HR-MGR-ADMIN"
    resolution: str = Field(..., description="'APPROVE' or 'BLOCK'")
    notes: str = Field(..., min_length=3, description="Manager review justification notes.")


class SimulationRequest(BaseModel):
    """Schema for What-If Policy Simulation."""

    broadband_cap: float = 50.0
    ergonomic_cap: float = 300.0
    meal_per_diem_cap: float = 75.0
    hotel_lodging_cap: float = 180.0
    sick_cert_threshold_days: float = 3.0
    max_submission_days: int = 60


@app.get("/health", tags=["System"])
def health_check() -> dict[str, Any]:
    """Health check endpoint verifying system readiness and index loading."""
    index_exists = config.INDEX_PATH.exists()
    return {
        "status": "healthy" if index_exists else "index_missing",
        "vector_index_loaded": index_exists,
        "model": config.OPENROUTER_MODEL,
        "architecture": "Enterprise Multi-Agent Orchestrator with RightAction Governance & HITL Queue",
    }


@app.post("/chat", response_model=ChatResponse, tags=["Agentic Assistant"])
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Processes user input through Orchestrator -> Specialist Agent -> RightAction Governance."""
    try:
        result = process_message(
            message=payload.message,
            session_id=payload.session_id,
        )

        formatted_sources = [
            SourceChunk(
                chunk_id=s.get("chunk_id"),
                doc_name=s.get("doc_name"),
                source_file=s.get("source_file"),
                text=s.get("text"),
                score=s.get("score"),
            )
            for s in result.get("sources", [])
        ]

        return ChatResponse(
            response=result["response"],
            agent_used=result["agent_used"],
            intent=result["intent"],
            confidence=result["confidence"],
            action_taken=result["action_taken"],
            governance_decision=result["governance_decision"],
            rule_cited=result.get("rule_cited"),
            log_id=result.get("log_id"),
            latency_ms=result.get("latency_ms", 0.0),
            sources=formatted_sources,
            refused=result.get("refused", False),
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Assistant processing failed: {str(e)}")


@app.get("/actions", tags=["Governance Audit"])
def get_action_audit_logs(limit: int = 50) -> list[dict[str, Any]]:
    """Returns persistent SQLite governance action audit logs."""
    return get_all_action_logs(limit=limit)


@app.get("/reviews/pending", tags=["Human-in-the-Loop"])
def get_pending_manager_reviews() -> list[dict[str, Any]]:
    """Returns all action items currently awaiting human manager review."""
    return get_pending_reviews()


@app.post("/reviews/resolve", tags=["Human-in-the-Loop"])
def resolve_manager_review(payload: ReviewResolutionRequest) -> dict[str, Any]:
    """Resolves a pending review ticket with managerial decision and audit justification."""
    success = resolve_review(
        log_id=payload.log_id,
        manager_id=payload.manager_id,
        resolution=payload.resolution,
        review_notes=payload.notes,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Review log record not found or already resolved.")
    return {"status": "success", "log_id": payload.log_id, "resolution": payload.resolution}


@app.post("/simulate", tags=["Policy Simulation"])
def run_policy_simulation(payload: SimulationRequest) -> dict[str, Any]:
    """Runs a What-If policy simulation over historical action logs."""
    return simulate_policy_changes(
        broadband_cap=payload.broadband_cap,
        ergonomic_cap=payload.ergonomic_cap,
        meal_per_diem_cap=payload.meal_per_diem_cap,
        hotel_lodging_cap=payload.hotel_lodging_cap,
        sick_cert_threshold_days=payload.sick_cert_threshold_days,
        max_submission_days=payload.max_submission_days,
    )


@app.get("/audit/verify", tags=["Cryptographic Verification"])
def verify_audit_trail() -> dict[str, Any]:
    """Cryptographically verifies the SHA-256 hash chain of the audit database."""
    return verify_audit_hash_chain()


@app.get("/telemetry", tags=["Observability"])
def get_system_telemetry() -> dict[str, Any]:
    """Returns live aggregated telemetry metrics."""
    return get_telemetry_metrics()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
