"""Pydantic models for todo tool."""

from pydantic import BaseModel, Field


VALID_STATUSES = ("pending", "in_progress", "completed", "cancelled")


class TodoItem(BaseModel):
    """A single todo item."""

    id: str = Field(description="Unique identifier for the todo item")
    content: str = Field(description="Description of the task")
    status: str = Field(description="Status: pending, in_progress, completed, or cancelled")


class TodoSummary(BaseModel):
    """Summary counts of todo items by status."""

    total: int = Field(description="Total number of todo items")
    pending: int = Field(description="Number of pending items")
    in_progress: int = Field(description="Number of in-progress items")
    completed: int = Field(description="Number of completed items")
    cancelled: int = Field(description="Number of cancelled items")


class WriteResult(BaseModel):
    """Result of writing todo items."""

    items: list[TodoItem] = Field(description="The full list of todo items after write")
    summary: TodoSummary = Field(description="Summary counts by status")


class ListResult(BaseModel):
    """Result of listing todo items."""

    items: list[TodoItem] = Field(description="The current list of todo items")
    summary: TodoSummary = Field(description="Summary counts by status")


class ClearResult(BaseModel):
    """Result of clearing all todo items."""

    cleared: int = Field(description="Number of items that were removed")
