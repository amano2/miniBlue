"""Leave Request Specialist Agent.

Extracts structured leave request parameters from natural language, retrieves relevant leave
policy constraints via RAG, and passes the proposed action through the RightAction Governance Layer.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from src.retrieve import retrieve_relevant_chunks
from src.generate import get_llm_client
from src.governance import evaluate_governance

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

LEAVE_EXTRACTION_PROMPT = """You are an HR Leave Request parser. Extract structured fields from the employee's message.
Respond ONLY in JSON with the following structure:
{{
  "leave_type": "Annual Leave | Sick Leave | Maternity Leave | Paternity Leave | Bereavement Leave | Comp-off | Unspecified",
  "days": <float number of days requested, e.g. 1.0, 3.0, 5.0>,
  "start_date": "<start date string or null>",
  "end_date": "<end date string or null>",
  "notice_given": "<e.g. 'none', 'same day', '2 days', '2 weeks', 'unknown'>",
  "has_medical_certificate": <true | false | null>,
  "reason": "<short summary of reason or null>"
}}

User Message: "{user_message}"
"""


def extract_leave_fields(message: str) -> dict[str, Any]:
    """Extracts structured leave fields from user text."""
    # Robust rule-based extractor
    clean_msg = message.lower()
    days_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:consecutive\s*)?(?:business\s*|calendar\s*|working\s*)?(?:day|days)", clean_msg)
    extracted_days = float(days_match.group(1)) if days_match else 1.0

    leave_type = "Annual Leave"
    if "sick" in clean_msg:
        leave_type = "Sick Leave"
    elif "maternity" in clean_msg:
        leave_type = "Maternity Leave"
    elif "paternity" in clean_msg:
        leave_type = "Paternity Leave"
    elif "bereavement" in clean_msg:
        leave_type = "Bereavement Leave"
    elif "comp" in clean_msg:
        leave_type = "Comp-off"

    has_cert = False
    if any(w in clean_msg for w in ["no cert", "no doctor", "do not have", "without doctor", "without cert", "without a"]):
        has_cert = False
    elif "certificate" in clean_msg or "doctor's note" in clean_msg:
        has_cert = True

    notice = "unknown"
    if "week" in clean_msg:
        notice = "2+ weeks"
    elif "today" in clean_msg or "tomorrow" in clean_msg or "same day" in clean_msg or "no notice" in clean_msg:
        notice = "same day"

    heuristic_dict = {
        "leave_type": leave_type,
        "days": extracted_days,
        "start_date": "Extracted from text",
        "end_date": "Extracted from text",
        "notice_given": notice,
        "has_medical_certificate": has_cert,
        "reason": message,
    }

    client, model_name = get_llm_client()
    prompt = LEAVE_EXTRACTION_PROMPT.format(user_message=message.strip())

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = ""
        if response and response.choices and len(response.choices) > 0:
            msg = response.choices[0].message
            raw = getattr(msg, "content", "") or getattr(msg, "reasoning", "") or ""

        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw, re.IGNORECASE)
        cleaned = match.group(1).strip() if match else raw.strip()
        parsed = json.loads(cleaned)
        # Verify days is populated
        if not parsed.get("days"):
            parsed["days"] = extracted_days
        return parsed
    except Exception as e:
        logger.warning(f"Failed to parse leave fields via LLM ({e}), using heuristic parser.")
        return heuristic_dict


def handle_leave_request(message: str, session_id: str = "default") -> dict[str, Any]:
    """Processes an employee leave request through extraction, repair merge, policy retrieval, and governance."""
    from src.memory import memory_store

    # Step 1: Structured parameter extraction
    extracted_fields = extract_leave_fields(message)
    
    # Check for conversational repair against last turn
    last_context = memory_store.get_last_action_context(session_id)
    if last_context and "Leave" in last_context.get("agent_used", ""):
        prev_payload = last_context.get("payload", {})
        # Merge repair updates
        if "certificate" in message.lower() or "doctor" in message.lower():
            if "attached" in message.lower() or "uploaded" in message.lower() or "have" in message.lower():
                extracted_fields["has_medical_certificate"] = True
                if not extracted_fields.get("days") or extracted_fields.get("days") == 1.0:
                    extracted_fields["days"] = prev_payload.get("days", 1.0)
                extracted_fields["leave_type"] = prev_payload.get("leave_type", "Sick Leave")
        elif "change" in message.lower() or "adjust" in message.lower() or "make it" in message.lower():
            extracted_fields["leave_type"] = prev_payload.get("leave_type", extracted_fields.get("leave_type"))

    leave_type = extracted_fields.get("leave_type", "Leave")
    days = extracted_fields.get("days", 1.0)

    # Step 2: Retrieve relevant policy rules for this leave type via RAG
    retrieval_query = f"{leave_type} approval workflow advance notice days medical certificate requirements leave policy"
    policy_chunks, _ = retrieve_relevant_chunks(retrieval_query, k=config.TOP_K)

    # Step 3: Mandatory Governance Layer Check
    gov_result = evaluate_governance(
        session_id=session_id,
        intent="leave_request",
        action_type="submit_leave_request",
        action_payload=extracted_fields,
        retrieved_policy_chunks=policy_chunks,
    )

    decision = gov_result["decision"]
    reason = gov_result["reason"]
    rule_cited = gov_result["rule_cited"]
    log_id = gov_result["log_id"]

    # Step 4: Build clear user-facing response
    if decision == "APPROVE":
        badge = "✅ **LEAVE REQUEST APPROVED**"
        action_desc = f"Submitted {days} day(s) of {leave_type} (Log ID: #{log_id})"
        explanation = f"{badge}\n\nYour request for **{days} day(s) of {leave_type}** has been validated against company policy and approved.\n\n- **Governance Status:** Compliant\n- **Policy Rule Applied:** {rule_cited}\n- **Details:** {reason}"
    elif decision == "FLAG_FOR_REVIEW":
        badge = "⚠️ **FLAGGED FOR HR / MANAGER REVIEW**"
        action_desc = f"Drafted {days} day(s) of {leave_type} - Pending Manager Review (Log ID: #{log_id})"
        explanation = f"{badge}\n\nYour request for **{days} day(s) of {leave_type}** requires human manager review.\n\n- **Governance Status:** Flagged for Review (Pending HRBP)\n- **Reason:** {reason}\n- **Policy Rule Applied:** {rule_cited}\n- **Next Steps:** Ticket #{log_id} routed to your reporting manager in the Governance Console."
    else:  # BLOCK
        badge = "🚫 **LEAVE REQUEST BLOCKED (POLICY VIOLATION)**"
        action_desc = f"Blocked {days} day(s) of {leave_type} (Log ID: #{log_id})"
        explanation = f"{badge}\n\nYour request for **{days} day(s) of {leave_type}** cannot be processed because it violates internal HR policy.\n\n- **Governance Status:** Blocked Violation\n- **Violation Reason:** {reason}\n- **Policy Rule Violated:** {rule_cited}"

    return {
        "response": explanation,
        "sources": policy_chunks,
        "refused": False,
        "action_taken": action_desc,
        "governance_decision": decision,
        "governance_payload": extracted_fields,
        "rule_cited": rule_cited,
        "log_id": log_id,
    }
