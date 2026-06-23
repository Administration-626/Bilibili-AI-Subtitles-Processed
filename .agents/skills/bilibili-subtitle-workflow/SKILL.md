---
name: bilibili-subtitle-workflow
description: B站视频字幕/语音转文字工作流。当用户需要整理B站视频内容、处理字幕文件、使用硅基流动ASR进行语音识别、或者将视频文字稿整理成结构化笔记时激活。关键词：字幕、B站、bilibili、语音识别、ASR、TeleSpeechASR、硅基流动、SiliconFlow、视频整理、文字稿。
---

# B站字幕/语音转文字工作流

## 工作流概览

```
有B站AI字幕  →  路径 A：浏览器插件下载字幕 → scripts/extract_subtitles.py → ./ (当前目录)
无字幕/字幕差 →  路径 B：浏览器插件下载音频 → scripts/asr_transcribe.py  → 用户指定路径
                                                        ↓
                                           直接在 agent 会话里说「整理 xxx_extracted.txt」
                                                        ↓
                                                   notes/整理稿.md
```

---

## 路径 A：B站AI字幕（快速路径）

**适用场景**：视频有B站自动字幕或上传者提供的字幕。

### Step 1：浏览器插件下载字幕
- 安装 Tampermonkey 脚本「B站字幕下载器」
- 打开视频，点击下载字幕，保存为 `.json` 或 `.srt` 文件

### Step 2：转换为纯文本
使用工作区脚本 `extract_subtitles.py`：
```bash
# 纯文本模式
python scripts/extract_subtitles.py 视频名.json

# 保留时间戳模式（用于做时间轴笔记）
python scripts/extract_subtitles.py 视频名.json --timestamp

# 批量处理当前目录
python scripts/extract_subtitles.py
```
输出：`视频名_extracted.txt` 或 `视频名_timestamped.txt`

### Step 3：在 agent 会话里原生整理
直接对 agent 说：
```
整理 ./视频名_extracted.txt，输出结构化纪要
整理 ./视频名_extracted.txt，直播闲聊模式
整理 ./视频名_timestamped.txt，做细节版观看笔记
```

> **核心逻辑**：Agent **必须直接使用 `view_file` 工具读取长文本**，并利用自身的顶级大模型能力完成要点提取和排版。因为现代模型的长上下文能力足以应对几万字的文本，无需也**绝对禁止**额外写代码或调用外部 API。

---

## 路径 B：ASR 语音识别（无字幕路径）

**适用场景**：视频无字幕，或字幕质量差（识别率低、断句乱）。

### Step 1：浏览器插件下载音频
- 使用浏览器音频下载插件（如 Media Downloader 等），直接下载视频音频
- 如文件超过 50MB，用 ffmpeg 分割：
```bash
ffmpeg -i input.mp3 -f segment -segment_time 1500 -c copy segment_%03d.mp3
```

### Step 2：ASR 转写
```bash
# 单文件
python scripts/asr_transcribe.py \
  --input "视频音频.mp3" \
  --output "视频名_extracted.txt"

# 多段合并
python scripts/asr_transcribe.py \
  --input "segment_*.mp3" \
  --output "视频名_extracted.txt" \
  --merge
```

### Step 3：在 agent 会话里整理
同路径 A 的 Step 3。

---

## 废弃声明：llm_summarize.py（禁止使用）

> **⚠️ 架构红线 (Architecture Rule)**：
> 过去版本中包含了 `llm_summarize.py` 脚本，用于调用外部小参数模型（如 7B/8B）进行文本总结。
> **现在严格禁止 Agent 运行该脚本或编写类似的 LLM API 包装器。**
> Agent 自身即为顶层大语言模型（Native Intelligence）。面对任何长文本提取、观点提炼、结构化纪要任务，Agent **必须直接读取文本 (`view_file`) 并利用自身的上下文窗口进行原生处理**。将核心智能任务下放给外部低端模型 API 属于严重的“执行层短视（Execution Myopia）”。

---

## 环境变量汇总

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `ASR_API_KEY` | ASR 转写 Key（必填）| — |
| `ASR_BASE_URL` | ASR 接口地址 | `https://api.siliconflow.cn/v1` |
| `ASR_MODEL` | ASR 模型 | `TeleAI/TeleSpeechASR` |

> API Key 在 [cloud.siliconflow.cn](https://cloud.siliconflow.cn) 申请。

---

## 选择路径的决策树

```
视频有B站字幕？
├── 是 → 字幕质量还可以？
│         ├── 是 → 路径 A
│         └── 否 → 路径 B
└── 否 → 路径 B

选摘要模式？
├── 讲课/访谈/播客   → general（默认）
├── 直播/多人连麦    → livestream
├── 想要细节全貌     → detail
└── 技术教程/操作录屏 → tech
```

---

## ASR 限制说明

- 单文件：时长 ≤ 1小时，大小 ≤ 50MB
- 超出大小：必须用 ffmpeg 分割后 `--merge` 合并
- `TeleSpeechASR`：普通话效果最佳
- 备选模型：`FunAudioLLM/SenseVoiceSmall`（中英混合效果好）
- 免费 Rate Limit 具体数字：登录控制台 → 模型广场 → TeleSpeechASR 查看

---

## 文件命名规范

| 原始文件 | 提取纯文本 | 带时间戳 | 整理后输出 |
|---------|-----------|---------|---------|
| `视频名.json` | `视频名_extracted.txt` | `视频名_timestamped.txt` | `视频名_整理稿.md` |
| `视频名.mp3` | `视频名_extracted.txt` | — | `视频名_整理稿.md` |
