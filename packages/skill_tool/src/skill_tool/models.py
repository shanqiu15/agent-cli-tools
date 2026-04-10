"""Pydantic models for skill tool."""

from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    """Metadata extracted from a skill's YAML frontmatter."""

    name: str = Field(description="Name of the skill")
    description: str = Field(description="Short description of the skill")
    category: str | None = Field(
        default=None, description="Optional category for the skill"
    )


class CreateResult(BaseModel):
    """Result of creating a skill or writing a supporting file."""

    name: str = Field(description="Name of the skill")
    path: str = Field(description="Absolute path to the created file")


class ListResult(BaseModel):
    """Result of listing skills."""

    skills: list[SkillMetadata] = Field(description="List of skill metadata")
    total: int = Field(description="Total number of skills")


class ViewResult(BaseModel):
    """Result of viewing a skill or supporting file."""

    name: str = Field(description="Name of the skill")
    path: str = Field(description="Absolute path to the viewed file")
    content: str = Field(description="Content of the file")


class EditResult(BaseModel):
    """Result of editing a skill."""

    name: str = Field(description="Name of the edited skill")
    path: str = Field(description="Absolute path to the edited file")


class DeleteResult(BaseModel):
    """Result of deleting a skill."""

    name: str = Field(description="Name of the deleted skill")
    deleted: bool = Field(description="Whether the skill was deleted")
