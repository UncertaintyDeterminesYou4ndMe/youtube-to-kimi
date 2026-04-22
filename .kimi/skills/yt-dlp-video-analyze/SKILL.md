---
name: yt-dlp-video-analyze
description: >
  Download YouTube videos via yt-dlp, split into <100MB chunks with ffmpeg,
  and analyze them with Kimi (kimi-k2.6) via ReadMediaFile. Use when the user wants to
  analyze a YouTube (or other platform) video with Kimi that is too large to upload
  directly, or when they mention video analysis, video summarization,
  or understanding video content from a URL with Kimi.
triggers:
  - "analyze this youtube video"
  - "summarize this video"
  - "这个视频讲了什么"
  - "分析这个 YouTube 视频"
  - "视频太大上传不了"
  - "video is too large"
  - "can't upload video"
  - "download and analyze video"
  - "yt-dlp"
  - "视频分析"
  - "视频总结"
---

# yt-dlp Video Analyze Skill

## When to Use

Use this skill when the user wants Kimi to analyze a video from YouTube or any other
platform supported by yt-dlp, and the video is too large to upload directly to Kimi.

Common scenarios:
- "Analyze this YouTube video for me with Kimi"
- "让 Kimi 分析这个视频"
- "Summarize the content of this video"
- "What does this technical talk cover?"
- "The video is 500MB, I can't upload it to Kimi"
- "Download and analyze this video"

## Prerequisites

Ensure the following tools are installed on the system:
- `yt-dlp` (for downloading videos)
- `ffmpeg` (for splitting videos without re-encoding)
- `youtube-to-kimi` CLI (this project's CLI tool)

If `youtube-to-kimi` is not installed, install it with:
```bash
uv tool install ~/code/youtube-to-kimi
# or from PyPI when published:
# uv tool install youtube-to-kimi
```

## Workflow

### Step 1: Download and Split

Run the `prepare` command to download the video and split it into <100MB chunks:

```bash
youtube-to-kimi prepare "<VIDEO_URL>"
```

This will:
1. Download the video using yt-dlp (best quality)
2. Automatically split it into ~85MB chunks using ffmpeg stream-copy
3. Output a list of `*_part_*.mp4` files

### Step 2: Analyze Each Chunk

Use `ReadMediaFile` to read each chunk sequentially. Start with a brief
introduction to establish context:

> "I will analyze this video in X parts. Here is part 1:"

Then call `ReadMediaFile` for `*_part_000.mp4`, `*_part_001.mp4`, etc.

After each chunk, confirm receipt and continue:
> "Got part N. Continuing with part N+1:"

### Step 3: Synthesize

After all chunks have been uploaded and read, provide a comprehensive analysis:
- Overall summary of the video
- Key points and takeaways
- Technical details (if applicable)
- Timeline of events (if applicable)

## Important Notes

- **Always use `youtube-to-kimi prepare`**, not manual yt-dlp + ffmpeg commands.
  The CLI handles subtitle extraction, filename sanitization, and optimal splitting.
- **Stream-copy is lossless** — video quality is preserved, text and UI remain readable.
- **If the video is already local and <100MB**, you can skip splitting and use
  `ReadMediaFile` directly on the original file.
- **If the user has a Kimi API key** (Moonshot `sk-...` key, not Kimi Code key),
  suggest using the `analyze` command for fully automated analysis:
  ```bash
  export KIMI_API_KEY="sk-..."
  youtube-to-kimi analyze "<URL>" --prompt "Summarize this video"
  ```

## Example Session

**User**: "Analyze this video for me: https://www.youtube.com/watch?v=dQw4w9WgXcQ"

**Agent**:
1. Run: `youtube-to-kimi prepare "https://www.youtube.com/watch?v=dQw4w9WgXcQ"`
2. Observe output: generates `dQw4w9WgXcQ_part_000.mp4`, `part_001.mp4`, etc.
3. Message user: "This video is 350MB. I've split it into 4 parts. Let me analyze them:"
4. ReadMediaFile on part_000: "Here's part 1..."
5. ReadMediaFile on part_001: "Part 2..."
6. Continue until all parts are read
7. Provide final comprehensive summary

## Why yt-dlp + ffmpeg stream-copy?

- **yt-dlp**: Supports 1000+ video platforms, always up-to-date
- **ffmpeg stream-copy**: Splits in seconds without quality loss
- **No re-encoding**: Preserves text readability, code clarity, UI details
- **Open source**: Fully transparent, auditable pipeline
