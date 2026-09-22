"""Document ingestion and multi-index pipeline.

Reads source HR policy documents across multiple formats (.md, .txt, .pdf, .docx),
chunks text preserving structure, generates local embeddings with sentence-transformers,
builds a FAISS IndexFlatIP (dense cosine index), builds a tokenized BM25 sparse index,
and persists all index artifacts.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts text content from a PDF document using pypdf."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(file_path))
        text_parts = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text.strip())
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"Error reading PDF file {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: Path) -> str:
    """Extracts text content from a Microsoft Word (.docx) document."""
    try:
        from docx import Document

        doc = Document(str(file_path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        logger.error(f"Error reading DOCX file {file_path}: {e}")
        return ""


def tokenize_text(text: str) -> list[str]:
    """Simple regex word tokenizer for BM25 search."""
    return re.findall(r"\w+", text.lower())


def chunk_text(
    text: str,
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> list[str]:
    """Splits a document text into overlapping chunks respecting paragraph/line boundaries.

    Args:
        text: The source text content.
        chunk_size: Target character count per chunk.
        chunk_overlap: Overlapping character count between consecutive chunks.

    Returns:
        A list of string chunks.
    """
    if not text.strip():
        return []

    # Split by double newline to preserve paragraph coherence
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current_chunk = ""

    for para in paragraphs:
        cleaned_para = para.strip()
        if not cleaned_para:
            continue

        if len(current_chunk) + len(cleaned_para) + 2 <= chunk_size:
            if current_chunk:
                current_chunk += "\n\n" + cleaned_para
            else:
                current_chunk = cleaned_para
        else:
            if current_chunk:
                chunks.append(current_chunk)
                if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                    overlap_seed = current_chunk[-chunk_overlap:]
                    current_chunk = overlap_seed + "\n\n" + cleaned_para
                else:
                    current_chunk = cleaned_para
            else:
                start = 0
                while start < len(cleaned_para):
                    end = start + chunk_size
                    chunks.append(cleaned_para[start:end])
                    start += chunk_size - chunk_overlap
                current_chunk = ""

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def load_raw_documents(docs_dir: Path = config.RAW_DOCS_DIR) -> list[dict[str, Any]]:
    """Loads all supported documents (.md, .txt, .pdf, .docx) from raw docs directory."""
    documents: list[dict[str, Any]] = []
    if not docs_dir.exists():
        logger.warning(f"Raw docs directory does not exist: {docs_dir}")
        return documents

    for file_path in sorted(docs_dir.glob("*.*")):
        suffix = file_path.suffix.lower()
        content = ""

        if suffix in [".md", ".txt", ".markdown"]:
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to read text file {file_path}: {e}")
        elif suffix == ".pdf":
            content = extract_text_from_pdf(file_path)
        elif suffix == ".docx":
            content = extract_text_from_docx(file_path)

        if content.strip():
            doc_title = file_path.stem.replace("_", " ").replace("-", " ").title()
            documents.append(
                {
                    "doc_name": doc_title,
                    "source_file": file_path.name,
                    "content": content,
                }
            )
            logger.info(f"Loaded {suffix.upper()} document: {file_path.name} ({len(content)} chars)")

    return documents


def build_and_save_index(
    docs_dir: Path = config.RAW_DOCS_DIR,
    index_path: Path = config.INDEX_PATH,
    metadata_path: Path = config.METADATA_PATH,
    bm25_path: Path = config.BM25_CORPUS_PATH,
    model_name: str = config.EMBEDDING_MODEL_NAME,
) -> int:
    """End-to-end ingestion: chunks documents, builds FAISS dense & BM25 sparse indexes, and saves to disk."""
    logger.info("Starting multi-index ingestion pipeline...")
    docs = load_raw_documents(docs_dir)
    if not docs:
        raise ValueError(f"No documents found in {docs_dir}")

    # Create chunks and metadata
    all_chunks: list[str] = []
    metadata_store: list[dict[str, Any]] = []
    bm25_corpus: list[list[str]] = []
    chunk_counter = 0

    for doc in docs:
        chunks = chunk_text(doc["content"])
        for idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            metadata_store.append(
                {
                    "chunk_id": chunk_counter,
                    "doc_name": doc["doc_name"],
                    "source_file": doc["source_file"],
                    "chunk_index": idx,
                    "text": chunk,
                }
            )
            bm25_corpus.append(tokenize_text(chunk))
            chunk_counter += 1

    logger.info(f"Total chunks created: {len(all_chunks)}")

    # 1. Dense Embeddings via SentenceTransformer
    logger.info(f"Loading local embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    embeddings = model.encode(all_chunks, show_progress_bar=False, convert_to_numpy=True)

    # Normalize vectors for Cosine Similarity (Inner Product on unit vectors)
    faiss.normalize_L2(embeddings)
    embedding_dim = embeddings.shape[1]

    logger.info(f"Building FAISS IndexFlatIP (dim={embedding_dim})...")
    index = faiss.IndexFlatIP(embedding_dim)
    index.add(embeddings.astype(np.float32))

    # Ensure output directory exists
    config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Persist FAISS index, metadata, and tokenized BM25 corpus
    faiss.write_index(index, str(index_path))
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_store, f, indent=2, ensure_ascii=False)
    with open(bm25_path, "w", encoding="utf-8") as f:
        json.dump(bm25_corpus, f, ensure_ascii=False)

    logger.info(f"Saved FAISS index to {index_path}")
    logger.info(f"Saved BM25 corpus to {bm25_path}")
    logger.info(f"Saved metadata to {metadata_path}")
    return len(all_chunks)


if __name__ == "__main__":
    count = build_and_save_index()
    print(f"\nMulti-index ingestion completed successfully! Total indexed chunks: {count}")
