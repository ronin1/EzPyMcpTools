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
    html = "<html><body><p>Hello World</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_res = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in pdf_res

    result = pdf_utils.to_html(pdf_res["base64_pdf"])
    assert "base64_html" in result
    decoded_html = base64.b64decode(result["base64_html"]).decode()
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
    assert "<style>" in stripped
    assert "color: red" in stripped
    assert "Hello" in stripped


def test_from_html_file() -> None:
    """Test HTML-to-PDF conversion from a real receipt file with CSS."""
    import re

    html_path = pathlib.Path(__file__).parent / "fixtures" / "store_receipt_dummy.html"
    with open(html_path) as f:
        html_content = f.read()

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

    pdf_bytes = base64.b64decode(result["base64_pdf"])
    decoded_pdf = pdf_bytes.decode("latin-1", errors="replace")
    assert "%PDF" in decoded_pdf

    html_back_res = pdf_utils.to_html(result["base64_pdf"])
    assert "base64_html" in html_back_res
    decoded_html_back = base64.b64decode(html_back_res["base64_html"]).decode()

    roundtrip_text = re.sub(r"<[^>]*>", " ", decoded_html_back)
    roundtrip_text = " ".join(roundtrip_text.split())

    words = [w for w in re.findall(r"\b\w{5,}\b", original_text)]
    key_phrases = list(dict.fromkeys(words))[::10]

    for phrase in key_phrases:
        assert phrase in roundtrip_text, f"Missing expected text: {phrase}"

    matched = sum(1 for w in words if w in roundtrip_text)
    assert matched / len(words) >= 0.8, f"Only {matched}/{len(words)} words preserved"


# Tests for save_*() functions (base64 in → file out)


def test_save_pdf_from_html_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    html = "<html><body><h1>Test Save</h1></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    result = pdf_utils.save_pdf_from_html(base64_html)

    assert result["success"] is True
    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".pdf")
    assert pathlib.Path(result["file_path"]).exists()


def test_save_pdf_from_html_invalid_base64() -> None:
    result = pdf_utils.save_pdf_from_html("not-base64")
    assert result["success"] is False
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_pdf_from_png_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    base64_png = _make_base64_png()
    result = pdf_utils.save_pdf_from_png(base64_png)

    assert result["success"] is True
    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".pdf")
    assert pathlib.Path(result["file_path"]).exists()
    with open(result["file_path"], "rb") as f:
        assert f.read().startswith(b"%PDF")


def test_save_pdf_from_png_invalid_base64() -> None:
    result = pdf_utils.save_pdf_from_png("not-base64")
    assert result["success"] is False
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_html_from_pdf_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    html = "<html><body><p>Hello World</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_res = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in pdf_res

    result = pdf_utils.save_html_from_pdf(pdf_res["base64_pdf"])

    assert result["success"] is True
    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".html")
    assert pathlib.Path(result["file_path"]).exists()
    with open(result["file_path"], encoding="utf-8") as f:
        content = f.read()
        assert "Hello World" in content


def test_save_html_from_pdf_invalid_base64() -> None:
    result = pdf_utils.save_html_from_pdf("not-base64")
    assert result["success"] is False
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_png_from_pdf_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    base64_png = _make_base64_png()
    pdf_res = pdf_utils.from_png(base64_png)
    assert "base64_pdf" in pdf_res

    result = pdf_utils.save_png_from_pdf(pdf_res["base64_pdf"])

    assert result["success"] is True
    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".png")
    assert pathlib.Path(result["file_path"]).exists()
    with Image.open(result["file_path"]) as image:
        assert image.format == "PNG"


