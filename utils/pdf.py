"""PDF generation utilities."""

from __future__ import annotations

import base64
import os
import re
from typing import Any

from fpdf import FPDF


def _html_to_pdf_bytes(html_content: str) -> bytes | None:
    """Convert HTML content string to PDF bytes.

    Args:
        html_content: HTML string content.

    Returns:
        PDF bytes or None if conversion fails.
    """
    try:
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


def from_html_file(src_path: str, dest_path: str | None = None) -> dict[str, Any]:
    """Read an HTML file and convert it to a PDF file.

    Args:
        src_path: Path to the input HTML file.
        dest_path: Optional path for the output PDF file. Defaults to same name with .pdf extension.

    Returns:
        Dict with "success", "file_size", and "output_path" keys.
    """
    try:
        with open(src_path, encoding="utf-8") as f:
            html_content = f.read()

        pdf_bytes = _html_to_pdf_bytes(html_content)
        if pdf_bytes is None:
            return {"success": False, "error": "Failed to generate PDF bytes", "file_size": 0}

        output_path = dest_path if dest_path else os.path.splitext(src_path)[0] + ".pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        file_size = os.path.getsize(output_path)
        return {"success": True, "file_size": file_size, "output_path": output_path}
    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {src_path}", "file_size": 0}
    except Exception as exc:
        return {"success": False, "error": str(exc), "file_size": 0}


def to_html_file(src_path: str, dest_path: str | None = None) -> dict[str, Any]:
    """Read a PDF file and convert it to an HTML file.

    Args:
        src_path: Path to the input PDF file.
        dest_path: Optional path for the output HTML file.
            Defaults to same name with .html extension.

    Returns:
        Dict with "success", "file_size", and "output_path" keys.
    """
    try:
        with open(src_path, "rb") as f:
            pdf_bytes = f.read()

        html_content = _pdf_bytes_to_html(pdf_bytes)
        if html_content is None:
            return {"success": False, "error": "Failed to extract HTML from PDF", "file_size": 0}

        output_path = dest_path if dest_path else os.path.splitext(src_path)[0] + ".html"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        file_size = os.path.getsize(output_path)
        return {"success": True, "file_size": file_size, "output_path": output_path}
    except FileNotFoundError:
        return {"success": False, "error": f"File not found: {src_path}", "file_size": 0}
    except Exception as exc:
        return {"success": False, "error": str(exc), "file_size": 0}
