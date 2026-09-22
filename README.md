<div align="center">

# 🏢 BlueVerse-Inspired Agentic HR Assistant
### Enterprise Multi-Agent Orchestration with RightAction™ Governance, Human-in-the-Loop Review, and Cryptographic Auditing

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Store-green.svg?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Author](https://img.shields.io/badge/Author-amano2-6366f1?style=for-the-badge&logo=github)](https://github.com/amano2)

<p align="center">
  <b>A production-grade, zero-cost Enterprise AI SaaS platform demonstrating agent-to-agent orchestration and compliantly bounded action taking.</b>
</p>

---

</div>

## 📌 Architectural Identity & Framing

> **Enterprise Framing Notice:**  
> This project is **inspired by LTM's (Larsen & Toubro Mindtree) BlueVerse ecosystem** — specifically two of its foundational architectural concepts: **multi-agent orchestration** (agent-to-agent task delegation) and **RightAction™ governance** (agents capable of executing real actions, but strictly bounded within compliant, auditable, and human-supervised guardrails).
>
> It is explicitly **not a reproduction** of commercial BlueVerse (which operates across 300+ agents with a proprietary Knowledge Fabric and multi-cloud studio); rather, it implements these two architectural paradigms at a small, fully transparent, and explainable scale for an HR operations domain.

---

## 🌟 Key Capabilities

- 🧭 **Multi-Agent Orchestration**: Dynamic intent classification router categorizes inquiries into `policy_question`, `leave_request`, `reimbursement_claim`, `escalation`, or `other` with confidence scoring.
- 🛡️ **RightAction™ Compliance Gate**: **Zero silent actions.** No specialist agent can finalize a leave booking or expense reimbursement without traversing the governance layer (`APPROVE`, `FLAG_FOR_REVIEW`, `BLOCK`) with mandatory policy rule citations.
- 👨‍💼 **Human-in-the-Loop (HITL) Review Queue**: Borderline and missing-information actions (e.g. sick leave $\ge 3$ days without a medical certificate, claims 31–60 days old) create pending tickets in a dedicated Manager Console for exception override or rejection with audit notes.
- 🧪 **"What-If" Policy Simulation Sandbox**: Interactive engine allowing HR leadership to model prospective policy threshold revisions (e.g. broadband caps, per diems, medical certificate requirements) over historical logs to project compliance and financial shifts.
- 🔒 **Cryptographic Tamper-Evident Audit Trail**: Blockchain-style **SHA-256 hash chaining** across all action records ensuring immutable, verifiable compliance records for SOC-2 and ISO audits.
- 💬 **Conversational Action Repair**: Context-aware session memory enables employees to negotiate or adjust blocked/flagged parameters conversationally (e.g., *"Adjust my claim to the policy max of $50"*).
- ⚡ **Deep Observability & Telemetry**: End-to-end token latency tracking (`latency_ms`), RAG similarity scores, and collapsible reasoning traces.

---

## 📐 System Architecture

```
                                      [User Request]
                                             │
                                             ▼
                       ┌───────────────────────────────────────────┐
                       │        Orchestrator Agent Router          │
                       │   (Intent Classification + Confidence)    │
                       └─────────────────────┬─────────────────────┘
                                             │
         ┌───────────────────────────────────┼───────────────────────────────────┐
         │                                   │                                   │
         ▼                                   ▼                                   ▼
┌──────────────────┐               ┌──────────────────┐               ┌──────────────────────┐
│ Policy Q&A Agent │               │Leave Action Agent│               │ Reimbursement Agent  │
│  (RAG Retrieval) │               │(Field Extraction)│               │  (Field Extraction)  │
└────────┬─────────┘               └─────────┬────────┘               └──────────┬───────────┘
         │                                   │                                   │
         │                            Retrieve Rules                      Retrieve Caps
         │                            (FAISS + BM25)                      (FAISS + BM25)
         │                                   │                                   │
         │                                   └─────────────────┬─────────────────┘
         │                                                     ▼
         │                                     ┌───────────────────────────────┐
         │                                     │ RightAction™ Governance Gate  │
         │                                     │ - Compliant Boundary Check    │
         │                                     │ - Decisions: APPROVE/FLAG/BLCK│
         │                                     │ - Mandatory Policy Rule Citing│
         │                                     └───────────────┬───────────────┘
         │                                                     │
         │                        ┌────────────────────────────┴────────────────────────────┐
         │                        ▼                                                         ▼
         │             [APPROVE / BLOCK]                                           [FLAG_FOR_REVIEW]
         │                        │                                                         │
         │                        │                                             ┌───────────▼───────────┐
         │                        │                                             │  Manager HITL Inbox   │
         │                        │                                             │ (Exception Override / │
         │                        │                                             │  Rejection with Note) │
         │                        │                                             └───────────┬───────────┘
         │                        │                                                         │
         │                        └────────────────────────────┬────────────────────────────┘
         │                                                     ▼
         │                                     ┌───────────────────────────────┐
         │                                     │   Tamper-Evident Audit DB     │
         │                                     │  (SQLite + SHA-256 Hash Chain)│
         │                                     └───────────────┬───────────────┘
         └─────────────────────────────────────────────────────┼────────────────────────────┘
                                                               ▼
                                              ┌─────────────────────────────────┐
                                              │      Executive SaaS Portal      │
                                              │  (Chat, Manager HITL, Simulator,│
                                              │   Live Telemetry & Audit Logs)  │
                                              └─────────────────────────────────┘
```

---

## 🛠️ Free & Open-Source Tech Stack

Strict adherence to a **100% zero-cost** operational model:

| Layer | Tool / Library | Rationale |
|---|---|---|
| **LLM Inference** | OpenRouter / Google Gemini API (Free Tier) | High instruction-following reasoning with structured JSON output capabilities. |
| **Dense Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local execution, 384-dimensional dense vectors, zero API calls or rate-limit consumption. |
| **Sparse Lexical Search** | `rank-bm25` (`BM25Okapi`) | High precision matching for exact policy codes, dollar amounts, and proper nouns. |
| **Vector Index** | FAISS (`IndexFlatIP`) | High-speed in-memory vector database with L2-normalized cosine similarity. |
| **Hybrid Rank Fusion** | Reciprocal Rank Fusion (RRF, $k=60$) | Combines dense semantic and sparse lexical rankings with balanced scoring. |
| **Orchestration** | Pure Python Router | Complete transparency and inspectability without opaque framework abstractions. |
| **Audit Persistence** | SQLite (`db/actions.db`) | Local ACID database with cryptographic SHA-256 hash chaining for tamper-evidence. |
| **Backend REST API** | FastAPI + Uvicorn | High-performance asynchronous API endpoints with automated OpenAPI / Swagger docs. |
| **Executive Frontend** | Streamlit | 4-Tab enterprise dashboard with live telemetry, manager review queue, and simulation sandbox. |

---

## 📋 Ground-Truth HR Policies Enforced

The system is strictly grounded in official policy documentation located in `data/raw_docs/`:

| Policy Document | ID | Key Compliant Constraints |
|---|---|---|
| **Leave Policy** | `HR-POL-001` | • **Annual Leave**: 20 days/year; $>2$ consecutive days requires at least 2 weeks advance notice.<br>• **Sick Leave**: 12 days/year; $\ge 3$ consecutive days strictly mandates a licensed medical certificate within 48 hours.<br>• **Parental Leave**: 16 weeks fully paid for primary caregivers. |
| **Reimbursement Policy** | `HR-POL-002` | • **Home Broadband**: Capped at $\$50.00\text{ USD/month}$ with itemized invoice.<br>• **Ergonomic Stipend**: $\$300.00\text{ USD}$ one-time within first 90 days of onboarding.<br>• **Travel Lodging**: Capped at $\$180.00\text{ USD/night}$ for Tier 1 Metro, and $\$120.00\text{ USD/night}$ for Tier 2.<br>• **Meals & Incidentals**: Capped at $\$75.00\text{ USD/day}$ for Tier 1 Metro, and $\$50.00\text{ USD/day}$ for Tier 2.<br>• **Submission Deadlines**: Standard 30-day window. Claims 31–60 days old trigger `FLAG_FOR_REVIEW`. Claims $>60$ days old are permanently `BLOCK`ed.<br>• **Prohibited Items**: Personal alcohol and non-business entertainment are strictly `BLOCK`ed. |
| **Onboarding FAQ** | `HR-FAQ-003` | IT provisioning, benefits enrollment schedules, payroll disbursement dates (15th & 30th), and probation timelines. |
| **Code of Conduct** | `HR-POL-004` | Conflicts of interest, anti-harassment protocols, confidential whistleblower reporting, and vendor gift limits ($\le \$50$). |

---

## 📊 Evaluation & Benchmark Scorecard

Evaluated via [`eval/run_eval.py`](eval/run_eval.py) over 15 policy questions (`eval/test_questions.json`) and 10 action governance scenarios (`eval/test_actions.json`), including deliberate policy violations:

```
================================================================================
📊 OVERALL AGENTIC SYSTEM SCORECARD
================================================================================
1. Orchestrator Intent Routing Accuracy:   100.0%  (10/10)  [PERFECT]
2. RightAction™ Governance Accuracy:      100.0%  (10/10)  [PERFECT]
3. Deliberate Violation Catch Rate:        100.0%   (6/6)   [PERFECT]
4. Policy Q&A Groundedness & Citations:     80.0%   (8/10)  [PASS]
5. Out-of-Scope Question Refusal Rate:      80.0%   (4/5)   [PASS]
================================================================================
```

---

## 🖥️ Executive 4-Tab SaaS Interface

The Streamlit dashboard (`app/streamlit_app.py`) provides an executive dark-mode experience:

1. **Tab 1: 💬 Enterprise Chat & Inspector**  
   - Real-time multi-agent conversation with quick-action demo buttons.  
   - Displays handling specialist agent pill (`Handled by: Leave Request Agent`), execution latency badge (`⚡ 480ms`), and RightAction outcome badge (`✅ APPROVED`, `⚠️ FLAGGED FOR REVIEW`, `🚫 BLOCKED VIOLATION`).  
   - Collapsible **Deep Trace** card inspecting retrieved chunks, similarity scores, and cited policy clauses.

2. **Tab 2: 👨‍💼 Manager Governance & HITL Review Inbox**  
   - Live queue of flagged action tickets requiring exception authorization.  
   - Inspects extracted JSON payload, cited rule, and flagging rationale.  
   - Interactive `Approve with Exception` (with mandatory managerial notes) and `Confirm Rejection` buttons.

3. **Tab 3: 🧪 Policy Sandbox & What-If Simulation**  
   - Dynamic sliders for broadband caps, meal per diems, lodging rates, and medical certificate thresholds.  
   - Simulates policy revisions over historical action logs with comparative shift bar charts.

4. **Tab 4: 📊 Observability & Cryptographic Audit Trail**  
   - Real-time KPI cards (Total Turns, Audited Actions, Compliance Rate, Pending Reviews, Avg Turn Latency).  
   - Real-time cryptographic integrity validator confirming `SHA-256` hash chain integrity.  
   - Searchable SQLite audit table with one-click `📥 Export Signed Audit Package (.CSV)` download.

---

## 🚀 Quickstart & Setup Guide

### 1. Clone Repository & Setup Environment
```bash
git clone https://github.com/amano2/miniBlue.git
cd miniBlue

# Create Python virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```
*(Alternatively, configure Google Gemini API credentials directly).*

### 3. Build Vector Database & Embeddings
```bash
python src/ingest.py
```

### 4. Launch Application

#### Streamlit Executive Portal:
```bash
streamlit run app/streamlit_app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

#### FastAPI Backend (REST & OpenAPI Swagger):
```bash
uvicorn api.main:app --port 8000 --reload
```
Interactive Swagger documentation available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

### 5. Run Automated Evaluation Suite
```bash
python eval/run_eval.py
```

---

## 📂 Repository File Structure

```
miniBlue/
├── data/
│   └── raw_docs/                  # Canonical corporate HR policy markdown documents
│       ├── leave_policy.md        # HR-POL-001 (Annual, Sick, Parental leave rules)
│       ├── reimbursement_policy.md# HR-POL-002 (Expense caps, Per Diem, Lodging)
│       ├── onboarding_faq.md      # HR-FAQ-003 (IT provisioning, payroll dates)
│       └── code_of_conduct.md     # HR-POL-004 (Whistleblower, anti-harassment)
├── src/
│   ├── config.py                  # Thresholds, model settings, and RRF constants
│   ├── db.py                      # SQLite persistence, HITL review queue & SHA-256 hash chaining
│   ├── generate.py                # Multi-tier LLM inference with provider fallback
│   ├── governance.py              # RightAction™ compliance evaluation engine
│   ├── ingest.py                  # Header-aware chunking, dense embeddings & FAISS index build
│   ├── memory.py                  # Multi-turn session memory with conversational action repair
│   ├── orchestrator.py            # Intent classification router with confidence thresholding
│   ├── pipeline.py                # Master orchestration connecting Chat, Agents, and Governance
│   ├── retrieve.py                # Hybrid FAISS (Dense) + BM25 (Sparse) with RRF fusion
│   ├── simulator.py               # What-If policy simulation & historical shift analysis
│   └── agents/
│       ├── policy_qa_agent.py     # Grounded policy Q&A agent with citations & refusal guardrail
│       ├── leave_agent.py         # Structured leave request agent with parameter repair
│       └── reimbursement_agent.py # Expense reimbursement agent with parameter repair
├── api/
│   └── main.py                    # FastAPI REST API endpoints (/chat, /actions, /simulate, etc.)
├── app/
│   └── streamlit_app.py           # 4-Tab Executive SaaS Portal & Observability Dashboard
├── eval/
│   ├── test_questions.json        # 15 Policy Q&A evaluation benchmark queries
│   ├── test_actions.json          # 10 Real-world action compliance & violation scenarios
│   └── run_eval.py                # Automated dual evaluation harness
├── requirements.txt               # Free & open-source Python dependencies
├── README.md                      # Comprehensive project documentation
└── GEMINI.md                      # Master engineering prompt & specification
```

---

## 🔒 Security & Data Integrity

- **Cryptographic Auditability**: Every governance decision is hashed via SHA-256 into a continuous cryptographic chain. Any manual manipulation of SQLite records breaks hash continuity and is flagged immediately by the observability console.
- **Zero Silent Actions**: Action agents have zero authority to commit records to the database; only the independent RightAction governance layer can sign and persist transactions.
- **Environment Confidentiality**: All credentials and API keys are stored strictly in untracked `.env` files protected by `.gitignore`.

---

## 👤 Author & Acknowledgments

- **Author**: [amano2](https://github.com/amano2)
- **Concept Inspiration**: Architecture inspired by **Larsen & Toubro Mindtree (LTM) BlueVerse** multi-agent orchestration and RightAction™ governance patterns.
