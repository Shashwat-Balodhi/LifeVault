"""
Metadata Extractor
-------------------
Extracts filesystem metadata and EXIF data (for images) from files.
Returns a flat dictionary suitable for ChromaDB metadata storage.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _safe_str(value: Any) -> str:
    """Convert any value to a string safely for ChromaDB metadata."""
    if value is None:
        return ""
    return str(value)


def extract_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract basic filesystem metadata from any file.
    
    Returns dict with:
        - file_name, file_path, file_extension, file_size_bytes
        - created_date, modified_date (ISO format strings)
    """
    p = Path(file_path)
    stat = p.stat()

    return {
        "file_name": p.name,
        "file_path": str(p.resolve()),
        "file_extension": p.suffix.lower(),
        "file_size_bytes": stat.st_size,
        "created_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "file_type": "image" if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"} else "document",
    }


def extract_exif_metadata(file_path: str) -> Dict[str, str]:
    """
    Extract EXIF metadata from images (GPS, camera, capture date).
    Returns empty dict on failure — never crashes the pipeline.
    """
    exif_data: Dict[str, str] = {}
    try:
        import exifread
        with open(file_path, "rb") as f:
            tags = exifread.process_file(f, details=False)

        # Camera info
        if "Image Make" in tags:
            exif_data["camera_make"] = _safe_str(tags["Image Make"])
        if "Image Model" in tags:
            exif_data["camera_model"] = _safe_str(tags["Image Model"])

        # Capture date
        if "EXIF DateTimeOriginal" in tags:
            exif_data["capture_date"] = _safe_str(tags["EXIF DateTimeOriginal"])
        elif "Image DateTime" in tags:
            exif_data["capture_date"] = _safe_str(tags["Image DateTime"])

        # GPS coordinates
        gps_lat = tags.get("GPS GPSLatitude")
        gps_lat_ref = tags.get("GPS GPSLatitudeRef")
        gps_lon = tags.get("GPS GPSLongitude")
        gps_lon_ref = tags.get("GPS GPSLongitudeRef")

        if gps_lat and gps_lon:
            lat = _convert_gps_to_decimal(gps_lat, gps_lat_ref)
            lon = _convert_gps_to_decimal(gps_lon, gps_lon_ref)
            if lat is not None and lon is not None:
                exif_data["gps_latitude"] = str(lat)
                exif_data["gps_longitude"] = str(lon)

    except Exception as e:
        logger.warning(f"EXIF extraction failed for {file_path}: {e}")

    return exif_data


def _convert_gps_to_decimal(
    gps_coords, gps_ref
) -> Optional[float]:
    """Convert EXIF GPS IFD rational values to decimal degrees."""
    try:
        values = gps_coords.values
        d = float(values[0].num) / float(values[0].den)
        m = float(values[1].num) / float(values[1].den)
        s = float(values[2].num) / float(values[2].den)
        decimal = d + (m / 60.0) + (s / 3600.0)
        if gps_ref and str(gps_ref) in ("S", "W"):
            decimal = -decimal
        return round(decimal, 6)
    except Exception:
        return None
