"""Tests for the OCR tool CLI."""

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from ocr_tool.cli import app
from ocr_tool.errors import OcrError
from ocr_tool.models import OcrResult

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "extract" in result.output.lower()


def test_missing_image_option() -> None:
    """Omitting --image exits with a non-zero code."""
    result = runner.invoke(app, [])
    assert result.exit_code != 0


@patch("ocr_tool.cli.run_ocr")
def test_successful_extract(mock_run_ocr, tmp_path: Path) -> None:
    """A successful extraction emits JSON with ok=true and the result payload."""
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")
    output = tmp_path / "photo.txt"

    mock_run_ocr.return_value = OcrResult(
        text="hello world",
        source_image=image,
        output_path=output,
        mode="local",
        model_used="easyocr",
    )

    result = runner.invoke(app, ["--image", str(image)])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["text"] == "hello world"
    assert data["result"]["mode"] == "local"
    assert data["result"]["model_used"] == "easyocr"


def test_invalid_mode() -> None:
    """An invalid --mode value emits JSON with ok=false and INVALID_MODE code."""
    result = runner.invoke(app, ["--image", "photo.png", "--mode", "bad"])
    # emit_error calls sys.exit(1), which typer runner captures as exit_code 1
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_MODE"


@patch(
    "ocr_tool.cli.run_ocr",
    side_effect=OcrError(code="IMAGE_NOT_FOUND", message="File not found"),
)
def test_ocr_error_emits_json_error(mock_run_ocr, tmp_path: Path) -> None:
    """An OcrError from the service is emitted as structured JSON error."""
    image = tmp_path / "missing.png"
    result = runner.invoke(app, ["--image", str(image)])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "IMAGE_NOT_FOUND"
