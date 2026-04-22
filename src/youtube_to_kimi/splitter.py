"""Video splitting via ffmpeg (lossless stream copy)."""

import json
import subprocess
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .exceptions import SplitError, VideoInfoError
from .utils import format_size

console = Console()


def _get_video_info(video_path: Path) -> dict:
    """Use ffprobe to extract bitrate and duration.

    Args:
        video_path: Path to the video file.

    Returns:
        Parsed JSON output from ffprobe.

    Raises:
        VideoInfoError: If ffprobe fails or returns invalid JSON.
    """
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise VideoInfoError(f"ffprobe failed: {result.stderr.strip()}")
    try:
        data: dict = json.loads(result.stdout)
        return data
    except json.JSONDecodeError as exc:
        raise VideoInfoError(f"ffprobe returned invalid JSON: {exc}") from exc


def _compute_segment_duration(info: dict, target_mb: float) -> float:
    """Compute a safe segment duration in seconds to stay under target_mb.

    Args:
        info: ffprobe output dict.
        target_mb: Target chunk size in megabytes.

    Returns:
        Segment duration in seconds.
    """
    fmt = info.get("format", {})

    # Try bit_rate from format
    bitrate = fmt.get("bit_rate")
    if bitrate is None:
        # Sum video + audio stream bitrates
        bitrate = sum(
            int(s.get("bit_rate", 0)) for s in info.get("streams", []) if s.get("bit_rate")
        )

    if not bitrate:
        # Fallback: use filesize / duration
        duration = float(fmt.get("duration", 0))
        size = int(fmt.get("size", 0))
        if duration > 0 and size > 0:
            bitrate = (size * 8) / duration
        else:
            # Ultimate fallback: 3 minutes segments
            return 180.0

    bitrate = int(bitrate)
    # target_bits = target_mb * 0.85 safety margin * 8
    target_bits = target_mb * 0.85 * 8 * 1024 * 1024
    return target_bits / bitrate


def split_video(
    video_path: Path,
    target_mb: float = 85.0,
) -> list[Path]:
    """Split video into chunks each under target_mb (lossless copy).

    Args:
        video_path: Path to the video file.
        target_mb: Target chunk size in megabytes.

    Returns:
        List of chunk file paths in order. If the video is already small
        enough, returns a single-element list containing the original path.

    Raises:
        VideoInfoError: If ffprobe cannot read the video.
        SplitError: If ffmpeg fails or produces no output.
    """
    size = video_path.stat().st_size
    if size <= target_mb * 1024 * 1024:
        console.print(f"[green]Video is {format_size(size)} — no splitting needed.[/green]")
        return [video_path]

    console.print(
        f"[yellow]Video is {format_size(size)} — "
        f"splitting into ~{target_mb:.0f}MB chunks...[/yellow]"
    )

    info = _get_video_info(video_path)
    seg_dur = _compute_segment_duration(info, target_mb)
    # Cap between 30s and 10min for sanity
    seg_dur = max(30.0, min(seg_dur, 600.0))

    stem = video_path.stem
    out_dir = video_path.parent
    out_pattern = str(out_dir / f"{stem}_part_%03d.mp4")

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-f",
        "segment",
        "-segment_time",
        str(seg_dur),
        "-reset_timestamps",
        "1",
        "-c",
        "copy",
        "-map",
        "0",
        out_pattern,
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Splitting with ffmpeg...", total=None)
        result = subprocess.run(cmd, capture_output=True, text=True)
        progress.update(task, completed=True)

    if result.returncode != 0:
        raise SplitError(f"ffmpeg failed:\n{result.stderr.strip()}")

    chunks = sorted(out_dir.glob(f"{stem}_part_*.mp4"))
    if not chunks:
        raise SplitError("No chunks were produced by ffmpeg.")

    return chunks
