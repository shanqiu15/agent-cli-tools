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
    result = runner.invoke(app, ["extract"])
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

    result = runner.invoke(app, ["extract", "--image", str(image), "--mode", "local"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["text"] == "hello world"
    assert data["result"]["mode"] == "local"
    assert data["result"]["model_used"] == "easyocr"


def test_invalid_mode() -> None:
    """An invalid --mode value emits JSON with ok=false and INVALID_MODE code."""
    result = runner.invoke(app, ["extract", "--image", "photo.png", "--mode", "bad"])
    # emit_error calls sys.exit(1), which typer runner captures as exit_code 1
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_MODE"


@patch("ocr_tool.cli.run_ocr")
def test_default_google_mode(mock_run_ocr, tmp_path: Path) -> None:
    """Without --mode, the extract command routes to the google engine."""
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")

    mock_run_ocr.return_value = OcrResult(
        text="google result",
        source_image=image,
        output_path=tmp_path / "photo.txt",
        mode="google",
        model_used="google-cloud-vision",
    )

    result = runner.invoke(app, ["extract", "--image", str(image)])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["mode"] == "google"
    assert data["result"]["model_used"] == "google-cloud-vision"

    # Verify the request was built with google mode and explicit_mode=False
    call_args = mock_run_ocr.call_args[0][0]
    assert call_args.mode == "google"
    assert call_args.explicit_mode is False


@patch("ocr_tool.cli.run_ocr")
def test_explicit_local_mode(mock_run_ocr, tmp_path: Path) -> None:
    """--mode local routes to the local engine."""
    image = tmp_path / "photo.png"
    image.write_bytes(b"fake")

    mock_run_ocr.return_value = OcrResult(
        text="local result",
        source_image=image,
        output_path=tmp_path / "photo.txt",
        mode="local",
        model_used="easyocr",
    )

    result = runner.invoke(app, ["extract", "--image", str(image), "--mode", "local"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["mode"] == "local"
    assert data["result"]["model_used"] == "easyocr"

    call_args = mock_run_ocr.call_args[0][0]
    assert call_args.mode == "local"
    assert call_args.explicit_mode is True


def test_invalid_mode_llm() -> None:
    """--mode llm emits a structured JSON error with INVALID_MODE code."""
    result = runner.invoke(app, ["extract", "--image", "photo.png", "--mode", "llm"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_MODE"


@patch(
    "ocr_tool.cli.run_ocr",
    side_effect=OcrError(
        code="UNSUPPORTED_FILE_TYPE",
        message="Local OCR mode does not support PDF files.",
    ),
)
def test_pdf_with_local_mode_error(mock_run_ocr, tmp_path: Path) -> None:
    """PDF input with local mode emits UNSUPPORTED_FILE_TYPE error."""
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"fake-pdf")

    result = runner.invoke(app, ["extract", "--image", str(pdf), "--mode", "local"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


@patch("ocr_tool.cli.run_ocr")
def test_pdf_with_google_mode_accepted(mock_run_ocr, tmp_path: Path) -> None:
    """PDF input with google mode does not fail validation."""
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"fake-pdf")

    mock_run_ocr.return_value = OcrResult(
        text="pdf text",
        source_image=pdf,
        output_path=tmp_path / "document.txt",
        mode="google",
        model_used="google-cloud-vision",
    )

    result = runner.invoke(app, ["extract", "--image", str(pdf), "--mode", "google"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["text"] == "pdf text"


@patch(
    "ocr_tool.cli.run_ocr",
    side_effect=OcrError(code="IMAGE_NOT_FOUND", message="File not found"),
)
def test_ocr_error_emits_json_error(mock_run_ocr, tmp_path: Path) -> None:
    """An OcrError from the service is emitted as structured JSON error."""
    image = tmp_path / "missing.png"
    result = runner.invoke(app, ["extract", "--image", str(image), "--mode", "local"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "IMAGE_NOT_FOUND"
