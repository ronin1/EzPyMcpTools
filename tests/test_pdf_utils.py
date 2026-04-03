"""Tests for PDF utilities."""

from __future__ import annotations

import base64

from utils.pdf import from_html


def test_from_html_success():
    html = "<html><body><h1>Hello</h1></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    result = from_html(base64_html)
    assert "base64_pdf" in result
    assert isinstance(result["base64_pdf"], str)


def test_from_html_invalid_base64():
    result = from_html("not-base64")
    assert "error" in result
