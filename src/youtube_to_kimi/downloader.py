"""YouTube video downloading via yt-dlp."""

import subprocess
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn

from .exceptions import DownloadError
from .utils import ensure_dir, sanitize_filename


def download_video(
    url: str,
    output_dir: Path,
    *,
    write_subs: bool = True,
    sub_langs: str = "en,zh,zh-CN,zh-TW",
) -> Path:
    """Download a YouTube video to output_dir.

    Args:
        url: YouTube video URL.
        output_dir: Directory to save the video.
        write_subs: Whether to download and embed subtitles.
        sub_langs: Comma-separated subtitle language codes.

    Returns:
        Path to the downloaded MP4 file.

    Raises:
        DownloadError: If yt-dlp fails or the output file cannot be located.
        SubtitleError: If subtitle download fails but video succeeds (non-fatal).
    """
    ensure_dir(output_dir)

    # Use yt-dlp to get the title for a clean filename prefix
    title_proc = subprocess.run(
        ["yt-dlp", "--print", "title", "--no-warnings", url],
        capture_output=True,
        text=True,
    )
    title = title_proc.stdout.strip() if title_proc.returncode == 0 else "video"
    safe_title = sanitize_filename(title)

    template = f"{safe_title}_%(id)s.%(ext)s"
    outtmpl = str(output_dir / template)

    cmd: list[str] = [
        "yt-dlp",
        "-f",
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format",
        "mp4",
        "-o",
        outtmpl,
        "--no-warnings",
        "--progress",
        "--newline",
    ]

    if write_subs:
        cmd += [
            "--write-subs",
            "--sub-langs",
            sub_langs,
            "--convert-subs",
            "srt",
            "--embed-subs",
        ]

    cmd.append(url)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(f"Downloading: {title}", total=None)
        result = subprocess.run(cmd, capture_output=True, text=True)
        progress.update(task, completed=True)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise DownloadError(f"yt-dlp failed to download video.\n{stderr}")

    # Find the actual downloaded file
    candidates = list(output_dir.glob(f"{safe_title}_*"))
    mp4s = [c for c in candidates if c.suffix == ".mp4"]
    if not mp4s:
        raise DownloadError(
            f"Download appeared to succeed but no MP4 file found in {output_dir} "
            f"matching '{safe_title}_*'."
        )

    return max(mp4s, key=lambda p: p.stat().st_size)
