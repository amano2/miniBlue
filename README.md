<div align="center">

# miniBlue — Agentic HR assistant

### Multi-agent orchestration with governed action-taking

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=white)](https://react.dev/)
[![Vite 8](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Store-green.svg?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

<p>
  Inspired by LTM's BlueVerse — specifically its multi-agent orchestration and RightAction governance concepts — implemented at a small, fully transparent scale for a single HR domain.
</p>

---

</div>

## What this is

A zero-cost, single-domain HR assistant that routes employee requests (policy questions, leave applications, expense claims) through specialist agents, validates every proposed action against retrieved policy rules before committing it, and logs every decision with a cryptographic hash chain.

The system demonstrates two architectural patterns drawn from LTM's BlueVerse ecosystem:

1. **Agent-to-agent orchestration** — an orchestrator classifies intent and delegates to the right specialist, each returning structured JSON rather than free-text hand-offs.
2. **RightAction-style governance** — no action agent can finalize a leave booking or reimbursement without passing through an independent compliance gate that cites the specific policy rule it relied on.

It is not a reproduction of commercial BlueVerse (300+ agents, proprietary Knowledge Fabric, multi-cloud studio). It applies the same two patterns at a scale one person can build and fully explain.

---

## System architecture

```
                                      [User request]
                                             │
                                             ▼
                       ┌───────────────────────────────────────────┐
                       │        Orchestrator agent router          │
                       │   (Intent classification + confidence)    │
                       └─────────────────────┬─────────────────────┘
                                             │
         ┌───────────────────────────────────┼───────────────────────────────────┐
         │                                   │                                   │
         ▼                                   ▼                                   ▼
┌──────────────────┐               ┌──────────────────┐               ┌──────────────────────┐
│ Policy Q&A agent │               │Leave action agent│               │ Reimbursement agent  │
│  (RAG retrieval) │               │(Field extraction)│               │  (Field extraction)  │
└────────┬─────────┘               └─────────┬────────┘               └──────────┬───────────┘
         │                                   │                                   │
         │                            Retrieve rules                      Retrieve caps
         │                            (FAISS + BM25)                      (FAISS + BM25)
         │                                   │                                   │
         │                                   └─────────────────┬─────────────────┘
         │                                                     ▼
         │                                     ┌───────────────────────────────┐
         │                                     │   RightAction governance gate │
         │                                     │ - Policy boundary check       │
         │                                     │ - APPROVE / FLAG / BLOCK      │
         │                                     │ - Mandatory rule citation     │
         │                                     └───────────────┬───────────────┘
         │                                                     │
         │                        ┌────────────────────────────┴────────────────────────────┐
         │                        ▼                                                         ▼
         │             [APPROVE / BLOCK]                                           [FLAG_FOR_REVIEW]
         │                        │                                                         │
         │                        │                                             ┌───────────▼───────────┐
         │                        │                                             │  Manager HITL inbox   │
         │                        │                                             │ (Override / reject    │
         │                        │                                             │  with audited notes)  │
         │                        │                                             └───────────┬───────────┘
         │                        │                                                         │
         │                        └────────────────────────────┬────────────────────────────┘
         │                                                     ▼
         │                                     ┌───────────────────────────────┐
         │                                     │   Tamper-evident audit DB     │
         │                                     │  (SQLite + SHA-256 chain)     │
         │                                     │  ↕ Supabase PostgreSQL sync   │
         │                                     └───────────────┬───────────────┘
         └─────────────────────────────────────────────────────┼────────────────────────────┘
                                                               ▼
                                              ┌─────────────────────────────────┐
                                              │   React + Vite SaaS console     │
                                              │ (9 pages, RBAC-gated routing)   │
                                              └─────────────────────────────────┘
```

---

## Capabilities

- **Intent routing** — single Gemini call classifies into `policy_question`, `leave_request`, `reimbursement_claim`, `escalation`, or `other` with a confidence score; low confidence routes to human escalation.
- **Grounded Q&A** — hybrid FAISS (dense) + BM25 (sparse) retrieval with reciprocal rank fusion, generating answers only from retrieved policy chunks with inline citations. Out-of-scope questions are refused.
- **Structured field extraction** — leave and reimbursement agents extract dates, amounts, categories via constrained JSON prompts, then check them against retrieved policy rules.
- **Governed action-taking** — every proposed action passes through an independent governance layer that returns `APPROVE`, `FLAG_FOR_REVIEW`, or `BLOCK` with the exact rule cited. No bypass path exists.
- **Human-in-the-loop review** — flagged actions enter a manager inbox for exception override or rejection with mandatory notes.
- **What-if policy simulation** — adjust thresholds (caps, notice periods) and project compliance/financial shifts over historical data.
- **Cryptographic audit trail** — SHA-256 hash chaining across all action records; any tampering breaks the chain and is flagged.
- **Cloud sync** — Supabase PostgreSQL mirrors action logs, conversation history, and review events for persistence beyond the local SQLite file.
- **JWT authentication with RBAC** — four roles (employee, manager, admin, auditor) controlling page visibility and API access.

---

## Tech stack

All zero-cost:

| Layer | Tool | Why |
|---|---|---|
| LLM | Google Gemini API via OpenRouter (free tier) | Structured JSON output, high instruction-following |
| Dense embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`), local | 384-dim vectors, no API calls |
| Sparse search | `rank-bm25` (`BM25Okapi`) | Exact matching for policy codes, amounts, proper nouns |
| Vector index | FAISS (`IndexFlatIP`) | In-memory cosine similarity search |
| Rank fusion | Reciprocal Rank Fusion (RRF, k=60) | Balances dense and sparse rankings |
| Orchestration | Plain Python router | Fully inspectable, no opaque framework |
| Audit persistence | SQLite (`db/actions.db`) + SHA-256 hash chain | Local ACID with tamper evidence |
| Cloud sync | Supabase PostgreSQL | Mirrors action logs, conversations, reviews |
| Auth | JWT (PyJWT + bcrypt) | 4-role RBAC: employee, manager, admin, auditor |
| Backend API | FastAPI + Uvicorn | Async endpoints with OpenAPI docs |
| Frontend | React 19 + Vite 8 + Tailwind CSS | 9-page SaaS console with RBAC-gated routing |
| State management | Zustand + TanStack Query | Lightweight client state and server cache |
| Icons | Lucide React | Consistent icon set |

---

## Pages

The frontend is a React SPA with role-based access control. Each page is visible only to the roles listed:

| Page | Path | Roles | Purpose |
|---|---|---|---|
| Chat assistant | `/chat` | All | Multi-agent conversation with governance badges and reasoning traces |
| My requests | `/requests` | All | Personal action ledger — submitted leave and reimbursement requests |
| Observability | `/dashboard` | Manager, Admin, Auditor | KPI cards, intent distribution, governance decision breakdown |
| Review inbox | `/reviews` | Manager, Admin | HITL queue for flagged actions; approve-with-exception or reject |
| Policy simulator | `/simulator` | Admin | What-if sandbox for threshold adjustments over historical data |
| Cryptographic audit | `/audit` | Admin, Auditor | Hash-chain integrity verification, searchable audit log, CSV export |
| Policy library | `/policies` | All | Browse the 4 ground-truth HR policy documents |
| Compliance eval | `/evaluation` | Admin, Auditor | Run and inspect automated evaluation benchmarks |
| User management | `/users` | Admin | Manage user accounts, roles, and departments |

---

## Ground-truth HR policies

The system is grounded in four documents in `data/raw_docs/`:

| Document | Key constraints |
|---|---|
| **Leave policy** | 20 annual leave days/year; >2 consecutive days requires 2 weeks notice; ≥3 sick days requires medical certificate within 48 hours; 16 weeks paid parental leave |
| **Reimbursement policy** | Broadband capped at \$50/month; ergonomic stipend \$300 one-time in first 90 days; lodging \$180/night Tier 1, \$120/night Tier 2; meals \$75/day Tier 1, \$50/day Tier 2; 30-day submission window (31–60 days → FLAG, >60 days → BLOCK); personal alcohol/entertainment → BLOCK |
| **Onboarding FAQ** | IT provisioning, benefits enrollment, payroll dates (15th & 30th), probation timelines |
| **Code of conduct** | Conflict of interest, anti-harassment, whistleblower reporting, vendor gift limit (≤\$50) |

---

## Evaluation scorecard

Evaluated via `eval/run_eval.py` over 15 policy questions and 10 action governance scenarios including deliberate policy violations:

```
================================================================================
  Agentic system scorecard
================================================================================
1. Orchestrator intent routing accuracy:   100.0%  (10/10)
2. Governance decision accuracy:           100.0%  (10/10)
3. Deliberate violation catch rate:        100.0%   (6/6)
4. Policy Q&A groundedness & citations:     80.0%   (8/10)
5. Out-of-scope question refusal rate:      80.0%   (4/5)
================================================================================
```

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/amano2/miniBlue.git
cd miniBlue

# Python backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt

# React frontend
cd web
npm install
cd ..
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your keys:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Optional — cloud sync
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Build the vector index

```bash
python src/ingest.py
```

### 4. Start the servers

```bash
# Terminal 1 — backend
uvicorn api.main:app --port 8000 --reload

# Terminal 2 — frontend
cd web
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

**Default demo accounts** (seeded on first backend start):

| Username | Password | Role |
|---|---|---|
| `alice` | `password123` | employee |
| `bob` | `password123` | manager |
| `charlie` | `password123` | admin |
| `diana` | `password123` | auditor |

### 5. Run evaluations

```bash
python eval/run_eval.py
```

Swagger API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Repository structure

```
miniBlue/
├── api/
│   ├── main.py                       # FastAPI app, CORS, router mounting
│   ├── auth.py                       # JWT token creation & verification
│   ├── db.py                         # SQLite connection & Supabase sync calls
│   ├── schemas.py                    # Pydantic request/response models
│   ├── seed.py                       # Default user seeding on startup
│   ├── supabase_client.py            # Supabase REST API sync functions
│   └── routers/
│       ├── auth.py                   # /login, /register, /me
│       ├── chat.py                   # /chat (orchestrator → agent → governance)
│       ├── actions.py                # /actions (CRUD for action ledger)
│       ├── reviews.py                # /reviews (HITL manager queue)
│       ├── simulate.py              # /simulate (what-if policy sandbox)
│       ├── audit.py                  # /audit (hash-chain verification)
│       ├── policies.py               # /policies (raw document retrieval)
│       ├── eval.py                   # /eval (run evaluation harness)
│       ├── telemetry.py              # /telemetry (latency & token metrics)
│       └── users.py                  # /users (admin user management)
├── src/
│   ├── config.py                     # Model names, k, thresholds, confidence cutoffs
│   ├── db.py                         # SQLite persistence & SHA-256 hash chaining
│   ├── generate.py                   # LLM inference with provider fallback
│   ├── governance.py                 # RightAction compliance: APPROVE/FLAG/BLOCK
│   ├── ingest.py                     # Chunking, embedding, FAISS index build
│   ├── memory.py                     # Session state (last N turns per session_id)
│   ├── orchestrator.py               # Intent classification + confidence routing
│   ├── pipeline.py                   # Master pipeline: chat → agent → governance
│   ├── retrieve.py                   # Hybrid FAISS + BM25 with RRF fusion
│   ├── simulator.py                  # What-if policy simulation engine
│   └── agents/
│       ├── policy_qa_agent.py        # RAG Q&A with citations and refusal guard
│       ├── leave_agent.py            # Structured leave field extraction
│       └── reimbursement_agent.py    # Structured expense field extraction
├── web/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── App.tsx                   # Router with RBAC-gated routes
│       ├── main.tsx                  # React entry point
│       ├── index.css                 # Tailwind base + custom design tokens
│       ├── lib/
│       │   ├── api.ts                # Fetch wrapper for backend API
│       │   ├── store.ts              # Zustand stores (auth, UI state)
│       │   └── supabase.ts           # Supabase client initialization
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Header.tsx
│       │   │   └── Sidebar.tsx
│       │   └── common/
│       │       └── GovernanceReceipt.tsx
│       ├── pages/
│       │   ├── LoginPage.tsx
│       │   ├── ChatPage.tsx
│       │   ├── RequestsPage.tsx
│       │   ├── DashboardPage.tsx
│       │   ├── ReviewsPage.tsx
│       │   ├── SimulatorPage.tsx
│       │   ├── AuditPage.tsx
│       │   ├── PoliciesPage.tsx
│       │   ├── EvaluationPage.tsx
│       │   └── UsersPage.tsx
│       └── types/
│           └── index.ts
├── data/
│   └── raw_docs/                     # 4 canonical HR policy documents
│       ├── leave_policy.md
│       ├── reimbursement_policy.md
│       ├── onboarding_faq.md
│       └── code_of_conduct.md
├── db/
│   └── .gitkeep
├── eval/
│   ├── test_questions.json           # 15 policy Q&A benchmark queries
│   ├── test_actions.json             # 10 action scenarios incl. violations
│   └── run_eval.py                   # Automated dual evaluation harness
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Design notes

**Typography**: Sora (display headings), Plus Jakarta Sans (body), JetBrains Mono (monospace/data). These were chosen for their optical weight contrast — Sora's geometric forms anchor headings while Plus Jakarta Sans keeps body text readable at small sizes.

**Palette**: Deep obsidian backgrounds (`#0a0a0f` → `#15151e`) with a sovereign amber accent (`#d4a853`). The palette is deliberately restrained — amber is spent only on the active nav state, governance decision badges, and the governance receipt card. Everything else stays neutral.

**Governance receipt**: The one intentionally bold UI element. When an action is approved, flagged, or blocked, a receipt card appears inline in the chat showing the decision, the rule cited, and the extracted fields. This is the single place where visual weight is concentrated.

---

## Security

- **JWT authentication** — bcrypt-hashed passwords, short-lived tokens, role claims embedded in the JWT payload.
- **RBAC routing** — both API endpoints and frontend routes enforce role checks; the frontend `ProtectedRoute` wrapper redirects unauthorized roles.
- **Cryptographic audit chain** — every governance decision is SHA-256 hashed with the previous record's hash, creating a tamper-evident chain. The audit page verifies chain integrity on demand.
- **No silent actions** — action agents cannot commit to the database; only the governance layer can persist decisions.
- **Environment secrets** — API keys stored in `.env`, excluded from version control via `.gitignore`.

---

## Author

[amano2](https://github.com/amano2)

Architecture inspired by Larsen & Toubro Mindtree (LTM) BlueVerse multi-agent orchestration and RightAction governance patterns.
