"""Tests for PDF utilities."""

from __future__ import annotations

import base64
import pathlib
from io import BytesIO

from PIL import Image

from utils import pdf as pdf_utils


def _make_base64_png(color: tuple[int, int, int] = (200, 50, 60)) -> str:
    image = Image.new("RGB", (48, 32), color)
    try:
        png_buffer = BytesIO()
        image.save(png_buffer, format="PNG")
        return base64.b64encode(png_buffer.getvalue()).decode()
    finally:
        image.close()


def test_from_html_success() -> None:
    html = "<html><body><h1>Hello</h1></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    result = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in result
    assert isinstance(result["base64_pdf"], str)


def test_from_html_invalid_base64() -> None:
    result = pdf_utils.from_html("not-base64")
    assert "error" in result


def test_from_png_success() -> None:
    result = pdf_utils.from_png(_make_base64_png())
    assert "base64_pdf" in result
    assert base64.b64decode(result["base64_pdf"]).startswith(b"%PDF")


def test_from_png_invalid_base64() -> None:
    result = pdf_utils.from_png("not-base64")
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
    # The round-tripped HTML should preserve the original phrase.
    assert "Hello World" in decoded_html


def test_to_html_returns_embedded_source_html() -> None:
    html = (
        "<html><head><style>body { background: #123456; color: white; }</style></head>"
        '<body><h1 onclick="evil()">Styled Receipt</h1>'
        "<script>console.log('nope')</script></body></html>"
    )
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_res = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in pdf_res

    result = pdf_utils.to_html(pdf_res["base64_pdf"])
    assert "base64_html" in result

    decoded_html = base64.b64decode(result["base64_html"]).decode()
    assert "background: #123456" in decoded_html
    assert "Styled Receipt" in decoded_html
    assert "<script" not in decoded_html
    assert "onclick" not in decoded_html


def test_to_html_invalid_base64() -> None:
    result = pdf_utils.to_html("not-base64")
    assert "error" in result


def test_to_html_renders_pages_for_pdf_without_embedded_html() -> None:
    pdf_res = pdf_utils.from_png(_make_base64_png())
    assert "base64_pdf" in pdf_res

    result = pdf_utils.to_html(pdf_res["base64_pdf"])
    assert "base64_html" in result

    decoded_html = base64.b64decode(result["base64_html"]).decode()
    assert 'data-render-mode="rendered-pages"' in decoded_html
    assert "data:image/png;base64," in decoded_html


def test_to_html_uses_ocr_when_text_extraction_is_missing(monkeypatch) -> None:
    pdf_res = pdf_utils.from_png(_make_base64_png())
    assert "base64_pdf" in pdf_res

    monkeypatch.setattr(pdf_utils, "_extract_pdf_text", lambda _: None)
    monkeypatch.setattr(pdf_utils, "_ocr_png_bytes", lambda _: "OCR receipt text")

    result = pdf_utils.to_html(pdf_res["base64_pdf"])
    assert "base64_html" in result

    decoded_html = base64.b64decode(result["base64_html"]).decode()
    assert "OCR receipt text" in decoded_html
    assert "Extracted text" in decoded_html


def test_to_png_success() -> None:
    pdf_res = pdf_utils.from_png(_make_base64_png())
    assert "base64_pdf" in pdf_res

    result = pdf_utils.to_png(pdf_res["base64_pdf"])
    assert "base64_png" in result

    with Image.open(BytesIO(base64.b64decode(result["base64_png"]))) as image:
        assert image.format == "PNG"
        assert image.size[0] > 0
        assert image.size[1] > 0


def test_to_png_invalid_base64() -> None:
    result = pdf_utils.to_png("not-base64")
    assert "error" in result


def test_to_png_invalid_page_number() -> None:
    pdf_res = pdf_utils.from_png(_make_base64_png())
    assert "base64_pdf" in pdf_res

    result = pdf_utils.to_png(pdf_res["base64_pdf"], page_number=0)
    assert result == {"error": "Page number must be greater than 0"}


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


def test_png_pdf_roundtrip() -> None:
    pdf_res = pdf_utils.from_png(_make_base64_png())
    assert "base64_pdf" in pdf_res

    png_res = pdf_utils.to_png(pdf_res["base64_pdf"])
    assert "base64_png" in png_res

    with Image.open(BytesIO(base64.b64decode(png_res["base64_png"]))) as image:
        rgb_image = image.convert("RGB")
        pixel = rgb_image.getpixel((rgb_image.size[0] // 2, rgb_image.size[1] // 2))
        assert isinstance(pixel, tuple)
        red = pixel[0]
        green = pixel[1]
        blue = pixel[2]
        assert red > green
        assert red > blue


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
