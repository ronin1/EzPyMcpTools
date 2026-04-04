"""PDF generation utilities."""

from __future__ import annotations

import base64
import re
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from weasyprint import HTML


def _strip_js_from_html(html_content: str) -> str:
    """Remove JavaScript from HTML content.

    Removes <script> tags and inline event handlers. Keeps <style> for CSS.

    Args:
        html_content: Raw HTML string.

    Returns:
        HTML with JavaScript removed.
    """
    html = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"\s+on\w+\s*=\s*[\"'][^\"']*[\"']", "", html, flags=re.IGNORECASE)
    html = re.sub(r"\s+on\w+\s*=\s*[^\s>]+", "", html, flags=re.IGNORECASE)
    return html


def _html_to_pdf_bytes(html_content: str) -> bytes | None:
    """Convert HTML content string to PDF bytes.

    Note: Uses WeasyPrint for proper HTML/CSS rendering. JavaScript is stripped.

    Args:
        html_content: HTML string content.

    Returns:
        PDF bytes or None if conversion fails.
    """
    try:
        html_content = _strip_js_from_html(html_content)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
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
        reader = PdfReader(BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        extracted_text = "\n".join(text_parts)
        safe_text = re.sub(r"<[^>]*>", " ", extracted_text)
        safe_text = " ".join(safe_text.split())
        return f"<html><body><p>{safe_text}</p></body></html>"
    except Exception:
        return None


def from_html(base64_html: str) -> dict[str, Any]:
    """Convert base64 encoded HTML content to a base64 encoded PDF.

    Note: Uses WeasyPrint for proper HTML/CSS rendering. JavaScript is stripped.

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
