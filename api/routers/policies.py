"""Policy Knowledge Base & Ingestion Router.

Endpoints:
- GET  /api/v1/policies (list official HR policy documents)
- GET  /api/v1/policies/{doc_id} (view full policy text and indexed chunks)
- POST /api/v1/policies/reingest (rebuild dense FAISS + sparse BM25 multi-indices)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import get_current_user, require_role
from api.db import get_db_connection
from api.schemas import PolicyDocOut
from api.seed import seed_policy_docs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["Policy Management"])

RAW_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw_docs"


@router.get("", response_model=list[PolicyDocOut])
def list_policies(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[PolicyDocOut]:
    """Lists all official corporate HR policies registered in the system."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT doc_id, title, filename, version, chunk_count
        FROM policy_docs
        ORDER BY doc_id ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        PolicyDocOut(
            doc_id=r["doc_id"],
            title=r["title"],
            filename=r["filename"],
            version=r["version"],
            chunk_count=r["chunk_count"],
        )
        for r in rows
    ]


@router.get("/{doc_id}", response_model=dict)
def get_policy_detail(
    doc_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Retrieves full text of a policy document and its structural RAG chunks."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT doc_id, title, filename, version, chunk_count, full_text
        FROM policy_docs
        WHERE doc_id = ?
        """,
        (doc_id,),
    )
    doc = cursor.fetchone()

    if not doc:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DOC_NOT_FOUND", "message": f"Policy '{doc_id}' not found."}},
        )

    # Chunks
    cursor.execute(
        """
        SELECT chunk_id, section, heading_path, text
        FROM policy_chunks
        WHERE doc_id = ?
        ORDER BY chunk_id ASC
        """,
        (doc_id,),
    )
    chunks = [dict(c) for c in cursor.fetchall()]
    conn.close()

    full_text = doc["full_text"] or ""
    if not full_text:
        file_path = RAW_DOCS_DIR / doc["filename"]
        if file_path.exists():
            full_text = file_path.read_text(encoding="utf-8")

    return {
        "doc_id": doc["doc_id"],
        "title": doc["title"],
        "filename": doc["filename"],
        "version": doc["version"],
        "chunk_count": doc["chunk_count"],
        "content": full_text,
        "chunks": chunks,
    }


@router.post("/reingest", response_model=dict)
def reingest_policies(
    current_user: dict[str, Any] = Depends(require_role(["admin"])),
) -> dict:
    """Rebuilds FAISS dense vector index and BM25 sparse index from raw documents.

    Also synchronizes policy_docs and policy_chunks in SQLite.
    """
    from src.ingest import build_and_save_index

    try:

        indexed_count = build_and_save_index()
        seed_policy_docs()
        return {
            "success": True,
            "chunks_indexed": indexed_count,
            "message": f"Successfully re-indexed {indexed_count} chunks into hybrid dense+sparse vector store.",
        }
    except Exception as e:
        logger.error(f"Reingestion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "REINGESTION_FAILED", "message": str(e)}},
        )
