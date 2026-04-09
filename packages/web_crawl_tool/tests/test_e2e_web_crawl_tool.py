"""End-to-end tests for web_crawl_tool."""

import json

import pytest
from typer.testing import CliRunner

from web_crawl_tool.cli import app

runner = CliRunner()


class TestWebCrawlValidation:
    def test_invalid_url_rejected(self) -> None:
        result = runner.invoke(app, ["crawl", "--url", "not-a-url"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_URL"

    def test_ftp_url_rejected(self) -> None:
        result = runner.invoke(app, ["crawl", "--url", "ftp://example.com"])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["ok"] is False
        assert data["error"]["code"] == "INVALID_URL"


@pytest.mark.external
class TestWebCrawlE2E:
    def test_crawl_example_com(self) -> None:
        result = runner.invoke(
            app, ["crawl", "--url", "https://example.com", "--max-length", "5000"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "Example Domain" in data["result"]["content"]
        assert data["result"]["url"] == "https://example.com"
