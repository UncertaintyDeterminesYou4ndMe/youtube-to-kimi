"""Tests for the CLI module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from youtube_to_kimi.cli import app
from youtube_to_kimi.exceptions import DependencyError, DownloadError

runner = CliRunner()


class TestVersionCommand:
    def test_shows_version(self) -> None:
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "youtube-to-kimi" in result.output


class TestDownloadCommand:
    @patch("youtube_to_kimi.cli.check_all")
    @patch("youtube_to_kimi.cli.download_video")
    def test_success(self, mock_download: MagicMock, mock_check: MagicMock, tmp_path: Path) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"x" * 1024)
        mock_download.return_value = video

        result = runner.invoke(app, ["download", "https://youtube.com/watch?v=abc", "-o", str(tmp_path)])
        assert result.exit_code == 0
        assert "Downloaded" in result.output

    @patch("youtube_to_kimi.cli.check_all")
    def test_dependency_error(self, mock_check: MagicMock) -> None:
        mock_check.side_effect = DependencyError("ffmpeg not found")
        result = runner.invoke(app, ["download", "https://youtube.com/watch?v=abc"])
        assert result.exit_code == 2
        assert "ffmpeg not found" in result.output

    @patch("youtube_to_kimi.cli.check_all")
    @patch("youtube_to_kimi.cli.download_video")
    def test_download_error(self, mock_download: MagicMock, mock_check: MagicMock) -> None:
        mock_download.side_effect = DownloadError("network failed")
        result = runner.invoke(app, ["download", "https://youtube.com/watch?v=abc"])
        assert result.exit_code == 3
        assert "network failed" in result.output


class TestSplitCommand:
    @patch("youtube_to_kimi.cli.check_all")
    @patch("youtube_to_kimi.cli.split_video")
    def test_success(self, mock_split: MagicMock, mock_check: MagicMock, tmp_path: Path) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"x" * 1024)
        mock_split.return_value = [video]

        result = runner.invoke(app, ["split", str(video)])
        assert result.exit_code == 0


class TestPrepareCommand:
    @patch("youtube_to_kimi.cli.check_all")
    @patch("youtube_to_kimi.cli.split_video")
    @patch("youtube_to_kimi.cli.download_video")
    def test_success_with_split(
        self,
        mock_download: MagicMock,
        mock_split: MagicMock,
        mock_check: MagicMock,
        tmp_path: Path,
    ) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"x" * 1024)
        chunk = tmp_path / "test_part_000.mp4"
        chunk.write_bytes(b"x" * 512)
        mock_download.return_value = video
        mock_split.return_value = [chunk]

        result = runner.invoke(app, ["prepare", "https://youtube.com/watch?v=abc", "-o", str(tmp_path)])
        assert result.exit_code == 0
        assert "Video Chunks Ready for Upload" in result.output

    @patch("youtube_to_kimi.cli.check_all")
    @patch("youtube_to_kimi.cli.split_video")
    @patch("youtube_to_kimi.cli.download_video")
    def test_keep_original(
        self,
        mock_download: MagicMock,
        mock_split: MagicMock,
        mock_check: MagicMock,
        tmp_path: Path,
    ) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"x" * 1024)
        chunk1 = tmp_path / "test_part_000.mp4"
        chunk1.write_bytes(b"x" * 512)
        chunk2 = tmp_path / "test_part_001.mp4"
        chunk2.write_bytes(b"x" * 512)
        mock_download.return_value = video
        mock_split.return_value = [chunk1, chunk2]

        result = runner.invoke(
            app, ["prepare", "https://youtube.com/watch?v=abc", "-o", str(tmp_path), "--keep-original"]
        )
        assert result.exit_code == 0
        assert video.exists()  # original kept
