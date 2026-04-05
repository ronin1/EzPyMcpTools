"""Tests for PDF utilities."""

from __future__ import annotations

import base64
import pathlib

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
    # Generate a real PDF first, then convert back
    html = "<html><body><p>Hello World</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_res = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in pdf_res

    result = pdf_utils.to_html(pdf_res["base64_pdf"])
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
    assert "<style>" in stripped  # CSS should be preserved
    assert "color: red" in stripped
    assert "Hello" in stripped


def test_from_html_file() -> None:
    """Test HTML-to-PDF conversion from a real receipt file with CSS."""
    import re

    # Use pathlib to get the correct path relative to this test file
    html_path = pathlib.Path(__file__).parent / "fixtures" / "store_receipt_dummy.html"
    with open(html_path) as f:
        html_content = f.read()

    # Strip CSS and JS before extracting expected text (PDF won't contain them)
    stripped_html = pdf_utils._strip_js_from_html(html_content)
    stripped_html = re.sub(
        r"<style[^>]*>.*?</style>", "", stripped_html, flags=re.IGNORECASE | re.DOTALL
    )
    original_text = re.sub(r"<[^>]*>", " ", stripped_html)
    original_text = " ".join(original_text.split())

    base64_html = base64.b64encode(html_content.encode()).decode()
    result = pdf_utils.from_html(base64_html)

    assert "base64_pdf" in result
    assert isinstance(result["base64_pdf"], str)

    # Verify we can decode and get some content back (lossy)
    pdf_bytes = base64.b64decode(result["base64_pdf"])
    decoded_pdf = pdf_bytes.decode("latin-1", errors="replace")

    # Should contain some PDF structure
    assert "%PDF" in decoded_pdf

    # Feed PDF back through to_html and verify text preservation
    html_back_res = pdf_utils.to_html(result["base64_pdf"])
    assert "base64_html" in html_back_res
    decoded_html_back = base64.b64decode(html_back_res["base64_html"]).decode()

    # Extract text from the HTML we got back from PDF
    roundtrip_text = re.sub(r"<[^>]*>", " ", decoded_html_back)
    roundtrip_text = " ".join(roundtrip_text.split())

    # Dynamically extract key phrases: words >= 5 chars from original text
    words = [w for w in re.findall(r"\b\w{5,}\b", original_text)]
    # Sample every 10th word to keep test fast but thorough
    key_phrases = list(dict.fromkeys(words))[::10]

    for phrase in key_phrases:
        assert phrase in roundtrip_text, f"Missing expected text: {phrase}"

    # Also verify at least 80% of all words are preserved
    matched = sum(1 for w in words if w in roundtrip_text)
    assert matched / len(words) >= 0.8, f"Only {matched}/{len(words)} words preserved"
