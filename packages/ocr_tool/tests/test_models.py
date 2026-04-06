"""Tests for ocr_tool.models — OcrRequest and OcrResult validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from ocr_tool.models import OcrRequest, OcrResult


def test_ocr_request_valid_defaults() -> None:
    request = OcrRequest(image_path=Path("photo.png"))
    assert request.image_path == Path("photo.png")
    assert request.output_path is None
    assert request.mode == "local"
    assert request.model is None


def test_ocr_request_all_fields() -> None:
    request = OcrRequest(
        image_path=Path("photo.png"),
        output_path=Path("result.txt"),
        mode="llm",
        model="claude-sonnet-4-20250514",
    )
    assert request.mode == "llm"
    assert request.model == "claude-sonnet-4-20250514"
    assert request.output_path == Path("result.txt")


def test_ocr_request_missing_image_path() -> None:
    with pytest.raises(ValidationError):
        OcrRequest()  # type: ignore[call-arg]


def test_ocr_request_invalid_mode() -> None:
    with pytest.raises(ValidationError):
        OcrRequest(image_path=Path("photo.png"), mode="invalid")  # type: ignore[arg-type]


def test_ocr_result_serialization() -> None:
    result = OcrResult(
        text="Hello world",
        source_image=Path("photo.png"),
        output_path=Path("photo.txt"),
        mode="local",
        model_used="easyocr-default",
    )
    data = result.model_dump()
    assert data["text"] == "Hello world"
    assert data["mode"] == "local"
    assert data["model_used"] == "easyocr-default"
