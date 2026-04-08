"""Accurate tool for text analysis and manipulation utilities."""

from __future__ import annotations

import base64
import shutil
from io import BytesIO
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
import pytesseract
from PIL import Image
from pypdf import PdfReader

OCR_TEXT_MIN_LENGTH = 32
_OCR_RENDER_SCALE = 3
_OCR_CONFIG = "--psm 6 -c preserve_interword_spaces=1"


def words_count(text: str) -> dict[str, Any]:
    """Count the number of words in a text string.

    Args:
        text: The input text to count words in.

    Returns:
        Dict with `words` as the word count.
    """
    if not isinstance(text, str):
        return {"error": "Input must be a string"}
    return {"words": len(text.split())}


def characters_count(text: str) -> dict[str, Any]:
    """Count the number of characters in a text string.

    Args:
        text: The input text to count characters in.

    Returns:
        Dict with `characters.with_spaces` (total characters) and
        `characters.excluding_spaces` (characters without spaces).
    """
    if not isinstance(text, str):
        return {"error": "Input must be a string"}
    return {
        "characters": {
            "with_spaces": len(text),
            "excluding_spaces": len(text.replace(" ", "")),
        },
    }


def show_characters(word: str) -> dict[str, Any]:
    """Show each character from an input word/string.

    Args:
        word: The input word/string to split into characters.

    Returns:
        Dict with the original `word` and a `characters` array.
    """
    if not isinstance(word, str):
        return {"error": "Input must be a string"}
    return {
        "word": word,
        "characters": list(word),
    }


def to_base64(text: str) -> dict[str, Any]:
    """Convert text to base64 encoded string.

    Args:
        text: The input text to encode.

    Returns:
        Dict with `base64` as the encoded string.
    """
    if not isinstance(text, str):
        return {"error": "Input must be a string"}
    encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    return {"base64": encoded}


def from_base64(base64_str: str) -> dict[str, Any]:
    """Convert base64 encoded string back to text.

    Args:
        base64_str: The base64 encoded string to decode.

    Returns:
        Dict with `text` as the decoded string.
    """
    try:
        padding = "=" * (-len(base64_str) % 4)
        decoded = base64.b64decode(base64_str + padding).decode("utf-8")
        return {"text": decoded}
    except Exception:
        return {"error": "Invalid base64 string"}


# PDF and Image Text Extraction Functions


