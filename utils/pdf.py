"""PDF generation utilities."""

from __future__ import annotations

import base64
import html as html_lib
import re
import shutil
from io import BytesIO
from typing import Any

import pypdfium2 as pdfium
import pytesseract
from PIL import Image
from pypdf import PdfReader, PdfWriter
from weasyprint import HTML

SOURCE_HTML_METADATA_KEY = "/EzPySourceHTML"
OCR_TEXT_MIN_LENGTH = 32


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
        if pdf_bytes is None:
            return None
        embedded_pdf_bytes = _embed_source_html_in_pdf(pdf_bytes, html_content)
        return embedded_pdf_bytes or pdf_bytes
    except Exception:
        return None


def _normalize_extracted_text(text: str) -> str:
    """Normalize extracted text while keeping line boundaries useful."""
    normalized_lines = []
    for line in text.splitlines():
        normalized_line = " ".join(line.split())
        if normalized_line:
            normalized_lines.append(normalized_line)
    return "\n".join(normalized_lines)


def _embed_source_html_in_pdf(pdf_bytes: bytes, html_content: str) -> bytes | None:
    """Embed sanitized HTML into generated PDF metadata for round-trips."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        metadata: dict[str, str] = {}
        if reader.metadata:
            for key, value in reader.metadata.items():
                if isinstance(key, str) and value is not None:
                    metadata[key] = str(value)

        metadata[SOURCE_HTML_METADATA_KEY] = base64.b64encode(html_content.encode("utf-8")).decode(
            "utf-8"
        )
        writer.add_metadata(metadata)

        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except Exception:
        return None


def _extract_embedded_source_html(pdf_bytes: bytes) -> str | None:
    """Recover embedded source HTML from generated PDFs."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        metadata = reader.metadata or {}
        encoded_html = metadata.get(SOURCE_HTML_METADATA_KEY)
        if not isinstance(encoded_html, str) or not encoded_html:
            return None
        return base64.b64decode(encoded_html, validate=True).decode("utf-8")
    except Exception:
        return None


def _extract_pdf_text(pdf_bytes: bytes) -> str | None:
    """Extract readable text from PDF bytes."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                normalized_text = _normalize_extracted_text(text)
                if normalized_text:
                    text_parts.append(normalized_text)
        extracted_text = "\n\n".join(text_parts)
        return extracted_text or None
    except Exception:
        return None


def _ocr_png_bytes(png_bytes: bytes) -> str | None:
    """OCR PNG bytes when no embedded PDF text is available."""
    if shutil.which("tesseract") is None:
        return None

    try:
        with Image.open(BytesIO(png_bytes)) as image:
            ocr_text = pytesseract.image_to_string(image)
        normalized_text = _normalize_extracted_text(ocr_text)
        return normalized_text or None
    except Exception:
        return None


def _pdf_bytes_to_all_png_bytes(pdf_bytes: bytes) -> list[bytes] | None:
    """Render all PDF pages to PNG bytes."""
    pdf_document = None

    try:
        pdf_document = pdfium.PdfDocument(pdf_bytes)
        page_pngs: list[bytes] = []

        for page_index in range(len(pdf_document)):
            page = None
            bitmap = None
            image = None

            try:
                page = pdf_document[page_index]
                bitmap = page.render(scale=2)
                image = bitmap.to_pil()

                png_buffer = BytesIO()
                image.save(png_buffer, format="PNG")
                page_pngs.append(png_buffer.getvalue())
            finally:
                if image is not None:
                    image.close()
                if bitmap is not None:
                    bitmap.close()
                if page is not None:
                    page.close()

        return page_pngs
    except Exception:
        return None
    finally:
        if pdf_document is not None:
            pdf_document.close()


def _rendered_pages_to_html(page_pngs: list[bytes], extracted_text: str | None) -> str:
    """Build visually faithful HTML from rendered page images."""
    rendered_pages = []
    for page_number, page_png in enumerate(page_pngs, start=1):
        base64_png = base64.b64encode(page_png).decode("utf-8")
        rendered_pages.append(
            "\n".join(
                [
                    '<figure class="page">',
                    (
                        f'  <img src="data:image/png;base64,{base64_png}" '
                        f'alt="PDF page {page_number}" />'
                    ),
                    "</figure>",
                ]
            )
        )

    extracted_text_section = ""
    if extracted_text:
        escaped_text = html_lib.escape(extracted_text)
        extracted_text_section = (
            '<details class="extracted-text" open>'
            "<summary>Extracted text</summary>"
            f"<pre>{escaped_text}</pre>"
            "</details>"
        )

    return (
        "<!DOCTYPE html>"
        '<html lang="en">'
        "<head>"
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        "<title>PDF Preview</title>"
        "<style>"
        "body { margin: 0; padding: 24px; background: #d1d5db; color: #111827; "
        "font-family: Arial, sans-serif; }"
        ".pages { display: grid; gap: 24px; }"
        ".page { margin: 0 auto; max-width: 960px; background: #ffffff; "
        "box-shadow: 0 12px 30px rgba(15, 23, 42, 0.2); }"
        ".page img { display: block; width: 100%; height: auto; }"
        ".extracted-text { max-width: 960px; margin: 24px auto 0; padding: 16px; "
        "background: #ffffff; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.12); }"
        ".extracted-text summary { cursor: pointer; font-weight: bold; }"
        ".extracted-text pre { white-space: pre-wrap; word-break: break-word; }"
        "</style>"
        "</head>"
        '<body data-render-mode="rendered-pages">'
        f'<main class="pages">{"".join(rendered_pages)}</main>'
        f"{extracted_text_section}"
        "</body>"
        "</html>"
    )


def _pdf_bytes_to_html(pdf_bytes: bytes) -> str | None:
    """Convert PDF bytes to HTML content string.

    Args:
        pdf_bytes: PDF file bytes.

    Returns:
        HTML string content or None if conversion fails. Returns embedded source
        HTML for PDFs generated by this tool when available; otherwise returns
        rendered page images plus extracted and OCR text.
    """
    embedded_html = _extract_embedded_source_html(pdf_bytes)
    if embedded_html is not None:
        return embedded_html

    page_pngs = _pdf_bytes_to_all_png_bytes(pdf_bytes)
    if not page_pngs:
        return None

    extracted_text = _extract_pdf_text(pdf_bytes)
    if extracted_text is None or len(extracted_text) < OCR_TEXT_MIN_LENGTH:
        ocr_text_parts = []
        for page_png in page_pngs:
            ocr_text = _ocr_png_bytes(page_png)
            if ocr_text:
                ocr_text_parts.append(ocr_text)
        ocr_text = "\n\n".join(ocr_text_parts) if ocr_text_parts else None
        if ocr_text and (extracted_text is None or len(ocr_text) > len(extracted_text)):
            extracted_text = ocr_text

    return _rendered_pages_to_html(page_pngs, extracted_text)


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

    Note: If this PDF was generated by `from_html`, the embedded source HTML is
    returned. Otherwise, this returns HTML containing rendered page images plus
    extracted text, with OCR used when the PDF has little or no embedded text.

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
