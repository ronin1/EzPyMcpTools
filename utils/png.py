"""PNG utilities with OCR text extraction."""

from __future__ import annotations

import base64
import os
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

import pytesseract
from PIL import Image


def _get_temp_dir() -> str:
    """Get or create the temporary directory for PNG files."""
    temp_dir = "/tmp/utils_png"
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def _extract_text_from_png_bytes(png_bytes: bytes) -> str | None:
    """Extract text from PNG bytes using OCR.

    Args:
        png_bytes: PNG image bytes.

    Returns:
        Extracted text or None if OCR fails.
    """
    try:
        with Image.open(BytesIO(png_bytes)) as image:
            text = pytesseract.image_to_string(image)
        # Normalize whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines) if lines else None
    except Exception:
        return None


def extract_text_from_base64(base64_png: str) -> dict[str, Any]:
    """Extract text from a base64 encoded PNG image.

    Uses Tesseract OCR to extract text from the image.

    Args:
        base64_png: Base64 encoded PNG image.

    Returns:
        Dict containing the extracted text under key "text" or "error".
    """
    if not isinstance(base64_png, str):
        return {"error": "Input must be a base64 encoded string", "text": None}
    if not base64_png:
        return {"error": "Input cannot be empty", "text": None}

    try:
        png_bytes = base64.b64decode(base64_png, validate=True)
        text = _extract_text_from_png_bytes(png_bytes)
        if text is None:
            return {"error": "Failed to extract text from image", "text": None}
        return {"text": text, "error": None}
    except Exception as exc:
        return {"error": f"An error occurred during extraction: {exc!s}", "text": None}


def extract_text_from_path(file_path: str) -> dict[str, Any]:
    """Extract text from a PNG file at the given path.

    Uses Tesseract OCR to extract text from the image.
    Designed for use with mounted volumes at /tmp/utils_png/.

    Args:
        file_path: Absolute path to the PNG file (typically in /tmp/utils_png/).

    Returns:
        Dict containing the extracted text under key "text" or "error".
    """
    if not isinstance(file_path, str):
        return {"error": "Input must be a file path string", "text": None}
    if not file_path:
        return {"error": "File path cannot be empty", "text": None}

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}", "text": None}
    if not path.is_file():
        return {"error": f"Path is not a file: {file_path}", "text": None}

    try:
        with open(path, "rb") as f:
            png_bytes = f.read()
        text = _extract_text_from_png_bytes(png_bytes)
        if text is None:
            return {"error": "Failed to extract text from image", "text": None}
        return {"text": text, "error": None}
    except Exception as exc:
        return {"error": f"An error occurred during extraction: {exc!s}", "text": None}


def save_to_tmp_dir(base64_png: str) -> dict[str, Any]:
    """Save a base64 encoded PNG to /tmp/utils_png/ for shared access.

    Args:
        base64_png: Base64 encoded PNG image.

    Returns:
        Dict containing the absolute file path and processing status.
    """
    if not isinstance(base64_png, str):
        return {"error": "Input must be a base64 encoded string", "file_path": None}
    if not base64_png:
        return {"error": "Input cannot be empty", "file_path": None}

    try:
        png_bytes = base64.b64decode(base64_png, validate=True)
        # Verify it's valid PNG by opening it
        with Image.open(BytesIO(png_bytes)) as img:
            if img.format != "PNG":
                return {"error": "Input must be a PNG image", "file_path": None}

        temp_dir = _get_temp_dir()
        file_name = f"{uuid.uuid4()}.png"
        file_path = os.path.join(temp_dir, file_name)

        with open(file_path, "wb") as f:
            f.write(png_bytes)

        return {"file_path": file_path, "error": None}
    except Exception as exc:
        return {"error": f"Failed to save file: {exc!s}", "file_path": None}
