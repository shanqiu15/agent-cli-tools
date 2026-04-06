"""Tests for cli_common.models — ToolResponse and ToolError serialization."""

import json

from cli_common.models import ToolError, ToolResponse


def test_tool_response_success_serialization() -> None:
    response = ToolResponse(ok=True, result={"path": "README.md", "content": "hello"})
    data = json.loads(response.model_dump_json())
    assert data["ok"] is True
    assert data["result"] == {"path": "README.md", "content": "hello"}
    assert data["error"] is None


def test_tool_response_error_serialization() -> None:
    error = ToolError(
        code="FILE_NOT_FOUND",
        message="Path does not exist",
        details={"path": "missing.txt"},
    )
    response = ToolResponse(ok=False, error=error)
    data = json.loads(response.model_dump_json())
    assert data["ok"] is False
    assert data["result"] is None
    assert data["error"]["code"] == "FILE_NOT_FOUND"
    assert data["error"]["message"] == "Path does not exist"
    assert data["error"]["details"] == {"path": "missing.txt"}


def test_tool_error_defaults() -> None:
    error = ToolError(code="INTERNAL_ERROR", message="Something went wrong")
    data = json.loads(error.model_dump_json())
    assert data["code"] == "INTERNAL_ERROR"
    assert data["message"] == "Something went wrong"
    assert data["details"] == {}


def test_tool_response_success_defaults() -> None:
    response = ToolResponse(ok=True)
    data = json.loads(response.model_dump_json())
    assert data["ok"] is True
    assert data["result"] is None
    assert data["error"] is None
