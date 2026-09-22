"""Configuration module for HR Policy RAG Assistant.

Contains all hyperparameters, file paths, embedding models, and API configurations.
Values can be overridden via environment variables or .env file.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load environment variables from .env file if present
load_dotenv()

# Base directories
BASE_DIR: Path = ROOT_DIR
DATA_DIR: Path = BASE_DIR / "data"
RAW_DOCS_DIR: Path = DATA_DIR / "raw_docs"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"

# Vector Store, BM25 and Metadata Persistence Paths
INDEX_PATH: Path = PROCESSED_DATA_DIR / "faiss_index.bin"
METADATA_PATH: Path = PROCESSED_DATA_DIR / "chunks_metadata.json"
BM25_CORPUS_PATH: Path = PROCESSED_DATA_DIR / "bm25_corpus.json"

# Chunking Configuration
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

# Embedding Model (Sentence Transformers - Local & Free)
EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
EMBEDDING_DIMENSION: int = 384

# Retrieval Configuration
TOP_K: int = 3
# Minimum cosine similarity threshold for considering retrieved chunks relevant
SIMILARITY_THRESHOLD: float = 0.35  # Strict cosine threshold to reliably refuse out-of-scope inquiries
# Hybrid search settings (Reciprocal Rank Fusion constant k)
RRF_K: int = 60
# Weight between Dense (FAISS) and Sparse (BM25)
HYBRID_DENSE_WEIGHT: float = 0.7
HYBRID_SPARSE_WEIGHT: float = 0.3

# LLM Generation Configuration (OpenRouter & Gemini free tier supported)
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Fallback direct Gemini API Key
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