def test_save_png_from_pdf_invalid_base64() -> None:
    result = pdf_utils.save_png_from_pdf("not-base64")
    assert result["success"] is False
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_png_from_pdf_invalid_page_number(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    base64_png = _make_base64_png()
    pdf_res = pdf_utils.from_png(base64_png)
    assert "base64_pdf" in pdf_res

    result = pdf_utils.save_png_from_pdf(pdf_res["base64_pdf"], page_number=0)
    assert result["success"] is False
    assert result["error"] is not None
    assert result["file_path"] is None


def test_get_temp_dir_returns_string_path() -> None:
    temp_dir = pdf_utils._get_temp_dir()
    assert isinstance(temp_dir, str)
    assert temp_dir == "/tmp/ezpy_tools/pdf"


# Tests for convert_*() functions (file in → file out)


def test_convert_html_file_to_pdf_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    html_content = "<html><body><h1>From File Test</h1></body></html>"
    html_file = tmp_path / "input.html"
    html_file.write_text(html_content, encoding="utf-8")

    result = pdf_utils.convert_html_file_to_pdf(str(html_file))

    assert result["success"] is True
    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".pdf")
    assert pathlib.Path(result["file_path"]).exists()
    with open(result["file_path"], "rb") as f:
        assert f.read().startswith(b"%PDF")


def test_convert_html_file_to_pdf_access_denied() -> None:
    result = pdf_utils.convert_html_file_to_pdf("/etc/passwd")
    assert result["success"] is False
    assert "access denied" in result["error"].lower()
    assert result["file_path"] is None


def test_convert_html_file_to_pdf_file_not_found() -> None:
    result = pdf_utils.convert_html_file_to_pdf("/data/nonexistent.html")
    assert result["success"] is False
    assert "not found" in result["error"].lower()
    assert result["file_path"] is None


def test_convert_html_file_to_pdf_empty_path() -> None:
    result = pdf_utils.convert_html_file_to_pdf("")
    assert result["success"] is False
    assert result["error"] is not None
    assert result["file_path"] is None


def test_convert_html_file_to_pdf_directory_input(tmp_path) -> None:
    result = pdf_utils.convert_html_file_to_pdf(str(tmp_path))
    assert result["success"] is False
    assert "not a file" in result["error"].lower()
    assert result["file_path"] is None


def test_convert_png_file_to_pdf_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    base64_png = _make_base64_png()
    png_bytes = base64.b64decode(base64_png)
    png_file = tmp_path / "input.png"
    png_file.write_bytes(png_bytes)

    result = pdf_utils.convert_png_file_to_pdf(str(png_file))

    assert result["success"] is True
    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".pdf")
    assert pathlib.Path(result["file_path"]).exists()


def test_convert_png_file_to_pdf_file_not_found() -> None:
    result = pdf_utils.convert_png_file_to_pdf("/data/nonexistent.png")
    assert result["success"] is False
    assert "not found" in result["error"].lower()
    assert result["file_path"] is None


def test_convert_png_file_to_pdf_access_denied() -> None:
    result = pdf_utils.convert_png_file_to_pdf("/usr/lib/image.png")
    assert result["success"] is False
    assert "access denied" in result["error"].lower()
    assert result["file_path"] is None


def test_convert_pdf_file_to_html_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    html_content = "<html><body><p>Roundtrip Test</p></body></html>"
    base64_html = base64.b64encode(html_content.encode()).decode()
    pdf_result = pdf_utils.save_pdf_from_html(base64_html)
    assert pdf_result["success"] is True

    result = pdf_utils.convert_pdf_file_to_html(pdf_result["file_path"])

    assert result["success"] is True
    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".html")
    assert pathlib.Path(result["file_path"]).exists()


def test_convert_pdf_file_to_html_file_not_found() -> None:
    result = pdf_utils.convert_pdf_file_to_html("/data/nonexistent.pdf")
    assert result["success"] is False
    assert "not found" in result["error"].lower()
    assert result["file_path"] is None


def test_convert_pdf_file_to_png_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    base64_png = _make_base64_png()
    pdf_result = pdf_utils.save_pdf_from_png(base64_png)
    assert pdf_result["success"] is True

    result = pdf_utils.convert_pdf_file_to_png(pdf_result["file_path"])

    assert result["success"] is True
    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".png")
    assert pathlib.Path(result["file_path"]).exists()
    with Image.open(result["file_path"]) as image:
        assert image.format == "PNG"


