"""Pydantic models for the cron tool."""

from pydantic import BaseModel, Field


class JobInfo(BaseModel):
    """Information about a scheduled job."""

    job_id: str = Field(description="Unique identifier for the job")
    name: str = Field(description="Name of the job")
    schedule: str = Field(description="Schedule expression")
    command: str = Field(description="Command to execute")
    timezone: str = Field(description="Timezone for the schedule")
    next_run_time: str | None = Field(
        default=None, description="Next scheduled run time in ISO format"
    )


class CreateJobResponse(BaseModel):
    """Response from creating a scheduled job."""

    job_id: str = Field(description="Unique identifier for the created job")
    next_run_time: str | None = Field(
        default=None, description="Next scheduled run time in ISO format"
    )


class ListJobsResponse(BaseModel):
    """Response from listing scheduled jobs."""

    jobs: list[JobInfo] = Field(description="List of scheduled jobs")


class DeleteJobResponse(BaseModel):
    """Response from deleting a scheduled job."""

    job_id: str = Field(description="ID of the deleted job")
    deleted: bool = Field(description="Whether the job was successfully deleted")
