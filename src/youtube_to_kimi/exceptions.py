"""Application-specific exceptions."""


class YouTubeToKimiError(Exception):
    """Base exception for all application errors."""

    exit_code: int = 1


class DependencyError(YouTubeToKimiError):
    """Required external dependency (ffmpeg, yt-dlp, ffprobe) is missing or too old."""

    exit_code = 2


class DownloadError(YouTubeToKimiError):
    """Video download failed."""

    exit_code = 3


class SubtitleError(YouTubeToKimiError):
    """Subtitle extraction/download failed."""

    exit_code = 4


class SplitError(YouTubeToKimiError):
    """Video splitting failed."""

    exit_code = 5


class VideoInfoError(YouTubeToKimiError):
    """Failed to read video metadata via ffprobe."""

    exit_code = 6


class ValidationError(YouTubeToKimiError):
    """User input validation failed."""

    exit_code = 7