def _normalize_extracted_text(text: str) -> str:
    """Normalize extracted text preserving horizontal spacing for form alignment.

    Strips trailing whitespace per line and collapses runs of blank lines
    while keeping internal horizontal spacing intact for column-aligned content.
    """
    lines: list[str] = []
    consecutive_blanks = 0
    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped:
            consecutive_blanks += 1
            if consecutive_blanks <= 1:
                lines.append("")
            continue
        consecutive_blanks = 0
        lines.append(stripped)
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _extract_pdf_text_with_fallback(pdf_bytes: bytes) -> str | None:
    """Extract text from PDF bytes, using OCR if embedded text is insufficient.

    First attempts layout-preserving embedded text extraction from PDF.
    If insufficient, renders pages at higher DPI and uses OCR with
    form-aware config that preserves interword spacing.

    Args:
        pdf_bytes: PDF file bytes.

    Returns:
        Extracted text or None if extraction fails.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text(extraction_mode="layout")
            if text:
                normalized = _normalize_extracted_text(text)
                if normalized:
                    text_parts.append(normalized)
        extracted_text = "\n\n".join(text_parts)
        if extracted_text and len(extracted_text) >= OCR_TEXT_MIN_LENGTH:
            return extracted_text
    except Exception:
        pass

    if shutil.which("tesseract") is None:
        return None

    pdf_document = None
    ocr_parts: list[str] = []

    try:
        pdf_document = pdfium.PdfDocument(pdf_bytes)
        for page_index in range(len(pdf_document)):
            page = None
            bitmap = None
            image = None
            gray = None
            try:
                page = pdf_document[page_index]
                bitmap = page.render(scale=_OCR_RENDER_SCALE)
                image = bitmap.to_pil()
                gray = image.convert("L")
                ocr_text = pytesseract.image_to_string(gray, config=_OCR_CONFIG)
                normalized = _normalize_extracted_text(ocr_text)
                if normalized:
                    ocr_parts.append(normalized)
            finally:
                if gray is not None:
                    gray.close()
                if image is not None:
                    image.close()
                if bitmap is not None:
                    bitmap.close()
                if page is not None:
                    page.close()

        ocr_result = "\n\n".join(ocr_parts)
        return ocr_result if ocr_result else None
    except Exception:
        return None
    finally:
        if pdf_document is not None:
            pdf_document.close()


def _extract_image_text(image_bytes: bytes) -> str | None:
    """Extract text from image bytes using OCR with form-aware config.

    Converts to grayscale for better OCR accuracy and uses Tesseract
    config that preserves interword spacing for form alignment.

    Supports all image formats supported by Pillow (PNG, JPEG, GIF, BMP,
    TIFF, WebP, ICO, PPM, PGM, PBM, etc.).

    Args:
        image_bytes: Image file bytes.

    Returns:
        Extracted text or None if OCR fails.
    """
    if shutil.which("tesseract") is None:
        return None

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            gray = image.convert("L")
            try:
                ocr_text = pytesseract.image_to_string(gray, config=_OCR_CONFIG)
            finally:
                gray.close()
        normalized = _normalize_extracted_text(ocr_text)
        return normalized if normalized else None
    except Exception:
        return None


def extract_from_pdf_base64(base64_pdf: str) -> dict[str, Any]:
    """Extract text from a base64 encoded PDF.

    Attempts embedded text extraction first, falls back to OCR if needed.

    Args:
        base64_pdf: Base64 encoded PDF content.

    Returns:
        Dict with extracted `text` or `error` message.
    """
    if not isinstance(base64_pdf, str):
        return {"error": "Input must be a base64 encoded string", "text": None}
    if not base64_pdf:
        return {"error": "Input cannot be empty", "text": None}

    try:
        pdf_bytes = base64.b64decode(base64_pdf, validate=True)
        text = _extract_pdf_text_with_fallback(pdf_bytes)
        if text is None:
            return {"error": "Failed to extract text from PDF", "text": None}
        return {"text": text}
    except Exception as exc:
        return {"error": f"An error occurred during extraction: {exc!s}", "text": None}


def extract_from_pdf_file(file_path: str) -> dict[str, Any]:
    """Extract text from a PDF file at the given path.

    Accepts any readable file path (e.g. mounted volumes, local files).

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Dict with extracted ``text`` or ``error`` message.
    """
    error = _validate_input_file(file_path)
    if error is not None:
        return error

    try:
        resolved = Path(file_path).resolve()
        with open(resolved, "rb") as f:
            pdf_bytes = f.read()
        text = _extract_pdf_text_with_fallback(pdf_bytes)
        if text is None:
            return {"error": "Failed to extract text from PDF", "text": None}
        return {"text": text}
    except Exception as exc:
        return {"error": f"An error occurred during extraction: {exc!s}", "text": None}


def extract_from_image_base64(base64_image: str) -> dict[str, Any]:
    """Extract text from a base64 encoded image.

    Uses OCR to extract text. Supports all image formats supported by
    Pillow: PNG, JPEG, GIF, BMP, TIFF, WebP, ICO, PPM, PGM, PBM, etc.

    Args:
        base64_image: Base64 encoded image content.

    Returns:
        Dict with extracted `text` or `error` message.
    """
    if not isinstance(base64_image, str):
        return {"error": "Input must be a base64 encoded string", "text": None}
    if not base64_image:
        return {"error": "Input cannot be empty", "text": None}

    try:
        image_bytes = base64.b64decode(base64_image, validate=True)
        # Verify it's a valid image
        with Image.open(BytesIO(image_bytes)) as img:
            img.verify()

        text = _extract_image_text(image_bytes)
        if text is None:
            return {"error": "Failed to extract text from image", "text": None}
        return {"text": text}
    except Exception as exc:
        return {"error": f"An error occurred during extraction: {exc!s}", "text": None}


def extract_from_image_file(file_path: str) -> dict[str, Any]:
    """Extract text from an image file at the given path using OCR.

    Accepts any readable file path (e.g. mounted volumes, local files).
    Supports all image formats supported by Pillow: PNG, JPEG, GIF, BMP,
    TIFF, WebP, ICO, PPM, PGM, PBM, etc.

    Args:
        file_path: Absolute path to the image file.

    Returns:
        Dict with extracted ``text`` or ``error`` message.
    """
    error = _validate_input_file(file_path)
    if error is not None:
        return error

    try:
        resolved = Path(file_path).resolve()
        with open(resolved, "rb") as f:
            image_bytes = f.read()
        text = _extract_image_text(image_bytes)
        if text is None:
            return {"error": "Failed to extract text from image", "text": None}
        return {"text": text}
    except Exception as exc:
        return {"error": f"An error occurred during extraction: {exc!s}", "text": None}


def _validate_input_file(file_path: str) -> dict[str, Any] | None:
    """Validate that a file path points to a readable file.

    Args:
        file_path: The file path to validate.

    Returns:
        Error dict if invalid, None if the path is a readable file.
    """
    if not isinstance(file_path, str):
        return {"error": "Input must be a file path string", "text": None}
    if not file_path:
        return {"error": "File path cannot be empty", "text": None}

    try:
        resolved = Path(file_path).resolve()
        if not resolved.exists():
            return {"error": f"File not found: {file_path}", "text": None}
        if not resolved.is_file():
            return {"error": f"Path is not a file: {file_path}", "text": None}
        return None
    except Exception as exc:
        return {"error": f"Invalid file path: {exc!s}", "text": None}
