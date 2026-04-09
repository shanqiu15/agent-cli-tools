"""Business logic for scheduling jobs via an HTTP gateway API."""

import os
import re

from cli_common.errors import ToolException
from cli_common.http import api_request

from cron_tool.models import CreateJobResponse, DeleteJobResponse, JobInfo, ListJobsResponse

CRON_GATEWAY_URL_ENV = "CRON_GATEWAY_URL"

# Cron expression: 5 fields (minute hour day month weekday)
_CRON_RE = re.compile(
    r"^(\*|[0-9,\-\/]+)\s+(\*|[0-9,\-\/]+)\s+(\*|[0-9,\-\/]+)\s+(\*|[0-9,\-\/]+)\s+(\*|[0-9,\-\/]+)$"
)
# Interval: "every <N><unit>" where unit is m, h, d, s
_INTERVAL_RE = re.compile(r"^every\s+(\d+)\s*([mhds])$", re.IGNORECASE)
# ISO 8601 timestamp (simplified check)
_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")


def _validate_schedule(schedule: str) -> str:
    """Validate and classify the schedule expression.

    Returns the schedule type: 'cron', 'interval', or 'one_shot'.

    Raises:
        ToolException: If the schedule format is invalid.
    """
    if _CRON_RE.match(schedule.strip()):
        return "cron"
    if _INTERVAL_RE.match(schedule.strip()):
        return "interval"
    if _ISO_TS_RE.match(schedule.strip()):
        return "one_shot"

    raise ToolException(
        code="INVALID_INPUT",
        message=f"Invalid schedule format: '{schedule}'. Use a cron expression "
        "(e.g. '0 9 * * *'), interval (e.g. 'every 5m'), or ISO timestamp.",
        details={"schedule": schedule},
    )


def _get_gateway_url() -> str:
    """Get the gateway URL from environment, raising on missing."""
    url = os.environ.get(CRON_GATEWAY_URL_ENV)
    if not url:
        raise ToolException(
            code="MISSING_CREDENTIALS",
            message=f"Environment variable {CRON_GATEWAY_URL_ENV} is not set",
            details={"env_var": CRON_GATEWAY_URL_ENV},
        )
    return url.rstrip("/")


def create_job(
    name: str,
    schedule: str,
    command: str,
    timezone: str = "UTC",
) -> CreateJobResponse:
    """Create a scheduled job via the gateway API.

    Args:
        name: Human-readable job name.
        schedule: Cron expression, interval, or ISO timestamp.
        command: Command to execute on schedule.
        timezone: Timezone for the schedule (default UTC).

    Returns:
        CreateJobResponse with job_id and next_run_time.

    Raises:
        ToolException: On missing credentials, invalid schedule, or API errors.
    """
    schedule_type = _validate_schedule(schedule)
    gateway_url = _get_gateway_url()

    response = api_request(
        "POST",
        f"{gateway_url}/jobs",
        json={
            "name": name,
            "schedule": schedule,
            "schedule_type": schedule_type,
            "command": command,
            "timezone": timezone,
        },
    )

    data = response.json()
    return CreateJobResponse(
        job_id=data["job_id"],
        next_run_time=data.get("next_run_time"),
    )


def list_jobs() -> ListJobsResponse:
    """List all scheduled jobs via the gateway API.

    Returns:
        ListJobsResponse with array of jobs.

    Raises:
        ToolException: On missing credentials or API errors.
    """
    gateway_url = _get_gateway_url()

    response = api_request("GET", f"{gateway_url}/jobs")

    data = response.json()
    jobs = [
        JobInfo(
            job_id=j["job_id"],
            name=j["name"],
            schedule=j["schedule"],
            command=j["command"],
            timezone=j.get("timezone", "UTC"),
            next_run_time=j.get("next_run_time"),
        )
        for j in data.get("jobs", [])
    ]
    return ListJobsResponse(jobs=jobs)


def delete_job(job_id: str) -> DeleteJobResponse:
    """Delete a scheduled job via the gateway API.

    Args:
        job_id: The ID of the job to delete.

    Returns:
        DeleteJobResponse confirming deletion.

    Raises:
        ToolException: On missing credentials or API errors.
    """
    gateway_url = _get_gateway_url()

    api_request("DELETE", f"{gateway_url}/jobs/{job_id}")

    return DeleteJobResponse(job_id=job_id, deleted=True)
