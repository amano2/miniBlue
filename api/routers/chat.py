"""Chat & Multi-Agent Orchestration Router.

Endpoints:
- POST /api/v1/chat (processes message via orchestrator, agents, and governance layer)
- GET  /api/v1/chat/sessions (list user sessions)
- GET  /api/v1/chat/sessions/{session_id} (get session transcript)
- DELETE /api/v1/chat/sessions/{session_id} (delete session)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import get_current_user, get_optional_current_user
from api.db import get_db_connection
from api.schemas import (
    ActionPayload,
    ChatRequest,
    ChatResponse,
    ChatSessionOut,
    CitationChunk,
    GovernanceResult,
)
from src.pipeline import process_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat & Orchestration"])


@router.post("", response_model=ChatResponse)
def handle_chat(
    payload: ChatRequest,
    current_user: dict = Depends(get_optional_current_user),
) -> ChatResponse:
    """Processes an HR query, leave application, or reimbursement claim.

    Orchestrates:
    1. Intent classification via Gemini / local router
    2. Routing to specialist agent (Leave, Reimbursement, Policy Q&A, Escalation)
    3. RightAction compliance validation & cryptographic hash-chain logging
    4. Multi-turn session memory updates
    """
    user_id = current_user.get("id", 1)  # Default to employee user if unauthenticated
    session_id = payload.session_id or f"sess-{user_id}-{int(time.time())}"
    message = payload.message.strip()

    now_iso = datetime.now(timezone.utc).isoformat()

    # Ensure chat_session exists or update timestamp
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, title FROM chat_sessions WHERE session_id = ?", (session_id,))
    session_row = cursor.fetchone()

    if not session_row:
        title = message[:40] + ("..." if len(message) > 40 else "")
        cursor.execute(
            """
            INSERT INTO chat_sessions (session_id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, title, now_iso, now_iso),
        )
    else:
        cursor.execute("UPDATE chat_sessions SET updated_at = ? WHERE session_id = ?", (now_iso, session_id))
    conn.commit()
    conn.close()

    # Execute agentic pipeline
    res = process_message(message=message, session_id=session_id)

    # Format citations
    citations: list[CitationChunk] = []
    for s in res.get("sources", []):
        citations.append(
            CitationChunk(
                doc_id=s.get("source_file") or s.get("doc_name") or "HR-POLICY",
                section=s.get("source_file"),
                text=s.get("text"),
                score=s.get("score"),
                source_file=s.get("source_file"),
                chunk_id=s.get("chunk_id"),
            )
        )

    # Format action & governance
    action_obj = None
    gov_payload = res.get("governance_payload")
    if res.get("action_taken") or gov_payload:
        act_type = "leave" if "leave" in res.get("intent", "") else ("reimbursement" if "reimbursement" in res.get("intent", "") else "action")
        action_obj = ActionPayload(
            id=res.get("log_id"),
            type=act_type,
            payload=gov_payload if isinstance(gov_payload, dict) else {"details": res.get("action_taken")},
        )

    gov_obj = None
    if res.get("governance_decision"):
        review_status = "pending" if res.get("governance_decision") == "FLAG_FOR_REVIEW" else "none"
        gov_obj = GovernanceResult(
            decision=res.get("governance_decision"),
            reason=res.get("response") if not res.get("action_taken") else res.get("rule_cited", "Policy evaluation completed."),
            cited_rule=res.get("rule_cited"),
            review_status=review_status,
        )

    # Persist into conversation_logs with user_id
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversation_logs (
                session_id, user_id, timestamp, user_message, intent,
                confidence, agent_used, reply, governance_decision,
                action_log_id, latency_ms, fallback_mode, citations_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                now_iso,
                message,
                res.get("intent", "other"),
                res.get("confidence", 1.0),
                res.get("agent_used", "Orchestrator"),
                res.get("response", ""),
                res.get("governance_decision"),
                res.get("log_id"),
                res.get("latency_ms", 0.0),
                0,
                json.dumps([c.dict() for c in citations]),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Error persisting conversation log for user {user_id}: {e}")

    return ChatResponse(
        session_id=session_id,
        message_id=f"msg-{int(time.time() * 1000)}",
        agent=res.get("agent_used", "Orchestrator"),
        intent=res.get("intent", "other"),
        confidence=res.get("confidence", 1.0),
        reply=res.get("response", ""),
        action=action_obj,
        governance=gov_obj,
        citations=citations,
        latency_ms=res.get("latency_ms", 0.0),
        fallback_mode=False,
        refused=res.get("refused", False),
        # Backward compatibility fields
        response=res.get("response", ""),
        agent_used=res.get("agent_used", "Orchestrator"),
        action_taken=res.get("action_taken"),
        governance_decision=res.get("governance_decision"),
        rule_cited=res.get("rule_cited"),
        log_id=res.get("log_id"),
        sources=citations,
    )


@router.get("/sessions", response_model=list[ChatSessionOut])
def get_user_sessions(current_user: dict = Depends(get_current_user)) -> list[ChatSessionOut]:
    """Retrieves all chat sessions for the current authenticated user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT session_id, user_id, title, created_at, updated_at, last_draft_json
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (current_user["id"],),
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        ChatSessionOut(
            session_id=r["session_id"],
            user_id=r["user_id"],
            title=r["title"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            last_draft_json=r["last_draft_json"],
        )
        for r in rows
    ]


@router.get("/sessions/{session_id}")
def get_session_transcript(
    session_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Retrieves full conversation transcript for a given session."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify session access
    cursor.execute("SELECT user_id, title FROM chat_sessions WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()
    if not session:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."}},
        )

    # Role check: employee can only see own; manager/admin/auditor can inspect
    if current_user["role"] == "employee" and session["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Cannot access another user's session."}},
        )

    cursor.execute(
        """
        SELECT id, timestamp, user_message, agent_used, intent, confidence,
               reply, governance_decision, action_log_id, latency_ms, citations_json
        FROM conversation_logs
        WHERE session_id = ?
        ORDER BY timestamp ASC
        """,
        (session_id,),
    )
    messages = cursor.fetchall()
    conn.close()

    turns = []
    for m in messages:
        citations = []
        if m["citations_json"]:
            try:
                citations = json.loads(m["citations_json"])
            except Exception:
                pass

        turns.append(
            {
                "id": m["id"],
                "timestamp": m["timestamp"],
                "user_message": m["user_message"],
                "agent_used": m["agent_used"],
                "intent": m["intent"],
                "confidence": m["confidence"],
                "reply": m["reply"],
                "governance_decision": m["governance_decision"],
                "action_log_id": m["action_log_id"],
                "latency_ms": m["latency_ms"],
                "citations": citations,
            }
        )

    return {"session_id": session_id, "title": session["title"], "messages": turns}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    """Deletes a chat session and associated messages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM chat_sessions WHERE session_id = ?", (session_id,))
    session = cursor.fetchone()
    if not session:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SESSION_NOT_FOUND", "message": "Session not found."}},
        )

    if current_user["role"] == "employee" and session["user_id"] != current_user["id"]:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "FORBIDDEN", "message": "Cannot delete another user's session."}},
        )

    cursor.execute("DELETE FROM conversation_logs WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    return {"deleted": True, "session_id": session_id}
