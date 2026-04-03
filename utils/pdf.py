"""PDF generation utilities."""

from __future__ import annotations

import base64
import re
from typing import Any

from fpdf import FPDF


def _strip_js_from_html(html_content: str) -> str:
    """Remove JavaScript from HTML content.

    Removes <script> tags, <style> tags, and inline event handlers.

    Args:
        html_content: Raw HTML string.

    Returns:
        HTML with JavaScript removed.
    """
    html = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"\s+on\w+\s*=\s*[\"'][^\"']*[\"']", "", html, flags=re.IGNORECASE)
    html = re.sub(r"\s+on\w+\s*=\s*[^\s>]+", "", html, flags=re.IGNORECASE)
    return html


def _html_to_pdf_bytes(html_content: str) -> bytes | None:
    """Convert HTML content string to PDF bytes.

    Note: JavaScript is stripped before rendering. Only plain text content
    is converted to PDF.

    Args:
        html_content: HTML string content.

    Returns:
        PDF bytes or None if conversion fails.
    """
    try:
        html_content = _strip_js_from_html(html_content)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)

        text = re.sub(r"<[^>]*>", " ", html_content)
        text = " ".join(text.split())
        safe_text = text.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 10, safe_text)

        pdf_bytes = pdf.output()
        if not isinstance(pdf_bytes, (bytes, bytearray)):
            if isinstance(pdf_bytes, str):
                return pdf_bytes.encode("latin-1")
            return None
        return bytes(pdf_bytes)
    except Exception:
        return None


def _pdf_bytes_to_html(pdf_bytes: bytes) -> str | None:
    """Convert PDF bytes to HTML content string.

    Args:
        pdf_bytes: PDF file bytes.

    Returns:
        HTML string content or None if conversion fails.
    """
    try:
        text_matches = re.findall(rb"\((.*?)\)", pdf_bytes)
        extracted_text = " ".join([m.decode("latin-1", errors="replace") for m in text_matches])
        return f"<html><body><p>{extracted_text}</p></body></html>"
    except Exception:
        return None


def from_html(base64_html: str) -> dict[str, Any]:
    """Convert base64 encoded HTML content to a base64 encoded PDF.

    Note: This implementation uses fpdf2 for maximum compatibility and avoids
    system dependencies like Cairo. It performs basic text extraction from HTML.

    Args:
        base64_html: Base64 encoded string of the HTML content.

    Returns:
        Dict containing the base64 encoded PDF content under the key "base64_pdf".
    """
    try:
        html_content = base64.b64decode(base64_html).decode("utf-8")
        pdf_bytes = _html_to_pdf_bytes(html_content)
        if pdf_bytes is None:
            return {"error": "Failed to generate PDF bytes"}
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return {"base64_pdf": base64_pdf}
    except Exception as exc:
        return {"error": f"An error occurred during conversion: {exc!s}"}


def to_html(base64_pdf: str) -> dict[str, Any]:
    """Convert base64 encoded PDF content back to a base64 encoded HTML string.

    Note: This is a lossy conversion that extracts text from the PDF bytes.

    Args:
        base64_pdf: Base64 encoded string of the PDF content.

    Returns:
        Dict containing the base64 encoded HTML content under the key "base64_html".
    """
    try:
        pdf_bytes = base64.b64decode(base64_pdf)
        html_content = _pdf_bytes_to_html(pdf_bytes)
        if html_content is None:
            return {"error": "Failed to extract HTML from PDF"}
        base64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
        return {"base64_html": base64_html}
    except Exception as exc:
        return {"error": f"An error occurred during conversion: {exc!s}"}
