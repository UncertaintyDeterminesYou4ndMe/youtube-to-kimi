"""Kimi API video analysis via OpenAI-compatible interface."""

import os
from pathlib import Path

import httpx

from .exceptions import DependencyError, DownloadError, ValidationError

DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_MODEL = "kimi-k2.6"
DEFAULT_MODEL = "kimi-k2.6"
MAX_VIDEO_MB = 100


def _get_api_key() -> str:
    """Get API key from environment or raise."""
    key = os.getenv("KIMI_API_KEY")
    if not key:
        raise DependencyError(
            "KIMI_API_KEY environment variable is not set.\n"
            "Get your key from https://platform.moonshot.cn and run:\n"
            "  export KIMI_API_KEY='sk-...'"
        )
    return key


def _get_base_url() -> str:
    """Get base URL from environment or default."""
    return os.getenv("KIMI_BASE_URL", DEFAULT_BASE_URL)


def upload_video(
    video_path: Path,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    """Upload a video file to Kimi and return an ms:// URL.

    Args:
        video_path: Path to the MP4 file.
        api_key: Kimi API key. Defaults to KIMI_API_KEY env var.
        base_url: API base URL. Defaults to KIMI_BASE_URL or Moonshot official.

    Returns:
        ms://{file_id} URL for use in chat completions.

    Raises:
        ValidationError: If file is too large or not found.
        DownloadError: If upload fails.
    """
    if not video_path.exists():
        raise ValidationError(f"Video file not found: {video_path}")

    size = video_path.stat().st_size
    if size > MAX_VIDEO_MB * 1024 * 1024:
        raise ValidationError(
            f"Video is {size / (1024 * 1024):.1f}MB, exceeds {MAX_VIDEO_MB}MB limit. "
            "Use 'split' command first."
        )

    key = api_key or _get_api_key()
    url = base_url or _get_base_url()

    with httpx.Client(timeout=120) as client:
        try:
            with video_path.open("rb") as f:
                response = client.post(
                    f"{url}/files",
                    headers={"Authorization": f"Bearer {key}"},
                    data={"purpose": "video"},
                    files={"file": (video_path.name, f, "video/mp4")},
                )
            response.raise_for_status()
            file_id = response.json()["id"]
            return f"ms://{file_id}"
        except httpx.HTTPStatusError as exc:
            body = exc.response.text
            raise DownloadError(
                f"Kimi API upload failed ({exc.response.status_code}): {body}"
            ) from exc
        except httpx.RequestError as exc:
            raise DownloadError(f"Kimi API request failed: {exc}") from exc


def analyze_video(
    video_url: str,
    prompt: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Send a video URL to Kimi chat completions and return the response text.

    Args:
        video_url: ms://{file_id} URL from upload_video.
        prompt: The analysis prompt.
        api_key: Kimi API key.
        base_url: API base URL.
        model: Model name, e.g. 'kimi-k2.6'.

    Returns:
        The model's response text.

    Raises:
        DownloadError: If API call fails.
    """
    key = api_key or _get_api_key()
    url = base_url or _get_base_url()

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": video_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "stream": False,
    }

    with httpx.Client(timeout=300) as client:
        try:
            response = client.post(
                f"{url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return str(data["choices"][0]["message"]["content"])
        except httpx.HTTPStatusError as exc:
            body = exc.response.text
            raise DownloadError(
                f"Kimi API chat failed ({exc.response.status_code}): {body}"
            ) from exc
        except (KeyError, IndexError) as exc:
            raise DownloadError(f"Unexpected API response format: {exc}") from exc
        except httpx.RequestError as exc:
            raise DownloadError(f"Kimi API request failed: {exc}") from exc


def analyze_chunks(
    chunks: list[Path],
    prompt: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
) -> list[str]:
    """Upload and analyze multiple video chunks sequentially.

    Args:
        chunks: List of video chunk paths.
        prompt: Analysis prompt applied to each chunk.
        api_key: Kimi API key.
        base_url: API base URL.
        model: Model name.

    Returns:
        List of analysis results, one per chunk.
    """
    results: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        video_url = upload_video(chunk, api_key=api_key, base_url=base_url)
        result = analyze_video(
            video_url,
            f"[Part {i}/{len(chunks)}] {prompt}",
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        results.append(result)
    return results
