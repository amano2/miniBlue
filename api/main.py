"""FastAPI Application for miniBlue Enterprise Agentic Platform & RightAction Governance.

Serves all REST API contracts defined in TRD §4 under `/api/v1` and maintains
backwards compatibility for root-level legacy endpoints.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from api.routers import (
    actions,
    audit,
    auth,
    chat,
    eval as eval_router,
    policies,
    reviews,
    simulate,
    telemetry,
    users,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="miniBlue — Enterprise Agentic HR Platform & RightAction Governance",
    description=(
        "Production-grade Multi-Agent Orchestration & RightAction Governance Platform.\n\n"
        "Features:\n"
        "- Deterministic Role-Based Access Control (RBAC)\n"
        "- Specialist Agents for Policy Q&A, Leave, & Reimbursements\n"
        "- Cryptographically Hash-Chained Action Ledger (SHA-256)\n"
        "- Human-in-the-Loop (HITL) Manager Review Queue\n"
        "- Counterfactual What-If Policy Simulator\n"
        "- Live Observability & Automated Compliance Scorecards"
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount modular routers under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(actions.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(simulate.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(telemetry.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(eval_router.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")

# Also mount under root for backwards compatibility
app.include_router(chat.router)
app.include_router(actions.router)
app.include_router(reviews.router)
app.include_router(simulate.router)
app.include_router(audit.router)
app.include_router(telemetry.router)


@app.get("/health", tags=["System Health"])
def health_check() -> dict[str, Any]:
    """Liveness probe, index readiness, and LLM configuration status."""
    faiss_path = config.INDEX_PATH
    index_status = "ready" if faiss_path.exists() else "missing"


    return {
        "status": "healthy",
        "version": "3.0.0",
        "index_status": index_status,
        "llm_provider": "gemini" if config.GEMINI_API_KEY else "local_fallback",
        "faiss_index_exists": faiss_path.exists(),
        "database": "SQLite (WAL enabled)",
    }


@app.get("/", tags=["Root"])
def root_info() -> dict[str, Any]:
    """API Discovery and System Manifest."""
    return {
        "name": "miniBlue Enterprise Agentic Platform",
        "version": "3.0.0",
        "docs": "/docs",
        "api_v1_prefix": "/api/v1",
        "demo_accounts": [
            {"role": "employee", "email": "employee@miniblue.dev"},
            {"role": "manager", "email": "manager@miniblue.dev"},
            {"role": "admin", "email": "admin@miniblue.dev"},
            {"role": "auditor", "email": "auditor@miniblue.dev"},
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
