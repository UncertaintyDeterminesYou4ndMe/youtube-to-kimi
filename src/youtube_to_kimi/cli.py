"""CLI entry point using Typer + Rich."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .check_deps import check_all, get_dependency_versions
from .downloader import download_video
from .exceptions import YouTubeToKimiError
from .splitter import split_video
from .utils import format_size, get_default_output_dir

app = typer.Typer(
    name="youtube-to-kimi",
    help="Download YouTube videos and split into <100MB chunks for AI analysis.",
    no_args_is_help=True,
)
console = Console()


def _print_chunks(chunks: list[Path]) -> None:
    """Pretty-print a table of chunk files."""
    table = Table(title="🎬 Video Chunks Ready for Upload", show_lines=True)
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Filename", style="magenta")
    table.add_column("Size", justify="right", style="green")

    total = 0
    for i, chunk in enumerate(chunks, 1):
        size = chunk.stat().st_size
        total += size
        table.add_row(str(i), chunk.name, format_size(size))

    table.add_row("", "[bold]Total[/bold]", f"[bold]{format_size(total)}[/bold]")
    console.print(table)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Global options."""
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


@app.command()
def download(
    url: str = typer.Argument(..., help="YouTube video URL"),
    output: Path = typer.Option(
        get_default_output_dir(),
        "--output",
        "-o",
        help="Output directory",
    ),
) -> None:
    """Download a YouTube video."""
    try:
        check_all()
        video_path = download_video(url, output)
        console.print(f"[bold green]✅ Downloaded:[/bold green] {video_path}")
        console.print(f"   Size: {format_size(video_path.stat().st_size)}")
    except YouTubeToKimiError as exc:
        console.print(f"[bold red]❌ Error:[/bold red] {exc}")
        raise typer.Exit(exc.exit_code) from exc


@app.command()
def split(
    file: Path = typer.Argument(..., help="Path to video file", exists=True),
    target_mb: float = typer.Option(85.0, "--target-mb", "-t", help="Target chunk size in MB"),
) -> None:
    """Split an existing video into <100MB chunks."""
    try:
        check_all()
        chunks = split_video(file, target_mb)
        _print_chunks(chunks)
    except YouTubeToKimiError as exc:
        console.print(f"[bold red]❌ Error:[/bold red] {exc}")
        raise typer.Exit(exc.exit_code) from exc


@app.command()
def prepare(
    url: str = typer.Argument(..., help="YouTube video URL"),
    output: Path = typer.Option(
        get_default_output_dir(),
        "--output",
        "-o",
        help="Output directory",
    ),
    target_mb: float = typer.Option(85.0, "--target-mb", "-t", help="Target chunk size in MB"),
    keep_original: bool = typer.Option(
        False, "--keep-original", help="Keep the original unsplit file"
    ),
) -> None:
    """One-shot: download + split into chunks ready for Kimi."""
    try:
        check_all()
        video_path = download_video(url, output)
        console.print()
        chunks = split_video(video_path, target_mb)

        if not keep_original and len(chunks) > 1:
            # Splitting happened; remove original to save space
            video_path.unlink()
            console.print(f"[dim]🗑  Removed original: {video_path.name}[/dim]")

        console.print()
        _print_chunks(chunks)
        console.print()
        console.print(
            "[bold cyan]💡 Tip:[/bold cyan] "
            "Upload these chunks to Kimi sequentially to analyze the full video."
        )
    except YouTubeToKimiError as exc:
        console.print(f"[bold red]❌ Error:[/bold red] {exc}")
        raise typer.Exit(exc.exit_code) from exc


@app.command()
def version() -> None:
    """Show version and dependency info."""
    console.print(f"youtube-to-kimi [bold green]{__version__}[/bold green]")
    console.print()
    deps = get_dependency_versions()
    for name, ver in deps.items():
        console.print(f"  {name}: {ver}")


def main() -> None:
    app()
