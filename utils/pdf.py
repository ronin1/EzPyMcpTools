"""PDF generation utilities."""

from __future__ import annotations

import base64
import re
from typing import Any

from fpdf import FPDF


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

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)

        # Basic HTML tag removal to extract text
        text = re.sub(r"<[^>]*>", " ", html_content)
        text = " ".join(text.split())

        # Encode text to latin-1, replacing unsupported characters with '?'
        # to avoid UnicodeEncodeError in fpdf2 core fonts
        safe_text = text.encode("latin-1", errors="replace").decode("latin-1")

        pdf.multi_cell(0, 10, safe_text)

        pdf_bytes = pdf.output()
        if not isinstance(pdf_bytes, (bytes, bytearray)):
            if isinstance(pdf_bytes, str):
                pdf_bytes = pdf_bytes.encode("latin-1")
            else:
                return {"error": "Failed to generate PDF bytes"}

        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return {"base64_pdf": base64_pdf}
    except Exception as exc:
        return {"error": f"An error occurred during conversion: {exc!s}"}
