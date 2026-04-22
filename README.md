# youtube-to-kimi

基于 **yt-dlp** + **ffmpeg stream-copy** 的视频分析预处理工具。

将 YouTube（及 1000+ 平台）视频下载并切割为 **<100MB** 的片段，让 **Kimi**（kimi-k2.6）能够进行逐帧视频分析。

> 切割后的 MP4 片段也可用于其他支持视频输入的 AI，但一键分析功能（`analyze` 命令）和 Kimi CLI Skill 均基于 Kimi 的视频理解能力构建。

> 🎬 [观看介绍视频](./assets/demo.mp4) — 30 秒快速了解功能和工作流

---

## 双线使用方式

| 路线 | 适用用户 | 需要什么 | 工作方式 |
|------|---------|---------|---------|
| **🤖 路线 A：独立 CLI + API** | 所有用户 | Moonshot API Key (`sk-...`) | `youtube-to-kimi analyze "URL"` 一键完成下载→切割→**Kimi 分析** |
| **💬 路线 B：Kimi CLI Skill** | Kimi Code CLI 订阅用户 | 无需 API Key | 在 Kimi CLI 对话中自然触发，自动下载切割后通过 **Kimi ReadMediaFile** 分析 |

### 路线 A 示例

```bash
export KIMI_API_KEY="sk-xxxxx"
youtube-to-kimi analyze "https://www.youtube.com/watch?v=..." \
  --prompt "总结这个技术演讲的核心观点" \
  --model kimi-k2.6
```

### 路线 B 示例

在 Kimi Code CLI 中直接说：

```
分析这个视频：https://www.youtube.com/watch?v=...
```

Kimi CLI 会自动触发 skill，完成下载、切割、逐段读取、汇总分析。

---

## 为什么基于 yt-dlp？

