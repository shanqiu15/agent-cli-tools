"""Tests for the cron tool service layer."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from cli_common.errors import ToolException
from cron_tool.service import create_job, delete_job, list_jobs


def test_create_missing_gateway_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing CRON_GATEWAY_URL raises MISSING_CREDENTIALS."""
    monkeypatch.delenv("CRON_GATEWAY_URL", raising=False)
    with pytest.raises(ToolException) as exc_info:
        create_job(name="test", schedule="0 9 * * *", command="test.sh")
    assert exc_info.value.code == "MISSING_CREDENTIALS"
    assert exc_info.value.details["env_var"] == "CRON_GATEWAY_URL"


def test_list_missing_gateway_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing CRON_GATEWAY_URL raises MISSING_CREDENTIALS for list."""
    monkeypatch.delenv("CRON_GATEWAY_URL", raising=False)
    with pytest.raises(ToolException) as exc_info:
        list_jobs()
    assert exc_info.value.code == "MISSING_CREDENTIALS"


def test_delete_missing_gateway_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing CRON_GATEWAY_URL raises MISSING_CREDENTIALS for delete."""
    monkeypatch.delenv("CRON_GATEWAY_URL", raising=False)
    with pytest.raises(ToolException) as exc_info:
        delete_job(job_id="job-123")
    assert exc_info.value.code == "MISSING_CREDENTIALS"


def test_invalid_schedule_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid schedule format raises INVALID_INPUT."""
    monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:8080")
    with pytest.raises(ToolException) as exc_info:
        create_job(name="test", schedule="not-valid", command="test.sh")
    assert exc_info.value.code == "INVALID_INPUT"
    assert "not-valid" in str(exc_info.value)


@patch("cli_common.http.httpx.request")
def test_create_job_success(mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful create returns job_id and next_run_time."""
    monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:8080")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "job_id": "job-abc",
        "next_run_time": "2026-04-07T09:00:00Z",
    }
    mock_request.return_value = mock_response

    result = create_job(name="backup", schedule="0 9 * * *", command="backup.sh")
    assert result.job_id == "job-abc"
    assert result.next_run_time == "2026-04-07T09:00:00Z"

    call_kwargs = mock_request.call_args
    assert call_kwargs.kwargs["json"]["name"] == "backup"
    assert call_kwargs.kwargs["json"]["schedule"] == "0 9 * * *"
    assert call_kwargs.kwargs["json"]["schedule_type"] == "cron"
    assert call_kwargs.kwargs["json"]["command"] == "backup.sh"


@patch("cli_common.http.httpx.request")
def test_create_job_interval(mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Interval schedule is accepted and classified correctly."""
    monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:8080")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "job_id": "job-def",
        "next_run_time": "2026-04-06T12:05:00Z",
    }
    mock_request.return_value = mock_response

    result = create_job(name="poll", schedule="every 5m", command="poll.sh")
    assert result.job_id == "job-def"

    call_kwargs = mock_request.call_args
    assert call_kwargs.kwargs["json"]["schedule_type"] == "interval"


@patch("cli_common.http.httpx.request")
def test_create_job_one_shot(mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """ISO timestamp schedule is accepted as one_shot."""
    monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:8080")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "job_id": "job-ghi",
        "next_run_time": "2026-12-31T23:59:00Z",
    }
    mock_request.return_value = mock_response

    result = create_job(
        name="one-time", schedule="2026-12-31T23:59:00Z", command="celebrate.sh"
    )
    assert result.job_id == "job-ghi"

    call_kwargs = mock_request.call_args
    assert call_kwargs.kwargs["json"]["schedule_type"] == "one_shot"


@patch("cli_common.http.httpx.request")
def test_list_jobs_success(mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful list returns array of jobs."""
    monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:8080")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "job_id": "job-1",
                "name": "backup",
                "schedule": "0 9 * * *",
                "command": "backup.sh",
                "timezone": "UTC",
                "next_run_time": "2026-04-07T09:00:00Z",
            },
            {
                "job_id": "job-2",
                "name": "poll",
                "schedule": "every 5m",
                "command": "poll.sh",
                "timezone": "US/Eastern",
                "next_run_time": None,
            },
        ],
    }
    mock_request.return_value = mock_response

    result = list_jobs()
    assert len(result.jobs) == 2
    assert result.jobs[0].job_id == "job-1"
    assert result.jobs[1].name == "poll"


@patch("cli_common.http.httpx.request")
def test_delete_job_success(mock_request: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful delete returns confirmation."""
    monkeypatch.setenv("CRON_GATEWAY_URL", "http://localhost:8080")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_request.return_value = mock_response

    result = delete_job(job_id="job-123")
    assert result.job_id == "job-123"
    assert result.deleted is True
