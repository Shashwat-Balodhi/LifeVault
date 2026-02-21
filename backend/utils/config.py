"""
LifeVault Configuration Module
-------------------------------
Centralizes all configuration from environment variables.
Loads .env file once; all other modules import from here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # lifevault/
load_dotenv(PROJECT_ROOT / ".env")

# ── Paths ─────────────────────────────────────────────────────────────────────
WATCH_FOLDER = os.getenv("WATCH_FOLDER", str(PROJECT_ROOT / "sample_files"))
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(PROJECT_ROOT / "data" / "chroma_db"))

# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ── Server ────────────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ── Search ────────────────────────────────────────────────────────────────────
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "10"))

# ── Model names (loaded once at startup) ──────────────────────────────────────
CLIP_MODEL_NAME = os.getenv("CLIP_MODEL_NAME", "ViT-B-32")
CLIP_PRETRAINED = os.getenv("CLIP_PRETRAINED", "laion2b_s34b_b79k")
SENTENCE_MODEL_NAME = os.getenv("SENTENCE_MODEL_NAME", "all-MiniLM-L6-v2")

# ── Supported file types ─────────────────────────────────────────────────────
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}
ALL_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS

# ── ChromaDB collection name ─────────────────────────────────────────────────
COLLECTION_NAME = "lifevault"
