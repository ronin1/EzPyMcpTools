"""Tests for PDF utilities."""

from __future__ import annotations

import base64

from utils import pdf as pdf_utils


def test_from_html_success() -> None:
    html = "<html><body><h1>Hello</h1></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    result = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in result
    assert isinstance(result["base64_pdf"], str)


def test_from_html_invalid_base64() -> None:
    result = pdf_utils.from_html("not-base64")
    assert "error" in result


def test_to_html_success() -> None:
    pdf_content = b"%PDF-1.4\n1 0 obj\n(Hello World)\nendobj"
    base64_pdf = base64.b64encode(pdf_content).decode()
    result = pdf_utils.to_html(base64_pdf)
    assert "base64_html" in result
    decoded_html = base64.b64decode(result["base64_html"]).decode()
    assert "Hello World" in decoded_html


def test_to_html_invalid_base64() -> None:
    result = pdf_utils.to_html("not-base64")
    assert "error" in result


def test_pdf_roundtrip() -> None:
    original_html = "<html><body><p>Test Content</p></body></html>"
    base64_html = base64.b64encode(original_html.encode()).decode()

    pdf_res = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in pdf_res

    html_back_res = pdf_utils.to_html(pdf_res["base64_pdf"])
    assert "base64_html" in html_back_res


def test_from_html_special_chars() -> None:
    html = "<html><body><p>Test</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_res = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in pdf_res

    html_back_res = pdf_utils.to_html(pdf_res["base64_pdf"])
    assert "base64_html" in html_back_res


def test_strip_js_from_html() -> None:
    html_with_js = (
        "<html><head><style>body { color: red; }</style></head>"
        '<body><p onclick="evil()">Hello</p>'
        "<script>console.log('hello');</script></body></html>"
    )
    stripped = pdf_utils._strip_js_from_html(html_with_js)
    assert "onclick" not in stripped
    assert "<script>" not in stripped
    assert "<style>" not in stripped
    assert "Hello" in stripped
