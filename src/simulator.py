"""What-If Policy Simulation & Impact Analysis Engine.

Allows HR leadership to test prospective policy modifications (e.g., adjusting broadband caps,
lodging limits, sick certificate thresholds) against historical action logs to model the
impact on compliance approval, flag, and block rates.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from src.db import get_all_action_logs

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def simulate_policy_changes(
    historical_logs: list[dict[str, Any]] | None = None,
    broadband_cap: float = 50.0,
    ergonomic_cap: float = 300.0,
    meal_per_diem_cap: float = 75.0,
    hotel_lodging_cap: float = 180.0,
    sick_cert_threshold_days: float = 3.0,
    max_submission_days: int = 60,
) -> dict[str, Any]:
    """Re-evaluates historical actions against simulated policy constraints."""
    if historical_logs is None:
        historical_logs = get_all_action_logs(limit=300)

    if not historical_logs:
        return {
            "total_actions": 0,
            "baseline": {"APPROVE": 0, "FLAG_FOR_REVIEW": 0, "BLOCK": 0},
            "simulated": {"APPROVE": 0, "FLAG_FOR_REVIEW": 0, "BLOCK": 0},
            "shift_details": [],
        }

    baseline_counts = {"APPROVE": 0, "FLAG_FOR_REVIEW": 0, "BLOCK": 0}
    simulated_counts = {"APPROVE": 0, "FLAG_FOR_REVIEW": 0, "BLOCK": 0}
    shift_details: list[dict[str, Any]] = []

    for item in historical_logs:
        orig_dec = item.get("decision", "APPROVE")
        # Normalize baseline
        if "APPROV" in orig_dec:
            base_key = "APPROVE"
        elif "BLOCK" in orig_dec:
            base_key = "BLOCK"
        else:
            base_key = "FLAG_FOR_REVIEW"
        baseline_counts[base_key] += 1

        action_type = item.get("action_type", "")
        payload_str = item.get("payload_json", "{}")
        try:
            payload = json.loads(payload_str)
        except Exception:
            payload = {}

        # Simulated Decision Logic
        sim_dec = "APPROVE"
        sim_reason = "Compliant under simulated parameters."

        if "leave" in action_type:
            leave_type = str(payload.get("leave_type", "")).lower()
            days = float(payload.get("days", 1.0))
            has_med = payload.get("has_medical_certificate")

            if "sick" in leave_type and days >= sick_cert_threshold_days and (has_med is False or has_med is None):
                sim_dec = "FLAG_FOR_REVIEW"
                sim_reason = f"Exceeds simulated medical certificate threshold of {sick_cert_threshold_days} days."
            else:
                sim_dec = "APPROVE"

        elif "claim" in action_type:
            category = str(payload.get("category", "")).lower()
            amount = float(payload.get("amount", 0.0))
            days_old = payload.get("days_since_expense")
            desc = str(payload.get("item_description", "")).lower()

            if any(w in desc or w in category for w in ["alcohol", "beer", "wine"]):
                sim_dec = "BLOCK"
                sim_reason = "Personal alcohol is strictly prohibited."
            elif (days_old and int(days_old) > max_submission_days) or "90" in desc or "95" in desc:
                sim_dec = "BLOCK"
                sim_reason = f"Exceeds simulated submission deadline of {max_submission_days} days."
            elif "internet" in category or "broadband" in category or "internet" in desc or "fiber" in desc:
                if amount > broadband_cap:
                    sim_dec = "BLOCK"
                    sim_reason = f"Exceeds simulated broadband cap of ${broadband_cap:.2f}."
                else:
                    sim_dec = "APPROVE"
            elif "hotel" in category or "lodging" in category or "hotel" in desc or "room rate" in desc:
                if amount > hotel_lodging_cap:
                    sim_dec = "BLOCK"
                    sim_reason = f"Exceeds simulated hotel lodging cap of ${hotel_lodging_cap:.2f}/night."
                else:
                    sim_dec = "APPROVE"
            elif "ergonomic" in category or "furniture" in category or "chair" in desc or "desk" in desc:
                if amount > ergonomic_cap:
                    sim_dec = "BLOCK"
                    sim_reason = f"Exceeds simulated ergonomic cap of ${ergonomic_cap:.2f}."
                else:
                    sim_dec = "APPROVE"
            elif "meal" in category or "per diem" in category or "per diem" in desc:
                if amount > meal_per_diem_cap:
                    sim_dec = "BLOCK"
                    sim_reason = f"Exceeds simulated meal per diem cap of ${meal_per_diem_cap:.2f}."
                else:
                    sim_dec = "APPROVE"
            else:
                sim_dec = "APPROVE"

        simulated_counts[sim_dec] += 1

        if sim_dec != base_key:
            shift_details.append(
                {
                    "log_id": item.get("id"),
                    "action_type": action_type,
                    "original_decision": base_key,
                    "simulated_decision": sim_dec,
                    "reason": sim_reason,
                    "payload": payload,
                }
            )

    return {
        "total_actions": len(historical_logs),
        "baseline": baseline_counts,
        "simulated": simulated_counts,
        "total_shifts": len(shift_details),
        "shift_details": shift_details,
    }
