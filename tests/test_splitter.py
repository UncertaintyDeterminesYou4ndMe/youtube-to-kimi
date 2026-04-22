"""Tests for the splitter module."""

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from youtube_to_kimi.exceptions import SplitError, VideoInfoError
from youtube_to_kimi.splitter import (
    _compute_segment_duration,
    _get_video_info,
    split_video,
)

FFPROBE_INFO = {
    "format": {
        "bit_rate": "4000000",
        "duration": "3600.0",
        "size": "1800000000",
    },
    "streams": [
        {"bit_rate": "3500000"},
        {"bit_rate": "500000"},
    ],
}


class TestGetVideoInfo:
    @patch("youtube_to_kimi.splitter.subprocess.run")
    def test_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps(FFPROBE_INFO)
        )
        info = _get_video_info(Path("/fake/video.mp4"))
        assert info["format"]["bit_rate"] == "4000000"

    @patch("youtube_to_kimi.splitter.subprocess.run")
    def test_ffprobe_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="file not found"
        )
        with pytest.raises(VideoInfoError, match="ffprobe failed"):
            _get_video_info(Path("/fake/video.mp4"))

    @patch("youtube_to_kimi.splitter.subprocess.run")
    def test_invalid_json(self, mock_run: MagicMock) -> None:
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not-json{{"
        )
        with pytest.raises(VideoInfoError, match="invalid JSON"):
            _get_video_info(Path("/fake/video.mp4"))


class TestComputeSegmentDuration:
    def test_with_format_bitrate(self) -> None:
        info: dict[str, Any] = {"format": {"bit_rate": "4000000"}, "streams": []}
        # target_mb=85, safety=0.85
        # target_bits = 85 * 0.85 * 8 * 1024^2 = 608,174,080
        # duration = 608,174,080 / 4,000,000 ≈ 152s
        duration = _compute_segment_duration(info, 85.0)
        assert 140 < duration < 160

    def test_with_stream_bitrates(self) -> None:
        info = {"format": {}, "streams": [{"bit_rate": "3000000"}, {"bit_rate": "500000"}]}
        duration = _compute_segment_duration(info, 85.0)
        assert 140 < duration < 180

    def test_fallback_filesize_duration(self) -> None:
        info = {
            "format": {"duration": "100", "size": "500000000"},
            "streams": [],
        }
        # bitrate = 500MB * 8 / 100s = 40,000,000 bps
        duration = _compute_segment_duration(info, 85.0)
        assert 10 < duration < 20

    def test_ultimate_fallback(self) -> None:
        info: dict[str, Any] = {"format": {}, "streams": []}
        duration = _compute_segment_duration(info, 85.0)
        assert duration == 180.0


class TestSplitVideo:
    def test_no_split_needed(self, tmp_path: Path) -> None:
        video = tmp_path / "small.mp4"
        video.write_bytes(b"x" * 1024)  # 1 KB
        chunks = split_video(video, target_mb=85.0)
        assert chunks == [video]

    @patch("youtube_to_kimi.splitter.subprocess.run")
    def test_successful_split(self, mock_run: MagicMock, tmp_path: Path) -> None:
        video = tmp_path / "large.mp4"
        video.write_bytes(b"x" * (100 * 1024 * 1024))  # 100 MB

        def side_effect(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            if "ffprobe" in cmd[0]:
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0, stdout=json.dumps(FFPROBE_INFO)
                )
            if "ffmpeg" in cmd[0]:
                # Create fake chunk files
                (tmp_path / "large_part_000.mp4").write_bytes(b"a")
                (tmp_path / "large_part_001.mp4").write_bytes(b"b")
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        chunks = split_video(video, target_mb=85.0)
        assert len(chunks) == 2
        assert chunks[0].name == "large_part_000.mp4"
        assert chunks[1].name == "large_part_001.mp4"

    @patch("youtube_to_kimi.splitter.subprocess.run")
    def test_ffmpeg_failure(self, mock_run: MagicMock, tmp_path: Path) -> None:
        video = tmp_path / "large.mp4"
        video.write_bytes(b"x" * (100 * 1024 * 1024))

        def side_effect(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            if "ffprobe" in cmd[0]:
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0, stdout=json.dumps(FFPROBE_INFO)
                )
            if "ffmpeg" in cmd[0]:
                return subprocess.CompletedProcess(
                    args=cmd, returncode=1, stdout="", stderr="codec not found"
                )
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        with pytest.raises(SplitError, match="ffmpeg failed"):
            split_video(video, target_mb=85.0)

    @patch("youtube_to_kimi.splitter.subprocess.run")
    def test_no_chunks_produced(self, mock_run: MagicMock, tmp_path: Path) -> None:
        video = tmp_path / "large.mp4"
        video.write_bytes(b"x" * (100 * 1024 * 1024))

        def side_effect(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            if "ffprobe" in cmd[0]:
                return subprocess.CompletedProcess(
                    args=cmd, returncode=0, stdout=json.dumps(FFPROBE_INFO)
                )
            if "ffmpeg" in cmd[0]:
                # ffmpeg succeeds but produces no files
                return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        mock_run.side_effect = side_effect

        with pytest.raises(SplitError, match="No chunks were produced"):
            split_video(video, target_mb=85.0)
