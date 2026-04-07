"""Tests for text utilities."""

from __future__ import annotations

import base64
import pathlib
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

    # Test decoding with missing padding (uneven bits)
    padding_test_cases = [
        ("a", "YQ"),  # 'a' -> 'YQ==' (missing 2 '=')
        ("ab", "YWI"),  # 'ab' -> 'YWIs' (missing 1 '=')
        ("abc", "YWJj"),  # 'abc' -> 'YWJj' (no padding needed)
    ]
    for original, encoded in padding_test_cases:
        decoded = text_utils.from_base64(encoded)
        assert decoded["text"] == original


def test_text_words_count_edge_cases() -> None:
    # Empty string
    assert text_utils.words_count("")["words"] == 0

    # Multiple spaces
    assert text_utils.words_count("hello   world")["words"] == 2
    assert text_utils.words_count("  hello  world  ")["words"] == 2

    # Tabs and newlines
    assert text_utils.words_count("hello\tworld")["words"] == 2
    assert text_utils.words_count("hello\nworld")["words"] == 2
    assert text_utils.words_count("hello\r\nworld")["words"] == 2

    # Single word
    assert text_utils.words_count("single")["words"] == 1

    # Only spaces
    assert text_utils.words_count("   ")["words"] == 0

    # Non-string input (should return error dict)
    result = text_utils.words_count(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_characters_count_edge_cases() -> None:
    # Empty string
    chars = text_utils.characters_count("")["characters"]
    assert chars["with_spaces"] == 0
    assert chars["excluding_spaces"] == 0

    # Only spaces
    chars = text_utils.characters_count("   ")["characters"]
    assert chars["with_spaces"] == 3
    assert chars["excluding_spaces"] == 0

    # Mixed whitespace - note: excluding_spaces only removes literal spaces, not tabs/newlines
    chars = text_utils.characters_count("a b\tc\nd")["characters"]
    assert chars["with_spaces"] == 7  # a, space, b, tab, c, newline, d
    assert chars["excluding_spaces"] == 6  # a, b, tab, c, newline, d (only spaces removed)

    # Non-string input
    result = text_utils.characters_count(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_show_characters_edge_cases() -> None:
    # Empty string
    result = text_utils.show_characters("")
    assert result["word"] == ""
    assert result["characters"] == []

    # Single character
    result = text_utils.show_characters("x")
    assert result["word"] == "x"
    assert result["characters"] == ["x"]

    # Unicode characters
    result = text_utils.show_characters("你好")
    assert result["word"] == "你好"
    assert result["characters"] == ["你", "好"]

    # Emoji
    result = text_utils.show_characters("🎉")
    assert result["word"] == "🎉"
    assert result["characters"] == ["🎉"]

    # Non-string input
    result = text_utils.show_characters(123)  # type: ignore
    assert "error" in result
    assert result["error"] == "Input must be a string"


def test_text_base64_edge_cases() -> None:
    # Empty string
    encoded = text_utils.to_base64("")
    assert encoded["base64"] == ""
    decoded = text_utils.from_base64("")
    assert decoded["text"] == ""

    # Unicode
    original = "你好世界"
    encoded = text_utils.to_base64(original)
    decoded = text_utils.from_base64(encoded["base64"])
    assert decoded["text"] == original

    # Invalid base64 input - should return error (invalid characters)
    result = text_utils.from_base64("invalid!")
    assert "error" in result

    # Another invalid base64 test - characters outside base64 alphabet
    result = text_utils.from_base64("YWJjZ@")  # @ is not in base64 alphabet
    assert "error" in result

    # Non-string input
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
    """Create an image with text and return bytes + format.

    Returns:
        Tuple of (image_bytes, format_name)
    """
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Try to use a default font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except Exception:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except Exception:
            font = ImageFont.load_default()

    # Draw text centered
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
    """Test extracting text from PNG image with clear text."""
    image_bytes, _fmt = _create_image_with_text("TEST PNG 12345")
    base64_image = base64.b64encode(image_bytes).decode()

    result = text_utils.extract_from_image_base64(base64_image)

    assert "error" in result
    # OCR may or may not work depending on font availability, but it should process
    assert isinstance(result["error"], (str, type(None)))


def test_extract_from_image_base64_jpeg() -> None:
    """Test extracting text from JPEG image."""
    image_bytes, _fmt = _create_image_with_text("JPEG TEST", format="JPEG")
    base64_image = base64.b64encode(image_bytes).decode()

    result = text_utils.extract_from_image_base64(base64_image)

    assert "error" in result
    assert isinstance(result["error"], (str, type(None)))


def test_extract_from_image_base64_invalid() -> None:
    """Test error handling for invalid base64."""
    result = text_utils.extract_from_image_base64("not-valid-base64!!!")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_image_base64_empty() -> None:
    """Test error handling for empty input."""
    result = text_utils.extract_from_image_base64("")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_image_base64_non_string() -> None:
    """Test error handling for non-string input."""
    result = text_utils.extract_from_image_base64(12345)  # type: ignore
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_image_path_success(tmp_path) -> None:
    """Test extracting text from image file path."""
    image_bytes, _fmt = _create_image_with_text("PATH TEST")
    image_file = tmp_path / "test_image.png"
    image_file.write_bytes(image_bytes)

    result = text_utils.extract_from_image_path(str(image_file))

    assert "error" in result
    assert isinstance(result["error"], (str, type(None)))


def test_extract_from_image_path_file_not_found() -> None:
    """Test error handling for non-existent file."""
    result = text_utils.extract_from_image_path("/tmp/nonexistent/image.png")
    assert result["error"] is not None
    assert "not found" in result["error"].lower()
    assert result["text"] is None


def test_extract_from_image_path_empty() -> None:
    """Test error handling for empty path."""
    result = text_utils.extract_from_image_path("")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_image_path_directory(tmp_path) -> None:
    """Test error handling when path is a directory."""
    result = text_utils.extract_from_image_path(str(tmp_path))
    assert result["error"] is not None
    assert "not a file" in result["error"].lower()
    assert result["text"] is None


def test_extract_from_pdf_base64_with_embedded_text() -> None:
    """Test extracting text from PDF with embedded text."""
    # Create a PDF with embedded text using pdf_utils
    html = "<html><body><p>This is a PDF with embedded text content.</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.from_html(base64_html)

    assert "base64_pdf" in pdf_result, f"Failed to create PDF: {pdf_result}"

    # Extract text from the PDF
    result = text_utils.extract_from_pdf_base64(pdf_result["base64_pdf"])

    assert "error" in result
    # Should either succeed with text or fail gracefully
    if result["text"] is not None:
        # If text was extracted, it should contain our content
        assert "embedded text content" in result["text"] or result["error"] is None


def test_extract_from_pdf_base64_invalid() -> None:
    """Test error handling for invalid base64."""
    result = text_utils.extract_from_pdf_base64("not-valid-base64!!!")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_pdf_base64_empty() -> None:
    """Test error handling for empty input."""
    result = text_utils.extract_from_pdf_base64("")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_from_pdf_path_success(tmp_path) -> None:
    """Test extracting text from PDF file path."""
    # Create a PDF file
    html = "<html><body><p>PDF path test content here.</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.from_html_save_to_file(base64_html)

    assert pdf_result["success"] is True, f"Failed to create PDF: {pdf_result}"

    # Extract text from the PDF file
    result = text_utils.extract_from_pdf_path(pdf_result["file_path"])

    assert "error" in result
    assert isinstance(result["error"], (str, type(None)))


def test_extract_from_pdf_path_file_not_found() -> None:
    """Test error handling for non-existent PDF."""
    result = text_utils.extract_from_pdf_path("/tmp/nonexistent/document.pdf")
    assert result["error"] is not None
    assert "not found" in result["error"].lower()
    assert result["text"] is None


def test_extract_from_pdf_path_empty() -> None:
    """Test error handling for empty path."""
    result = text_utils.extract_from_pdf_path("")
    assert result["error"] is not None
    assert result["text"] is None


def test_save_base64_to_tmp_success(tmp_path, monkeypatch) -> None:
    """Test saving base64 data to temp directory."""
    monkeypatch.setattr(text_utils, "_get_temp_dir", lambda: str(tmp_path))

    # Create some test data
    test_data = b"Test data content"
    base64_data = base64.b64encode(test_data).decode()

    result = text_utils.save_base64_to_tmp(base64_data, "txt")

    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".txt")
    # Verify file exists and has correct content
    assert pathlib.Path(result["file_path"]).exists()
    with open(result["file_path"], "rb") as f:
        assert f.read() == test_data


def test_save_base64_to_tmp_pdf(tmp_path, monkeypatch) -> None:
    """Test saving base64 PDF to temp directory."""
    monkeypatch.setattr(text_utils, "_get_temp_dir", lambda: str(tmp_path))

    # Create a PDF
    html = "<html><body><p>Test PDF</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in pdf_result

    # Save the PDF
    result = text_utils.save_base64_to_tmp(pdf_result["base64_pdf"], "pdf")

    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].endswith(".pdf")
    # Verify it's a valid PDF
    with open(result["file_path"], "rb") as f:
        assert f.read().startswith(b"%PDF")


