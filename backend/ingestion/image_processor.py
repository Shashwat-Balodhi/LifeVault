"""
Image Processor
----------------
Handles image files: generates CLIP embeddings and extracts text via OCR.
All model instances are passed in (loaded once globally) to avoid reload overhead.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def process_image(
    file_path: str,
    clip_model,
    clip_preprocess,
    clip_tokenizer,
    ocr_reader,
) -> Dict[str, Any]:
    """
    Process a single image file.
    
    Returns:
        {
            "embedding": List[float]  (512-dim CLIP embedding),
            "text_content": str       (OCR-extracted text, if any),
        }
    """
    import torch

    result: Dict[str, Any] = {"embedding": [], "text_content": ""}

    try:
        # ── Load and preprocess image ────────────────────────────────────
        image = Image.open(file_path).convert("RGB")
        image_tensor = clip_preprocess(image).unsqueeze(0)

        # Move to same device as model
        device = next(clip_model.parameters()).device
        image_tensor = image_tensor.to(device)

        # ── Generate CLIP embedding ──────────────────────────────────────
        with torch.no_grad():
            image_features = clip_model.encode_image(image_tensor)
            # L2 normalize for cosine similarity
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            result["embedding"] = image_features.squeeze().cpu().numpy().tolist()

        logger.info(f"✓ CLIP embedding generated for {Path(file_path).name}")

    except Exception as e:
        logger.error(f"✗ CLIP embedding failed for {file_path}: {e}")
        return result

    # ── OCR text extraction (best effort) ────────────────────────────────
    try:
        if ocr_reader is not None:
            ocr_results = ocr_reader.readtext(file_path, detail=0)
            extracted_text = " ".join(ocr_results).strip()
            if extracted_text:
                result["text_content"] = extracted_text
                logger.info(f"  ↳ OCR extracted {len(extracted_text)} chars from {Path(file_path).name}")
    except Exception as e:
        logger.warning(f"  ↳ OCR failed for {file_path}: {e}")

    return result
