"""Supabase Client & Synchronization Engine for miniBlue Enterprise Platform.

Synchronizes action ledger, cryptographic receipts, user sessions,
and HITL reviews to Supabase PostgreSQL (Project mtodhmyaikedwojxhsfw).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any
import requests

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mtodhmyaikedwojxhsfw.supabase.co")
SUPABASE_KEY = os.getenv(
    "SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im10b2RobXlhaWtlZHdvanhoc2Z3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ1NjM4NDgsImV4cCI6MjExMDEzOTg0OH0.nqqX6q-ykiaj-zXoyRlMFiRnQ4BkxgkvyXe70-4wQcM",
)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}


def sync_action_log_to_supabase(action: dict[str, Any]) -> bool:
    """Pushes a new action log record to Supabase action_logs table."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/action_logs"
        payload = {
            "id": action.get("id"),
            "entry_type": action.get("entry_type", "action"),
            "ref_action_id": action.get("ref_action_id"),
            "session_id": action.get("session_id"),
            "requester_id": action.get("requester_id", 1),
            "timestamp": action.get("timestamp"),
            "intent": action.get("intent", "policy_question"),
            "action_type": action.get("action_type"),
            "payload_json": action.get("payload_json") if isinstance(action.get("payload_json"), dict) else json.loads(action.get("payload_json", "{}")),
            "decision": action.get("decision", "APPROVE"),
            "reason": action.get("reason", ""),
            "cited_rule": action.get("cited_rule", ""),
            "prev_hash": action.get("prev_hash", "0" * 64),
            "entry_hash": action.get("entry_hash", ""),
            "review_status": action.get("review_status", "none"),
        }
        res = requests.post(url, headers=HEADERS, json=payload, timeout=5)
        return res.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"Supabase action_log sync error: {e}")
        return False


def sync_conversation_log_to_supabase(conv: dict[str, Any]) -> bool:
    """Pushes a conversation turn to Supabase conversation_logs table."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/conversation_logs"
        payload = {
            "session_id": conv.get("session_id"),
            "user_id": conv.get("user_id", 1),
            "timestamp": conv.get("timestamp"),
            "user_message": conv.get("user_message", ""),
            "intent": conv.get("intent", "other"),
            "agent_used": conv.get("agent_used", "Orchestrator"),
            "confidence": float(conv.get("confidence", 1.0)),
            "response": conv.get("response", ""),
            "citations_json": conv.get("citations_json"),
            "fallback_mode": bool(conv.get("fallback_mode", False)),
            "latency_ms": int(conv.get("latency_ms", 0)),
            "action_id": conv.get("action_id"),
        }
        res = requests.post(url, headers=HEADERS, json=payload, timeout=5)
        return res.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"Supabase conversation_log sync error: {e}")
        return False


def sync_review_event_to_supabase(review: dict[str, Any]) -> bool:
    """Pushes a manager resolution event to Supabase review_events table."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/review_events"
        payload = {
            "action_id": review.get("action_id"),
            "reviewer_id": review.get("reviewer_id", 2),
            "previous_decision": review.get("previous_decision", "FLAG_FOR_REVIEW"),
            "resolution": review.get("resolution"),
            "notes": review.get("notes", ""),
            "timestamp": review.get("timestamp"),
            "resolution_hash": review.get("resolution_hash", ""),
        }
        res = requests.post(url, headers=HEADERS, json=payload, timeout=5)
        return res.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"Supabase review_event sync error: {e}")
        return False

