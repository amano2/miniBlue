"""Reimbursement Claim Specialist Agent.

Extracts structured expense fields from free text, retrieves relevant expense policy caps,
and validates claims through the RightAction Governance Layer before submission.
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

REIMBURSEMENT_EXTRACTION_PROMPT = """You are an HR Expense Reimbursement parser. Extract structured fields from the employee's claim message.
Respond ONLY in JSON with the following structure:
{{
  "category": "Home Internet | Ergonomic Setup | Daily Meal / Per Diem | Travel Lodging | Learning & Development | Client Entertainment | Other",
  "amount": <float numeric amount, e.g. 50.0, 300.0, 120.0, 75.0>,
  "currency": "<USD | INR | EUR | other>",
  "receipt_attached": <true | false | null>,
  "days_since_expense": <integer days or null>,
  "city_tier": "<Tier 1 | Tier 2 | not applicable>",
  "item_description": "<concise description of the expense item>"
}}

User Message: "{user_message}"
"""


def extract_reimbursement_fields(message: str) -> dict[str, Any]:
    """Extracts structured expense fields from natural language."""
    clean_msg = message.lower()
    amount_match = re.search(r"[\$₹]?\s*(\d+(?:\.\d{1,2})?)", message)
    amt = float(amount_match.group(1)) if amount_match else 50.0

    category = "General Expense"
    if "internet" in clean_msg or "broadband" in clean_msg or "fiber" in clean_msg or "wifi" in clean_msg:
        category = "Home Internet"
    elif "ergonomic" in clean_msg or "chair" in clean_msg or "desk" in clean_msg or "furniture" in clean_msg or "stipend" in clean_msg:
        category = "Ergonomic Setup"
    elif "per diem" in clean_msg or "meal" in clean_msg or "dinner" in clean_msg or "lunch" in clean_msg:
        category = "Daily Meal / Per Diem"
    elif "hotel" in clean_msg or "lodging" in clean_msg or "room" in clean_msg or "ritz" in clean_msg:
        category = "Travel Lodging"
    elif "alcohol" in clean_msg or "beer" in clean_msg or "wine" in clean_msg:
        category = "Personal Expenses"
    elif "taxi" in clean_msg or "cab" in clean_msg or "uber" in clean_msg or "flight" in clean_msg:
        category = "Ground Transportation"

    days_old = None
    days_old_match = re.search(r"(\d+)\s*days\s*ago", clean_msg)
    if days_old_match:
        days_old = int(days_old_match.group(1))
    elif "yesterday" in clean_msg:
        days_old = 1

    heuristic_dict = {
        "category": category,
        "amount": amt,
        "currency": "USD" if "$" in message or "usd" in clean_msg else "INR",
        "receipt_attached": True if "receipt" in clean_msg or "bill" in clean_msg or "invoice" in clean_msg else False,
        "days_since_expense": days_old or 10,
        "city_tier": "Tier 1" if "tier 1" in clean_msg or "london" in clean_msg or "new york" in clean_msg else "Tier 2",
        "item_description": message,
    }

    client, model_name = get_llm_client()
    prompt = REIMBURSEMENT_EXTRACTION_PROMPT.format(user_message=message.strip())

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
        if not parsed.get("amount") or parsed.get("amount") == 0:
            parsed["amount"] = amt
        if not parsed.get("category") or parsed.get("category") == "Other":
            parsed["category"] = category
        return parsed
    except Exception as e:
        logger.warning(f"Failed to parse reimbursement fields via LLM ({e}), using heuristic parser.")
        return heuristic_dict


def handle_reimbursement_claim(message: str, session_id: str = "default") -> dict[str, Any]:
    """Processes an employee expense claim through extraction, repair merge, policy retrieval, and governance."""
    from src.memory import memory_store

    # Step 1: Extract structured claim parameters
    extracted_fields = extract_reimbursement_fields(message)
    
    # Check for conversational repair against previous turn
    last_context = memory_store.get_last_action_context(session_id)
    if last_context and "Reimbursement" in last_context.get("agent_used", ""):
        prev_payload = last_context.get("payload", {})
        # Merge previous category / merchant if not specified in repair prompt
        if not extracted_fields.get("category") or extracted_fields.get("category") == "General Expense":
            extracted_fields["category"] = prev_payload.get("category", "Home Internet")
        if "receipt" in message.lower() and ("attach" in message.lower() or "have" in message.lower()):
            extracted_fields["receipt_attached"] = True

    category = extracted_fields.get("category", "General Expense")
    amount = extracted_fields.get("amount", 0.0)
    currency = extracted_fields.get("currency", "USD")

    # Step 2: Retrieve relevant reimbursement policy rules & caps via RAG
    retrieval_query = f"{category} reimbursement limit ceiling monthly allowance receipts documentation per diem reimbursement policy"
    policy_chunks, _ = retrieve_relevant_chunks(retrieval_query, k=config.TOP_K)

    # Step 3: Mandatory RightAction Governance Evaluation
    gov_result = evaluate_governance(
        session_id=session_id,
        intent="reimbursement_claim",
        action_type="submit_reimbursement_claim",
        action_payload=extracted_fields,
        retrieved_policy_chunks=policy_chunks,
    )

    decision = gov_result["decision"]
    reason = gov_result["reason"]
    rule_cited = gov_result["rule_cited"]
    log_id = gov_result["log_id"]

    # Step 4: Build clear user-facing response
    currency_symbol = "$" if currency.upper() == "USD" else ("₹" if currency.upper() == "INR" else f"{currency} ")

    if decision == "APPROVE":
        badge = "✅ **REIMBURSEMENT CLAIM APPROVED**"
        action_desc = f"Approved claim of {currency_symbol}{amount:.2f} for {category} (Log ID: #{log_id})"
        explanation = f"{badge}\n\nYour reimbursement claim for **{currency_symbol}{amount:.2f}** ({category}) has been verified against policy caps and approved for payroll disbursement.\n\n- **Governance Status:** Fully Compliant\n- **Policy Rule Applied:** {rule_cited}\n- **Settlement Schedule:** Processed on 15th / 30th salary cycle\n- **Audit Reason:** {reason}"
    elif decision == "FLAG_FOR_REVIEW":
        badge = "⚠️ **FLAGGED FOR FINANCE / MANAGER REVIEW**"
        action_desc = f"Claim of {currency_symbol}{amount:.2f} for {category} - Pending Human Review (Log ID: #{log_id})"
        explanation = f"{badge}\n\nYour claim of **{currency_symbol}{amount:.2f}** ({category}) requires additional human review or documentation.\n\n- **Governance Status:** Flagged for Review (Pending Finance/HRBP)\n- **Reason:** {reason}\n- **Policy Rule Applied:** {rule_cited}\n- **Next Steps:** Ticket #{log_id} routed to Finance / Manager Review queue."
    else:  # BLOCK
        badge = "🚫 **REIMBURSEMENT CLAIM BLOCKED (POLICY VIOLATION)**"
        action_desc = f"Blocked claim of {currency_symbol}{amount:.2f} for {category} (Log ID: #{log_id})"
        explanation = f"{badge}\n\nYour claim for **{currency_symbol}{amount:.2f}** ({category}) cannot be approved as it violates company reimbursement limits.\n\n- **Governance Status:** Blocked Violation\n- **Violation Reason:** {reason}\n- **Policy Rule Violated:** {rule_cited}"

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
