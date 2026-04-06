"""PDF generation utilities."""

from __future__ import annotations

import base64
import re
from io import BytesIO
from typing import Any

import pypdfium2 as pdfium
from PIL import Image
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
        safe_text = safe_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<html><body><p>{safe_text}</p></body></html>"
    except Exception:
        return None


def _png_bytes_to_pdf_bytes(png_bytes: bytes) -> bytes | None:
    """Convert PNG bytes to PDF bytes."""
    try:
        with Image.open(BytesIO(png_bytes)) as image:
            rgba_image = image.convert("RGBA")
            rgb_image = Image.new("RGB", rgba_image.size, "white")
            rgb_image.paste(rgba_image, mask=rgba_image.getchannel("A"))
            try:
                pdf_buffer = BytesIO()
                rgb_image.save(pdf_buffer, format="PDF")
                return pdf_buffer.getvalue()
            finally:
                rgba_image.close()
                rgb_image.close()
    except Exception:
        return None


def _pdf_bytes_to_png_bytes(pdf_bytes: bytes, page_number: int = 1) -> bytes | None:
    """Convert a PDF page to PNG bytes."""
    pdf_document = None
    page = None
    bitmap = None
    image = None

    try:
        pdf_document = pdfium.PdfDocument(pdf_bytes)
        if page_number > len(pdf_document):
            return None

        page = pdf_document[page_number - 1]
        bitmap = page.render(scale=2)
        image = bitmap.to_pil()

        png_buffer = BytesIO()
        image.save(png_buffer, format="PNG")
        return png_buffer.getvalue()
    except Exception:
        return None
    finally:
        if image is not None:
            image.close()
        if bitmap is not None:
            bitmap.close()
        if page is not None:
            page.close()
        if pdf_document is not None:
            pdf_document.close()


def from_html(base64_html: str) -> dict[str, Any]:
    """Convert base64 encoded HTML content to a base64 encoded PDF.

    Note: Uses WeasyPrint for proper HTML/CSS rendering. JavaScript is stripped.

    Args:
        base64_html: Base64 encoded string of the HTML content.

    Returns:
        Dict containing the base64 encoded PDF content under the key "base64_pdf".
    """
    if not isinstance(base64_html, str):
        return {"error": "Input must be a base64 encoded string"}
    if not base64_html:
        return {"error": "Input cannot be empty"}
    try:
        html_content = base64.b64decode(base64_html, validate=True).decode("utf-8")
        pdf_bytes = _html_to_pdf_bytes(html_content)
        if pdf_bytes is None:
            return {"error": "Failed to generate PDF bytes"}
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return {"base64_pdf": base64_pdf}
    except Exception:
        return {"error": "An error occurred during conversion"}


def from_png(base64_png: str) -> dict[str, Any]:
    """Convert base64 encoded PNG content to a base64 encoded PDF.

    Args:
        base64_png: Base64 encoded string of the PNG content.

    Returns:
        Dict containing the base64 encoded PDF content under the key "base64_pdf".
    """
    if not isinstance(base64_png, str):
        return {"error": "Input must be a base64 encoded string"}
    if not base64_png:
        return {"error": "Input cannot be empty"}
    try:
        png_bytes = base64.b64decode(base64_png, validate=True)
        pdf_bytes = _png_bytes_to_pdf_bytes(png_bytes)
        if pdf_bytes is None:
            return {"error": "Failed to generate PDF bytes"}
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return {"base64_pdf": base64_pdf}
    except Exception:
        return {"error": "An error occurred during conversion"}


def to_html(base64_pdf: str) -> dict[str, Any]:
    """Convert base64 encoded PDF content back to a base64 encoded HTML string.

    Note: This is a lossy conversion that extracts text from the PDF bytes.

    Args:
        base64_pdf: Base64 encoded string of the PDF content.

    Returns:
        Dict containing the base64 encoded HTML content under the key "base64_html".
    """
    if not isinstance(base64_pdf, str):
        return {"error": "Input must be a base64 encoded string"}
    if not base64_pdf:
        return {"error": "Input cannot be empty"}
    try:
        pdf_bytes = base64.b64decode(base64_pdf)
        html_content = _pdf_bytes_to_html(pdf_bytes)
        if html_content is None:
            return {"error": "Failed to extract HTML from PDF"}
        base64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
        return {"base64_html": base64_html}
    except Exception as exc:
        return {"error": f"An error occurred during conversion: {exc!s}"}


def to_png(base64_pdf: str, page_number: int = 1) -> dict[str, Any]:
    """Convert base64 encoded PDF content to a base64 encoded PNG.

    Args:
        base64_pdf: Base64 encoded string of the PDF content.
        page_number: One-based PDF page number to render.

    Returns:
        Dict containing the base64 encoded PNG content under the key "base64_png".
    """
    if not isinstance(base64_pdf, str):
        return {"error": "Input must be a base64 encoded string"}
    if not base64_pdf:
        return {"error": "Input cannot be empty"}
    if isinstance(page_number, bool) or not isinstance(page_number, int):
        return {"error": "Page number must be an integer"}
    if page_number < 1:
        return {"error": "Page number must be greater than 0"}

    try:
        pdf_bytes = base64.b64decode(base64_pdf, validate=True)
        png_bytes = _pdf_bytes_to_png_bytes(pdf_bytes, page_number=page_number)
        if png_bytes is None:
            return {"error": "Failed to generate PNG bytes"}
        base64_png = base64.b64encode(png_bytes).decode("utf-8")
        return {"base64_png": base64_png}
    except Exception:
        return {"error": "An error occurred during conversion"}
