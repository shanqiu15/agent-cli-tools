"""Business logic for safe filesystem operations."""

import fnmatch
import os
import re
from pathlib import Path

from file_tool.errors import FileError
from file_tool.models import (
    FileEntry,
    ListResult,
    PatchResult,
    ReadResult,
    SearchMatch,
    SearchResult,
    TreeEntry,
    TreeResult,
    WriteResult,
)

MAX_READ_CHARS = 100_000

BLOCKED_PATH_PREFIXES = (
    "/dev/",
    "/proc/",
    "/sys/",
)

_SENSITIVE_RAW = (
    os.path.expanduser("~/.ssh/"),
    os.path.expanduser("~/.gnupg/"),
    os.path.expanduser("~/.aws/credentials"),
    os.path.expanduser("~/.config/gcloud/"),
    "/etc/shadow",
    "/etc/gshadow",
    "/etc/sudoers",
)

# Build a set that includes both the raw paths and their realpath-resolved forms
# so that symlink resolution (e.g. /etc -> /private/etc on macOS) is handled.
SENSITIVE_PATHS: tuple[str, ...] = tuple(
    dict.fromkeys(list(_SENSITIVE_RAW) + [os.path.realpath(p) for p in _SENSITIVE_RAW])
)

BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".tiff", ".tif",
    ".svg", ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".wav",
    ".ogg", ".flac", ".aac", ".wma", ".zip", ".tar", ".gz", ".bz2", ".xz",
    ".7z", ".rar", ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a",
    ".class", ".jar", ".war", ".ear", ".pyc", ".pyo", ".whl", ".egg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".sqlite", ".db", ".sqlite3",
})


def _check_blocked_path(path: str) -> None:
    """Raise if the path is under a blocked prefix (e.g. /dev/).

    Args:
        path: The resolved absolute path to check.

    Raises:
        FileError: With code BLOCKED_PATH if the path is blocked.
    """
    for prefix in BLOCKED_PATH_PREFIXES:
        if path.startswith(prefix) or path == prefix.rstrip("/"):
            raise FileError(
                code="BLOCKED_PATH",
                message=f"Access to {path} is blocked",
                details={"path": path},
            )