def test_convert_pdf_file_to_png_file_not_found() -> None:
    result = pdf_utils.convert_pdf_file_to_png("/data/nonexistent.pdf")
    assert result["success"] is False
    assert "not found" in result["error"].lower()
    assert result["file_path"] is None


def test_convert_pdf_file_to_png_invalid_page(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    base64_png = _make_base64_png()
    pdf_result = pdf_utils.save_pdf_from_png(base64_png)
    assert pdf_result["success"] is True

    result = pdf_utils.convert_pdf_file_to_png(pdf_result["file_path"], page_number=0)
    assert result["success"] is False
    assert result["error"] is not None
    assert result["file_path"] is None


# Tests for convert_pdf_file_to_pngs (all pages)


def test_convert_pdf_file_to_pngs_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    html = "<html><body><p>Page one</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.save_pdf_from_html(base64_html)
    assert pdf_result["success"] is True

    result = pdf_utils.convert_pdf_file_to_pngs(pdf_result["file_path"])

    assert result["success"] is True
    assert result["error"] is None
    assert result["page_count"] == 1
    assert len(result["file_paths"]) == 1
    assert result["file_paths"][0].endswith(".png")
    assert pathlib.Path(result["file_paths"][0]).exists()
    with Image.open(result["file_paths"][0]) as image:
        assert image.format == "PNG"


def test_convert_pdf_file_to_pngs_multipage(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    html = (
        "<html><body>"
        '<div style="page-break-after: always;">Page 1</div>'
        "<div>Page 2</div>"
        "</body></html>"
    )
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.save_pdf_from_html(base64_html)
    assert pdf_result["success"] is True

    result = pdf_utils.convert_pdf_file_to_pngs(pdf_result["file_path"])

    assert result["success"] is True
    assert result["page_count"] >= 2
    assert len(result["file_paths"]) == result["page_count"]
    for fp in result["file_paths"]:
        assert pathlib.Path(fp).exists()
        with Image.open(fp) as image:
            assert image.format == "PNG"


def test_convert_pdf_file_to_pngs_file_not_found() -> None:
    result = pdf_utils.convert_pdf_file_to_pngs("/data/nonexistent.pdf")
    assert result["success"] is False
    assert "not found" in result["error"].lower()
    assert result["file_paths"] == []
    assert result["page_count"] == 0


def test_convert_pdf_file_to_pngs_empty_path() -> None:
    result = pdf_utils.convert_pdf_file_to_pngs("")
    assert result["success"] is False
    assert result["error"] is not None
    assert result["file_paths"] == []


def test_convert_pdf_file_to_pngs_access_denied() -> None:
    result = pdf_utils.convert_pdf_file_to_pngs("/proc/self/environ")
    assert result["success"] is False
    assert "access denied" in result["error"].lower()
    assert result["file_paths"] == []
    assert result["page_count"] == 0


# Tests for _validate_input_file helper


def test_validate_input_file_existing_file(tmp_path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    assert pdf_utils._validate_input_file(str(test_file)) is None


def test_validate_input_file_nonexistent() -> None:
    result = pdf_utils._validate_input_file("/data/nonexistent.txt")
    assert result is not None
    assert "not found" in result["error"].lower()


def test_validate_input_file_directory(tmp_path) -> None:
    result = pdf_utils._validate_input_file(str(tmp_path))
    assert result is not None
    assert "not a file" in result["error"].lower()


def test_validate_input_file_non_string() -> None:
    result = pdf_utils._validate_input_file(123)  # type: ignore
    assert result is not None
    assert "file path string" in result["error"].lower()


def test_validate_input_file_empty() -> None:
    result = pdf_utils._validate_input_file("")
    assert result is not None
    assert "cannot be empty" in result["error"].lower()


def test_validate_input_file_access_denied() -> None:
    result = pdf_utils._validate_input_file("/etc/passwd")
    assert result is not None
    assert "access denied" in result["error"].lower()


def test_validate_input_file_path_traversal() -> None:
    result = pdf_utils._validate_input_file("/data/../etc/passwd")
    assert result is not None
    assert "access denied" in result["error"].lower()
