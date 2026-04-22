# youtube-to-kimi

一个 CLI 工具，用于将 YouTube 视频下载并切割为 **<100MB** 的小片段，以便上传给 Kimi 等大模型进行逐帧视频分析。

## 为什么需要这个工具？

大多数 AI 助手（包括 Kimi）**无法直接访问 YouTube 链接**来分析视频内容。你需要先把视频下载到本地，再上传给 AI。但还有一个限制：

- **单次文件上传通常有 100MB 上限**
- 一个 45 分钟的技术演讲（1080p）通常有 300~600MB

`youtube-to-kimi` 帮你一键完成：

```
YouTube URL → 下载 → 自动切割成 <100MB 片段 → 按顺序上传给 AI
```

切割使用 ffmpeg 的 **无损 stream-copy** 模式，不重新编码，不损失画质，速度极快。

---

## 前置依赖

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| [uv](https://docs.astral.sh/uv/) | Python 包管理和运行 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 下载 YouTube 视频 | `brew install yt-dlp` 或 `uv tool install yt-dlp` |
| [ffmpeg](https://ffmpeg.org/) | 视频切割（无损） | `brew install ffmpeg` |

验证安装：

```bash
uv --version      # >= 0.6
yt-dlp --version  # >= 2025
ffmpeg -version   # 任意版本
```

---

## 安装

```bash
# 方式 1：作为全局工具安装（推荐）
cd /path/to/youtube-to-kimi
uv tool install .

# 方式 2：直接运行（无需安装）
cd /path/to/youtube-to-kimi
uv run youtube-to-kimi --help
```

---

## 使用方法

### 一键工作流（推荐）

```bash
youtube-to-kimi prepare "https://www.youtube.com/watch?v=xxxxx"
```

输出示例：

```
✅ Downloaded: ~/Downloads/youtube_to_kimi/How_Conductor_Builds_xxxx.mp4
   Size: 325.5 MB

Video is 325.5 MB — splitting into ~85MB chunks...

🎬 Video Chunks Ready for Upload
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃  # ┃ Filename                              ┃ Size    ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│  1 │ How_Conductor_Builds_xxxx_part_000.mp4 │ 67.8 MB │
│  2 │ How_Conductor_Builds_xxxx_part_001.mp4 │ 65.2 MB │
│  3 │ How_Conductor_Builds_xxxx_part_002.mp4 │ 64.9 MB │
│  4 │ How_Conductor_Builds_xxxx_part_003.mp4 │ 62.1 MB │
│  5 │ How_Conductor_Builds_xxxx_part_004.mp4 │ 59.5 MB │
│  6 │ How_Conductor_Builds_xxxx_part_005.mp4 │  3.5 MB │
├────┼───────────────────────────────────────┼─────────┤
│    │ Total                                 │ 323.0 MB│
└────┴───────────────────────────────────────┴─────────┘

💡 Tip: Upload these chunks to Kimi sequentially to analyze the full video.
```

### 分步执行

```bash
# 1. 仅下载
youtube-to-kimi download "https://www.youtube.com/watch?v=xxxxx"

# 2. 仅切割（对已有本地视频使用）
youtube-to-kimi split path/to/video.mp4 --target-mb 90
```

### 命令参考

```bash
# 查看帮助
youtube-to-kimi --help

# 查看版本
youtube-to-kimi version

# 自定义输出目录和切片大小
youtube-to-kimi prepare "URL" \
  --output ~/Videos/analysis \
  --target-mb 90 \
  --keep-original
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | YouTube 视频链接 | 必填 |
| `--output, -o` | 输出目录 | `~/Downloads/youtube_to_kimi` |
| `--target-mb, -t` | 每个片段的目标大小 | `85.0` |
| `--keep-original` | 保留原始未切割文件 | `False` |

---

## 完整工作流：从 YouTube 到 AI 分析

```bash
# 1. 下载并切割
youtube-to-kimi prepare "https://www.youtube.com/watch?v=xxxxx"

# 2. 在 Kimi 中按顺序上传片段
#    - 上传 part_000.mp4，并说 "这是视频第 1 部分"
#    - 上传 part_001.mp4，并说 "这是视频第 2 部分，继续分析"
#    - ...以此类推
#
# 3. 等所有片段上传完成后，提问：
#    "请总结这个视频的核心观点"
#    "视频里提到了哪些技术架构？"
#    "画一张架构图来描述这个系统"
```

> 💡 **提示**：一次上传所有片段给 Kimi，AI 会自动按顺序理解完整内容。你也可以每上传一个片段就简要说明进度。

---

## 技术细节

### 为什么用 stream-copy 而不是压缩？

| 方案 | 画质损失 | 处理速度 | 文件大小可控性 |
|------|----------|----------|----------------|
| **Stream-copy（本项目）** | 零损失 | 极快（秒级） | 按时间切割，片段大小接近 |
| 压缩/转码 | 有损 | 慢（分钟级） | 大小可控但画质下降 |

对于技术演讲、代码演示、UI 录屏等场景，**保持画质至关重要**（需要看清文字和代码）。Stream-copy 通过复制原始码流来切割，画质完全无损，速度极快。

### 切割逻辑

1. 通过 `ffprobe` 获取视频码率（bitrate）
2. 计算每个片段的安全时长：`segment_time = (target_mb × 0.85 × 8 × 1024²) / bitrate`
3. 使用 `ffmpeg -f segment -c copy` 进行无损切割
4. 每个片段大小 ≤ target_mb，最后一片可能较小

### 字幕

下载时自动提取英文字幕和中文字幕（`en,zh,zh-CN,zh-TW`），并嵌入到 MP4 文件中，方便 AI 理解对话内容。

---

## 常见问题

**Q: 支持哪些视频平台？**
> 所有 [yt-dlp 支持的平台](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)都可以，包括 YouTube、Bilibili、Twitter/X、Vimeo 等。

**Q: 为什么切片后总大小比原文件小？**
> 因为去除了原始文件的元数据冗余，且最后一个片段通常较小。内容本身没有任何损失。

**Q: 可以调整切片大小吗？**
> 可以，使用 `--target-mb` 参数。建议设置在 85~95MB 之间，留出余量避免刚好超过 100MB 限制。

**Q: 需要 YouTube API Key 吗？**
> 不需要。yt-dlp 直接解析页面获取视频流地址。

---

## License

MIT
