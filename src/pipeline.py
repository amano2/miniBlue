"""Master Enterprise Agentic Orchestration Pipeline.

Orchestrates intent classification, routes to specialist agents (Policy Q&A, Leave Request,
Reimbursement Claim), enforces RightAction Governance, updates session memory with action repair states,
and logs all telemetry with latency tracking and SHA-256 hash chaining.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from src.db import log_conversation_turn
from src.memory import memory_store
from src.orchestrator import classify_intent
from src.agents.policy_qa_agent import handle_policy_qa
from src.agents.leave_agent import handle_leave_request
from src.agents.reimbursement_agent import handle_reimbursement_claim

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

HUMAN_ESCALATION_MESSAGE = """🛡️ **ROUTED TO HUMAN HR SUPPORT**

This request or situation requires direct human judgment, policy exception handling, or confidential assistance.

- **Status:** Escalated to People Operations Team
- **Contact:** `hr-operations@enterprise.org` or your dedicated HR Business Partner (HRBP)
- **Ticket Created:** Reference #HR-ESC-"""


def process_message(message: str, session_id: str = "default") -> dict[str, Any]:
    """Master entry point: orchestrates classification, routing, governance, and session logging.

    Args:
        message: Employee input message.
        session_id: Session identifier for tracking conversation context.

    Returns:
        Structured response dictionary with rich observability telemetry.
    """
    start_time = time.perf_counter()
    clean_msg = message.strip()

    if not clean_msg:
        return {
            "response": "Please enter a valid message or question.",
            "agent_used": "Orchestrator",
            "intent": "other",
            "confidence": 1.0,
            "action_taken": None,
            "governance_decision": None,
            "sources": [],
            "refused": True,
            "latency_ms": 0.0,
            "log_id": None,
            "rule_cited": None,
        }

    # Step 1: Orchestrator Intent Classification
    intent_result = classify_intent(clean_msg)
    intent = intent_result.get("intent", "policy_question")
    confidence = float(intent_result.get("confidence", 0.8))

    logger.info(f"Orchestrator classified message as '{intent}' (Confidence: {confidence:.2f})")

    # Step 2: Route to Specialist Agent based on Intent
    if intent == "leave_request":
        agent_used = "Leave Request Agent"
        agent_output = handle_leave_request(clean_msg, session_id=session_id)

    elif intent == "reimbursement_claim":
        agent_used = "Reimbursement Claim Agent"
        agent_output = handle_reimbursement_claim(clean_msg, session_id=session_id)

    elif intent == "policy_question":
        agent_used = "Policy Q&A Agent"
        agent_output = handle_policy_qa(clean_msg, session_id=session_id)

    elif intent == "escalation":
        agent_used = "Human Escalation Router"
        ticket_num = abs(hash(clean_msg + session_id)) % 100000
        agent_output = {
            "response": f"{HUMAN_ESCALATION_MESSAGE}{ticket_num:05d}\n\n*A representative will follow up with you within 1 business day.*",
            "sources": [],
            "refused": False,
            "action_taken": f"Created HR Escalation Ticket #HR-ESC-{ticket_num:05d}",
            "governance_decision": "ESCALATED",
            "log_id": None,
            "rule_cited": "HR-ESC-001 (Human Exception Protocol)",
        }

    else:  # other
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "who are you", "help"]
        is_greeting = any(g in clean_msg.lower() for g in greetings) and len(clean_msg.split()) <= 4
        if is_greeting:
            agent_used = "General HR Assistant"
            agent_output = {
                "response": "Hello! I am the Enterprise HR Assistant. You can ask me questions about leave policies, expense reimbursements, onboarding, or submit leave requests and expense claims directly.",
                "sources": [],
                "refused": False,
                "action_taken": None,
                "governance_decision": None,
                "log_id": None,
                "rule_cited": None,
            }
        else:
            agent_used = "Policy Q&A Agent"
            from src.generate import REFUSAL_RESPONSE
            agent_output = {
                "response": REFUSAL_RESPONSE,
                "sources": [],
                "refused": True,
                "action_taken": None,
                "governance_decision": None,
                "log_id": None,
                "rule_cited": None,
            }

    latency_ms = round((time.perf_counter() - start_time) * 1000, 1)

    final_response = agent_output.get("response", "")
    action_taken = agent_output.get("action_taken")
    governance_decision = agent_output.get("governance_decision")
    sources = agent_output.get("sources", [])
    refused = agent_output.get("refused", False)
    log_id = agent_output.get("log_id")
    rule_cited = agent_output.get("rule_cited")
    gov_payload = agent_output.get("governance_payload")

    # Step 3: Update Session Memory with Context for Multi-Turn Repair
    memory_store.add_turn(
        session_id=session_id,
        user_message=clean_msg,
        assistant_response=final_response,
        agent_used=agent_used,
        governance_decision=governance_decision,
        action_payload=gov_payload,
    )

    # Step 4: Persist Conversation Turn into SQLite with Latency Telemetry
    try:
        log_conversation_turn(
            session_id=session_id,
            user_message=clean_msg,
            agent_used=agent_used,
            intent=intent,
            confidence=confidence,
            response_text=final_response,
            governance_decision=governance_decision,
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.error(f"Failed to log conversation turn to SQLite: {e}")

    return {
        "response": final_response,
        "agent_used": agent_used,
        "intent": intent,
        "confidence": confidence,
        "action_taken": action_taken,
        "governance_decision": governance_decision,
        "sources": sources,
        "refused": refused,
        "latency_ms": latency_ms,
        "log_id": log_id,
        "rule_cited": rule_cited,
        "governance_payload": gov_payload,
    }


# Backwards compatibility helper
def answer_query(query: str, session_id: str = "default", **kwargs) -> dict[str, Any]:
    """Compatibility wrapper for evaluation runner and legacy callers."""
    result = process_message(query, session_id=session_id)
    return {
        "answer": result["response"],
        "sources": result["sources"],
        "refused": result["refused"],
        "agent_used": result["agent_used"],
        "intent": result["intent"],
        "governance_decision": result["governance_decision"],
    }
