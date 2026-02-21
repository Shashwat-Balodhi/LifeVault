"""
Embedder Module
----------------
Loads AI models ONCE at startup and provides embedding generation functions.
This is the single source of truth for all model instances.

Models loaded:
    - OpenCLIP ViT-B-32 (512-dim image embeddings)
    - SentenceTransformer all-MiniLM-L6-v2 (384-dim text embeddings)
    - EasyOCR reader (English)
"""

import torch
from backend.utils.config import CLIP_MODEL_NAME, CLIP_PRETRAINED, SENTENCE_MODEL_NAME
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EmbedderService:
    """
    Singleton-style service that holds all loaded AI models.
    Instantiate once in main.py and pass to all processing pipelines.
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🔧 Using device: {self.device}")

        self.clip_model = None
        self.clip_preprocess = None
        self.clip_tokenizer = None
        self.sentence_model = None
        self.ocr_reader = None

    def load_all_models(self):
        """Load every model. Call once at app startup."""
        self._load_clip()
        self._load_sentence_model()
        self._load_ocr()
        logger.info("✅ All AI models loaded successfully.")

    # ── CLIP ─────────────────────────────────────────────────────────────

    def _load_clip(self):
        """Load OpenCLIP model for image + text embeddings (512-dim)."""
        try:
            import open_clip

            logger.info(f"Loading OpenCLIP {CLIP_MODEL_NAME} ({CLIP_PRETRAINED})...")
            self.clip_model, _, self.clip_preprocess = open_clip.create_model_and_transforms(
                CLIP_MODEL_NAME, pretrained=CLIP_PRETRAINED
            )
            self.clip_tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)
            self.clip_model = self.clip_model.to(self.device).eval()
            logger.info("✓ OpenCLIP loaded.")
        except Exception as e:
            logger.error(f"✗ Failed to load OpenCLIP: {e}")
            raise

    def get_text_clip_embedding(self, text: str):
        """Generate a CLIP text embedding (for cross-modal image search)."""
        import open_clip

        tokens = self.clip_tokenizer([text]).to(self.device)
        with torch.no_grad():
            text_features = self.clip_model.encode_text(tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        return text_features.squeeze().cpu().numpy().tolist()

    # ── Sentence Transformer ─────────────────────────────────────────────

    def _load_sentence_model(self):
        """Load SentenceTransformers model for document embeddings (384-dim)."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading SentenceTransformer {SENTENCE_MODEL_NAME}...")
            self.sentence_model = SentenceTransformer(SENTENCE_MODEL_NAME, device=self.device)
            logger.info("✓ SentenceTransformer loaded.")
        except Exception as e:
            logger.error(f"✗ Failed to load SentenceTransformer: {e}")
            raise

    def get_sentence_embedding(self, text: str):
        """Generate a sentence embedding for document-level search."""
        embedding = self.sentence_model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        )
        return embedding.tolist()

    # ── OCR ──────────────────────────────────────────────────────────────

    def _load_ocr(self):
        """Load EasyOCR reader (English). Non-critical; failure is OK."""
        try:
            import easyocr

            logger.info("Loading EasyOCR (English)...")
            self.ocr_reader = easyocr.Reader(
                ["en"], gpu=(self.device == "cuda"), verbose=False
            )
            logger.info("✓ EasyOCR loaded.")
        except Exception as e:
            logger.warning(f"⚠ EasyOCR not loaded (non-critical): {e}")
            self.ocr_reader = None