def _check_binary_extension(path: str) -> None:
    """Raise if the file has a known binary extension.

    Args:
        path: The file path to check.

    Raises:
        FileError: With code BINARY_FILE if the extension is binary.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in BINARY_EXTENSIONS:
        raise FileError(
            code="BINARY_FILE",
            message=f"File appears to be binary ({ext}): {path}",
            details={"path": path, "extension": ext},
        )


def _check_sensitive_path(path: str) -> None:
    """Raise if the path is a known sensitive location.

    Args:
        path: The resolved absolute path to check.

    Raises:
        FileError: With code PERMISSION_DENIED if the path is sensitive.
    """
    for sensitive in SENSITIVE_PATHS:
        if path == sensitive or path.startswith(sensitive):
            raise FileError(
                code="PERMISSION_DENIED",
                message=f"Write to sensitive path is blocked: {path}",
                details={"path": path},
            )


def read_file(
    file: str,
    offset: int = 1,
    limit: int | None = None,
) -> ReadResult:
    """Read a file and return its contents.

    Args:
        file: Path to the file to read.
        offset: 1-indexed starting line number.
        limit: Maximum number of lines to return.

    Returns:
        ReadResult with file contents.

    Raises:
        FileError: On blocked path, binary file, file not found, or read error.
    """
    resolved = os.path.realpath(file)
    _check_blocked_path(resolved)
    _check_binary_extension(resolved)

    if not os.path.exists(resolved):
        raise FileError(
            code="FILE_NOT_FOUND",
            message=f"File not found: {resolved}",
            details={"path": resolved},
        )

    if not os.path.isfile(resolved):
        raise FileError(
            code="INVALID_INPUT",
            message=f"Path is not a file: {resolved}",
            details={"path": resolved},
        )

    try:
        with open(resolved, encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
    except OSError as exc:
        raise FileError(
            code="READ_ERROR",
            message=f"Failed to read file: {exc}",
            details={"path": resolved},
        ) from exc

    if offset < 1:
        offset = 1

    selected = all_lines[offset - 1:]
    if limit is not None and limit > 0:
        selected = selected[:limit]

    content = "".join(selected)
    truncated = False
    if len(content) > MAX_READ_CHARS:
        content = content[:MAX_READ_CHARS]
        truncated = True

    return ReadResult(
        path=resolved,
        content=content,
        lines=content.count("\n") + (1 if content and not content.endswith("\n") else 0),
        truncated=truncated,
        char_count=len(content),
    )


def write_file(file: str, content: str) -> WriteResult:
    """Write content to a file.

    Args:
        file: Path to the file to write.
        content: Content to write.

    Returns:
        WriteResult with path and bytes written.

    Raises:
        FileError: On blocked path, sensitive path, or write error.
    """
    resolved = os.path.realpath(file)
    _check_blocked_path(resolved)
    _check_sensitive_path(resolved)

    parent = os.path.dirname(resolved)
    try:
        os.makedirs(parent, exist_ok=True)
    except OSError as exc:
        raise FileError(
            code="WRITE_ERROR",
            message=f"Failed to create parent directory: {exc}",
            details={"path": resolved},
        ) from exc

    try:
        encoded = content.encode("utf-8")
        with open(resolved, "wb") as f:
            f.write(encoded)
    except OSError as exc:
        raise FileError(
            code="WRITE_ERROR",
            message=f"Failed to write file: {exc}",
            details={"path": resolved},
        ) from exc

    return WriteResult(
        path=resolved,
        bytes_written=len(encoded),
    )


def patch_file(
    file: str,
    old: str,
    new: str,
    replace_all: bool = False,
) -> PatchResult:
    """Find and replace text in a file.

    Args:
        file: Path to the file to patch.
        old: Text to find.
        new: Replacement text.
        replace_all: If True, replace all occurrences.

    Returns:
        PatchResult with path and replacement count.

    Raises:
        FileError: On blocked path, file not found, not found, or non-unique match.
    """
    resolved = os.path.realpath(file)
    _check_blocked_path(resolved)

    if not os.path.exists(resolved):
        raise FileError(
            code="FILE_NOT_FOUND",
            message=f"File not found: {resolved}",
            details={"path": resolved},
        )

    try:
        with open(resolved, encoding="utf-8") as f:
            content = f.read()
    except OSError as exc:
        raise FileError(
            code="READ_ERROR",
            message=f"Failed to read file: {exc}",
            details={"path": resolved},
        ) from exc

    count = content.count(old)

    if count == 0:
        raise FileError(
            code="NOT_FOUND",
            message="old_string not found in file",
            details={"path": resolved, "old": old},
        )

    if not replace_all and count > 1:
        raise FileError(
            code="NOT_UNIQUE",
            message=f"old_string found {count} times; use --replace-all to replace all",
            details={"path": resolved, "old": old, "count": count},
        )

    if replace_all:
        new_content = content.replace(old, new)
        replacements = count
    else:
        new_content = content.replace(old, new, 1)
        replacements = 1

    try:
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(new_content)
    except OSError as exc:
        raise FileError(
            code="WRITE_ERROR",
            message=f"Failed to write file: {exc}",
            details={"path": resolved},
        ) from exc

    return PatchResult(
        path=resolved,
        replacements=replacements,
    )


def search_files(
    pattern: str,
    path: str = ".",
    glob: str | None = None,
    context_lines: int = 0,
    offset: int = 0,
    limit: int = 100,
) -> SearchResult:
    """Search files for a regex pattern.

    Args:
        pattern: Regex pattern to search for.
        path: Directory to search in.
        glob: Optional glob pattern to filter files (e.g. "*.py").
        context_lines: Number of context lines before and after each match.
        offset: Number of matches to skip.
        limit: Maximum number of matches to return.

    Returns:
        SearchResult with matches.

    Raises:
        FileError: On invalid pattern or directory not found.
    """
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise FileError(
            code="INVALID_INPUT",
            message=f"Invalid regex pattern: {exc}",
            details={"pattern": pattern},
        ) from exc

    resolved = os.path.realpath(path)

    if not os.path.isdir(resolved):
        raise FileError(
            code="DIR_NOT_FOUND",
            message=f"Directory not found: {resolved}",
            details={"path": resolved},
        )

    all_matches: list[SearchMatch] = []

    for dirpath, _dirnames, filenames in sorted(os.walk(resolved)):
        for filename in sorted(filenames):
            filepath = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(filepath, resolved)

            # Skip hidden files/dirs
            if any(part.startswith(".") for part in Path(rel_path).parts):
                continue

            # Apply glob filter
            if glob is not None and not fnmatch.fnmatch(filename, glob):
                continue

            # Skip binary files
            ext = os.path.splitext(filename)[1].lower()
            if ext in BINARY_EXTENSIONS:
                continue

            try:
                with open(filepath, encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except OSError:
                continue

            for i, line in enumerate(lines):
                if compiled.search(line):
                    match_lines = []
                    start = max(0, i - context_lines)
                    end = min(len(lines), i + context_lines + 1)
                    for j in range(start, end):
                        match_lines.append(lines[j].rstrip("\n"))
                    content = "\n".join(match_lines)
                    all_matches.append(
                        SearchMatch(
                            file=rel_path,
                            line=i + 1,
                            content=content,
                        )
                    )

    total = len(all_matches)
    truncated = offset + limit < total
    selected = all_matches[offset: offset + limit]

    return SearchResult(
        pattern=pattern,
        matches=selected,
        total=total,
        truncated=truncated,
    )


def list_directory(path: str = ".", depth: int = 1) -> ListResult:
    """List the contents of a directory.

    Args:
        path: Directory path to list.
        depth: How many levels deep to list (1 = immediate children).

    Returns:
        ListResult with entries.

    Raises:
        FileError: If the path is not a directory.
    """
    resolved = os.path.realpath(path)

    if not os.path.isdir(resolved):
        raise FileError(
            code="DIR_NOT_FOUND",
            message=f"Directory not found: {resolved}",
            details={"path": resolved},
        )

    entries: list[FileEntry] = []
    _collect_entries(resolved, resolved, entries, depth, current_depth=1)
    entries.sort(key=lambda e: e.path)

    return ListResult(
        path=resolved,
        entries=entries,
        total=len(entries),
    )


def _collect_entries(
    root: str,
    current: str,
    entries: list[FileEntry],
    max_depth: int,
    current_depth: int,
) -> None:
    """Recursively collect directory entries up to max_depth."""
    try:
        items = sorted(os.listdir(current))
    except OSError:
        return

    for name in items:
        if name.startswith("."):
            continue
        full = os.path.join(current, name)
        rel = os.path.relpath(full, root)
        is_dir = os.path.isdir(full)
        size = 0 if is_dir else _safe_size(full)
        entries.append(FileEntry(name=name, path=rel, is_dir=is_dir, size=size))
        if is_dir and current_depth < max_depth:
            _collect_entries(root, full, entries, max_depth, current_depth + 1)


def _safe_size(path: str) -> int:
    """Return file size, or 0 on error."""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def tree_directory(path: str = ".", depth: int = 3) -> TreeResult:
    """Generate a flat tree listing of a directory.

    Args:
        path: Directory path to tree.
        depth: Maximum depth to recurse.

    Returns:
        TreeResult with entries.

    Raises:
        FileError: If the path is not a directory.
    """
    resolved = os.path.realpath(path)

    if not os.path.isdir(resolved):
        raise FileError(
            code="DIR_NOT_FOUND",
            message=f"Directory not found: {resolved}",
            details={"path": resolved},
        )

    entries: list[TreeEntry] = []
    _collect_tree(resolved, resolved, entries, depth, current_depth=1)
    entries.sort(key=lambda e: e.path)

    return TreeResult(
        path=resolved,
        entries=entries,
        total=len(entries),
    )


def _collect_tree(
    root: str,
    current: str,
    entries: list[TreeEntry],
    max_depth: int,
    current_depth: int,
) -> None:
    """Recursively collect tree entries up to max_depth."""
    try:
        items = sorted(os.listdir(current))
    except OSError:
        return

    for name in items:
        if name.startswith("."):
            continue
        full = os.path.join(current, name)
        rel = os.path.relpath(full, root)
        is_dir = os.path.isdir(full)
        entries.append(TreeEntry(path=rel, is_dir=is_dir))
        if is_dir and current_depth < max_depth:
            _collect_tree(root, full, entries, max_depth, current_depth + 1)
