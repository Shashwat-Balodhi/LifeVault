"""
LifeVault — FastAPI Backend
=============================
Main application entry point. Orchestrates:
    - Model loading at startup
    - File watching and ingestion pipeline
    - RESTful API for semantic search
    - Startup scan of existing files

Run with:
    uvicorn backend.main:app --reload --port 8000
"""

import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# ── Ensure project root is in path ───────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.config import (
    WATCH_FOLDER, API_HOST, API_PORT, DEFAULT_TOP_K, 
    IMAGE_EXTENSIONS, DOCUMENT_EXTENSIONS,
)
from backend.utils.logger import get_logger
from backend.ai.embedder import EmbedderService
from backend.ai.vector_store import VectorStore
from backend.ai.query_engine import QueryEngine
from backend.ai.auto_tagger import auto_tag_image
from backend.ingestion.metadata_extractor import extract_file_metadata, extract_exif_metadata
from backend.ingestion.image_processor import process_image
from backend.ingestion.doc_processor import process_document
from backend.ingestion.file_watcher import FileWatcher

logger = get_logger(__name__)

# ── Global service instances (loaded once) ────────────────────────────────────
embedder: Optional[EmbedderService] = None
vector_store: Optional[VectorStore] = None
query_engine: Optional[QueryEngine] = None
file_watcher: Optional[FileWatcher] = None


# =============================================================================
# INGESTION PIPELINE
# =============================================================================

def ingest_file(file_path: str):
    """
    Master ingestion function: process a single file end-to-end.
    Called by the file watcher for each new/modified file.
    """
    global embedder, vector_store

    file_path = str(Path(file_path).resolve())
    ext = Path(file_path).suffix.lower()

    # Skip if already indexed (check modified date)
    if vector_store.is_file_indexed(file_path):
        logger.debug(f"Skipping already indexed file: {file_path}")
        return

    # ── Extract metadata ─────────────────────────────────────────────────
    metadata = extract_file_metadata(file_path)

    # ── Process based on file type ───────────────────────────────────────
    if ext in IMAGE_EXTENSIONS:
        # Add EXIF metadata
        exif = extract_exif_metadata(file_path)
        metadata.update(exif)

        # Generate CLIP embedding
        result = process_image(
            file_path,
            clip_model=embedder.clip_model,
            clip_preprocess=embedder.clip_preprocess,
            clip_tokenizer=embedder.clip_tokenizer,
            ocr_reader=embedder.ocr_reader,
        )

        if not result["embedding"]:
            logger.warning(f"No embedding generated for {file_path}")
            return

        # Auto-tag the image
        tags = auto_tag_image(
            file_path,
            clip_model=embedder.clip_model,
            clip_preprocess=embedder.clip_preprocess,
            clip_tokenizer=embedder.clip_tokenizer,
            device=embedder.device,
        )
        if tags:
            metadata["auto_tags"] = ", ".join(t[0] for t in tags)
            metadata["top_tag"] = tags[0][0]
            metadata["top_tag_score"] = tags[0][1]

        # Store in vector DB
        vector_store.upsert_image(
            file_path=file_path,
            embedding=result["embedding"],
            metadata=metadata,
            text_content=result.get("text_content", ""),
        )

    elif ext in DOCUMENT_EXTENSIONS:
        # Generate sentence embedding
        result = process_document(
            file_path,
            sentence_model=embedder.sentence_model,
        )

        if not result["embedding"]:
            logger.warning(f"No embedding generated for {file_path}")
            return

        # Store in vector DB
        vector_store.upsert_document(
            file_path=file_path,
            embedding=result["embedding"],
            metadata=metadata,
            text_content=result.get("text_content", ""),
        )

    logger.info(f"✅ Indexed: {Path(file_path).name}")


# =============================================================================
# APPLICATION LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    global embedder, vector_store, query_engine, file_watcher

    logger.info("=" * 60)
    logger.info("🧠 LifeVault — Starting up...")
    logger.info("=" * 60)

    # 1. Load AI models
    embedder = EmbedderService()
    embedder.load_all_models()

    # 2. Initialize vector store
    vector_store = VectorStore()

    # 3. Initialize query engine
    query_engine = QueryEngine(embedder, vector_store)

    # 4. Start file watcher
    watch_path = str(Path(WATCH_FOLDER).resolve())
    Path(watch_path).mkdir(parents=True, exist_ok=True)
    file_watcher = FileWatcher(watch_path, ingest_file)

    # 5. Scan existing files
    logger.info("📂 Scanning existing files...")
    file_watcher.scan_existing_files()

    # 6. Start real-time monitoring
    file_watcher.start()

    logger.info("=" * 60)
    logger.info("✅ LifeVault is READY!")
    logger.info(f"   API: http://{API_HOST}:{API_PORT}")
    logger.info(f"   Watching: {watch_path}")
    logger.info(f"   Stats: {vector_store.get_stats()}")
    logger.info("=" * 60)

    yield  # ── App is running ──

    # Shutdown
    logger.info("Shutting down LifeVault...")
    if file_watcher:
        file_watcher.stop()


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="LifeVault API",
    description="AI-Powered Personal Memory Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (allow Streamlit frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    top_k: int = DEFAULT_TOP_K
    search_type: str = "all"  # "all", "images", "documents"


class IngestRequest(BaseModel):
    file_path: str


# ── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "LifeVault API",
        "status": "running",
        "version": "1.0.0",
        "stats": vector_store.get_stats() if vector_store else {},
    }


@app.post("/api/search")
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search across all indexed files.
    Uses Gemini for intent parsing + CLIP/MiniLM for embedding search.
    """
    if not query_engine:
        raise HTTPException(status_code=503, detail="System not ready")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        results = await query_engine.search(
            query=request.query,
            top_k=request.top_k,
            search_type=request.search_type,
        )
        return results
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest")
async def manual_ingest(request: IngestRequest):
    """Manually trigger ingestion for a specific file."""
    file_path = request.file_path
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    try:
        ingest_file(file_path)
        return {"status": "success", "file": file_path}
    except Exception as e:
        logger.error(f"Manual ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Return indexing statistics."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="System not ready")
    return vector_store.get_stats()


@app.get("/api/all-files")
async def get_all_files():
    """Return metadata for all indexed files."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="System not ready")
    return {"files": vector_store.get_all_metadata()}


@app.get("/api/surprise")
async def surprise_me():
    """Return a random memory from the vault."""
    if not vector_store:
        raise HTTPException(status_code=503, detail="System not ready")

    memory = vector_store.get_random_memory()
    if not memory:
        return {"message": "No memories yet! Add some files to your vault."}
    return {"memory": memory}


@app.get("/api/thumbnail")
async def get_thumbnail(file_path: str = Query(...)):
    """Serve file thumbnails for the frontend."""
    p = Path(file_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if p.suffix.lower() in IMAGE_EXTENSIONS:
        return FileResponse(str(p))
    
    return JSONResponse({"type": "document", "name": p.name})


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,  # Disable in production; models are too large to reload
        log_level="info",
    )
