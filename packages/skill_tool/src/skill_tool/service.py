"""Business logic for skill definition management."""

import os
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from skill_tool.errors import SkillError
from skill_tool.models import (
    CreateResult,
    DeleteResult,
    EditResult,
    ListResult,
    SkillMetadata,
    ViewResult,
)

DEFAULT_SKILLS_DIR = os.path.join(
    Path.home(), ".local", "share", "agent-cli-tools", "skills"
)
SKILL_FILENAME = "SKILL.md"

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
ALLOWED_SUBDIRS = frozenset({"references", "templates", "scripts", "assets"})

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def _skills_dir(skills_dir: str | None = None) -> str:
    """Return the resolved skills directory path.

    Args:
        skills_dir: Optional override for the skills directory.

    Returns:
        Absolute path to the skills directory.
    """
    return skills_dir or DEFAULT_SKILLS_DIR


def _validate_name(name: str) -> None:
    """Validate a skill name.

    Args:
        name: The skill name to validate.

    Raises:
        SkillError: If the name is invalid.
    """
    if not name or not _NAME_RE.match(name):
        raise SkillError(
            code="INVALID_INPUT",
            message=(
                f"Invalid skill name: {name!r}. "
                "Must be 1-64 lowercase alphanumeric characters, "
                "hyphens, dots, or underscores."
            ),
            details={"name": name},
        )


def _parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse and validate YAML frontmatter from SKILL.md content.

    Args:
        content: The full SKILL.md content string.

    Returns:
        Parsed frontmatter as a dictionary.

    Raises:
        SkillError: If frontmatter is missing, malformed, or incomplete.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        raise SkillError(
            code="INVALID_INPUT",
            message="Missing or malformed YAML frontmatter. Content must start with '---'.",
        )
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise SkillError(
            code="INVALID_INPUT",
            message=f"Malformed YAML frontmatter: {exc}",
        ) from exc

    if not isinstance(data, dict):
        raise SkillError(
            code="INVALID_INPUT",
            message="YAML frontmatter must be a mapping.",
        )
    if "name" not in data:
        raise SkillError(
            code="INVALID_INPUT",
            message="YAML frontmatter missing required field: name",
        )
    if "description" not in data:
        raise SkillError(
            code="INVALID_INPUT",
            message="YAML frontmatter missing required field: description",
        )
    return data


def _validate_subpath(subpath: str) -> None:
    """Validate a supporting file subpath.

    Args:
        subpath: The subpath relative to the skill directory.

    Raises:
        SkillError: If the subpath is invalid or uses a disallowed subdirectory.
    """
    if ".." in subpath:
        raise SkillError(
            code="INVALID_INPUT",
            message="Path traversal not allowed in supporting file paths.",
            details={"subpath": subpath},
        )
    parts = subpath.replace("\\", "/").split("/")
    if len(parts) < 2 or not parts[0]:
        raise SkillError(
            code="INVALID_INPUT",
            message="Supporting file path must include a subdirectory and filename.",
            details={"subpath": subpath},
        )
    if parts[0] not in ALLOWED_SUBDIRS:
        raise SkillError(
            code="INVALID_INPUT",
            message=(
                f"Subdirectory {parts[0]!r} not allowed. "
                f"Allowed: {', '.join(sorted(ALLOWED_SUBDIRS))}"
            ),
            details={"subpath": subpath, "allowed": sorted(ALLOWED_SUBDIRS)},
        )


def create_skill(
    name: str,
    content: str,
    skills_dir: str | None = None,
) -> CreateResult:
    """Create a new skill from SKILL.md content.

    Args:
        name: Name of the skill (used as directory name).
        content: Full SKILL.md content with YAML frontmatter.
        skills_dir: Optional override for the skills directory.

    Returns:
        CreateResult with the skill name and path.

    Raises:
        SkillError: On invalid name, frontmatter, or write failure.
    """
    _validate_name(name)
    _parse_frontmatter(content)

    base = _skills_dir(skills_dir)
    skill_dir = os.path.join(base, name)
    skill_path = os.path.join(skill_dir, SKILL_FILENAME)

    if os.path.exists(skill_path):
        raise SkillError(
            code="ALREADY_EXISTS",
            message=f"Skill {name!r} already exists.",
            details={"name": name, "path": skill_path},
        )

    try:
        os.makedirs(skill_dir, exist_ok=True)
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        raise SkillError(
            code="WRITE_ERROR",
            message=f"Failed to create skill: {exc}",
            details={"path": skill_path},
        ) from exc

    return CreateResult(name=name, path=os.path.realpath(skill_path))


def write_supporting_file(
    name: str,
    subpath: str,
    content: str,
    skills_dir: str | None = None,
) -> CreateResult:
    """Write a supporting file to a skill's directory.

    Args:
        name: Name of the skill.
        subpath: Relative path within the skill directory (e.g. templates/prompt.txt).
        content: File content to write.
        skills_dir: Optional override for the skills directory.

    Returns:
        CreateResult with the skill name and file path.

    Raises:
        SkillError: On invalid name, subpath, or write failure.
    """
    _validate_name(name)
    _validate_subpath(subpath)

    base = _skills_dir(skills_dir)
    skill_dir = os.path.join(base, name)

    if not os.path.isdir(skill_dir):
        raise SkillError(
            code="NOT_FOUND",
            message=f"Skill {name!r} does not exist.",
            details={"name": name},
        )

    file_path = os.path.join(skill_dir, subpath)

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        raise SkillError(
            code="WRITE_ERROR",
            message=f"Failed to write supporting file: {exc}",
            details={"path": file_path},
        ) from exc

    return CreateResult(name=name, path=os.path.realpath(file_path))


