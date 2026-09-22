"""Generation module for HR Policy RAG Assistant.

Supports grounded generation, real-time token streaming, and multi-turn query rewriting.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Generator

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from openai import OpenAI
from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Standard refusal text mandated by system instructions
REFUSAL_RESPONSE = "I don't have enough information in the policy documents to answer that."

SYSTEM_PROMPT_TEMPLATE = """You are an HR policy assistant. Answer the user's question using ONLY the
context provided below. Do not use any outside knowledge.

If the answer cannot be found in the context, respond exactly with:
"I don't have enough information in the policy documents to answer that."

Always end your answer with a "Source:" line naming which document(s) the
answer came from.

Context:
{retrieved_chunks}

Question: {user_query}"""


def format_context(retrieved_chunks: list[dict[str, Any]]) -> str:
    """Formats retrieved document chunks into clean readable context string for prompt."""
    if not retrieved_chunks:
        return "No relevant context found."

    formatted_sections: list[str] = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        doc_name = chunk.get("doc_name", "Unknown Document")
        source_file = chunk.get("source_file", "unknown")
        text = chunk.get("text", "").strip()
        formatted_sections.append(
            f"--- Document {idx}: {doc_name} (File: {source_file}) ---\n{text}"
        )

    return "\n\n".join(formatted_sections)


def get_llm_client() -> tuple[OpenAI, str]:
    """Initializes and returns the OpenAI client configured for OpenRouter, along with model name."""
    api_key = config.OPENROUTER_API_KEY or config.GEMINI_API_KEY
    if not api_key:
        raise ValueError(
            "API Key not found. Please set OPENROUTER_API_KEY in your .env file or environment."
        )

    base_url = config.OPENROUTER_BASE_URL
    model_name = config.OPENROUTER_MODEL

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )
    return client, model_name


def condense_query_with_history(
    query: str,
    history: list[dict[str, Any]] | None = None,
    client: OpenAI | None = None,
    model_name: str | None = None,
) -> str:
    """Rewrites a follow-up query into a standalone search query if conversational history exists."""
    clean_query = query.strip()
    if not history or len(history) == 0:
        return clean_query

    # Extract last 2-4 conversation turns
    recent_history = history[-4:]
    history_text = ""
    for msg in recent_history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        content = msg.get("content", "")[:250]
        history_text += f"{role}: {content}\n"

    condensation_prompt = f"""Given the conversation history and the latest user question, rewrite the latest question to be a complete, standalone question suitable for searching an HR policy knowledge base. Do not answer the question; only return the rewritten standalone question.

Chat History:
{history_text}

Latest Question: {clean_query}
Standalone Question:"""

    try:
        if client is None:
            client, detected_model = get_llm_client()
            if model_name is None:
                model_name = detected_model

        response = client.chat.completions.create(
            model=model_name or config.OPENROUTER_MODEL,
            messages=[{"role": "user", "content": condensation_prompt}],
            temperature=0.0,
            max_tokens=60,
        )
        condensed = response.choices[0].message.content
        if condensed and condensed.strip():
            logger.info(f"Query condensed from '{query}' -> '{condensed.strip()}'")
            return condensed.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"Failed to condense query with history, using original query: {e}")

    return clean_query


def generate_answer(
    query: str,
    retrieved_chunks: list[dict[str, Any]],
    client: OpenAI | None = None,
    model_name: str | None = None,
) -> str:
    """Calls LLM with grounded prompt and returns generated answer."""
    if client is None or model_name is None:
        client, detected_model = get_llm_client()
        if model_name is None:
            model_name = detected_model

    formatted_context = format_context(retrieved_chunks)
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        retrieved_chunks=formatted_context,
        user_query=query.strip(),
    )

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        if not response or not getattr(response, "choices", None) or len(response.choices) == 0:
            return REFUSAL_RESPONSE

        first_choice = response.choices[0]
        message = getattr(first_choice, "message", None)
        if message is None:
            return REFUSAL_RESPONSE

        content = getattr(message, "content", None)
        if not content and hasattr(message, "reasoning"):
            content = getattr(message, "reasoning", None)

        if content is None or not str(content).strip():
            return REFUSAL_RESPONSE

        return str(content).strip()

    except Exception as e:
        logger.warning(f"Error calling LLM API ({e}); extracting grounded answer from top retrieved chunks.")
        if not retrieved_chunks:
            return REFUSAL_RESPONSE
        top_chunk = retrieved_chunks[0]
        top_text = top_chunk.get("text", "").strip()
        doc_name = top_chunk.get("doc_name", "Official HR Policy")
        return f"Based on company policy:\n\n{top_text}\n\nSource: {doc_name}"


def generate_answer_stream(
    query: str,
    retrieved_chunks: list[dict[str, Any]],
    client: OpenAI | None = None,
    model_name: str | None = None,
) -> Generator[str, None, None]:
    """Generates an answer from the LLM, yielding tokens in real time for UI streaming."""
    if client is None or model_name is None:
        client, detected_model = get_llm_client()
        if model_name is None:
            model_name = detected_model

    formatted_context = format_context(retrieved_chunks)
    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        retrieved_chunks=formatted_context,
        user_query=query.strip(),
    )

    try:
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = getattr(delta, "content", None)
            if content:
                yield content

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        yield f"Error generating answer: {str(e)}"
