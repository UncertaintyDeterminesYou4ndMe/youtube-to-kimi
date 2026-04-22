"""Check that required external dependencies are available."""

import shutil
import subprocess
from typing import NamedTuple

from .exceptions import DependencyError


class DependencyInfo(NamedTuple):
    """Information about a required external dependency."""

    name: str
    command: str
    version_flag: str
    min_version: str | None = None


REQUIRED_DEPS: list[DependencyInfo] = [
    DependencyInfo("yt-dlp", "yt-dlp", "--version"),
    DependencyInfo("ffmpeg", "ffmpeg", "-version"),
    DependencyInfo("ffprobe", "ffprobe", "-version"),
]


def check_all() -> None:
    """Verify all required external dependencies are installed.

    Raises:
        DependencyError: If any dependency is missing.
    """
    missing: list[str] = []
    for dep in REQUIRED_DEPS:
        if shutil.which(dep.command) is None:
            missing.append(dep.name)
            continue
        # Optional: version check could go here

    if missing:
        msg = (
            f"Missing required dependencies: {', '.join(missing)}\n\n"
            "Install them with:\n"
            "  brew install yt-dlp ffmpeg     (macOS)\n"
            "  apt install yt-dlp ffmpeg      (Debian/Ubuntu)\n"
            "  uv tool install yt-dlp         (if using uv)\n"
        )
        raise DependencyError(msg)


def get_dependency_versions() -> dict[str, str]:
    """Get version strings for all dependencies.

    Returns:
        Mapping from dependency name to version string (or "unknown").
    """
    versions: dict[str, str] = {}
    for dep in REQUIRED_DEPS:
        cmd_path = shutil.which(dep.command)
        if cmd_path is None:
            versions[dep.name] = "not found"
            continue
        try:
            result = subprocess.run(
                [cmd_path, dep.version_flag],
                capture_output=True,
                text=True,
                timeout=5,
            )
            first_line = result.stdout.strip().splitlines()[0] if result.stdout else ""
            versions[dep.name] = first_line
        except (subprocess.TimeoutExpired, IndexError, OSError):
            versions[dep.name] = "unknown"
    return versions