def list_skills(skills_dir: str | None = None) -> ListResult:
    """List all skills with their metadata.

    Scans the skills directory for subdirectories containing SKILL.md files
    and extracts metadata from their YAML frontmatter.

    Args:
        skills_dir: Optional override for the skills directory.

    Returns:
        ListResult with skill metadata and total count.

    Raises:
        SkillError: On directory read errors.
    """
    base = _skills_dir(skills_dir)

    if not os.path.isdir(base):
        return ListResult(skills=[], total=0)

    skills: list[SkillMetadata] = []

    try:
        entries = sorted(os.listdir(base))
    except OSError as exc:
        raise SkillError(
            code="READ_ERROR",
            message=f"Failed to list skills directory: {exc}",
            details={"path": base},
        ) from exc

    for entry in entries:
        skill_dir = os.path.join(base, entry)
        if not os.path.isdir(skill_dir):
            continue
        skill_path = os.path.join(skill_dir, SKILL_FILENAME)
        if not os.path.isfile(skill_path):
            continue

        try:
            with open(skill_path, encoding="utf-8") as f:
                content = f.read()
            meta = _parse_frontmatter(content)
            skills.append(
                SkillMetadata(
                    name=meta.get("name", entry),
                    description=meta.get("description", ""),
                    category=meta.get("category"),
                )
            )
        except (OSError, SkillError):
            # Skip skills with unreadable or malformed frontmatter
            continue

    return ListResult(skills=skills, total=len(skills))


def view_skill(
    name: str,
    file: str | None = None,
    skills_dir: str | None = None,
) -> ViewResult:
    """View a skill's SKILL.md or a supporting file.

    Args:
        name: Name of the skill.
        file: Optional subpath to a supporting file.
        skills_dir: Optional override for the skills directory.

    Returns:
        ViewResult with the file content.

    Raises:
        SkillError: On invalid name or missing skill/file.
    """
    _validate_name(name)

    base = _skills_dir(skills_dir)
    skill_dir = os.path.join(base, name)

    if not os.path.isdir(skill_dir):
        raise SkillError(
            code="NOT_FOUND",
            message=f"Skill {name!r} does not exist.",
            details={"name": name},
        )

    if file:
        target = os.path.join(skill_dir, file)
    else:
        target = os.path.join(skill_dir, SKILL_FILENAME)

    if not os.path.isfile(target):
        raise SkillError(
            code="NOT_FOUND",
            message=f"File not found: {file or SKILL_FILENAME}",
            details={"name": name, "path": target},
        )

    try:
        with open(target, encoding="utf-8") as f:
            content = f.read()
    except OSError as exc:
        raise SkillError(
            code="READ_ERROR",
            message=f"Failed to read file: {exc}",
            details={"path": target},
        ) from exc

    return ViewResult(name=name, path=os.path.realpath(target), content=content)


def edit_skill(
    name: str,
    content: str,
    skills_dir: str | None = None,
) -> EditResult:
    """Replace a skill's SKILL.md with new content.

    Validates YAML frontmatter before writing. If validation fails,
    the original file is preserved.

    Args:
        name: Name of the skill.
        content: New SKILL.md content with valid YAML frontmatter.
        skills_dir: Optional override for the skills directory.

    Returns:
        EditResult with the skill name and path.

    Raises:
        SkillError: On invalid name, frontmatter, or write failure.
    """
    _validate_name(name)
    _parse_frontmatter(content)

    base = _skills_dir(skills_dir)
    skill_dir = os.path.join(base, name)
    skill_path = os.path.join(skill_dir, SKILL_FILENAME)

    if not os.path.isfile(skill_path):
        raise SkillError(
            code="NOT_FOUND",
            message=f"Skill {name!r} does not exist.",
            details={"name": name},
        )

    try:
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        raise SkillError(
            code="WRITE_ERROR",
            message=f"Failed to edit skill: {exc}",
            details={"path": skill_path},
        ) from exc

    return EditResult(name=name, path=os.path.realpath(skill_path))


def delete_skill(
    name: str,
    force: bool = False,
    skills_dir: str | None = None,
) -> DeleteResult:
    """Delete a skill and its directory.

    Args:
        name: Name of the skill.
        force: Must be True to confirm deletion.
        skills_dir: Optional override for the skills directory.

    Returns:
        DeleteResult with the skill name and deletion status.

    Raises:
        SkillError: On invalid name, missing skill, or unconfirmed deletion.
    """
    _validate_name(name)

    base = _skills_dir(skills_dir)
    skill_dir = os.path.join(base, name)

    if not os.path.isdir(skill_dir):
        raise SkillError(
            code="NOT_FOUND",
            message=f"Skill {name!r} does not exist.",
            details={"name": name},
        )

    if not force:
        raise SkillError(
            code="CONFIRMATION_NEEDED",
            message=f"Use --force to confirm deletion of skill {name!r}.",
            details={"name": name},
        )

    try:
        shutil.rmtree(skill_dir)
    except OSError as exc:
        raise SkillError(
            code="DELETE_ERROR",
            message=f"Failed to delete skill: {exc}",
            details={"path": skill_dir},
        ) from exc

    return DeleteResult(name=name, deleted=True)
