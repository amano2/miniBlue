"""Enterprise Agentic HR & RightAction Governance SaaS Portal.

Features:
- Tab 1: 💬 Enterprise Multi-Agent Chat & Thought Inspector
- Tab 2: 👨‍💼 Manager Governance & HITL Review Inbox (Interactive Ticket Resolution)
- Tab 3: 🧪 What-If Policy Simulation & Impact Sandbox
- Tab 4: 📊 Observability, Cryptographic Audit Verification & Data Export
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import streamlit as st
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

# Page Configuration
st.set_page_config(
    page_title="BlueVerse SaaS | Agentic HR & RightAction Governance",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Executive Styling
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    .portal-banner {
        background: linear-gradient(135deg, #111827 0%, #1e1b4b 50%, #0b0f19 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        padding: 18px 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .agent-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        margin-bottom: 10px;
    }
    .pill-qa { background-color: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .pill-leave { background-color: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .pill-claim { background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .pill-esc { background-color: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }

    .latency-pill {
        background-color: rgba(148, 163, 184, 0.1);
        color: #94a3b8;
        border: 1px solid rgba(148, 163, 184, 0.2);
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-family: 'JetBrains Mono', monospace;
    }

    .gov-badge {
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin: 8px 0;
        display: inline-block;
    }
    .gov-approve { background-color: rgba(6, 78, 59, 0.8); color: #a7f3d0; border: 1px solid #059669; }
    .gov-flag { background-color: rgba(120, 53, 15, 0.8); color: #fde68a; border: 1px solid #d97706; }
    .gov-block { background-color: rgba(136, 19, 55, 0.8); color: #fecdd3; border: 1px solid #e11d48; }

    .metric-card {
        background: linear-gradient(180deg, #111827 0%, #0f172a 100%);
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    .metric-val {
        font-size: 1.9rem;
        font-weight: 800;
        color: #ffffff;
    }
    .metric-lbl {
        font-size: 0.78rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 4px;
    }
    .hitl-ticket-card {
        background-color: #111827;
        border: 1px solid #374151;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .hash-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #a5b4fc;
        background-color: rgba(99, 102, 241, 0.1);
        padding: 4px 8px;
        border-radius: 4px;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Banner
st.markdown(
    """
    <div class="portal-banner">
        <div>
            <div style="font-size: 1.35rem; font-weight: 800; color: #ffffff;">
                BlueVerse <span style="font-weight:400; color:#6366f1;">|</span> <span style="font-size:1.15rem; color:#e0e7ff;">Enterprise Multi-Agent HR & RightAction™ Platform</span>
            </div>
            <div style="font-size: 0.84rem; color: #94a3b8; margin-top: 4px;">
                Governed Agent-to-Agent Architecture with Human-in-the-Loop Review, Policy Simulation, and Cryptographic Auditing.
            </div>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(99, 102, 241, 0.15); color:#818cf8; border:1px solid #6366f1; padding:5px 14px; border-radius:20px; font-size:0.75rem; font-weight:700;">
                🔒 RIGHTACTION™ SECURED
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.markdown("### 🏢 Compliance Console")
    st.caption("Inspired by LTM BlueVerse Multi-Agent Pattern")
    st.divider()

    st.markdown("##### 🤖 Specialist Agent Fleet")
    st.markdown("- 🧭 `Orchestrator Agent` (Intent Classifier)")
    st.markdown("- 📖 `Policy Q&A Agent` (Grounded RAG)")
    st.markdown("- 🌴 `Leave Request Agent` (Action Drafter)")
    st.markdown("- 💳 `Reimbursement Agent` (Expense Drafter)")
    st.markdown("- 🛡️ `RightAction™ Governance Layer` (Auditor)")

    st.divider()
    st.markdown("##### ⚙️ System Specifications")
    st.markdown(f"**Model:** `{config.OPENROUTER_MODEL.split('/')[-1]}`")
    st.markdown(f"**Embeddings:** `{config.EMBEDDING_MODEL_NAME}`")
    st.markdown(f"**Audit Storage:** `SQLite (db/actions.db)`")
    st.markdown(f"**Integrity Engine:** `SHA-256 Hash Chaining`")

    st.divider()
    if st.button("🗑️ Reset Chat & Memory", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = f"session-{datetime.now().strftime('%H%M%S')}"
        st.rerun()

# Initialize session
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session-{datetime.now().strftime('%H%M%S')}"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Top Tabs Navigation
pending_count = len(get_pending_reviews())
tab1_label = "💬 Enterprise Chat"
tab2_label = f"👨‍💼 Manager Review Inbox {'🔴 ' + str(pending_count) if pending_count > 0 else '🟢'}"
tab3_label = "🧪 Policy Sandbox & Simulation"
tab4_label = "📊 Observability & Audit Trail"

tab_chat, tab_hitl, tab_sim, tab_audit = st.tabs([tab1_label, tab2_label, tab3_label, tab4_label])

# ==============================================================================
# TAB 1: ENTERPRISE CHAT & AGENT INSPECTOR
# ==============================================================================
with tab_chat:
    st.markdown("<div style='font-size: 0.82rem; font-weight: 700; color: #94a3b8; margin-bottom: 8px;'>QUICK ENTERPRISE ACTIONS:</div>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🌴 Apply for 3 Days Annual Leave", use_container_width=True):
            st.session_state.selected_prompt = "I would like to apply for 3 days of Annual Leave from November 15th to November 17th. Giving 3 weeks notice."
    with c2:
        if st.button("💳 Submit $48.50 Broadband Bill", use_container_width=True):
            st.session_state.selected_prompt = "Please reimburse my home broadband bill of $48.50 for October. Receipt attached."
    with c3:
        if st.button("⚠️ Test Flag: 4-Day Sick (No Note)", use_container_width=True):
            st.session_state.selected_prompt = "I was sick with flu for 4 consecutive business days last week. I do not have a doctor's certificate."
    with c4:
        if st.button("🚫 Test Block: $650 Luxury Hotel", use_container_width=True):
            st.session_state.selected_prompt = "Please reimburse $650 per night for 2 nights at the Ritz Carlton in Tier 1 city."

    st.divider()

    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                agent = msg.get("agent_used", "Agent")
                gov_dec = msg.get("governance_decision")
                lat = msg.get("latency_ms", 0.0)

                pill_class = "pill-qa"
                if "Leave" in agent:
                    pill_class = "pill-leave"
                elif "Reimbursement" in agent:
                    pill_class = "pill-claim"
                elif "Escalation" in agent:
                    pill_class = "pill-esc"

                st.markdown(
                    f'<span class="agent-pill {pill_class}">Handled by: {agent}</span> <span class="latency-pill">⚡ {lat}ms</span>',
                    unsafe_allow_html=True,
                )

                if gov_dec == "APPROVE":
                    st.markdown('<span class="gov-badge gov-approve">✅ RightAction: APPROVED</span>', unsafe_allow_html=True)
                elif gov_dec == "FLAG_FOR_REVIEW":
                    st.markdown('<span class="gov-badge gov-flag">⚠️ RightAction: FLAGGED FOR REVIEW</span>', unsafe_allow_html=True)
                elif gov_dec == "BLOCK":
                    st.markdown('<span class="gov-badge gov-block">🚫 RightAction: BLOCKED VIOLATION</span>', unsafe_allow_html=True)

                st.markdown(msg["content"])

                if msg.get("sources"):
                    with st.expander(f"🔍 Deep Trace & Policy Citations ({len(msg['sources'])} chunks)"):
                        for idx, s in enumerate(msg["sources"], start=1):
                            st.markdown(f"**[{idx}] {s.get('doc_name')} (`{s.get('source_file')}`) — Similarity Score: {s.get('score', 'N/A')}**")
                            st.markdown(f"```markdown\n{s.get('text', '')}\n```")
            else:
                st.markdown(msg["content"])

    # Input handling
    prompt = st.chat_input("Ask a policy question, request leave, or submit an expense claim...")

    if "selected_prompt" in st.session_state and st.session_state.selected_prompt:
        prompt = st.session_state.selected_prompt
        st.session_state.selected_prompt = None

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Orchestrator routing to specialist agent & validating RightAction boundaries..."):
                res = process_message(prompt, session_id=st.session_state.session_id)

            agent = res.get("agent_used", "Agent")
            gov_dec = res.get("governance_decision")
            content = res.get("response", "")
            sources = res.get("sources", [])
            lat = res.get("latency_ms", 0.0)

            pill_class = "pill-qa"
            if "Leave" in agent:
                pill_class = "pill-leave"
            elif "Reimbursement" in agent:
                pill_class = "pill-claim"
            elif "Escalation" in agent:
                pill_class = "pill-esc"

            st.markdown(
                f'<span class="agent-pill {pill_class}">Handled by: {agent}</span> <span class="latency-pill">⚡ {lat}ms</span>',
                unsafe_allow_html=True,
            )

            if gov_dec == "APPROVE":
                st.markdown('<span class="gov-badge gov-approve">✅ RightAction: APPROVED</span>', unsafe_allow_html=True)
            elif gov_dec == "FLAG_FOR_REVIEW":
                st.markdown('<span class="gov-badge gov-flag">⚠️ RightAction: FLAGGED FOR REVIEW</span>', unsafe_allow_html=True)
            elif gov_dec == "BLOCK":
                st.markdown('<span class="gov-badge gov-block">🚫 RightAction: BLOCKED VIOLATION</span>', unsafe_allow_html=True)

            st.markdown(content)

            if sources:
                with st.expander(f"🔍 Deep Trace & Policy Citations ({len(sources)} chunks)"):
                    for idx, s in enumerate(sources, start=1):
                        st.markdown(f"**[{idx}] {s.get('doc_name')} (`{s.get('source_file')}`) — Similarity Score: {s.get('score', 'N/A')}**")
                        st.markdown(f"```markdown\n{s.get('text', '')}\n```")

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": content,
                    "agent_used": agent,
                    "governance_decision": gov_dec,
                    "sources": sources,
                    "latency_ms": lat,
                }
            )

