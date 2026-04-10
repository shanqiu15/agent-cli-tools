"""Tests for the skill tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from skill_tool.cli import app
from skill_tool.errors import SkillError
from skill_tool.models import (
    CreateResult,
    DeleteResult,
    EditResult,
    ListResult,
    SkillMetadata,
    ViewResult,
)

runner = CliRunner()

VALID_CONTENT = "---\nname: test\ndescription: A test skill\n---\n\nContent here.\n"


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    output = result.output.lower()
    assert "list" in output
    assert "view" in output
    assert "create" in output
    assert "edit" in output
    assert "delete" in output


@patch("skill_tool.cli.create_skill")
def test_create_success(mock_create) -> None:  # type: ignore[no-untyped-def]
    """A successful create emits JSON with ok=true."""
    mock_create.return_value = CreateResult(
        name="test", path="/skills/test/SKILL.md"
    )
    result = runner.invoke(app, ["create", "--name", "test"], input=VALID_CONTENT)
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["name"] == "test"


@patch("skill_tool.cli.list_skills")
def test_list_success(mock_list) -> None:  # type: ignore[no-untyped-def]
    """A successful list emits JSON with ok=true."""
    mock_list.return_value = ListResult(
        skills=[
            SkillMetadata(name="test", description="A test", category="utils"),
        ],
        total=1,
    )
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert len(data["result"]["skills"]) == 1
    assert data["result"]["total"] == 1


@patch("skill_tool.cli.view_skill")
def test_view_success(mock_view) -> None:  # type: ignore[no-untyped-def]
    """A successful view emits JSON with ok=true and content."""
    mock_view.return_value = ViewResult(
        name="test", path="/skills/test/SKILL.md", content=VALID_CONTENT
    )
    result = runner.invoke(app, ["view", "--name", "test"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["content"] == VALID_CONTENT


@patch("skill_tool.cli.edit_skill")
def test_edit_success(mock_edit) -> None:  # type: ignore[no-untyped-def]
    """A successful edit emits JSON with ok=true."""
    mock_edit.return_value = EditResult(name="test", path="/skills/test/SKILL.md")
    result = runner.invoke(app, ["edit", "--name", "test"], input=VALID_CONTENT)
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["name"] == "test"


@patch(
    "skill_tool.cli.delete_skill",
    side_effect=SkillError(
        code="CONFIRMATION_NEEDED",
        message="Use --force to confirm deletion",
    ),
)
def test_delete_without_force_error(mock_delete) -> None:  # type: ignore[no-untyped-def]
    """Deleting without --force emits structured error."""
    result = runner.invoke(app, ["delete", "--name", "test"])
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "CONFIRMATION_NEEDED"


@patch("skill_tool.cli.delete_skill")
def test_delete_with_force_success(mock_delete) -> None:  # type: ignore[no-untyped-def]
    """A successful delete with --force emits JSON with ok=true."""
    mock_delete.return_value = DeleteResult(name="test", deleted=True)
    result = runner.invoke(app, ["delete", "--name", "test", "--force"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["deleted"] is True


@patch(
    "skill_tool.cli.create_skill",
    side_effect=SkillError(
        code="INVALID_INPUT",
        message="Invalid skill name",
        details={"name": "Bad!"},
    ),
)
def test_create_error(mock_create) -> None:  # type: ignore[no-untyped-def]
    """A create error emits structured error."""
    result = runner.invoke(app, ["create", "--name", "bad"], input="content")
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"
