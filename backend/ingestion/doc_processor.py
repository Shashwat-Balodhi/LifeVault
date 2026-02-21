"""
Document Processor
-------------------
Handles text-based documents (.pdf, .txt, .docx, .md).
Extracts text content and generates sentence-transformer embeddings.
"""

from pathlib import Path
from typing import Dict, Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Maximum characters to embed (MiniLM has a 256-token window; 
# ~1500 chars is a safe limit for the first chunk)
MAX_TEXT_LENGTH = 3000


def process_document(
    file_path: str,
    sentence_model,
) -> Dict[str, Any]:
    """
    Process a document file and return embedding + extracted text.
    
    Returns:
        {
            "embedding": List[float]  (384-dim sentence embedding),
            "text_content": str       (extracted plain text),
        }
    """
    result: Dict[str, Any] = {"embedding": [], "text_content": ""}
    ext = Path(file_path).suffix.lower()

    try:
        # ── Extract text based on file type ─────────────────────────────
        if ext == ".pdf":
            text = _extract_pdf_text(file_path)
        elif ext == ".docx":
            text = _extract_docx_text(file_path)
        elif ext in (".txt", ".md"):
            text = _extract_plain_text(file_path)
        else:
            logger.warning(f"Unsupported document type: {ext}")
            return result

        if not text or len(text.strip()) < 10:
            logger.warning(f"Insufficient text extracted from {file_path}")
            return result

        result["text_content"] = text[:MAX_TEXT_LENGTH]

        # ── Generate sentence embedding ─────────────────────────────────
        embedding = sentence_model.encode(
            result["text_content"],
            convert_to_numpy=True,
            normalize_embeddings=True,  # L2 normalize for cosine sim
        )
        result["embedding"] = embedding.tolist()

        logger.info(
            f"✓ Doc embedding generated for {Path(file_path).name} "
            f"({len(result['text_content'])} chars)"
        )

    except Exception as e:
        logger.error(f"✗ Document processing failed for {file_path}: {e}")

    return result


# ── Text Extraction Helpers ──────────────────────────────────────────────────


def _extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF. Falls back to OCR for scanned pages."""
    import fitz  # PyMuPDF

    text_parts = []
    try:
        doc = fitz.open(file_path)
        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)
        doc.close()
    except Exception as e:
        logger.error(f"PDF text extraction error: {e}")

    full_text = "\n".join(text_parts).strip()

    # If no text extracted (scanned PDF), try OCR on first page
    if not full_text:
        full_text = _ocr_pdf_first_page(file_path)

    return full_text


def _ocr_pdf_first_page(file_path: str) -> str:
    """OCR the first page of a scanned PDF as a fallback."""
    try:
        import fitz
        import easyocr
        from PIL import Image
        import io

        doc = fitz.open(file_path)
        if len(doc) == 0:
            return ""

        # Render first page to image
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        doc.close()

        # OCR the rendered image
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        results = reader.readtext(img_bytes, detail=0)
        return " ".join(results).strip()

    except Exception as e:
        logger.warning(f"PDF OCR fallback failed: {e}")
        return ""


def _extract_docx_text(file_path: str) -> str:
    """Extract text from .docx files using python-docx."""
    try:
        from docx import Document

        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        return ""


def _extract_plain_text(file_path: str) -> str:
    """Read plain text / markdown files."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Text file read error: {e}")
        return ""
