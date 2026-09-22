"""Policy Q&A Specialist Agent.

Performs RAG retrieval against company HR documents and generates strictly grounded answers
with document citations and refusal guardrails.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

# Ensure project root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import config
from src.retrieve import retrieve_relevant_chunks
from src.generate import generate_answer, REFUSAL_RESPONSE

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def handle_policy_qa(query: str, session_id: str = "default") -> dict[str, Any]:
    """Processes general HR policy questions.

    Returns:
        Dict: {"response": str, "sources": list, "refused": bool, "action_taken": None, "governance_decision": None}
    """
    clean_query = query.strip()
    if not clean_query:
        return {
            "response": "Please enter a valid policy question.",
            "sources": [],
            "refused": True,
            "action_taken": None,
            "governance_decision": None,
        }

    retrieved_chunks, is_relevant = retrieve_relevant_chunks(clean_query, k=config.TOP_K)

    if not is_relevant or not retrieved_chunks:
        return {
            "response": REFUSAL_RESPONSE,
            "sources": retrieved_chunks,
            "refused": True,
            "action_taken": None,
            "governance_decision": None,
        }

    try:
        raw_answer = generate_answer(clean_query, retrieved_chunks)
        is_refusal = REFUSAL_RESPONSE.lower() in raw_answer.lower()
        return {
            "response": raw_answer,
            "sources": retrieved_chunks,
            "refused": is_refusal,
            "action_taken": None,
            "governance_decision": None,
        }
    except Exception as e:
        logger.error(f"Policy Q&A generation failed: {e}")
        return {
            "response": f"Error retrieving policy answer: {str(e)}",
            "sources": retrieved_chunks,
            "refused": True,
            "action_taken": None,
            "governance_decision": None,
        }
