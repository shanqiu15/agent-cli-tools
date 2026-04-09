"""End-to-end tests for image_gen_tool."""

import json
from datetime import datetime

import pytest
from typer.testing import CliRunner

from image_gen_tool.cli import app

runner = CliRunner()


class TestImageGenValidation:
    def test_invalid_aspect_ratio(self) -> None:
        result = runner.invoke(
            app,
            ["generate", "--prompt", "test", "--output-path", "/tmp/test.png", "--aspect-ratio", "2:1"],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_missing_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        result = runner.invoke(
            app,
            ["generate", "--prompt", "test", "--output-path", "/tmp/test.png"],
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "MISSING_CREDENTIALS"


@pytest.mark.external
class TestImageGenE2E:
    def test_generate_image(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"./build/imagen/e2e_test/{timestamp}/output.png"
        result = runner.invoke(
            app,
            ["generate", "--prompt", "A blue circle on white background", "--output-path", output, "--image-size", "512"],
        )
        assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["result"]["path"].endswith(output[2:])
