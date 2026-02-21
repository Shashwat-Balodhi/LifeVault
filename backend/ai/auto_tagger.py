"""
Auto Tagger Module
-------------------
Provides zero-shot classification for images using CLIP.
Generates descriptive tags without any training data.
"""

from typing import List, Tuple

import torch
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ── Default tag categories for zero-shot classification ──────────────────────
DEFAULT_TAGS = [
    "nature", "landscape", "sunset", "mountains", "beach", "ocean", "forest",
    "city", "architecture", "building", "street",
    "people", "portrait", "group photo", "selfie", "family",
    "food", "cooking", "restaurant",
    "animal", "pet", "dog", "cat", "bird", "wildlife",
    "car", "vehicle", "travel", "airplane",
    "sports", "fitness", "outdoor activity",
    "celebration", "party", "wedding", "birthday",
    "document", "screenshot", "text", "whiteboard", "handwriting",
    "art", "painting", "illustration", "design",
    "technology", "computer", "gadget",
    "flower", "garden", "plant",
    "night", "indoor", "outdoor",
    "meme", "comic", "infographic",
]


def auto_tag_image(
    file_path: str,
    clip_model,
    clip_preprocess,
    clip_tokenizer,
    tags: List[str] = None,
    top_n: int = 5,
    device: str = "cpu",
) -> List[Tuple[str, float]]:
    """
    Zero-shot classify an image into top_n tags using CLIP.
    
    Args:
        file_path: Path to image file.
        clip_model: Loaded OpenCLIP model.
        clip_preprocess: CLIP image preprocessor.
        clip_tokenizer: CLIP text tokenizer.
        tags: List of tag strings to classify against.
        top_n: Number of top tags to return.
        device: "cpu" or "cuda".
    
    Returns:
        List of (tag_name, confidence_score) tuples, sorted by score.
    """
    if tags is None:
        tags = DEFAULT_TAGS

    try:
        from PIL import Image

        image = Image.open(file_path).convert("RGB")
        image_tensor = clip_preprocess(image).unsqueeze(0).to(device)

        # Tokenize all tag labels
        text_tokens = clip_tokenizer(
            [f"a photo of {tag}" for tag in tags]
        ).to(device)

        with torch.no_grad():
            image_features = clip_model.encode_image(image_tensor)
            text_features = clip_model.encode_text(text_tokens)

            # Normalize
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Cosine similarity → softmax probabilities
            similarity = (image_features @ text_features.T).squeeze(0)
            probs = torch.softmax(similarity * 100, dim=0)  # temperature scaling

        # Get top-N tags
        top_indices = probs.argsort(descending=True)[:top_n]
        result = [
            (tags[idx.item()], round(probs[idx.item()].item(), 4))
            for idx in top_indices
        ]

        tag_str = ", ".join(f"{t[0]}({t[1]:.2f})" for t in result)
        logger.info(f"  ↳ Auto-tags: {tag_str}")
        return result

    except Exception as e:
        logger.warning(f"Auto-tagging failed for {file_path}: {e}")
        return []
