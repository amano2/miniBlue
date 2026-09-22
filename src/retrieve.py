"""Hybrid Retrieval module combining Dense FAISS Cosine Search and Sparse BM25.

Performs semantic search via sentence-transformers + FAISS and keyword search via BM25,
merging candidate rankings with Reciprocal Rank Fusion (RRF).
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
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def tokenize_text(text: str) -> list[str]:
    """Tokenize query string for BM25 matching."""
    return re.findall(r"\w+", text.lower())


class HybridRetriever:
    """Handles hybrid (Dense + BM25) query retrieval with Reciprocal Rank Fusion."""

    def __init__(
        self,
        index_path: Path = config.INDEX_PATH,
        metadata_path: Path = config.METADATA_PATH,
        bm25_path: Path = config.BM25_CORPUS_PATH,
        model_name: str = config.EMBEDDING_MODEL_NAME,
        similarity_threshold: float = config.SIMILARITY_THRESHOLD,
    ) -> None:
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.bm25_path = bm25_path
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold

        self._model: SentenceTransformer | None = None
        self._index: faiss.Index | None = None
        self._metadata: list[dict[str, Any]] | None = None
        self._bm25: BM25Okapi | None = None

    def reload(self) -> None:
        """Forces reloading of index and metadata from disk (used after dynamic document upload)."""
        self._index = None
        self._metadata = None
        self._bm25 = None
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        """Lazy-loads embedding model, FAISS index, chunk metadata, and BM25 index."""
        if self._model is None:
            logger.info(f"Loading retriever embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)

        if self._index is None:
            if not self.index_path.exists():
                raise FileNotFoundError(
                    f"FAISS index not found at {self.index_path}. Please run ingest.py first."
                )
            self._index = faiss.read_index(str(self.index_path))

        if self._metadata is None:
            if not self.metadata_path.exists():
                raise FileNotFoundError(
                    f"Metadata store not found at {self.metadata_path}. Please run ingest.py first."
                )
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

        if self._bm25 is None and self.bm25_path.exists():
            with open(self.bm25_path, "r", encoding="utf-8") as f:
                tokenized_corpus = json.load(f)
            self._bm25 = BM25Okapi(tokenized_corpus)

    def retrieve(
        self,
        query: str,
        k: int = config.TOP_K,
        use_hybrid: bool = True,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Retrieves top-k chunks using Hybrid Search (Dense + BM25 with RRF).

        Args:
            query: User question string.
            k: Number of final chunks to return.
            use_hybrid: If True, combines FAISS + BM25; otherwise pure dense search.

        Returns:
            Tuple of (retrieved_chunks, is_relevant).
        """
        if not query.strip():
            return [], False

        self._ensure_loaded()
        assert self._model is not None
        assert self._index is not None
        assert self._metadata is not None

        candidate_k = min(len(self._metadata), max(k * 3, 10))

        # 1. Dense Search (FAISS)
        query_embedding = self._model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        dense_scores, dense_indices = self._index.search(query_embedding.astype(np.float32), candidate_k)

        dense_top_scores = dense_scores[0]
        dense_top_indices = dense_indices[0]
        max_dense_score = float(dense_top_scores[0]) if len(dense_top_scores) > 0 else 0.0

        if not use_hybrid or self._bm25 is None:
            # Fallback to pure dense search
            is_relevant = max_dense_score >= self.similarity_threshold
            retrieved: list[dict[str, Any]] = []
            for score, idx in zip(dense_top_scores[:k], dense_top_indices[:k]):
                if idx == -1 or idx >= len(self._metadata):
                    continue
                meta = self._metadata[idx].copy()
                meta["score"] = round(float(score), 4)
                meta["dense_score"] = round(float(score), 4)
                retrieved.append(meta)
            return retrieved, is_relevant

        # 2. Sparse Search (BM25)
        query_tokens = tokenize_text(query)
        bm25_scores = self._bm25.get_scores(query_tokens)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:candidate_k]
        max_bm25_score = float(bm25_scores[bm25_top_indices[0]]) if len(bm25_top_indices) > 0 else 0.0

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_constant = config.RRF_K
        dense_weight = config.HYBRID_DENSE_WEIGHT
        sparse_weight = config.HYBRID_SPARSE_WEIGHT

        rrf_scores: dict[int, float] = {}
        dense_score_map: dict[int, float] = {}
        sparse_score_map: dict[int, float] = {}

        for rank, (idx, score) in enumerate(zip(dense_top_indices, dense_top_scores)):
            if idx == -1:
                continue
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (dense_weight * (1.0 / (rrf_constant + rank + 1)))
            dense_score_map[idx] = float(score)

        for rank, idx in enumerate(bm25_top_indices):
            if bm25_scores[idx] > 0:
                rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (sparse_weight * (1.0 / (rrf_constant + rank + 1)))
                sparse_score_map[idx] = float(bm25_scores[idx])

        # Sort candidate indices by merged RRF score
        sorted_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:k]

        # Guardrail check: Is the query relevant?
        # Relevant if dense cosine score is above threshold OR strong BM25 match exists
        is_relevant = (max_dense_score >= self.similarity_threshold) or (max_bm25_score > 3.0)

        retrieved_chunks: list[dict[str, Any]] = []
        for idx in sorted_indices:
            if idx >= len(self._metadata):
                continue
            meta = self._metadata[idx].copy()
            meta["score"] = round(dense_score_map.get(idx, max_dense_score), 4)
            meta["rrf_score"] = round(rrf_scores[idx], 6)
            meta["bm25_score"] = round(sparse_score_map.get(idx, 0.0), 3)
            retrieved_chunks.append(meta)

        return retrieved_chunks, is_relevant


# Singleton instance
retriever_instance = HybridRetriever()


def retrieve_relevant_chunks(
    query: str,
    k: int = config.TOP_K,
    use_hybrid: bool = True,
) -> tuple[list[dict[str, Any]], bool]:
    """Convenience function for hybrid retrieval."""
    return retriever_instance.retrieve(query, k=k, use_hybrid=use_hybrid)


if __name__ == "__main__":
    test_q = "HR-POL-002 $50 internet allowance"
    chunks, relevant = retrieve_relevant_chunks(test_q)
    print(f"Query: {test_q}")
    print(f"Is Relevant: {relevant}")
    for c in chunks:
        print(f"\n[Dense: {c.get('score')} | BM25: {c.get('bm25_score')} | RRF: {c.get('rrf_score')}]")
        print(f"Doc: {c['doc_name']} | File: {c['source_file']}")
        print(f"Snippet: {c['text'][:120]}...")
