"""End-to-end tests that run real OCR engines against a test image."""

from pathlib import Path

import pytest

from ocr_tool.engines.local import extract_text_local
from ocr_tool.engines.google import extract_text_google

_TEST_IMAGE = Path(__file__).parent / "data" / "ocr_test.png"
_EXPECTED_TEXT = "This is a test"


def _normalize(text: str) -> str:
    """Collapse whitespace for fuzzy comparison."""
    return " ".join(text.lower().split())


class TestLocalE2E:
    def test_local_detects_expected_text(self) -> None:
        text = extract_text_local(_TEST_IMAGE)
        normalized = _normalize(text)
        for word in ("this", "is", "test"):
            assert word in normalized, f"Expected '{word}' in '{normalized}'"


@pytest.mark.external
class TestGoogleE2E:
    def test_google_detects_expected_text(self) -> None:
        text = extract_text_google(_TEST_IMAGE)
        assert _EXPECTED_TEXT.lower() in _normalize(text)
