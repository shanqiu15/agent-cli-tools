"""Tests for the cron tool CLI."""

import json
from unittest.mock import patch

from typer.testing import CliRunner

from cli_common.errors import ToolException
from cron_tool.cli import app
from cron_tool.models import CreateJobResponse, DeleteJobResponse, JobInfo, ListJobsResponse

runner = CliRunner()


def test_help_text() -> None:
    """The --help flag prints usage information and exits 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "create" in result.output.lower()
    assert "list" in result.output.lower()
    assert "delete" in result.output.lower()


@patch("cron_tool.cli.create_job")
def test_create_job_success(mock_create) -> None:  # type: ignore[no-untyped-def]
    """A successful create emits JSON with ok=true and job_id."""
    mock_create.return_value = CreateJobResponse(
        job_id="job-123",
        next_run_time="2026-04-07T09:00:00Z",
    )

    result = runner.invoke(
        app,
        [
            "create",
            "--name", "daily-backup",
            "--schedule", "0 9 * * *",
            "--command", "backup.sh",
        ],
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["job_id"] == "job-123"
    assert data["result"]["next_run_time"] == "2026-04-07T09:00:00Z"


@patch("cron_tool.cli.list_jobs")
def test_list_jobs_success(mock_list) -> None:  # type: ignore[no-untyped-def]
    """A successful list emits JSON with ok=true and jobs array."""
    mock_list.return_value = ListJobsResponse(
        jobs=[
            JobInfo(
                job_id="job-1",
                name="backup",
                schedule="0 9 * * *",
                command="backup.sh",
                timezone="UTC",
                next_run_time="2026-04-07T09:00:00Z",
            ),
        ]
    )

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert len(data["result"]["jobs"]) == 1
    assert data["result"]["jobs"][0]["job_id"] == "job-1"


@patch("cron_tool.cli.delete_job")
def test_delete_job_success(mock_delete) -> None:  # type: ignore[no-untyped-def]
    """A successful delete emits JSON with ok=true and confirmation."""
    mock_delete.return_value = DeleteJobResponse(job_id="job-123", deleted=True)

    result = runner.invoke(app, ["delete", "--job-id", "job-123"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["ok"] is True
    assert data["result"]["job_id"] == "job-123"
    assert data["result"]["deleted"] is True


@patch(
    "cron_tool.cli.create_job",
    side_effect=ToolException(
        code="MISSING_CREDENTIALS",
        message="Environment variable CRON_GATEWAY_URL is not set",
        details={"env_var": "CRON_GATEWAY_URL"},
    ),
)
def test_missing_gateway_url(mock_create) -> None:  # type: ignore[no-untyped-def]
    """Missing CRON_GATEWAY_URL emits structured error."""
    result = runner.invoke(
        app,
        [
            "create",
            "--name", "test",
            "--schedule", "0 9 * * *",
            "--command", "test.sh",
        ],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "MISSING_CREDENTIALS"


@patch(
    "cron_tool.cli.create_job",
    side_effect=ToolException(
        code="INVALID_INPUT",
        message="Invalid schedule format: 'not-a-schedule'",
        details={"schedule": "not-a-schedule"},
    ),
)
def test_invalid_schedule(mock_create) -> None:  # type: ignore[no-untyped-def]
    """Invalid schedule format emits INVALID_INPUT error."""
    result = runner.invoke(
        app,
        [
            "create",
            "--name", "test",
            "--schedule", "not-a-schedule",
            "--command", "test.sh",
        ],
    )
    assert result.exit_code == 1

    data = json.loads(result.output)
    assert data["ok"] is False
    assert data["error"]["code"] == "INVALID_INPUT"
