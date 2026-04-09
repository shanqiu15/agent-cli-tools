"""Tests for the image gen tool service layer."""

import base64
from unittest.mock import MagicMock, patch

import httpx
import pytest

from cli_common.errors import ToolException
from image_gen_tool.service import generate

# A minimal valid 1x1 red PNG for test purposes
TEST_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
    b"\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00"
    b"\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing GOOGLE_API_KEY raises MISSING_CREDENTIALS."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ToolException) as exc_info:
        generate("a cat", "/tmp/out.png")
    assert exc_info.value.code == "MISSING_CREDENTIALS"
    assert exc_info.value.details["env_var"] == "GOOGLE_API_KEY"


@patch("cli_common.http.httpx.request")
def test_successful_generate(
    mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch, tmp_path: object
) -> None:
    """Successful API call saves image and returns ImageGenResponse."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    from pathlib import Path

    out_file = str(Path(str(tmp_path)) / "output.png")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "predictions": [
            {"bytesBase64Encoded": base64.b64encode(TEST_PNG_BYTES).decode()}
        ]
    }
    mock_request.return_value = mock_response

    result = generate("a cat", out_file, aspect_ratio="16:9")

    assert result.prompt == "a cat"
    assert result.aspect_ratio == "16:9"
    assert Path(result.path).exists()
    assert Path(result.path).read_bytes() == TEST_PNG_BYTES

    call_kwargs = mock_request.call_args
    assert "test-key" in call_kwargs.args[1]
    assert call_kwargs.kwargs["json"]["instances"][0]["prompt"] == "a cat"
    assert call_kwargs.kwargs["json"]["parameters"]["aspectRatio"] == "16:9"


@patch("cli_common.http.httpx.request")
def test_invalid_output_path(
    mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Invalid output path raises INVALID_OUTPUT_PATH error."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "predictions": [
            {"bytesBase64Encoded": base64.b64encode(TEST_PNG_BYTES).decode()}
        ]
    }
    mock_request.return_value = mock_response

    with pytest.raises(ToolException) as exc_info:
        generate("a cat", "/dev/null/impossible/path/out.png")
    assert exc_info.value.code in ("INVALID_OUTPUT_PATH", "FILE_WRITE_ERROR")


@pytest.mark.external
def test_real_gemini_api(tmp_path: object) -> None:
    """Integration test that hits the real Gemini API.

    Requires GOOGLE_API_KEY to be set. Skipped by default.
    """
    from pathlib import Path

    out_file = str(Path(str(tmp_path)) / "real_output.png")
    result = generate("a simple red circle on white background", out_file)
    assert Path(result.path).exists()
    assert result.prompt == "a simple red circle on white background"