[yt-dlp](https://github.com/yt-dlp/yt-dlp) 是当今最强大的视频下载工具：

- **1000+ 平台支持**：YouTube、Bilibili、Twitter/X、Vimeo、抖音...
- **持续更新**：社区活跃，平台变动几小时内修复
- **最佳画质**：自动选择最高可用质量
- **字幕提取**：自动下载并嵌入多语言字幕
- **开源可审计**：无黑盒，无隐私风险

我们不重新发明下载轮子，而是把 yt-dlp 的能力无缝接入 AI 工作流。

---

## 核心链路

```
YouTube/Bilibili/... URL
    ↓  yt-dlp 下载（最佳画质 + 字幕嵌入）
本地视频文件（可能 300~600MB）
    ↓  ffmpeg -c copy 无损切割
<100MB 片段 × N
    ↓
┌─────────────────┬──────────────────┐
│  路线 A：API     │  路线 B：Kimi CLI │
│  自动上传分析    │  ReadMediaFile   │
│  返回文本结果   │  逐段读取分析    │
└─────────────────┴──────────────────┘
```

切割使用 ffmpeg **无损 stream-copy**（不重新编码），画质零损失，速度极快。

---

## 前置依赖

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| [uv](https://docs.astral.sh/uv/) | Python 包管理和运行 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | 下载视频（1000+ 平台） | `brew install yt-dlp` 或 `uv tool install yt-dlp` |
| [ffmpeg](https://ffmpeg.org/) | 无损视频切割 | `brew install ffmpeg` |

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

## 命令参考

### 路线 A：一键 AI 分析

```bash
# 分析 YouTube 视频（自动下载→切割→调用 Kimi API）
youtube-to-kimi analyze "https://www.youtube.com/watch?v=..."

# 分析本地视频文件
youtube-to-kimi analyze path/to/video.mp4 --prompt "总结内容"

# 自定义模型和保存结果
youtube-to-kimi analyze "URL" \
  --prompt "提取所有提到的技术架构" \
  --model kimi-k2.6 \
  --save result.md
```

环境变量：
- `KIMI_API_KEY` — Moonshot API Key（`sk-...` 格式）
- `KIMI_BASE_URL` — 可选，默认 `https://api.moonshot.cn/v1`

### 路线 B：下载切割（供 Kimi CLI 使用）

```bash
# 下载并切割（供后续手动/Skill 上传）
youtube-to-kimi prepare "https://www.youtube.com/watch?v=..."

# 仅下载
youtube-to-kimi download "URL"

# 仅切割本地视频
youtube-to-kimi split path/to/video.mp4 --target-mb 90
```

### 其他命令

```bash
youtube-to-kimi --help      # 查看所有命令
youtube-to-kimi version     # 查看版本和依赖信息
```

---

## 技术细节

### 为什么用 stream-copy 而不是压缩？

| 方案 | 画质损失 | 处理速度 | 适用场景 |
|------|----------|----------|----------|
| **Stream-copy（本项目）** | 零损失 | 极快（秒级） | 技术演讲、代码演示、UI 录屏 |
| 压缩/转码 | 有损 | 慢（分钟级） | 普通观影、社交媒体 |

对于需要看清**文字、代码、UI 细节**的技术视频，stream-copy 是唯一正确的选择。

### 切割逻辑

1. `ffprobe` 获取视频码率
2. 计算安全时长：`segment_time = (target_mb × 0.85 × 8 × 1024²) / bitrate`
3. `ffmpeg -f segment -c copy` 无损切割
4. 每片 ≤ target_mb，最后一片可能较小

### 字幕处理

下载时自动提取英文字幕和中文字幕（`en,zh,zh-CN,zh-TW`），嵌入到 MP4 中，帮助 AI 理解对话内容。

---

## 完整工作流示例

### 路线 A（独立 CLI + API）

```bash
# 1. 设置 API Key
export KIMI_API_KEY="sk-xxxxx"

# 2. 一键分析
youtube-to-kimi analyze "https://www.youtube.com/watch?v=..." \
  --prompt "请画一张架构图来描述这个系统的技术架构" \
  --save analysis.md

# 3. 查看结果
cat analysis.md
```

### 路线 B（Kimi CLI Skill）

```
# 在 Kimi CLI 中输入
分析这个视频：https://www.youtube.com/watch?v=...

# Kimi CLI 会自动：
# 1. 运行 youtube-to-kimi prepare 下载并切割
# 2. 用 ReadMediaFile 逐个读取片段
# 3. 汇总并输出完整分析
```

---

## 常见问题

**Q: 支持哪些视频平台？**
> 所有 [yt-dlp 支持的平台](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)都可以，包括 YouTube、Bilibili、Twitter/X、Vimeo、抖音等 1000+ 平台。

**Q: 为什么需要切割？**
> 大多数 AI 助手（包括 Kimi）的单次文件上传限制为 100MB。一个 45 分钟 1080p 视频通常有 300~600MB。

**Q: 切割后视频质量会下降吗？**
> 不会。ffmpeg `-c copy` 是 stream-copy，直接复制原始码流，画质零损失。之后由 **Kimi k2.6** 模型进行视频理解分析。

**Q: 需要 YouTube API Key 吗？**
> 不需要。yt-dlp 直接解析页面获取视频流地址。

**Q: Kimi Code 的 key（`sk-kimi-...`）能用吗？**
> 不能。Kimi Code API 仅限 Coding Agent 环境使用。请使用 Moonshot 开放平台申请的 key（`sk-...` 格式）。

**Q: 为什么强调 Kimi？其他 AI 不能用吗？**
> 切割后的 MP4 片段是通用格式，任何支持视频输入的 AI 都可以使用。但本项目的一键分析功能（`analyze` 命令）和 Kimi CLI Skill 是专门基于 **Kimi k2.6 的视频理解能力**构建的，目前仅支持调用 Kimi API。

**Q: 可以调整切片大小吗？**
> 可以，使用 `--target-mb` 参数。建议 85~95MB，留出余量避免刚好超过 100MB 限制。

---

## License

MIT
