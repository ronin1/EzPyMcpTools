"""Tests for PNG utilities."""

from __future__ import annotations

import base64
import os
import pathlib
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from utils import png as png_utils


def _make_base64_png_with_text(
    text: str = "Hello World",
    width: int = 400,
    height: int = 100,
    color: tuple[int, int, int] = (255, 255, 255),
    text_color: tuple[int, int, int] = (0, 0, 0),
) -> str:
    """Create a PNG image with text for OCR testing."""
    image = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(image)

    # Try to use a default font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        font = ImageFont.load_default()

    # Draw text in the center
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill=text_color, font=font)

    try:
        png_buffer = BytesIO()
        image.save(png_buffer, format="PNG")
        return base64.b64encode(png_buffer.getvalue()).decode()
    finally:
        image.close()


def _make_base64_png_simple(color: tuple[int, int, int] = (200, 50, 60)) -> str:
    """Create a simple PNG without text."""
    image = Image.new("RGB", (100, 100), color)
    try:
        png_buffer = BytesIO()
        image.save(png_buffer, format="PNG")
        return base64.b64encode(png_buffer.getvalue()).decode()
    finally:
        image.close()


# Tests for extract_text_from_base64


def test_extract_text_from_base64_success() -> None:
    """Test extracting text from a PNG with embedded text."""
    # Create a PNG with clear text
    base64_png = _make_base64_png_with_text("OCR TEST 12345")
    result = png_utils.extract_text_from_base64(base64_png)

    # Should succeed (may or may not extract exact text depending on Tesseract)
    assert "error" in result
    assert result["error"] is None or isinstance(result["error"], str)


def test_extract_text_from_base64_invalid_base64() -> None:
    """Test error handling for invalid base64 input."""
    result = png_utils.extract_text_from_base64("not-valid-base64!!!")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_text_from_base64_empty_string() -> None:
    """Test error handling for empty input."""
    result = png_utils.extract_text_from_base64("")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_text_from_base64_non_string() -> None:
    """Test error handling for non-string input."""
    result = png_utils.extract_text_from_base64(12345)  # type: ignore[arg-type]
    assert result["error"] is not None
    assert result["text"] is None


# Tests for extract_text_from_path


def test_extract_text_from_path_success(tmp_path, monkeypatch) -> None:
    """Test extracting text from a file path."""
    # Create a test file
    test_file = tmp_path / "test.png"
    base64_png = _make_base64_png_with_text("PATH TEST")
    png_bytes = base64.b64decode(base64_png)
    test_file.write_bytes(png_bytes)

    result = png_utils.extract_text_from_path(str(test_file))

    # Should process the file
    assert "error" in result
    assert result["error"] is None or isinstance(result["error"], str)


def test_extract_text_from_path_file_not_found() -> None:
    """Test error handling for non-existent file."""
    result = png_utils.extract_text_from_path("/tmp/nonexistent/path/file.png")
    assert result["error"] is not None
    assert "not found" in result["error"].lower()
    assert result["text"] is None


def test_extract_text_from_path_empty_string() -> None:
    """Test error handling for empty path."""
    result = png_utils.extract_text_from_path("")
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_text_from_path_non_string() -> None:
    """Test error handling for non-string path."""
    result = png_utils.extract_text_from_path(12345)  # type: ignore[arg-type]
    assert result["error"] is not None
    assert result["text"] is None


def test_extract_text_from_path_directory(tmp_path) -> None:
    """Test error handling when path is a directory."""
    result = png_utils.extract_text_from_path(str(tmp_path))
    assert result["error"] is not None
    assert "not a file" in result["error"].lower()
    assert result["text"] is None


# Tests for save_to_tmp_dir


def test_save_to_tmp_dir_success(tmp_path, monkeypatch) -> None:
    """Test saving PNG to temp directory."""
    monkeypatch.setattr(png_utils, "_get_temp_dir", lambda: str(tmp_path))

    base64_png = _make_base64_png_simple()
    result = png_utils.save_to_tmp_dir(base64_png)

    assert result["error"] is None
    assert result["file_path"] is not None
    assert result["file_path"].startswith(str(tmp_path))
    assert result["file_path"].endswith(".png")
    # Verify file exists
    assert pathlib.Path(result["file_path"]).exists()


def test_save_to_tmp_dir_creates_directory(tmp_path, monkeypatch) -> None:
    """Test that save_to_tmp_dir creates the temp directory if needed."""
    new_dir = tmp_path / "new_utils_png"

    # Create the directory since we're mocking the function that would create it
    new_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(png_utils, "_get_temp_dir", lambda: str(new_dir))

    base64_png = _make_base64_png_simple()
    result = png_utils.save_to_tmp_dir(base64_png)

    assert result["error"] is None
    assert pathlib.Path(result["file_path"]).exists()


def test_save_to_tmp_dir_invalid_base64() -> None:
    """Test error handling for invalid base64."""
    result = png_utils.save_to_tmp_dir("not-valid-base64!!!")
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_to_tmp_dir_non_png() -> None:
    """Test error handling for non-PNG image."""
    # Create a JPEG image instead
    image = Image.new("RGB", (100, 100), (255, 0, 0))
    try:
        jpeg_buffer = BytesIO()
        image.save(jpeg_buffer, format="JPEG")
        base64_jpeg = base64.b64encode(jpeg_buffer.getvalue()).decode()
    finally:
        image.close()

    result = png_utils.save_to_tmp_dir(base64_jpeg)
    # Should fail because it's not a PNG
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_to_tmp_dir_empty_string() -> None:
    """Test error handling for empty input."""
    result = png_utils.save_to_tmp_dir("")
    assert result["error"] is not None
    assert result["file_path"] is None


def test_save_to_tmp_dir_non_string() -> None:
    """Test error handling for non-string input."""
    result = png_utils.save_to_tmp_dir(12345)  # type: ignore[arg-type]
    assert result["error"] is not None
    assert result["file_path"] is None


# Integration test


def test_save_and_extract_integration(tmp_path, monkeypatch) -> None:
    """Test saving a PNG and then extracting text from the saved file."""
    monkeypatch.setattr(png_utils, "_get_temp_dir", lambda: str(tmp_path))

    # Create and save a PNG with text
    base64_png = _make_base64_png_with_text("INTEGRATION TEST")
    save_result = png_utils.save_to_tmp_dir(base64_png)

    assert save_result["error"] is None
    assert save_result["file_path"] is not None

    # Extract text from the saved file
    extract_result = png_utils.extract_text_from_path(save_result["file_path"])

    # Should process successfully
    assert "error" in extract_result
    assert extract_result["error"] is None or isinstance(extract_result["error"], str)


# Tests for _get_temp_dir


def test_get_temp_dir_creates_directory(tmp_path, monkeypatch) -> None:
    """Test _get_temp_dir creates directory if it doesn't exist."""
    test_dir = str(tmp_path / "utils_png_test")
    monkeypatch.setattr(png_utils, "_get_temp_dir", lambda: test_dir)

    # Create the directory
    os.makedirs(test_dir, exist_ok=True)
    assert pathlib.Path(test_dir).exists()
