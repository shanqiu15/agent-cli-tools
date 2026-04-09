"""Business logic for file-based memory operations."""

from pathlib import Path

from memory_tool.errors import MemoryError
from memory_tool.models import ReadResult, SearchMatch, SearchResult, WriteResult


def _validate_path(memory_dir: Path, relative_path: str) -> Path:
    """Validate that the path stays within the memory directory.

    Raises:
        MemoryError: If the path escapes the memory directory.
    """
    if Path(relative_path).is_absolute():
        raise MemoryError(
            code="INVALID_PATH",
            message="Absolute paths are not allowed",
            details={"path": relative_path},
        )

    resolved = (memory_dir / relative_path).resolve()
    if not resolved.is_relative_to(memory_dir.resolve()):
        raise MemoryError(
            code="INVALID_PATH",
            message="Path must be within the memory directory",
            details={"path": relative_path},
        )

    return resolved


def write_memory(
    memory_dir: Path,
    path: str,
    content: str,
    append: bool = False,
) -> WriteResult:
    """Write content to a file in the memory directory.

    Args:
        memory_dir: Root memory directory.
        path: Relative path within memory_dir.
        content: Content to write.
        append: If True, append to existing file.

    Returns:
        WriteResult with path, bytes written, and append flag.
    """
    resolved = _validate_path(memory_dir, path)
    resolved.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if append else "w"
    with open(resolved, mode) as f:
        f.write(content)

    return WriteResult(
        path=path,
        bytes_written=len(content.encode("utf-8")),
        appended=append,
    )


def read_memory(memory_dir: Path, path: str) -> ReadResult:
    """Read a file from the memory directory.

    Args:
        memory_dir: Root memory directory.
        path: Relative path within memory_dir.

    Returns:
        ReadResult with path, content, and size.
    """
    resolved = _validate_path(memory_dir, path)

    if not resolved.is_file():
        raise MemoryError(
            code="FILE_NOT_FOUND",
            message=f"File not found: {path}",
            details={"path": path},
        )

    content = resolved.read_text()
    return ReadResult(
        path=path,
        content=content,
        size=len(content.encode("utf-8")),
    )


def search_memory(memory_dir: Path, query: str) -> SearchResult:
    """Search .md files in the memory directory for matching content.

    Args:
        memory_dir: Root memory directory.
        query: Substring to search for.

    Returns:
        SearchResult with matches sorted by modification time (newest first).
    """
    memory_dir = memory_dir.resolve()
    matches: list[SearchMatch] = []

    if memory_dir.is_dir():
        for md_file in memory_dir.rglob("*.md"):
            try:
                content = md_file.read_text()
            except OSError:
                continue

            if query.lower() in content.lower():
                rel_path = str(md_file.relative_to(memory_dir))
                matches.append(
                    SearchMatch(
                        path=rel_path,
                        size=len(content.encode("utf-8")),
                        modified=md_file.stat().st_mtime,
                    )
                )

    matches.sort(key=lambda m: m.modified, reverse=True)

    return SearchResult(
        query=query,
        matches=matches,
        total=len(matches),
    )