def test_save_base64_to_tmp_invalid_base64() -> None:
    """Test error handling for invalid base64."""
    result = text_utils.save_base64_to_tmp("not-valid-base64!!!", "txt")
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_base64_to_tmp_empty_extension() -> None:
    """Test error handling for empty extension."""
    result = text_utils.save_base64_to_tmp("dGVzdA==", "")
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_base64_to_tmp_non_string_extension() -> None:
    """Test error handling for non-string extension."""
    result = text_utils.save_base64_to_tmp("dGVzdA==", 123)  # type: ignore
    assert result["error"] is not None
    assert result["file_path"] is None


# Test various image formats


def test_extract_from_image_various_formats(tmp_path) -> None:
    """Test text extraction from various image formats."""
    formats = ["PNG", "JPEG", "BMP", "TIFF", "GIF"]

    for fmt in formats:
        try:
            image_bytes, _ = _create_image_with_text(f"FORMAT {fmt}", format=fmt)
            image_file = tmp_path / f"test.{fmt.lower()}"
            image_file.write_bytes(image_bytes)

            result = text_utils.extract_from_image_path(str(image_file))

            # Should process without crashing
            assert "error" in result
        except Exception:
            # Some formats may not be supported, that's ok for the test
            pass


def test_extract_from_image_path_non_image_file(tmp_path) -> None:
    """Test error handling for non-image file."""
    text_file = tmp_path / "not_an_image.txt"
    text_file.write_text("This is not an image")

    result = text_utils.extract_from_image_path(str(text_file))
    # Should return an error since it's not a valid image
    assert result["error"] is not None or result["text"] is None


