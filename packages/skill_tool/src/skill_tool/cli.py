"""Typer CLI for the skill tool."""

import sys
from typing import Annotated

import typer

from cli_common.errors import ToolException
from cli_common.io import emit_error, emit_success

from skill_tool.service import (
    create_skill,
    delete_skill,
    edit_skill,
    list_skills,
    view_skill,
    write_supporting_file,
)

app = typer.Typer(add_completion=False)


@app.callback()
def main() -> None:
    """Skill definition management tool for LLM agents."""


@app.command("list")
def list_cmd(
    skills_dir: Annotated[
        str | None,
        typer.Option(help="Override the default skills directory"),
    ] = None,
) -> None:
    """List all skills with their metadata."""
    try:
        result = list_skills(skills_dir=skills_dir)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("view")
def view_cmd(
    name: Annotated[
        str,
        typer.Option(help="Name of the skill to view"),
    ],
    file: Annotated[
        str | None,
        typer.Option(help="Path to a supporting file within the skill directory"),
    ] = None,
    skills_dir: Annotated[
        str | None,
        typer.Option(help="Override the default skills directory"),
    ] = None,
) -> None:
    """View a skill's SKILL.md or a supporting file."""
    try:
        result = view_skill(name=name, file=file, skills_dir=skills_dir)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("create")
def create_cmd(
    name: Annotated[
        str,
        typer.Option(help="Name of the skill to create"),
    ],
    write_file: Annotated[
        str | None,
        typer.Option("--write-file", help="Write a supporting file instead of SKILL.md"),
    ] = None,
    skills_dir: Annotated[
        str | None,
        typer.Option(help="Override the default skills directory"),
    ] = None,
) -> None:
    """Create a new skill from SKILL.md content on stdin, or write a supporting file."""
    try:
        content = sys.stdin.read()
        if write_file:
            result = write_supporting_file(
                name=name,
                subpath=write_file,
                content=content,
                skills_dir=skills_dir,
            )
        else:
            result = create_skill(name=name, content=content, skills_dir=skills_dir)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("edit")
def edit_cmd(
    name: Annotated[
        str,
        typer.Option(help="Name of the skill to edit"),
    ],
    skills_dir: Annotated[
        str | None,
        typer.Option(help="Override the default skills directory"),
    ] = None,
) -> None:
    """Replace a skill's SKILL.md with new content from stdin."""
    try:
        content = sys.stdin.read()
        result = edit_skill(name=name, content=content, skills_dir=skills_dir)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


@app.command("delete")
def delete_cmd(
    name: Annotated[
        str,
        typer.Option(help="Name of the skill to delete"),
    ],
    force: Annotated[
        bool,
        typer.Option("--force", help="Confirm deletion"),
    ] = False,
    skills_dir: Annotated[
        str | None,
        typer.Option(help="Override the default skills directory"),
    ] = None,
) -> None:
    """Delete a skill and its directory."""
    try:
        result = delete_skill(name=name, force=force, skills_dir=skills_dir)
        emit_success(result.model_dump(mode="json"))
    except ToolException as exc:
        emit_error(code=exc.code, message=str(exc), details=exc.details)


if __name__ == "__main__":
    app()
