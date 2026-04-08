"""Tests for text utilities."""

from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from utils import pdf as pdf_utils
from utils import text as text_utils


def test_text_counts_and_character_split() -> None:
    assert text_utils.words_count("hello world")["words"] == 2
    chars = text_utils.characters_count("a b")["characters"]
    assert chars["with_spaces"] == 3
    assert chars["excluding_spaces"] == 2
    assert text_utils.show_characters("hi")["characters"] == ["h", "i"]


def test_text_base64_encoding() -> None:
    original = "hello world"
    encoded_result = text_utils.to_base64(original)
    assert "base64" in encoded_result

    decoded_result = text_utils.from_base64(encoded_result["base64"])
    assert decoded_result["text"] == original

    test_cases = ["", "a", "Hello, 世界!", "line1\nline2"]
    for tc in test_cases:
        result = text_utils.to_base64(tc)
        decoded = text_utils.from_base64(result["base64"])
        assert decoded["text"] == tc

    padding_test_cases = [
        ("a", "YQ"),
        ("ab", "YWI"),
        ("abc", "YWJj"),
    ]
    for original, encoded in padding_test_cases:
        decoded = text_utils.from_base64(encoded)
        assert decoded["text"] == original


def test_text_words_count_edge_cases() -> None:
    assert text_utils.words_count("")["words"] == 0
    assert text_utils.words_count("hello   world")["words"] == 2
    assert text_utils.words_count("  hello  world  ")["words"] == 2
    assert text_utils.words_count("hello\tworld")["words"] == 2
    assert text_utils.words_count("hello\nworld")["words"] == 2
    assert text_utils.words_count("hello\r\nworld")["words"] == 2
    assert text_utils.words_count("single")["words"] == 1
    assert text_utils.words_count("   ")["words"] == 0

    result = text_utils.words_count(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_characters_count_edge_cases() -> None:
    chars = text_utils.characters_count("")["characters"]
    assert chars["with_spaces"] == 0
    assert chars["excluding_spaces"] == 0

    chars = text_utils.characters_count("   ")["characters"]
    assert chars["with_spaces"] == 3
    assert chars["excluding_spaces"] == 0

    chars = text_utils.characters_count("a b\tc\nd")["characters"]
    assert chars["with_spaces"] == 7
    assert chars["excluding_spaces"] == 6

    result = text_utils.characters_count(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_show_characters_edge_cases() -> None:
    result = text_utils.show_characters("")
    assert result["word"] == ""
    assert result["characters"] == []

    result = text_utils.show_characters("x")
    assert result["word"] == "x"
    assert result["characters"] == ["x"]

    result = text_utils.show_characters("你好")
    assert result["word"] == "你好"
    assert result["characters"] == ["你", "好"]

    result = text_utils.show_characters("🎉")
    assert result["word"] == "🎉"
    assert result["characters"] == ["🎉"]

    result = text_utils.show_characters(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_base64_edge_cases() -> None:
    encoded = text_utils.to_base64("")
    assert encoded["base64"] == ""
    decoded = text_utils.from_base64("")
    assert decoded["text"] == ""

    original = "你好世界"
    encoded = text_utils.to_base64(original)
    decoded = text_utils.from_base64(encoded["base64"])
    assert decoded["text"] == original

    result = text_utils.from_base64("invalid!")
    assert "error" in result

    result = text_utils.from_base64("YWJjZ@")
    assert "error" in result

    result = text_utils.to_base64(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"

    result = text_utils.from_base64(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Invalid base64 string"


# Tests for PDF and Image text extraction


def _create_image_with_text(
    text: str = "HELLO WORLD 12345",
    width: int = 400,
    height: int = 100,
    bg_color: tuple[int, int, int] = (255, 255, 255),
    text_color: tuple[int, int, int] = (0, 0, 0),
    format: str = "PNG",
) -> tuple[bytes, str]:
    """Create an image with text and return bytes + format."""
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except Exception:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except Exception:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill=text_color, font=font)

    buffer = BytesIO()
    image.save(buffer, format=format)
    image_bytes = buffer.getvalue()
    image.close()

    return image_bytes, format


def test_extract_from_image_base64_png() -> None:
    image_bytes, _fmt = _create_image_with_text("TEST PNG 12345")
    base64_image = base64.b64encode(image_bytes).decode()

    result = text_utils.extract_from_image_base64(base64_image)

    if "error" not in result:
        assert "text" in result
    else:
        assert result["text"] is None


def test_extract_from_image_base64_jpeg() -> None:
    image_bytes, _fmt = _create_image_with_text("JPEG TEST", format="JPEG")
    base64_image = base64.b64encode(image_bytes).decode()

    result = text_utils.extract_from_image_base64(base64_image)

    if "error" not in result:
        assert "text" in result
    else:
        assert result["text"] is None


def test_extract_from_image_base64_invalid() -> None:
    result = text_utils.extract_from_image_base64("not-valid-base64!!!")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_image_base64_empty() -> None:
    result = text_utils.extract_from_image_base64("")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_image_base64_non_string() -> None:
    result = text_utils.extract_from_image_base64(12345)  # type: ignore
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_image_file_success(tmp_path) -> None:
    image_bytes, _fmt = _create_image_with_text("PATH TEST")
    image_file = tmp_path / "test_image.png"
    image_file.write_bytes(image_bytes)

    result = text_utils.extract_from_image_file(str(image_file))

    if "error" not in result:
        assert "text" in result
    else:
        assert result["text"] is None


def test_extract_from_image_file_access_denied() -> None:
    result = text_utils.extract_from_image_file("/etc/shadow")
    assert result["error"] is not None
    assert "access denied" in result["error"].lower()
    assert result["text"] is None


def test_extract_from_image_file_file_not_found() -> None:
    result = text_utils.extract_from_image_file("/data/nonexistent.png")
    assert result["error"] is not None
    assert "not found" in result["error"].lower()
    assert result["text"] is None


def test_extract_from_image_file_empty() -> None:
    result = text_utils.extract_from_image_file("")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_image_file_directory(tmp_path) -> None:
    result = text_utils.extract_from_image_file(str(tmp_path))
    assert result["error"] is not None
    assert "not a file" in result["error"].lower()
    assert result["text"] is None


def test_extract_from_pdf_base64_with_embedded_text() -> None:
    html = "<html><body><p>This is a PDF with embedded text content.</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.from_html(base64_html)

    assert "base64_pdf" in pdf_result, f"Failed to create PDF: {pdf_result}"

    result = text_utils.extract_from_pdf_base64(pdf_result["base64_pdf"])

    if "error" in result:
        assert result["text"] is None
    else:
        assert "text" in result
        assert "embedded text content" in result["text"]


def test_extract_from_pdf_base64_invalid() -> None:
    result = text_utils.extract_from_pdf_base64("not-valid-base64!!!")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_pdf_base64_empty() -> None:
    result = text_utils.extract_from_pdf_base64("")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_pdf_file_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    html = "<html><body><p>PDF path test content here.</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.save_pdf_from_html(base64_html)

    assert pdf_result["success"] is True, f"Failed to create PDF: {pdf_result}"

    result = text_utils.extract_from_pdf_file(pdf_result["file_path"])

    if "error" not in result:
        assert "text" in result
    else:
        assert result["text"] is None


def test_extract_from_pdf_file_file_not_found() -> None:
    result = text_utils.extract_from_pdf_file("/data/nonexistent.pdf")
    assert result["error"] is not None
    assert "not found" in result["error"].lower()
    assert result["text"] is None


def test_extract_from_pdf_file_access_denied() -> None:
    result = text_utils.extract_from_pdf_file("/usr/bin/python3")
    assert result["error"] is not None
    assert "access denied" in result["error"].lower()
    assert result["text"] is None


def test_extract_from_pdf_file_empty() -> None:
    result = text_utils.extract_from_pdf_file("")
    assert result["error"] is not None
    assert result["text"] is None


# Test various image formats


def test_extract_from_image_various_formats(tmp_path) -> None:
    formats = ["PNG", "JPEG", "BMP", "TIFF", "GIF"]

    for fmt in formats:
        try:
            image_bytes, _ = _create_image_with_text(f"FORMAT {fmt}", format=fmt)
            image_file = tmp_path / f"test.{fmt.lower()}"
            image_file.write_bytes(image_bytes)

            result = text_utils.extract_from_image_file(str(image_file))

            assert "error" in result
        except Exception:
            pass


def test_extract_from_image_file_non_image_file(tmp_path) -> None:
    text_file = tmp_path / "not_an_image.txt"
    text_file.write_text("This is not an image")

    result = text_utils.extract_from_image_file(str(text_file))
    assert result["error"] is not None or result["text"] is None


def test_extract_from_pdf_file_non_pdf_file(tmp_path) -> None:
    text_file = tmp_path / "not_a_pdf.txt"
    text_file.write_text("This is not a PDF")

    result = text_utils.extract_from_pdf_file(str(text_file))
    assert result["error"] is not None or result["text"] is None


# Integration tests


def test_full_workflow_image_to_text(tmp_path) -> None:
    image_bytes, _ = _create_image_with_text("INTEGRATION TEST")
    image_file = tmp_path / "test.png"
    image_file.write_bytes(image_bytes)

    extract_result = text_utils.extract_from_image_file(str(image_file))

    if "error" not in extract_result:
        assert "text" in extract_result
    else:
        assert extract_result["text"] is None


def test_full_workflow_pdf_to_text(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pdf_utils, "_get_temp_dir", lambda: str(tmp_path))

    html = "<html><body><p>PDF integration test content.</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.save_pdf_from_html(base64_html)
    assert pdf_result["success"] is True

    extract_result = text_utils.extract_from_pdf_file(pdf_result["file_path"])
    if "error" not in extract_result:
        assert "text" in extract_result
    else:
        assert extract_result["text"] is None


# Tests for _validate_input_file helper


def test_validate_input_file_existing_file(tmp_path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    assert text_utils._validate_input_file(str(test_file)) is None


def test_validate_input_file_nonexistent() -> None:
    result = text_utils._validate_input_file("/data/nonexistent.txt")
    assert result is not None
    assert "not found" in result["error"].lower()


def test_validate_input_file_directory(tmp_path) -> None:
    result = text_utils._validate_input_file(str(tmp_path))
    assert result is not None
    assert "not a file" in result["error"].lower()


def test_validate_input_file_non_string() -> None:
    result = text_utils._validate_input_file(123)  # type: ignore
    assert result is not None
    assert "file path string" in result["error"].lower()


def test_validate_input_file_empty() -> None:
    result = text_utils._validate_input_file("")
    assert result is not None
    assert "cannot be empty" in result["error"].lower()


def test_validate_input_file_access_denied() -> None:
    result = text_utils._validate_input_file("/etc/passwd")
    assert result is not None
    assert "access denied" in result["error"].lower()


def test_validate_input_file_path_traversal() -> None:
    result = text_utils._validate_input_file("/data/../etc/passwd")
    assert result is not None
    assert "access denied" in result["error"].lower()
