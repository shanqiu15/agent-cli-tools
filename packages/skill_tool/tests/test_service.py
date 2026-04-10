"""Tests for the skill tool service layer."""

import os

import pytest

from skill_tool.errors import SkillError
from skill_tool.service import (
    create_skill,
    delete_skill,
    edit_skill,
    list_skills,
    view_skill,
    write_supporting_file,
)


VALID_CONTENT = "---\nname: test\ndescription: A test skill\n---\n\nContent here.\n"


# --- name validation ---


def test_create_invalid_name_special_chars(tmp_path: object) -> None:
    """Special characters in the name raise INVALID_INPUT."""
    with pytest.raises(SkillError) as exc_info:
        create_skill(name="My Skill!", content=VALID_CONTENT, skills_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


def test_create_invalid_name_too_long(tmp_path: object) -> None:
    """Names longer than 64 characters raise INVALID_INPUT."""
    long_name = "a" * 65
    with pytest.raises(SkillError) as exc_info:
        create_skill(name=long_name, content=VALID_CONTENT, skills_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


def test_create_invalid_name_uppercase(tmp_path: object) -> None:
    """Uppercase characters in the name raise INVALID_INPUT."""
    with pytest.raises(SkillError) as exc_info:
        create_skill(name="MySkill", content=VALID_CONTENT, skills_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


# --- frontmatter validation ---


def test_create_missing_name_field(tmp_path: object) -> None:
    """Missing name field in frontmatter raises INVALID_INPUT."""
    content = "---\ndescription: A test\n---\n\nContent.\n"
    with pytest.raises(SkillError) as exc_info:
        create_skill(name="test", content=content, skills_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


def test_create_missing_description_field(tmp_path: object) -> None:
    """Missing description field in frontmatter raises INVALID_INPUT."""
    content = "---\nname: test\n---\n\nContent.\n"
    with pytest.raises(SkillError) as exc_info:
        create_skill(name="test", content=content, skills_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


def test_create_malformed_yaml(tmp_path: object) -> None:
    """Malformed YAML in frontmatter raises INVALID_INPUT."""
    content = "---\n: invalid: yaml: [[\n---\n\nContent.\n"
    with pytest.raises(SkillError) as exc_info:
        create_skill(name="test", content=content, skills_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"


def test_create_no_frontmatter(tmp_path: object) -> None:
    """Missing frontmatter raises INVALID_INPUT."""
    with pytest.raises(SkillError) as exc_info:
        create_skill(
            name="test", content="No frontmatter here.", skills_dir=str(tmp_path)
        )
    assert exc_info.value.code == "INVALID_INPUT"


# --- create_skill ---


def test_create_success(tmp_path: object) -> None:
    """Creating a skill writes SKILL.md and returns success."""
    result = create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    assert result.name == "test"
    assert os.path.isfile(result.path)

    with open(result.path) as f:
        assert f.read() == VALID_CONTENT


def test_create_already_exists(tmp_path: object) -> None:
    """Creating a skill that already exists raises ALREADY_EXISTS."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    with pytest.raises(SkillError) as exc_info:
        create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    assert exc_info.value.code == "ALREADY_EXISTS"


# --- list_skills ---


def test_list_empty(tmp_path: object) -> None:
    """Listing with no skills returns an empty list."""
    result = list_skills(skills_dir=str(tmp_path))
    assert result.skills == []
    assert result.total == 0


def test_list_multiple_skills(tmp_path: object) -> None:
    """Listing returns metadata for all skills."""
    content_a = "---\nname: alpha\ndescription: First skill\n---\n\nFirst.\n"
    content_b = (
        "---\nname: beta\ndescription: Second skill\ncategory: utils\n---\n\nSecond.\n"
    )
    create_skill(name="alpha", content=content_a, skills_dir=str(tmp_path))
    create_skill(name="beta", content=content_b, skills_dir=str(tmp_path))

    result = list_skills(skills_dir=str(tmp_path))
    assert result.total == 2
    names = {s.name for s in result.skills}
    assert names == {"alpha", "beta"}

    cats = {s.name: s.category for s in result.skills}
    assert cats["beta"] == "utils"
    assert cats["alpha"] is None


# --- view_skill ---


def test_view_success(tmp_path: object) -> None:
    """Viewing a skill returns its full content."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    result = view_skill(name="test", skills_dir=str(tmp_path))
    assert result.content == VALID_CONTENT


def test_view_not_found(tmp_path: object) -> None:
    """Viewing a non-existent skill raises NOT_FOUND."""
    with pytest.raises(SkillError) as exc_info:
        view_skill(name="missing", skills_dir=str(tmp_path))
    assert exc_info.value.code == "NOT_FOUND"


def test_view_supporting_file(tmp_path: object) -> None:
    """Viewing a supporting file returns its content."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    write_supporting_file(
        name="test",
        subpath="templates/prompt.txt",
        content="Hello prompt",
        skills_dir=str(tmp_path),
    )
    result = view_skill(
        name="test", file="templates/prompt.txt", skills_dir=str(tmp_path)
    )
    assert result.content == "Hello prompt"


# --- edit_skill ---


def test_edit_success(tmp_path: object) -> None:
    """Editing a skill replaces its SKILL.md content."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))

    new_content = "---\nname: test\ndescription: Updated description\n---\n\nNew content.\n"
    result = edit_skill(name="test", content=new_content, skills_dir=str(tmp_path))
    assert result.name == "test"

    viewed = view_skill(name="test", skills_dir=str(tmp_path))
    assert viewed.content == new_content


def test_edit_validates_frontmatter(tmp_path: object) -> None:
    """Editing validates frontmatter before writing."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))

    with pytest.raises(SkillError) as exc_info:
        edit_skill(name="test", content="No frontmatter", skills_dir=str(tmp_path))
    assert exc_info.value.code == "INVALID_INPUT"

    # Original content should be preserved
    viewed = view_skill(name="test", skills_dir=str(tmp_path))
    assert viewed.content == VALID_CONTENT


def test_edit_not_found(tmp_path: object) -> None:
    """Editing a non-existent skill raises NOT_FOUND."""
    new_content = "---\nname: test\ndescription: desc\n---\n"
    with pytest.raises(SkillError) as exc_info:
        edit_skill(name="missing", content=new_content, skills_dir=str(tmp_path))
    assert exc_info.value.code == "NOT_FOUND"


# --- delete_skill ---


def test_delete_with_force(tmp_path: object) -> None:
    """Deleting with --force removes the skill directory."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    result = delete_skill(name="test", force=True, skills_dir=str(tmp_path))
    assert result.deleted is True
    assert not os.path.exists(os.path.join(str(tmp_path), "test"))


def test_delete_without_force(tmp_path: object) -> None:
    """Deleting without --force raises CONFIRMATION_NEEDED."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    with pytest.raises(SkillError) as exc_info:
        delete_skill(name="test", force=False, skills_dir=str(tmp_path))
    assert exc_info.value.code == "CONFIRMATION_NEEDED"


def test_delete_not_found(tmp_path: object) -> None:
    """Deleting a non-existent skill raises NOT_FOUND."""
    with pytest.raises(SkillError) as exc_info:
        delete_skill(name="missing", force=True, skills_dir=str(tmp_path))
    assert exc_info.value.code == "NOT_FOUND"


# --- write_supporting_file ---


def test_write_supporting_file_success(tmp_path: object) -> None:
    """Writing a supporting file to an allowed subdirectory succeeds."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    result = write_supporting_file(
        name="test",
        subpath="templates/prompt.txt",
        content="Template content",
        skills_dir=str(tmp_path),
    )
    assert result.name == "test"
    assert os.path.isfile(result.path)

    with open(result.path) as f:
        assert f.read() == "Template content"


def test_write_supporting_file_invalid_subdir(tmp_path: object) -> None:
    """Writing to a disallowed subdirectory raises INVALID_INPUT."""
    create_skill(name="test", content=VALID_CONTENT, skills_dir=str(tmp_path))
    with pytest.raises(SkillError) as exc_info:
        write_supporting_file(
            name="test",
            subpath="secret/data.txt",
            content="Bad",
            skills_dir=str(tmp_path),
        )
    assert exc_info.value.code == "INVALID_INPUT"


# --- full CRUD lifecycle ---


def test_full_crud_lifecycle(tmp_path: object) -> None:
    """Full create/list/view/edit/delete lifecycle."""
    skills_dir = str(tmp_path)

    # Create
    create_result = create_skill(
        name="lifecycle", content=VALID_CONTENT, skills_dir=skills_dir
    )
    assert create_result.name == "lifecycle"

    # List
    list_result = list_skills(skills_dir=skills_dir)
    assert list_result.total == 1

    # View
    view_result = view_skill(name="lifecycle", skills_dir=skills_dir)
    assert view_result.content == VALID_CONTENT

    # Edit
    new_content = "---\nname: lifecycle\ndescription: Updated\n---\n\nNew.\n"
    edit_result = edit_skill(
        name="lifecycle", content=new_content, skills_dir=skills_dir
    )
    assert edit_result.name == "lifecycle"

    # Verify edit
    view_result = view_skill(name="lifecycle", skills_dir=skills_dir)
    assert view_result.content == new_content

    # Delete
    delete_result = delete_skill(name="lifecycle", force=True, skills_dir=skills_dir)
    assert delete_result.deleted is True

    # Verify deletion
    list_result = list_skills(skills_dir=skills_dir)
    assert list_result.total == 0
