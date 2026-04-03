"""Tests for PDF utilities."""

from __future__ import annotations

import base64
import os
import tempfile

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


def test_from_html_file_success() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write("<html><body><p>Test File</p></body></html>")
        html_path = f.name

    try:
        result = pdf_utils.from_html_file(html_path)
        assert result["success"] is True
        assert result["file_size"] > 0
        assert result["output_path"].endswith(".pdf")
        assert os.path.exists(result["output_path"])
        os.unlink(result["output_path"])
    finally:
        os.unlink(html_path)


def test_from_html_file_not_found() -> None:
    result = pdf_utils.from_html_file("/nonexistent/file.html")
    assert result["success"] is False
    assert "error" in result
    assert result["file_size"] == 0


def test_to_html_file_success() -> None:
    pdf_content = b"%PDF-1.4\n1 0 obj\n(File Test)\nendobj"
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
        f.write(pdf_content)
        pdf_path = f.name

    try:
        result = pdf_utils.to_html_file(pdf_path)
        assert result["success"] is True
        assert result["file_size"] > 0
        assert result["output_path"].endswith(".html")
        assert os.path.exists(result["output_path"])
        os.unlink(result["output_path"])
    finally:
        os.unlink(pdf_path)


def test_to_html_file_not_found() -> None:
    result = pdf_utils.to_html_file("/nonexistent/file.pdf")
    assert result["success"] is False
    assert "error" in result
    assert result["file_size"] == 0


def test_from_html_file_with_dest_path() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write("<html><body><p>Custom Dest</p></body></html>")
        html_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        dest_path = f.name

    try:
        result = pdf_utils.from_html_file(html_path, dest_path)
        assert result["success"] is True
        assert result["file_size"] > 0
        assert result["output_path"] == dest_path
        assert os.path.exists(dest_path)
    finally:
        os.unlink(html_path)
        if os.path.exists(dest_path):
            os.unlink(dest_path)


def test_to_html_file_with_dest_path() -> None:
    pdf_content = b"%PDF-1.4\n1 0 obj\n(Custom Dest)\nendobj"
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
        f.write(pdf_content)
        pdf_path = f.name

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        dest_path = f.name

    try:
        result = pdf_utils.to_html_file(pdf_path, dest_path)
        assert result["success"] is True
        assert result["file_size"] > 0
        assert result["output_path"] == dest_path
        assert os.path.exists(dest_path)
    finally:
        os.unlink(pdf_path)
        if os.path.exists(dest_path):
            os.unlink(dest_path)
