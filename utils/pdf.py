"""PDF generation utilities."""

from __future__ import annotations

import base64
import html as html_lib
import os
import re
import shutil
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

import pypdfium2 as pdfium
import pytesseract
from PIL import Image
from pypdf import PdfReader, PdfWriter
from weasyprint import HTML

SOURCE_HTML_METADATA_KEY = "/EzPySourceHTML"
OCR_TEXT_MIN_LENGTH = 32
_OCR_RENDER_SCALE = 3
_OCR_CONFIG = "--psm 6 -c preserve_interword_spaces=1"


def _get_temp_dir() -> str:
    """Get or create the temporary directory for PDF files."""
    temp_dir = "/tmp/ezpy_tools/pdf"
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def _validate_input_file(file_path: str) -> dict[str, Any] | None:
    """Validate that a file path points to a readable file.

    Args:
        file_path: The file path to validate.

    Returns:
        Error dict if invalid, None if the path is a readable file.
    """
    if not isinstance(file_path, str):
        return {"success": False, "error": "Input must be a file path string", "file_path": None}
    if not file_path:
        return {"success": False, "error": "File path cannot be empty", "file_path": None}

    try:
        resolved = Path(file_path).resolve()
        if not resolved.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
                "file_path": None,
            }
        if not resolved.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {file_path}",
                "file_path": None,
            }
        return None
    except Exception as exc:
        return {"success": False, "error": f"Invalid file path: {exc!s}", "file_path": None}


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
    """Extract readable text from PDF bytes preserving layout spacing."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text(extraction_mode="layout")
            if text:
                normalized_text = _normalize_extracted_text(text)
                if normalized_text:
                    text_parts.append(normalized_text)
        extracted_text = "\n\n".join(text_parts)
        return extracted_text or None
    except Exception:
        return None


def _ocr_png_bytes(png_bytes: bytes) -> str | None:
    """OCR PNG bytes with grayscale preprocessing and form-aware config."""
    if shutil.which("tesseract") is None:
        return None

    try:
        with Image.open(BytesIO(png_bytes)) as image:
            gray = image.convert("L")
            try:
                ocr_text = pytesseract.image_to_string(gray, config=_OCR_CONFIG)
            finally:
                gray.close()
        normalized_text = _normalize_extracted_text(ocr_text)
        return normalized_text or None
    except Exception:
        return None


def _pdf_bytes_to_all_png_bytes(pdf_bytes: bytes, scale: int = 2) -> list[bytes] | None:
    """Render all PDF pages to PNG bytes.

    Args:
        pdf_bytes: PDF file bytes.
        scale: Render scale multiplier (72 DPI x scale). Default 2 (144 DPI)
            for display; use ``_OCR_RENDER_SCALE`` for OCR.
    """
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
                bitmap = page.render(scale=scale)
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
        ocr_pngs = _pdf_bytes_to_all_png_bytes(pdf_bytes, scale=_OCR_RENDER_SCALE)
        if ocr_pngs:
            ocr_text_parts = []
            for page_png in ocr_pngs:
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


def save_pdf_from_html(base64_html: str) -> dict[str, Any]:
    """Convert base64 encoded HTML content to a PDF file saved in /tmp.

    Note: Uses WeasyPrint for proper HTML/CSS rendering. JavaScript is stripped.

    Args:
        base64_html: Base64 encoded string of the HTML content.

    Returns:
        Dict with ``success``, ``file_path``, and ``error``.
    """
    result = from_html(base64_html)

    if "error" in result:
        return {"success": False, "error": result["error"], "file_path": None}

    try:
        temp_dir = _get_temp_dir()
        file_name = f"{uuid.uuid4()}.pdf"
        file_path = os.path.join(temp_dir, file_name)

        pdf_bytes = base64.b64decode(result["base64_pdf"])
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        return {"success": True, "file_path": file_path, "error": None}
    except Exception as exc:
        return {"success": False, "error": f"Failed to save file: {exc!s}", "file_path": None}


def save_pdf_from_png(base64_png: str) -> dict[str, Any]:
    """Convert base64 encoded PNG content to a PDF file saved in /tmp.

    Args:
        base64_png: Base64 encoded string of the PNG content.

    Returns:
        Dict with ``success``, ``file_path``, and ``error``.
    """
    result = from_png(base64_png)

    if "error" in result:
        return {"success": False, "error": result["error"], "file_path": None}

    try:
        temp_dir = _get_temp_dir()
        file_name = f"{uuid.uuid4()}.pdf"
        file_path = os.path.join(temp_dir, file_name)

        pdf_bytes = base64.b64decode(result["base64_pdf"])
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        return {"success": True, "file_path": file_path, "error": None}
    except Exception as exc:
        return {"success": False, "error": f"Failed to save file: {exc!s}", "file_path": None}


def save_html_from_pdf(base64_pdf: str) -> dict[str, Any]:
    """Convert base64 encoded PDF content to an HTML file saved in /tmp.

    Args:
        base64_pdf: Base64 encoded string of the PDF content.

    Returns:
        Dict with ``success``, ``file_path``, and ``error``.
    """
    result = to_html(base64_pdf)

    if "error" in result:
        return {"success": False, "error": result["error"], "file_path": None}

    try:
        temp_dir = _get_temp_dir()
        file_name = f"{uuid.uuid4()}.html"
        file_path = os.path.join(temp_dir, file_name)

        html_bytes = base64.b64decode(result["base64_html"])
        with open(file_path, "wb") as f:
            f.write(html_bytes)

        return {"success": True, "file_path": file_path, "error": None}
    except Exception as exc:
        return {"success": False, "error": f"Failed to save file: {exc!s}", "file_path": None}


def save_png_from_pdf(base64_pdf: str, page_number: int = 1) -> dict[str, Any]:
    """Convert base64 encoded PDF content to a PNG file saved in /tmp.

    Args:
        base64_pdf: Base64 encoded string of the PDF content.
        page_number: One-based PDF page number to render.

    Returns:
        Dict with ``success``, ``file_path``, and ``error``.
    """
    result = to_png(base64_pdf, page_number=page_number)

    if "error" in result:
        return {"success": False, "error": result["error"], "file_path": None}

    try:
        temp_dir = _get_temp_dir()
        file_name = f"{uuid.uuid4()}.png"
        file_path = os.path.join(temp_dir, file_name)

        png_bytes = base64.b64decode(result["base64_png"])
        with open(file_path, "wb") as f:
            f.write(png_bytes)

        return {"success": True, "file_path": file_path, "error": None}
    except Exception as exc:
        return {"success": False, "error": f"Failed to save file: {exc!s}", "file_path": None}


def convert_html_file_to_pdf(file_path: str) -> dict[str, Any]:
    """Read an HTML file and convert it to a PDF file saved in /tmp.

    Accepts any readable file path. Output is written to /tmp/ezpy_tools/pdf/.

    Args:
        file_path: Absolute path to the HTML file.

    Returns:
        Dict with ``success``, ``file_path``, and ``error``.
    """
    error = _validate_input_file(file_path)
    if error is not None:
        return error

    try:
        resolved = Path(file_path).resolve()
        with open(resolved, encoding="utf-8") as f:
            html_content = f.read()

        base64_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
        return save_pdf_from_html(base64_html)
    except Exception as exc:
        return {"success": False, "error": f"Failed to process file: {exc!s}", "file_path": None}


def convert_png_file_to_pdf(file_path: str) -> dict[str, Any]:
    """Read a PNG file and convert it to a PDF file saved in /tmp.

    Accepts any readable file path. Output is written to /tmp/ezpy_tools/pdf/.

    Args:
        file_path: Absolute path to the PNG file.

    Returns:
        Dict with ``success``, ``file_path``, and ``error``.
    """
    error = _validate_input_file(file_path)
    if error is not None:
        return error

    try:
        resolved = Path(file_path).resolve()
        with open(resolved, "rb") as f:
            png_bytes = f.read()

        base64_png = base64.b64encode(png_bytes).decode("utf-8")
        return save_pdf_from_png(base64_png)
    except Exception as exc:
        return {"success": False, "error": f"Failed to process file: {exc!s}", "file_path": None}


def convert_pdf_file_to_html(file_path: str) -> dict[str, Any]:
    """Read a PDF file and convert it to an HTML file saved in /tmp.

    Accepts any readable file path. Output is written to /tmp/ezpy_tools/pdf/.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        Dict with ``success``, ``file_path``, and ``error``.
    """
    error = _validate_input_file(file_path)
    if error is not None:
        return error

    try:
        resolved = Path(file_path).resolve()
        with open(resolved, "rb") as f:
            pdf_bytes = f.read()

        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return save_html_from_pdf(base64_pdf)
    except Exception as exc:
        return {"success": False, "error": f"Failed to process file: {exc!s}", "file_path": None}


def convert_pdf_file_to_png(file_path: str, page_number: int = 1) -> dict[str, Any]:
    """Read a PDF file and convert a page to a PNG file saved in /tmp.

    Accepts any readable file path. Output is written to /tmp/ezpy_tools/pdf/.

    Args:
        file_path: Absolute path to the PDF file.
        page_number: One-based PDF page number to render.

    Returns:
        Dict with ``success``, ``file_path``, and ``error``.
    """
    error = _validate_input_file(file_path)
    if error is not None:
        return error

    try:
        resolved = Path(file_path).resolve()
        with open(resolved, "rb") as f:
            pdf_bytes = f.read()

        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return save_png_from_pdf(base64_pdf, page_number=page_number)
    except Exception as exc:
        return {"success": False, "error": f"Failed to process file: {exc!s}", "file_path": None}
