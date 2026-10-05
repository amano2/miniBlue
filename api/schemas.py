"""Pydantic schemas for miniBlue Enterprise Platform.

Fully type-annotated schemas for authentication, chat, governance actions,
HITL reviews, policy simulator, audit verification, telemetry, and evaluations.
Supports both the strict v1 specification and backward compatibility fields.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Auth Schemas
# -----------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email (e.g. employee@miniblue.dev)")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes in seconds
    role: str
    full_name: str
    email: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    employee_id: str
    email: str
    full_name: str
    role: str
    department: str | None = None
    is_active: bool = True
    last_login_at: str | None = None


# -----------------------------------------------------------------------------
# Chat & Observability Schemas
# -----------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str = Field(
        default="default-session",
        description="Session identifier for multi-turn conversation and context repair.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Employee request, question, or reimbursement claim.",
    )


class ChatSessionOut(BaseModel):
    session_id: str
    user_id: int
    title: str | None = None
    created_at: str
    updated_at: str
    last_draft_json: str | None = None


class CitationChunk(BaseModel):
    doc_id: str | None = None
    section: str | None = None
    text: str | None = None
    score: float | None = None
    source_file: str | None = None
    chunk_id: int | None = None


class ActionPayload(BaseModel):
    id: int | None = None
    type: str | None = None
    payload: dict[str, Any] | None = None


class GovernanceResult(BaseModel):
    decision: str | None = None
    reason: str | None = None
    cited_rule: str | None = None
    review_status: str | None = "none"


class ChatResponse(BaseModel):
    session_id: str
    message_id: str | None = None
    agent: str = Field(..., description="Specialist agent that processed the turn.")
    intent: str
    confidence: float
    reply: str
    action: ActionPayload | None = None
    governance: GovernanceResult | None = None
    citations: list[CitationChunk] = []
    latency_ms: float = 0.0
    fallback_mode: bool = False
    refused: bool = False

    # Backward-compatible fields
    response: str | None = None
    agent_used: str | None = None
    action_taken: str | None = None
    governance_decision: str | None = None
    rule_cited: str | None = None
    log_id: int | None = None
    sources: list[CitationChunk] = []


# -----------------------------------------------------------------------------
# Actions & Review Schemas
# -----------------------------------------------------------------------------

class ActionLogOut(BaseModel):
    id: int
    entry_type: str = "action"
    ref_action_id: int | None = None
    session_id: str | None = None
    requester_id: int | None = None
    requester_name: str | None = None
    employee_id: str | None = None
    timestamp: str
    intent: str
    action_type: str | None = None
    payload: dict[str, Any]
    decision: str
    reason: str
    cited_rule: str
    prev_hash: str
    entry_hash: str
    review_status: str = "none"
    citations: list[CitationChunk] = []


class ReviewResolutionRequest(BaseModel):
    action_id: int | None = None
    log_id: int | None = None  # backward-compat alias
    resolution: str = Field(
        ...,
        description="'APPROVE', 'APPROVE_WITH_EXCEPTION', 'BLOCK', or 'REJECT_CONFIRMED'",
    )
    note: str | None = None
    notes: str | None = None  # backward-compat alias
    manager_id: str | None = None


class ReviewEventOut(BaseModel):
    id: int
    action_log_id: int
    reviewer_id: int
    reviewer_name: str | None = None
    action: str
    notes: str | None = None
    created_at: str


# -----------------------------------------------------------------------------
# Policy Simulator Schemas
# -----------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    broadband_cap: float = Field(75.0, description="Monthly broadband cap in USD")
    ergonomic_cap: float = Field(300.0, description="Ergonomic equipment annual cap in USD")
    meal_cap: float = Field(30.0, description="Daily meal cap in USD")
    hotel_cap: float = Field(200.0, description="Nightly hotel cap in USD")
    sick_notice_threshold: int = Field(3, description="Days of sick leave before medical cert required")


class ShiftDetail(BaseModel):
    action_id: int
    action_type: str | None = None
    original_decision: str
    simulated_decision: str
    rule_applied: str
    description: str | None = None


class SimulateResponse(BaseModel):
    params: dict[str, Any]
    before: dict[str, int]
    after: dict[str, int]
    shifts: list[dict[str, Any]]
    total_evaluated: int
    chain_head_hash: str
    created_at: str


# -----------------------------------------------------------------------------
# Cryptographic Audit Schemas
# -----------------------------------------------------------------------------

class AuditVerifyResponse(BaseModel):
    valid: bool
    entries: int
    first_broken_id: int | None = None
    message: str
    head_hash: str | None = None


# -----------------------------------------------------------------------------
# Telemetry Schemas
# -----------------------------------------------------------------------------

class TelemetryResponse(BaseModel):
    total_actions: int
    total_reviews_pending: int
    approved_count: int
    flagged_count: int
    blocked_count: int
    approved_rate: float
    flagged_rate: float
    blocked_rate: float
    avg_latency_ms: float
    intent_distribution: dict[str, int]
    daily_trend: list[dict[str, Any]]


# -----------------------------------------------------------------------------
# Policy Documents Schemas
# -----------------------------------------------------------------------------

class PolicyDocOut(BaseModel):
    doc_id: str
    title: str
    filename: str
    version: str
    chunk_count: int
    content: str | None = None


class PolicyChunkOut(BaseModel):
    id: int
    chunk_id: int
    doc_id: str
    section: str | None = None
    text: str


# -----------------------------------------------------------------------------
# Eval Schemas
# -----------------------------------------------------------------------------

class EvalRunResponse(BaseModel):
    id: int
    metrics: dict[str, Any]
    passed: bool
    git_sha: str | None = None
    created_at: str
