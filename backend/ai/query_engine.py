"""
Query Engine
-------------
Orchestrates semantic search:
    1. Accepts a natural language query.
    2. (Optional) Uses Google Gemini to extract intent and refine the query.
    3. Generates query embeddings for both image and document search.
    4. Queries ChromaDB and returns ranked results.

If Gemini fails → falls back to direct semantic search with original query.
"""

import json
from typing import Dict, Any, List, Optional

from backend.utils.config import GEMINI_API_KEY, DEFAULT_TOP_K
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class QueryEngine:
    """Handles semantic search queries with optional Gemini intent parsing."""

    def __init__(self, embedder_service, vector_store):
        self.embedder = embedder_service
        self.store = vector_store
        self.gemini_model = None

        # Initialize Gemini if API key is available
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                import google.generativeai as genai

                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("✓ Gemini API initialized for intent parsing.")
            except Exception as e:
                logger.warning(f"⚠ Gemini init failed — using direct search: {e}")
        else:
            logger.info("Gemini API key not configured — using direct semantic search.")

    async def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        search_type: str = "all",  # "all", "images", "documents"
    ) -> Dict[str, Any]:
        """
        Main search entry point.
        
        Args:
            query: Natural language search query.
            top_k: Number of results to return.
            search_type: Filter by file type.
            
        Returns:
            {
                "query": str,
                "refined_query": str,
                "intent": dict,
                "results": List[dict],
                "total_results": int,
            }
        """
        # ── Step 1: Parse intent with Gemini (optional) ─────────────────
        intent = {}
        refined_query = query

        if self.gemini_model:
            intent, refined_query = await self._parse_intent(query)
            if not refined_query:
                refined_query = query  # fallback

        # ── Step 2: Determine search type from intent ───────────────────
        if intent.get("file_type") == "image":
            search_type = "images"
        elif intent.get("file_type") == "document":
            search_type = "documents"

        # ── Step 3: Generate embeddings and search ──────────────────────
        results = []

        if search_type in ("all", "images"):
            try:
                # Use CLIP text embedding for image search
                clip_embedding = self.embedder.get_text_clip_embedding(refined_query)
                image_results = self.store.search_images(clip_embedding, top_k)
                results.extend(image_results)
            except Exception as e:
                logger.error(f"Image search failed: {e}")

        if search_type in ("all", "documents"):
            try:
                # Use sentence embedding for document search
                sent_embedding = self.embedder.get_sentence_embedding(refined_query)
                doc_results = self.store.search_documents(sent_embedding, top_k)
                results.extend(doc_results)
            except Exception as e:
                logger.error(f"Document search failed: {e}")

        # ── Step 4: Merge, sort, and return top-K ───────────────────────
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

        return {
            "query": query,
            "refined_query": refined_query,
            "intent": intent,
            "results": results,
            "total_results": len(results),
        }

    async def _parse_intent(self, query: str) -> tuple:
        """
        Use Gemini to extract structured intent from a natural language query.
        Returns (intent_dict, refined_query_string).
        """
        prompt = f"""You are a search intent parser for a personal file memory system.
Given a user query, extract the intent and return a JSON object with these fields:
- "refined_query": A concise, searchable version of the user's query.
- "file_type": One of "image", "document", "any".
- "time_filter": Relevant time context (e.g., "last week", "2024") or null.
- "tags": List of relevant tags/keywords.
- "emotion": Detected emotional tone (e.g., "nostalgic", "urgent", "casual") or null.

RESPOND WITH ONLY valid JSON. No markdown, no explanation.

User query: "{query}"
"""
        try:
            response = self.gemini_model.generate_content(prompt)
            raw_text = response.text.strip()

            # Clean markdown code fences if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[-1]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()

            intent = json.loads(raw_text)
            refined = intent.get("refined_query", query)
            logger.info(f"Gemini intent: {intent}")
            return intent, refined

        except Exception as e:
            logger.warning(f"Gemini intent parsing failed — using original query: {e}")
            return {}, query
