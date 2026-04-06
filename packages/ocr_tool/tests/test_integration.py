"""Integration tests for the OCR tool CLI end-to-end flow."""

import json
import struct
import zlib
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ocr_tool.cli import app

runner = CliRunner()


def _create_minimal_png(path: Path) -> None:
    """Create a valid 1x1 pixel PNG file."""
    # IHDR chunk: 1x1, 8-bit RGB
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    ihdr = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + ihdr_crc

    # IDAT chunk: single red pixel, filter byte 0
    raw_data = b"\x00\xff\x00\x00"  # filter=None, R=255, G=0, B=0
    compressed = zlib.compress(raw_data)
    idat_crc = struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    idat = struct.pack(">I", len(compressed)) + b"IDAT" + compressed + idat_crc

    # IEND chunk
    iend_crc = struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + iend_crc

    path.write_bytes(b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend)


@patch("ocr_tool.service.extract_text_local")
def test_full_cli_flow_local(mock_engine: object, tmp_path: Path) -> None:
    """End-to-end: extract command with local mode produces valid JSON and output file."""
    mock_engine.return_value = "hello from ocr"  # type: ignore[union-attr]

    image = tmp_path / "test_image.png"
    _create_minimal_png(image)
    output = tmp_path / "result.txt"

    result = runner.invoke(
        app,
        ["extract", "--image", str(image), "--output", str(output), "--mode", "local"],
    )

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["text"] == "hello from ocr"
    assert data["result"]["mode"] == "local"

    assert output.exists()
    assert output.read_text(encoding="utf-8") == "hello from ocr"


@patch("ocr_tool.service.extract_text_google")
def test_full_cli_flow_google(mock_engine: object, monkeypatch, tmp_path: Path) -> None:
    """End-to-end: extract command with google mode produces valid JSON and output file."""
    monkeypatch.setenv("GOOGLE_CLOUD_VISION_API_KEY", "test-key")
    mock_engine.return_value = "text from google"  # type: ignore[union-attr]

    image = tmp_path / "test_image.png"
    _create_minimal_png(image)
    output = tmp_path / "output.txt"

    result = runner.invoke(
        app,
        ["extract", "--image", str(image), "--output", str(output), "--mode", "google"],
    )

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["text"] == "text from google"
    assert data["result"]["mode"] == "google"

    assert output.exists()
    assert output.read_text(encoding="utf-8") == "text from google"


@patch("ocr_tool.service.extract_text_local")
def test_default_output_path(mock_engine: object, monkeypatch, tmp_path: Path) -> None:
    """When --output is omitted, the output file defaults to <image_stem>.txt."""
    monkeypatch.delenv("GOOGLE_CLOUD_VISION_API_KEY", raising=False)
    mock_engine.return_value = "default path text"  # type: ignore[union-attr]

    image = tmp_path / "photo.png"
    _create_minimal_png(image)

    # No --mode passed, defaults to google, but no API key => falls back to local
    result = runner.invoke(app, ["extract", "--image", str(image)])

    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True

    default_output = tmp_path / "photo.txt"
    assert default_output.exists()
    assert default_output.read_text(encoding="utf-8") == "default path text"
