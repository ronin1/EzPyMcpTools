"""PDF generation utilities."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any

from xhtml2pdf import pisa


def from_html(base64_html: str) -> dict[str, Any]:
    """Convert base64 encoded HTML content to a base64 encoded PDF.

    Args:
        base64_html: Base64 encoded string of the HTML content.

    Returns:
        Dict containing the base64 encoded PDF content under the key "base64_pdf".
    """
    try:
        html_content = base64.b64decode(base64_html).decode("utf-8")
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

        if pisa_status.err:
            return {"error": "Failed to convert HTML to PDF"}

        pdf_bytes = pdf_buffer.getvalue()
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        return {"base64_pdf": base64_pdf}
    except Exception as exc:
        return {"error": f"An error occurred during conversion: {exc!s}"}
