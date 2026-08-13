# B站视频内容整理工作流

## 目录结构

```
.
├── raw/          原始字幕/音频文件（从浏览器下载后放这里，已加入 .gitignore）
├── transcripts/  提取的纯文本（_extracted.txt / _timestamped.txt）
├── notes/        AI 整理后的笔记和总结
├── scripts/      工具脚本
│   ├── audio_to_text.sh         通用音频转写(参数化,支持通配符)
│   ├── process_batch.sh         批处理 shim(→ audio_to_text.sh)
│   ├── process_batch_2.sh       批处理 shim(→ audio_to_text.sh)
│   ├── distill_cognitive_model.py  知识蒸馏/内容总结(支持 --mode)
│   ├── sync_distill_to_xiaofan.py  蒸馏产物→Xiaofan persona 模块
│   ├── extract_subtitles.py   字幕提取（支持 .json/.srt/.txt）
│   ├── asr_transcribe.py      语音转文字（硅基流动 ASR）
│   ├── llm_summarize.py       入口包装器（无人值守批量用）
│   └── llm_pipeline/          V4 LLM 处理引擎（模块化架构）
│       ├── config.py          配置 Dataclass
│       ├── prompts.py         Prompt 集中管理
│       ├── chunker.py         tiktoken 精确 Token 切分
│       ├── engine.py          aiohttp 全异步网络引擎
│       ├── merger.py          树状递归合并（Tree Summarization）
│       ├── telemetry.py       Token 消费遥测与财报
│       └── cli.py             命令行入口与 ASR 清洗
├── Xiaofan_Knowledge_Distillation/
│   ├── README.md              目录索引(人格内容 vs 框架设计分类)
│   ├── Prompt_System.md       手写版 System Prompt v2.0
│   ├── Style_Profile.md       风格画像
│   ├── Thinking_Framework.md  认知框架
│   ├── Output_Patterns.md     输出模板
│   ├── Vocabulary.md          核心词汇库
│   ├── Boundary_Controller.md  Agent 边界控制(框架设计)
│   ├── State_Machine.md        Agent 状态机(框架设计)
│   ├── Permission_Model.md     Agent 权限模型(框架设计)
│   └── Verification_Protocol.md Agent 验证协议(框架设计)
├── test_persona.py             人格测试脚本(支持 --test-file)
├── tests/
│   ├── test_cases.json         15 道基础测试题
│   ├── test_cases_extended.json 80 道扩展测试题
│   └── TESTING.md              测试指南
├── .env.example                环境变量模板
├── process_new_audio.sh        批量转写 shim(→ audio_to_text.sh)
```

---

## 环境与依赖准备

在使用本工作流前，请确保您的环境中已配置以下依赖：

### 1. 基础环境与系统工具
- **Python 3.9+**：用于运行提取脚本与大模型调用脚本。
- **FFmpeg**：用于将超过 50MB 的大体积音频分割为多段（仅**路径 B**无字幕音频转写时需要，如果全是有字幕的视频可不装）。
  - 安装参考：`sudo apt install ffmpeg` (Linux) / `brew install ffmpeg` (macOS) / Windows 下请下载静态包并配置环境变量。

### 2. Python 依赖
```bash
# LLM 引擎核心依赖（V4 必须）
pip install aiohttp tiktoken requests
```

