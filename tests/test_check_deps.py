"""Tests for dependency checking."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from youtube_to_kimi.check_deps import (
    REQUIRED_DEPS,
    check_all,
    get_dependency_versions,
)
from youtube_to_kimi.exceptions import DependencyError


class TestCheckAll:
    @patch("youtube_to_kimi.check_deps.shutil.which")
    def test_all_present(self, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/fake"
        check_all()  # should not raise

    @patch("youtube_to_kimi.check_deps.shutil.which")
    def test_one_missing(self, mock_which: MagicMock) -> None:
        def side_effect(cmd: str) -> str | None:
            return None if cmd == "ffmpeg" else "/usr/bin/fake"

        mock_which.side_effect = side_effect
        with pytest.raises(DependencyError, match="Missing required dependencies: ffmpeg"):
            check_all()

    @patch("youtube_to_kimi.check_deps.shutil.which")
    def test_multiple_missing(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None
        with pytest.raises(DependencyError) as exc_info:
            check_all()
        err_msg = str(exc_info.value)
        for dep in REQUIRED_DEPS:
            assert dep.name in err_msg


class TestGetDependencyVersions:
    @patch("youtube_to_kimi.check_deps.shutil.which")
    @patch("youtube_to_kimi.check_deps.subprocess.run")
    def test_success(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/fake"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="2025.03.31\n"
        )
        versions = get_dependency_versions()
        for dep in REQUIRED_DEPS:
            assert dep.name in versions
            assert versions[dep.name] == "2025.03.31"

    @patch("youtube_to_kimi.check_deps.shutil.which")
    def test_not_found(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None
        versions = get_dependency_versions()
        for dep in REQUIRED_DEPS:
            assert versions[dep.name] == "not found"

    @patch("youtube_to_kimi.check_deps.shutil.which")
    @patch("youtube_to_kimi.check_deps.subprocess.run")
    def test_timeout(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/fake"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="fake", timeout=5)
        versions = get_dependency_versions()
        for dep in REQUIRED_DEPS:
            assert versions[dep.name] == "unknown"