# ==============================================================================
# TAB 2: MANAGER GOVERNANCE & HITL REVIEW INBOX
# ==============================================================================
with tab_hitl:
    st.markdown("### 👨‍💼 Manager Governance & Human-in-the-Loop Review Queue")
    st.caption("Review requests flagged by the RightAction™ compliance engine requiring managerial exception authorization.")

    pending_items = get_pending_reviews()

    if not pending_items:
        st.success("🎉 All governance action requests are reviewed! Zero pending tickets.")
    else:
        st.info(f"📋 **{len(pending_items)} Action Item(s)** currently pending manager approval.")

        for item in pending_items:
            log_id = item["id"]
            action_type = item["action_type"]
            timestamp = item["timestamp"]
            session = item["session_id"]
            reason = item["reason"]
            rule_cited = item["rule_cited"]
            payload_str = item["payload_json"]

            try:
                payload = json.loads(payload_str)
            except Exception:
                payload = {}

            with st.container():
                st.markdown(
                    f"""
                    <div class="hitl-ticket-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:1.05rem; font-weight:700; color:#f59e0b;">
                                ⚠️ Review Ticket #{log_id} — {action_type.replace('_', ' ').title()}
                            </span>
                            <span class="hash-badge">Session: {session}</span>
                        </div>
                        <div style="margin-top:8px; font-size:0.85rem; color:#cbd5e1;">
                            <strong>Timestamp:</strong> {timestamp} | <strong>Policy Rule:</strong> {rule_cited}
                        </div>
                        <div style="margin-top:6px; font-size:0.88rem; color:#fcd34d;">
                            <strong>Flag Reason:</strong> {reason}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_details, col_actions = st.columns([1.4, 1])
                with col_details:
                    st.markdown("**Structured Action Parameters:**")
                    st.json(payload)

                with col_actions:
                    st.markdown("**Manager Determination:**")
                    notes_input = st.text_input(
                        "Manager Review Justification",
                        value="Approved per department head discretion.",
                        key=f"notes_{log_id}",
                    )
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅ Approve Exception", key=f"app_{log_id}", use_container_width=True):
                            resolve_review(log_id, "HR-MGR-ADMIN", "APPROVE", notes_input)
                            st.success(f"Ticket #{log_id} Approved with Exception!")
                            st.rerun()
                    with b2:
                        if st.button("🚫 Confirm Rejection", key=f"rej_{log_id}", use_container_width=True):
                            resolve_review(log_id, "HR-MGR-ADMIN", "BLOCK", notes_input)
                            st.error(f"Ticket #{log_id} Rejected.")
                            st.rerun()

                st.divider()

# ==============================================================================
# TAB 3: POLICY SANDBOX & SIMULATION
# ==============================================================================
with tab_sim:
    st.markdown("### 🧪 What-If Policy Simulation & Sandboxing")
    st.caption("Model the financial and compliance impact of prospective policy revisions over historical action data.")

    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        sim_broadband = st.slider("Monthly Broadband Allowance Cap ($)", 30.0, 150.0, 50.0, step=5.0)
        sim_ergo = st.slider("Ergonomic Equipment Stipend ($)", 100.0, 600.0, 300.0, step=25.0)
    with s_col2:
        sim_meal = st.slider("Tier 1 Daily Meal Per Diem ($)", 40.0, 150.0, 75.0, step=5.0)
        sim_hotel = st.slider("Tier 1 Hotel Lodging Cap ($/night)", 100.0, 400.0, 180.0, step=10.0)
    with s_col3:
        sim_sick = st.slider("Sick Note Certificate Threshold (Days)", 1.0, 7.0, 3.0, step=1.0)
        sim_deadline = st.slider("Maximum Expense Window (Days)", 15, 120, 60, step=5)

    if st.button("🚀 Run What-If Simulation Over Historical Logs", use_container_width=True):
        sim_results = simulate_policy_changes(
            broadband_cap=sim_broadband,
            ergonomic_cap=sim_ergo,
            meal_per_diem_cap=sim_meal,
            hotel_lodging_cap=sim_hotel,
            sick_cert_threshold_days=sim_sick,
            max_submission_days=sim_deadline,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Historical Records", sim_results["total_actions"])
        with m2:
            base_app = sim_results["baseline"]["APPROVE"]
            sim_app = sim_results["simulated"]["APPROVE"]
            st.metric("Approved Actions", sim_app, delta=f"{sim_app - base_app} shifts")
        with m3:
            base_flag = sim_results["baseline"]["FLAG_FOR_REVIEW"]
            sim_flag = sim_results["simulated"]["FLAG_FOR_REVIEW"]
            st.metric("Flagged for Review", sim_flag, delta=f"{sim_flag - base_flag} shifts")
        with m4:
            base_blk = sim_results["baseline"]["BLOCK"]
            sim_blk = sim_results["simulated"]["BLOCK"]
            st.metric("Blocked Violations", sim_blk, delta=f"{sim_blk - base_blk} shifts")

        st.divider()
        st.markdown("##### 📈 Baseline vs Simulated Distribution")
        df_comp = pd.DataFrame(
            {
                "Baseline Policy": sim_results["baseline"],
                "Simulated Policy": sim_results["simulated"],
            }
        )
        st.bar_chart(df_comp)

        if sim_results["shift_details"]:
            st.markdown("##### 🔄 Granular Shift Impact Analysis")
            df_shifts = pd.DataFrame(sim_results["shift_details"])
            st.dataframe(df_shifts[["log_id", "action_type", "original_decision", "simulated_decision", "reason"]], use_container_width=True)

# ==============================================================================
# TAB 4: OBSERVABILITY & CRYPTOGRAPHIC AUDIT TRAIL
# ==============================================================================
with tab_audit:
    st.markdown("### 📊 Observability Telemetry & Cryptographic Audit Trail")
    st.caption("Real-time telemetry, tamper-evident SHA-256 hash chain verification, and data export.")

    metrics = get_telemetry_metrics()
    logs = get_all_action_logs(limit=200)

    # Top KPI Metrics Row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{metrics["total_inquiries"]}</div><div class="metric-lbl">Total Turns</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{metrics["total_actions"]}</div><div class="metric-lbl">Audited Actions</div></div>', unsafe_allow_html=True)
    with k3:
        approvals = metrics["decision_counts"].get("APPROVE", 0) + metrics["decision_counts"].get("APPROVE (Manager Override)", 0)
        app_rate = (approvals / metrics["total_actions"] * 100) if metrics["total_actions"] else 0.0
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#34d399;">{app_rate:.1f}%</div><div class="metric-lbl">Compliance Rate</div></div>', unsafe_allow_html=True)
    with k4:
        pending = metrics["pending_reviews"]
        p_color = "#f59e0b" if pending > 0 else "#34d399"
        st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:{p_color};">{pending}</div><div class="metric-lbl">Pending Reviews</div></div>', unsafe_allow_html=True)
    with k5:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{metrics["avg_latency_ms"]} ms</div><div class="metric-lbl">Avg Turn Latency</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Cryptographic Hash Chain Verification
    chain_status = verify_audit_hash_chain()
    if chain_status["valid"]:
        st.success(f"🔒 **Cryptographic Hash Chain Integrity:** {chain_status['message']} ({chain_status['total_records']} blocks verified)")
    else:
        st.error(f"🚨 **Integrity Alert:** {chain_status['message']}")

    # Charts Row
    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown("##### 🧭 Intent Classification Breakdown")
        if metrics["intent_counts"]:
            df_intent = pd.DataFrame(list(metrics["intent_counts"].items()), columns=["Intent", "Count"]).set_index("Intent")
            st.bar_chart(df_intent, color="#3b82f6")
    with ch2:
        st.markdown("##### 🛡️ Governance Decision Breakdown")
        if metrics["decision_counts"]:
            df_gov = pd.DataFrame(list(metrics["decision_counts"].items()), columns=["Decision", "Count"]).set_index("Decision")
            st.bar_chart(df_gov, color="#10b981")

    st.divider()

    # Real-Time SQLite Audit Log Table
    st.markdown("##### 📜 Immutable SQLite Action Audit Trail (`db/actions.db`)")
    if logs:
        df_logs = pd.DataFrame(logs)
        display_cols = ["id", "timestamp", "intent", "action_type", "decision", "status", "reviewed_by", "rule_cited", "entry_hash"]
        available_cols = [c for c in display_cols if c in df_logs.columns]
        st.dataframe(df_logs[available_cols], use_container_width=True, hide_index=True)

        # Export Button
        csv_data = df_logs.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Signed Audit Package (.CSV)",
            data=csv_data,
            file_name=f"governance_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("No governed actions logged in `db/actions.db` yet.")
