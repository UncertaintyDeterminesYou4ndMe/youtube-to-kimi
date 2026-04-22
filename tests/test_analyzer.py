"""Tests for the analyzer module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from youtube_to_kimi.analyzer import analyze_video, upload_video
from youtube_to_kimi.exceptions import DownloadError, ValidationError


class TestUploadVideo:
    @patch("youtube_to_kimi.analyzer.httpx.Client")
    def test_success(self, mock_client_cls: MagicMock, tmp_path: Path) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"fake video data")

        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "file_123"}
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = upload_video(video, api_key="sk-test", base_url="https://test/v1")
        assert result == "ms://file_123"
        mock_client.post.assert_called_once()

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError, match="not found"):
            upload_video(tmp_path / "nonexistent.mp4", api_key="sk-test")

    def test_file_too_large(self, tmp_path: Path) -> None:
        video = tmp_path / "big.mp4"
        video.write_bytes(b"x" * (101 * 1024 * 1024))
        with pytest.raises(ValidationError, match="exceeds"):
            upload_video(video, api_key="sk-test")

    @patch("youtube_to_kimi.analyzer.httpx.Client")
    def test_api_error(self, mock_client_cls: MagicMock, tmp_path: Path) -> None:
        video = tmp_path / "test.mp4"
        video.write_bytes(b"fake")

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_response
        )

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(DownloadError, match="Kimi API upload failed"):
            upload_video(video, api_key="sk-test", base_url="https://test/v1")


class TestAnalyzeVideo:
    @patch("youtube_to_kimi.analyzer.httpx.Client")
    def test_success(self, mock_client_cls: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Analysis result"}}]
        }
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = analyze_video(
            "ms://file_123",
            "Summarize",
            api_key="sk-test",
            base_url="https://test/v1",
            model="kimi-k2.6",
        )
        assert result == "Analysis result"

    @patch("youtube_to_kimi.analyzer.httpx.Client")
    def test_invalid_response(self, mock_client_cls: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "data"}
        mock_response.raise_for_status.return_value = None

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=None)
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value = mock_client

        with pytest.raises(DownloadError, match="Unexpected API response"):
            analyze_video("ms://file_123", "Summarize", api_key="sk-test")
