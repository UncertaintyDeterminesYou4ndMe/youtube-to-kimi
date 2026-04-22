"""Tests for the downloader module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from youtube_to_kimi.downloader import download_video
from youtube_to_kimi.exceptions import DownloadError


class TestDownloadVideo:
    @patch("youtube_to_kimi.downloader.subprocess.run")
    def test_successful_download(self, mock_run: MagicMock, tmp_path: Path) -> None:
        # First call: get title
        # Second call: yt-dlp download
        def side_effect(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            if "--print" in cmd:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="Test Video\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        # Create a fake MP4 file so the locator finds it
        fake_mp4 = tmp_path / "Test_Video_abc123.mp4"
        fake_mp4.write_bytes(b"fake mp4 data")

        result = download_video("https://youtube.com/watch?v=abc", tmp_path)

        assert result == fake_mp4
        assert result.stat().st_size == len(b"fake mp4 data")

    @patch("youtube_to_kimi.downloader.subprocess.run")
    def test_ytdlp_fails(self, mock_run: MagicMock, tmp_path: Path) -> None:
        def side_effect(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            if "--print" in cmd:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="Test Video\n")
            return subprocess.CompletedProcess(
                args=cmd, returncode=1, stdout="", stderr="HTTP Error 404"
            )

        mock_run.side_effect = side_effect

        with pytest.raises(DownloadError, match="yt-dlp failed"):
            download_video("https://youtube.com/watch?v=bad", tmp_path)

    @patch("youtube_to_kimi.downloader.subprocess.run")
    def test_no_mp4_found(self, mock_run: MagicMock, tmp_path: Path) -> None:
        def side_effect(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            if "--print" in cmd:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="Test Video\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect
        # Intentionally do NOT create an MP4 file

        with pytest.raises(DownloadError, match="no MP4 file found"):
            download_video("https://youtube.com/watch?v=abc", tmp_path)

    @patch("youtube_to_kimi.downloader.subprocess.run")
    def test_picks_largest_mp4(self, mock_run: MagicMock, tmp_path: Path) -> None:
        def side_effect(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            if "--print" in cmd:
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="Test Video\n")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        small_mp4 = tmp_path / "Test_Video_abc123.mp4"
        small_mp4.write_bytes(b"x" * 100)
        large_mp4 = tmp_path / "Test_Video_abc123.f137.mp4"
        large_mp4.write_bytes(b"x" * 1000)

        result = download_video("https://youtube.com/watch?v=abc", tmp_path)
        assert result == large_mp4
