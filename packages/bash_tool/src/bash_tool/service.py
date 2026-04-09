"""Business logic for shell command execution."""

import subprocess

from bash_tool.errors import BashError
from bash_tool.models import CommandResult


def run_command(command: str, timeout: int = 30, max_output: int = 10000) -> CommandResult:
    """Execute a shell command and return structured output.

    Args:
        command: The shell command to execute.
        timeout: Maximum execution time in seconds.
        max_output: Maximum characters for stdout/stderr.

    Returns:
        CommandResult with stdout, stderr, exit_code, and truncated flag.

    Raises:
        BashError: On timeout or empty command.
    """
    if not command.strip():
        raise BashError(
            code="INVALID_INPUT",
            message="Command must not be empty",
        )

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        raise BashError(
            code="TIMEOUT",
            message=f"Command timed out after {timeout} seconds",
            details={
                "timeout": timeout,
                "partial_stdout": _truncate(stdout, max_output),
                "partial_stderr": _truncate(stderr, max_output),
            },
        ) from exc

    stdout = result.stdout
    stderr = result.stderr
    truncated = len(stdout) > max_output or len(stderr) > max_output

    return CommandResult(
        stdout=_truncate(stdout, max_output),
        stderr=_truncate(stderr, max_output),
        exit_code=result.returncode,
        truncated=truncated,
    )


def _truncate(text: str, max_length: int) -> str:
    """Truncate text to max_length with an indicator if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n[Truncated — total length: {len(text)} chars]"
