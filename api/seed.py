"""Seed script for miniBlue Enterprise Platform.

Seeds:
1. Four demo users (one per role):
   - employee@miniblue.dev (role: employee)
   - manager@miniblue.dev (role: manager)
   - admin@miniblue.dev (role: admin)
   - auditor@miniblue.dev (role: auditor)
2. Policy docs & chunks in database from data/raw_docs/.
3. ≥ 60 realistic historical actions covering all 10 evaluation scenarios with 100% valid SHA-256 hash chaining.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.auth import hash_password
from api.db import append_action_log, get_db_connection, init_extended_db, verify_entire_hash_chain

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "MiniBlue2026!")


def seed_users() -> dict[str, int]:
    """Inserts or updates the 4 canonical demo users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    hashed = hash_password(DEMO_PASSWORD)

    users_data = [
        ("EMP-001", "employee@miniblue.dev", "Alex Mercer (Employee)", hashed, "employee", "Engineering"),
        ("MGR-002", "manager@miniblue.dev", "Sarah Chen (Manager & HRBP)", hashed, "manager", "People Operations"),
        ("ADM-003", "admin@miniblue.dev", "David Vance (HR Admin)", hashed, "admin", "Human Resources"),
        ("AUD-004", "auditor@miniblue.dev", "Elena Rostova (Compliance Auditor)", hashed, "auditor", "Internal Audit"),
    ]

    user_ids: dict[str, int] = {}
    for emp_id, email, name, p_hash, role, dept in users_data:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            user_ids[role] = row["id"]
            cursor.execute(
                "UPDATE users SET full_name = ?, password_hash = ?, role = ?, department = ? WHERE id = ?",
                (name, p_hash, role, dept, row["id"]),
            )
        else:
            cursor.execute(
                """
                INSERT INTO users (employee_id, email, full_name, password_hash, role, department, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (emp_id, email, name, p_hash, role, dept, now_iso),
            )
            user_ids[role] = cursor.lastrowid

    conn.commit()
    conn.close()
    logger.info(f"Seeded 4 demo users: {list(user_ids.keys())}")
    return user_ids


def seed_policy_docs() -> None:
    """Populates policy_docs table with metadata from data/raw_docs/."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()

    docs_meta = [
        ("HR-POL-001", "Annual, Sick & Parental Leave Policy", "data/raw_docs/leave_policy.md", "2.1"),
        ("HR-POL-002", "Travel, Lodging & Expense Reimbursement Policy", "data/raw_docs/reimbursement_policy.md", "3.0"),
        ("HR-FAQ-003", "Employee Onboarding & Payroll FAQ", "data/raw_docs/onboarding_faq.md", "1.4"),
        ("HR-POL-004", "Corporate Code of Conduct & Business Ethics", "data/raw_docs/code_of_conduct.md", "2.0"),
    ]

    for doc_id, title, rel_path, ver in docs_meta:
        abs_path = ROOT_DIR / rel_path
        content = abs_path.read_text(encoding="utf-8") if abs_path.exists() else ""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        chunk_count = len(content.split("\n## "))

        cursor.execute(
            """
            INSERT OR REPLACE INTO policy_docs (doc_id, title, file_path, version, content_sha256, chunk_count, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, title, str(abs_path), ver, content_hash, chunk_count, now_iso),
        )

    conn.commit()
    conn.close()
    logger.info("Seeded 4 canonical policy documents.")


def seed_historical_actions(user_ids: dict[str, int]) -> None:
    """Populates ≥ 60 realistic historical actions ensuring valid hash continuity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM action_logs")
    existing_count = cursor.fetchone()["cnt"]
    conn.close()

    if existing_count >= 50:
        logger.info(f"Database already contains {existing_count} actions; skipping action seed to preserve chain.")
        return

    emp_id = user_ids.get("employee", 1)

    # Scenarios covering compliant, flagged, and blocked items
    scenarios = [
        # 1. Compliant Annual Leave
        ("leave_request", "leave", {"leave_type": "annual", "days": 3, "notice_given_days": 18, "start_date": "2026-11-01"}, "APPROVE", "Annual leave of 3 days with 18 days notice conforms with 2-week requirement.", "HR-POL-001 §2.1"),
        # 2. Compliant Broadband
        ("reimbursement_claim", "reimbursement", {"category": "broadband", "amount": 48.50, "currency": "USD", "receipt_attached": True, "days_since_expense": 14}, "APPROVE", "Broadband expense is within $50 monthly allowance limit.", "HR-POL-002 §4.1"),
        # 3. Compliant Ergonomic
        ("reimbursement_claim", "reimbursement", {"category": "ergonomic", "amount": 280.00, "currency": "USD", "receipt_attached": True, "days_since_expense": 40}, "APPROVE", "Ergonomic claim is within $300 cap and 90-day onboarding window.", "HR-POL-002 §3.1"),
        # 4. Compliant Per Diem
        ("reimbursement_claim", "reimbursement", {"category": "meal", "amount": 68.00, "currency": "USD", "receipt_attached": True, "days_since_expense": 10}, "APPROVE", "Meal per diem conforms with $75 Tier 1 limit.", "HR-POL-002 §5.1"),
        # 5. Flagged: 4 days sick leave without note
        ("leave_request", "leave", {"leave_type": "sick", "days": 4, "has_medical_certificate": False, "notice_given_days": 0}, "FLAG_FOR_REVIEW", "Absence of 3+ consecutive days mandates medical certificate within 48h.", "HR-POL-001 §3.2"),
        # 6. Flagged: 45 days late expense
        ("reimbursement_claim", "reimbursement", {"category": "ground_transportation", "amount": 35.00, "currency": "USD", "receipt_attached": True, "days_since_expense": 45}, "FLAG_FOR_REVIEW", "Claim submitted between 31 and 60 days requires manager exception review.", "HR-POL-002 §8.1"),
        # 7. Blocked: $160 broadband
        ("reimbursement_claim", "reimbursement", {"category": "broadband", "amount": 160.00, "currency": "USD", "receipt_attached": True, "days_since_expense": 15}, "BLOCK", "Broadband claim exceeds $50.00 monthly allowance cap.", "HR-POL-002 §4.1"),
        # 8. Blocked: 90 days old
        ("reimbursement_claim", "reimbursement", {"category": "office_supplies", "amount": 42.00, "currency": "USD", "receipt_attached": True, "days_since_expense": 90}, "BLOCK", "Expenses older than 60 days are permanently non-reimbursable.", "HR-POL-002 §8.2"),
        # 9. Blocked: $650 luxury hotel
        ("reimbursement_claim", "reimbursement", {"category": "hotel", "amount": 650.00, "currency": "USD", "receipt_attached": True, "days_since_expense": 12}, "BLOCK", "Rate exceeds Tier 1 maximum lodging limit of $180.00/night.", "HR-POL-002 §5.3"),
        # 10. Blocked: Alcohol
        ("reimbursement_claim", "reimbursement", {"category": "alcohol", "amount": 85.00, "currency": "USD", "receipt_attached": True, "days_since_expense": 8}, "BLOCK", "Alcohol purchases are strictly prohibited from reimbursement.", "HR-POL-002 §7.1"),
    ]

    # Generate 60 records by cycling and adding realistic variations
    base_date = datetime.now(timezone.utc) - timedelta(days=45)
    for i in range(65):
        template = scenarios[i % len(scenarios)]
        intent, act_type, payload_tpl, dec, reason, rule = template
        payload = payload_tpl.copy()

        # Slight variations
        if "amount" in payload:
            payload["amount"] = round(payload["amount"] + (i % 7) * 1.5, 2)

        res = append_action_log(
            intent=intent,
            action_type=act_type,
            payload=payload,
            decision=dec,
            reason=reason,
            cited_rule=rule,
            requester_id=emp_id,
            session_id=f"hist-session-{i:03d}",
        )

    logger.info("Successfully seeded 65 historical actions with valid SHA-256 hash chaining.")


def run_seed() -> None:
    """Executes full database initialization and seeding."""
    init_extended_db()
    user_ids = seed_users()
    seed_policy_docs()
    seed_historical_actions(user_ids)

    # Verify chain
    verification = verify_entire_hash_chain()
    logger.info(f"Verification result: {verification['message']} (Total blocks: {verification['entries']})")
    assert verification["valid"], "Hash chain failed verification!"


if __name__ == "__main__":
    run_seed()