### 3. API 账号申请
- 注册 [SiliconFlow (硅基流动)](https://cloud.siliconflow.cn)，申请并获取 API Key。它将用于为您提供高效的语音识别（ASR）与大模型总结（LLM）能力。

---

## 路径 A：有字幕（快速）

### 1. 下载字幕
浏览器使用脚本，下载后保存到 `raw/`。

### 2. 提取纯文本

```bash
# 纯文本（自动去重 + 按时间间隔分段）
python scripts/extract_subtitles.py raw/视频名.json

# 保留时间戳（用于做细节版观看笔记）
python scripts/extract_subtitles.py raw/视频名.json --timestamp

# 批量处理 raw/ 目录
python scripts/extract_subtitles.py --dir raw/
```

输出到当前目录，手动移入 `transcripts/`。

### 3. AI 整理

直接在 agent 会话里说：

```
整理 transcripts/视频名_extracted.txt，输出结构化纪要
整理 transcripts/视频名_extracted.txt，直播闲聊模式
整理 transcripts/视频名_timestamped.txt，做细节版观看笔记，输出到 notes/
整理 transcripts/视频名_extracted.txt，技术教程模式
```

---

## 路径 B：无字幕（ASR 转写）

### 1. 下载音频
用浏览器音频下载插件下载音频，保存到 `raw/`。

超过 50MB 先分割：
```bash
ffmpeg -i raw/视频名.mp3 -f segment -segment_time 1500 -c copy raw/segment_%03d.mp3
```

### 2. ASR 转写

```bash
# 配置（写入 ~/.bashrc 后一劳永逸）
export ASR_API_KEY="your_key"   # 硅基流动 API Key

# 单文件
python scripts/asr_transcribe.py --input raw/视频名.mp3 --output transcripts/视频名_extracted.txt

# 多段合并
python scripts/asr_transcribe.py --input "raw/segment_*.mp3" --output transcripts/视频名_extracted.txt --merge
```

### 3. AI 整理
同路径 A 第 3 步。

---

## 路径 C：知识蒸馏 / 内容总结

将 transcripts 中的语料通过 LLM 进行结构化提取,产出 Xiaofan 人格模块或笔记。

### 环境变量

```bash
export ASR_API_KEY="your_key"   # 硅基流动 API Key（蒸馏/总结共用）
```

### 蒸馏（4 维度提取 → Xiaofan 模块）

```bash
# 默认蒸馏（3 篇语料 → notes/distill_output.json）
python3 scripts/distill_cognitive_model.py

# 指定文件 + 输出 Markdown 报告
python3 scripts/distill_cognitive_model.py --files 京都风云录之黑金时代_extracted.txt --report

# 转换到 Xiaofan 仓库
python3 scripts/sync_distill_to_xiaofan.py --dry-run   # 预览
python3 scripts/sync_distill_to_xiaofan.py              # 写入
```

### 总结（内容摘要 → 笔记）

```bash
# 总结默认语料 → notes/summary_report.md
python3 scripts/distill_cognitive_model.py --mode summary

# 指定文件
python3 scripts/distill_cognitive_model.py --mode summary --files 京都风云录之黑金时代_extracted.txt

# JSON 输出
python3 scripts/distill_cognitive_model.py --mode summary --output-format json
```

---

## 人格测试

```bash
# 默认问题
python3 test_persona.py

# 从基础 15 题选第 5 题
python3 test_persona.py --test-file tests/test_cases.json --test-id 5

# 从扩展 80 题选第 1 题
python3 test_persona.py --test-file tests/test_cases_extended.json

# 列出所有用例
python3 test_persona.py --test-file tests/test_cases_extended.json --list
```

---

### 1. 下载音频
用浏览器音频下载插件下载音频，保存到 `raw/`。

超过 50MB 先分割：
```bash
ffmpeg -i raw/视频名.mp3 -f segment -segment_time 1500 -c copy raw/segment_%03d.mp3
```

### 2. ASR 转写

```bash
# 配置（写入 ~/.bashrc 后一劳永逸）
export ASR_API_KEY="your_key"   # 硅基流动 API Key

# 单文件
python scripts/asr_transcribe.py --input raw/视频名.mp3 --output transcripts/视频名_extracted.txt

# 多段合并
python scripts/asr_transcribe.py --input "raw/segment_*.mp3" --output transcripts/视频名_extracted.txt --merge
```

### 3. AI 整理
同路径 A 第 3 步。

---

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `ASR_API_KEY` | ASR 转写 Key（必填）| — |
| `ASR_BASE_URL` | ASR 接口 | `https://api.siliconflow.cn/v1` |
| `ASR_MODEL` | ASR 模型 | `TeleAI/TeleSpeechASR` |
| `LLM_API_KEY` | LLM 摘要 Key（必填）| — |
| `LLM_BASE_URL` | LLM 接口 | `https://api.siliconflow.cn/v1` |
| `LLM_MODEL` | LLM 模型 | `Qwen/Qwen3-8B` |
| `WEIBO_COOKIE` | 微博抓取 Cookie（必填）| — |
| `WEIBO_UID` | 微博用户 UID | `6231346896` |
| `WEIBO_OUTPUT` | 微博抓取输出路径 | `local_file/小饭-微博-自动抓取.md` |
| `BILI_COOKIE_PATH` | B站下载 Cookie 路径 | `/tmp/bili_cookie.txt` |
| `BILI_OUTPUT_DIR` | B站下载输出目录 | `raw/xiaofan_new_clips` |

> 硅基流动同一个 API Key 同时支持 ASR 和 LLM，两个 Key 可以设成同一个值。
> API Key 在 [cloud.siliconflow.cn](https://cloud.siliconflow.cn) 申请。

---

## Prompt 模板

Prompt 统一管理于 `scripts/llm_pipeline/prompts.py`，通过 `--mode` 参数选择：

| 模式 | 参数 | 适用场景 |
|------|------|---------|
| 通用 | `--mode general`（默认）| 讲课、访谈、播客、视频解说 |
| 直播闲聊 | `--mode livestream` | 多人连麦、直播、弹幕多 |
| 细节版观看笔记 | `--mode detail` | 想还原视频细节、做精读笔记 |
| 技术教学版 | `--mode tech` | 提取编程教程、操作指南的具体步骤和代码 |

```bash
# 无人值守批量处理示例（V4 引擎）
python scripts/llm_summarize.py \
  --input transcripts/视频名_extracted.txt \
  --output notes/视频名_整理稿.md \
  --mode tech \
  --workers 3        # 遇 429 限流可调低，默认 5
  # --chunk-size 6000  # Token 切片阈值（默认 6000）
```

> **V4 引擎**采用全异步 `aiohttp` + `tiktoken` 精确 Token 切片 + 树状递归合并架构，
> 支持任意长度字幕无损处理。运行结束后自动打印 Token 消费财报。
