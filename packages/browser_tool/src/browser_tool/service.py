"""Business logic for browser automation via @playwright/cli."""

import shutil
import subprocess

from browser_tool.errors import BrowserError
from browser_tool.models import BrowserResult, BrowserStatus

_DEFAULT_SESSION = "default"
_DEFAULT_TIMEOUT = 30


class PlaywrightCLI:
    """Wraps @playwright/cli binary and shells out to it."""

    def __init__(self, session: str = _DEFAULT_SESSION) -> None:
        self.session = session
        self._binary = self._find_binary()

    def _find_binary(self) -> str:
        """Locate the playwright-cli binary in PATH."""
        path = shutil.which("playwright-cli")
        if path is None:
            raise BrowserError(
                code="PLAYWRIGHT_CLI_NOT_FOUND",
                message=(
                    "playwright-cli not found in PATH. "
                    "Install it with: npm install -g @playwright/cli@latest"
                ),
            )
        return path

    def _run(
        self, args: list[str], timeout: int = _DEFAULT_TIMEOUT
    ) -> subprocess.CompletedProcess[str]:
        """Run a playwright-cli command with session flag."""
        cmd = [self._binary, *args, f"-s={self.session}"]
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise BrowserError(
                code="TIMEOUT",
                message=f"playwright-cli command timed out after {timeout} seconds",
                details={"args": args, "timeout": timeout},
            ) from exc

    def start(self) -> BrowserResult:
        """Launch a headless browser session."""
        result = self._run(["open"])
        if result.returncode != 0:
            raise BrowserError(
                code="BROWSER_START_FAILED",
                message=f"Failed to start browser: {result.stderr.strip()}",
                details={"stderr": result.stderr},
            )
        return BrowserResult(
            action="start",
            output=result.stdout.strip(),
            session=self.session,
        )

    def stop(self) -> BrowserResult:
        """Terminate the browser session."""
        result = self._run(["close"])
        if result.returncode != 0:
            raise BrowserError(
                code="BROWSER_STOP_FAILED",
                message=f"Failed to stop browser: {result.stderr.strip()}",
                details={"stderr": result.stderr},
            )
        return BrowserResult(
            action="stop",
            output=result.stdout.strip(),
            session=self.session,
        )

    def status(self) -> BrowserStatus:
        """Check whether the browser session is active."""
        result = self._run(["status"])
        running = result.returncode == 0 and "active" in result.stdout.lower()
        return BrowserStatus(
            running=running,
            session=self.session,
            output=result.stdout.strip(),
        )

    def navigate(self, url: str) -> BrowserResult:
        """Navigate to a URL and return the page snapshot."""
        result = self._run(["goto", url])
        if result.returncode != 0:
            raise BrowserError(
                code="NAVIGATION_FAILED",
                message=f"Failed to navigate to {url}: {result.stderr.strip()}",
                details={"url": url, "stderr": result.stderr},
            )
        return BrowserResult(
            action="navigate",
            output=result.stdout.strip(),
            session=self.session,
        )

    def snapshot(self) -> BrowserResult:
        """Return the accessibility tree of the current page."""
        result = self._run(["snapshot"])
        if result.returncode != 0:
            raise BrowserError(
                code="SNAPSHOT_FAILED",
                message=f"Failed to capture snapshot: {result.stderr.strip()}",
                details={"stderr": result.stderr},
            )
        return BrowserResult(
            action="snapshot",
            output=result.stdout.strip(),
            session=self.session,
        )

    def screenshot(self, path: str) -> BrowserResult:
        """Capture a screenshot and save to the given path."""
        result = self._run(["screenshot", f"--output={path}"])
        if result.returncode != 0:
            raise BrowserError(
                code="SCREENSHOT_FAILED",
                message=f"Failed to capture screenshot: {result.stderr.strip()}",
                details={"path": path, "stderr": result.stderr},
            )
        return BrowserResult(
            action="screenshot",
            output=path,
            session=self.session,
        )

    def click(self, ref: str) -> BrowserResult:
        """Click an element by its accessibility ref."""
        result = self._run(["click", ref])
        if result.returncode != 0:
            raise BrowserError(
                code="CLICK_FAILED",
                message=f"Failed to click ref '{ref}': {result.stderr.strip()}",
                details={"ref": ref, "stderr": result.stderr},
            )
        return BrowserResult(
            action="click",
            output=result.stdout.strip(),
            session=self.session,
        )

    def type_text(self, ref: str, text: str) -> BrowserResult:
        """Type text into an element by its accessibility ref."""
        result = self._run(["fill", ref, text])
        if result.returncode != 0:
            raise BrowserError(
                code="TYPE_FAILED",
                message=f"Failed to type into ref '{ref}': {result.stderr.strip()}",
                details={"ref": ref, "stderr": result.stderr},
            )
        return BrowserResult(
            action="type",
            output=result.stdout.strip(),
            session=self.session,
        )

    def press(self, key: str) -> BrowserResult:
        """Press a keyboard key."""
        result = self._run(["press", key])
        if result.returncode != 0:
            raise BrowserError(
                code="PRESS_FAILED",
                message=f"Failed to press key '{key}': {result.stderr.strip()}",
                details={"key": key, "stderr": result.stderr},
            )
        return BrowserResult(
            action="press",
            output=result.stdout.strip(),
            session=self.session,
        )