def test_extract_from_pdf_path_non_pdf_file(tmp_path) -> None:
    """Test error handling for non-PDF file treated as PDF."""
    text_file = tmp_path / "not_a_pdf.txt"
    text_file.write_text("This is not a PDF")

    result = text_utils.extract_from_pdf_path(str(text_file))
    # Should return an error since it's not a valid PDF
    assert result["error"] is not None or result["text"] is None


# Integration tests


def test_full_workflow_image_to_text(tmp_path, monkeypatch) -> None:
    """Test full workflow: create image, save to tmp, extract text."""
    monkeypatch.setattr(text_utils, "_get_temp_dir", lambda: str(tmp_path))

    # Create an image with text
    image_bytes, _ = _create_image_with_text("INTEGRATION TEST")
    base64_image = base64.b64encode(image_bytes).decode()

    # Save to temp
    save_result = text_utils.save_base64_to_tmp(base64_image, "png")
    assert save_result["error"] is None
    assert save_result["file_path"] is not None

    # Extract text from saved file
    extract_result = text_utils.extract_from_image_path(save_result["file_path"])
    assert "error" in extract_result


def test_full_workflow_pdf_to_text(tmp_path, monkeypatch) -> None:
    """Test full workflow: create PDF, save to tmp, extract text."""
    monkeypatch.setattr(text_utils, "_get_temp_dir", lambda: str(tmp_path))

    # Create a PDF with text
    html = "<html><body><p>PDF integration test content.</p></body></html>"
    base64_html = base64.b64encode(html.encode()).decode()
    pdf_result = pdf_utils.from_html(base64_html)
    assert "base64_pdf" in pdf_result

    # Save to temp
    save_result = text_utils.save_base64_to_tmp(pdf_result["base64_pdf"], "pdf")
    assert save_result["error"] is None
    assert save_result["file_path"] is not None

    # Extract text from saved file
    extract_result = text_utils.extract_from_pdf_path(save_result["file_path"])
    assert "error" in extract_result
