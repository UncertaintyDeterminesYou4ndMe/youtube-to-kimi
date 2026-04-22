"""CLI entry point using Typer + Rich."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .analyzer import analyze_chunks, analyze_video, upload_video
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
        if len(chunks) > 1:
            console.print(
                f"[bold yellow]⚠️  Important:[/bold yellow] "
                f"Make sure Kimi reads all {len(chunks)} parts before summarizing. "
                f"Stopping early may miss key content in later segments."
            )
    except YouTubeToKimiError as exc:
        console.print(f"[bold red]❌ Error:[/bold red] {exc}")
        raise typer.Exit(exc.exit_code) from exc


@app.command()
def analyze(
    source: str = typer.Argument(..., help="YouTube URL or path to local video file"),
    prompt: str = typer.Option(
        "请分析这个视频的核心内容。",
        "--prompt",
        "-p",
        help="Analysis prompt sent to the AI model",
    ),
    output: Path = typer.Option(
        get_default_output_dir(),
        "--output",
        "-o",
        help="Output directory for downloaded videos",
    ),
    target_mb: float = typer.Option(85.0, "--target-mb", "-t", help="Target chunk size in MB"),
    model: str = typer.Option("kimi-k2.6", "--model", "-m", help="Kimi model name"),
    save: Path = typer.Option(None, "--save", "-s", help="Save result to file"),
) -> None:
    """Analyze a video with Kimi API (auto download, split, upload, analyze)."""
    try:
        check_all()

        # Determine if source is a URL or local file
        video_path: Path
        if source.startswith(("http://", "https://", "www.")):
            console.print("[bold blue]📥 Downloading video...[/bold blue]")
            video_path = download_video(source, output)
            console.print(f"[green]✅ Downloaded:[/green] {video_path.name}")
        else:
            video_path = Path(source).expanduser()
            if not video_path.exists():
                raise YouTubeToKimiError(f"File not found: {video_path}")
            console.print(f"[green]✅ Using local file:[/green] {video_path.name}")

        # Auto-split if too large for API upload (100MB)
        size = video_path.stat().st_size
        if size > 100 * 1024 * 1024:
            console.print(
                f"[yellow]Video is {format_size(size)} — "
                f"splitting into ~{target_mb:.0f}MB chunks...[/yellow]"
            )
            chunks = split_video(video_path, target_mb)
            if not chunks:
                raise YouTubeToKimiError("No chunks were produced.")
        else:
            chunks = [video_path]

        # Analyze chunks
        if len(chunks) == 1:
            console.print("[bold blue]🤖 Analyzing with Kimi API...[/bold blue]")
            video_url = upload_video(chunks[0])
            result = analyze_video(video_url, prompt, model=model)
        else:
            console.print(
                f"[bold blue]🤖 Analyzing {len(chunks)} chunks with Kimi API...[/bold blue]"
            )
            part_results = analyze_chunks(chunks, prompt, model=model)

            # Summarize partial results
            console.print("[bold blue]📝 Summarizing all parts...[/bold blue]")
            result = "\n\n".join(
                f"## 片段 {i + 1} 分析\n{r}" for i, r in enumerate(part_results)
            )

        console.print()
        console.print("[bold green]📋 Analysis Result:[/bold green]")
        console.print(result)

        if save:
            save.write_text(result, encoding="utf-8")
            console.print()
            console.print(f"[dim]💾 Saved to {save}[/dim]")

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
