#!/usr/bin/env python3
"""
scripts/distill_cognitive_model.py — 小饭语料处理脚本

支持多种模式:
  distill  — 4 维度知识蒸馏(Recurring Ideas / Decision Rules / Mental Models / Vocabulary)
  summary  — 内容总结/整理笔记(核心主题 + 主要观点 + 关键信息 + 独特视角)

用法:
  # 蒸馏(默认)
  python3 scripts/distill_cognitive_model.py
  python3 scripts/distill_cognitive_model.py --mode distill --report

  # 总结
  python3 scripts/distill_cognitive_model.py --mode summary
  python3 scripts/distill_cognitive_model.py --mode summary --output-format json

  # 通用
  python3 scripts/distill_cognitive_model.py --list-transcripts
  python3 scripts/distill_cognitive_model.py --mode summary --files 京都风云录之黑金时代_extracted.txt

环境变量:
  ASR_API_KEY    (必填) 硅基流动 API Key
  ASR_BASE_URL   (可选) API 地址,默认 https://api.siliconflow.cn/v1/chat/completions
  ASR_MODEL      (可选) 模型名,默认 Qwen/Qwen2.5-7B-Instruct
"""

import os
import sys
import json
import asyncio
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

# ── 路径与 API 配置 ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPTS_DIR = REPO_ROOT / "transcripts"
DEFAULT_OUTPUT = REPO_ROOT / "notes" / "distill_output.json"
DEFAULT_REPORT = REPO_ROOT / "notes" / "xiaofan_cognitive_model_v1.1.md"

# 硅基流动 API 配置(从环境变量读取,禁止硬编码明文)
API_KEY = os.environ.get("ASR_API_KEY")
BASE_URL = os.environ.get("ASR_BASE_URL", "https://api.siliconflow.cn/v1/chat/completions")
MODEL = os.environ.get("ASR_MODEL", "Qwen/Qwen2.5-7B-Instruct")

# 默认语料(Feel free to override via --files)
DEFAULT_FILES = [
    "京都风云录之黑金时代_extracted.txt",
    "凡人炒股传_extracted.txt",
    "女神异闻录_extracted.txt",
]

# ── Prompt 模板 ─────────────────────────────────────────────────────────────
PROMPT_TEMPLATES = {
    "distill": """
你是一个执行「小饭认知模型」知识蒸馏的 Agent。
请仔细阅读以下视频/文章的文本转录稿，并提取出其中属于"小饭"这个人的核心认知模型。

你需要严格按照以下四个维度输出（必须使用中文）：
1. Recurring Ideas (高频核心观点)：他对某些事物的固执看法或反复强调的理论。
2. Decision Rules (行为与判断准则)：格式必须是 IF... THEN... 的规则。
3. Mental Models (底层心智模型)：他理解世界的基础框架（如对资本、人性的定义）。
4. Vocabulary (专属词汇与话语标记)：具有强个人色彩的词汇。

【绝对红线（RFC-002 Evidence Model）】：
你提取的任何一条结论，都必须在末尾附带严格的证据挂载，格式为：
*Evidence [Line XX-YY]*: "原话摘录..."
如果没有找到明确的原话证据，宁可不写，绝不允许自己凭空总结（幻觉）！

文本内容如下（每行开头有行号，请用作 Line XX 的参考）：
{content}

请直接输出 Markdown 格式的蒸馏结果。
""",

    "summary": """
你是一个内容总结助手。请仔细阅读以下转录稿，提取核心要点。

请按以下格式输出（Markdown）：

## 核心主题
用一句话概括这段内容的主题

## 主要观点
- 观点1...
- 观点2...

## 关键信息
- 事实/数据1...
- 事实/数据2...

## 独特视角
- 视角1...
- 视角2...
""",
}


# ── 工具函数 ─────────────────────────────────────────────────────────────────
def list_transcripts() -> None:
    """列出 transcripts/ 下所有可用的 _extracted.txt 文件"""
    if not TRANSCRIPTS_DIR.is_dir():
        print(f"❌ 目录不存在: {TRANSCRIPTS_DIR}")
        sys.exit(1)
    files = sorted(TRANSCRIPTS_DIR.glob("*_extracted.txt"))
    if not files:
        print(f"⚠️ 未找到任何 *_extracted.txt 文件于 {TRANSCRIPTS_DIR}")
        sys.exit(0)
    print(f"📂 可用语料 ({len(files)} 个):\n")
    for f in files:
        stat = f.stat()
        print(f"  {f.name}  ({stat.st_size / 1024:.0f} KB)")


def get_file_metadata(filepath: Path) -> tuple:
    """返回 (mtime, sha256)"""
    stat = os.stat(filepath)
    with open(filepath, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    return stat.st_mtime, file_hash


async def call_llm(session, content: str, prompt_template: str, temperature: float = 0.2) -> str:
    """调用硅基流动 LLM"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个严格的、基于证据的文本分析引擎。"},
            {"role": "user", "content": prompt_template.replace("{content}", content[:15000])}
        ],
        "temperature": temperature
    }
    try:
        async with session.post(BASE_URL, headers=headers, json=payload, timeout=60) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"# Error 调用 LLM 失败\n\n```\n{str(e)}\n```\n"


# ── 输出解析 ─────────────────────────────────────────────────────────────────
def parse_dimensions(raw: str) -> dict:
    """
    从 LLM 的 Markdown 输出中按 ## 标题启发式提取各维度文本(dict 模式)。
    若无法分割,归入 recurring_ideas。
    """
    lines = raw.splitlines()
    current = "recurring_ideas"
    result = {"recurring_ideas": "", "decision_rules": "", "mental_models": "", "vocabulary": ""}
    keywords = {
        "recurring": "recurring_ideas",
        "高频核心观点": "recurring_ideas",
        "recurring ideas": "recurring_ideas",
        "decision": "decision_rules",
        "行为与判断准则": "decision_rules",
        "decision rules": "decision_rules",
        "mental": "mental_models",
        "底层心智模型": "mental_models",
        "mental models": "mental_models",
        "vocabulary": "vocabulary",
        "专属词汇": "vocabulary",
        "话语标记": "vocabulary",
    }
    for line in lines:
        lower = line.strip().lower()
        for kw, dim in keywords.items():
            if kw in lower and line.strip().startswith("##"):
                current = dim
                break
        if not line.strip().startswith("##"):
            result[current] += line + "\n"
    for k in result:
        result[k] = result[k].strip()
    return result


def parse_summary(raw: str) -> dict:
    """
    从 LLM 的 Markdown 输出中按 ## 标题提取 summary 结构。
    """
    lines = raw.splitlines()
    current = "summary"
    result = {"summary": "", "key_points": [], "key_info": [], "unique_perspectives": []}
    key_points_buffer = []
    key_info_buffer = []
    unique_buffer = []

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("## 核心主题") or stripped.startswith("## 核心主题"):
            current = "summary"
            continue
        if "主要观点" in lower or "主要观点" in stripped:
            current = "key_points"
            continue
        if "关键信息" in lower or "关键信息" in stripped:
            current = "key_info"
            continue
        if "独特视角" in lower or "独特视角" in stripped:
            current = "unique_perspectives"
            continue

        if current == "summary":
            result["summary"] += line + "\n"
        elif current == "key_points":
            if stripped.startswith("- ") or stripped.startswith("* "):
                key_points_buffer.append(stripped[2:].strip())
        elif current == "key_info":
            if stripped.startswith("- ") or stripped.startswith("* "):
                key_info_buffer.append(stripped[2:].strip())
        elif current == "unique_perspectives":
            if stripped.startswith("- ") or stripped.startswith("* "):
                unique_buffer.append(stripped[2:].strip())

    result["summary"] = result["summary"].strip()
    result["key_points"] = key_points_buffer
    result["key_info"] = key_info_buffer
    result["unique_perspectives"] = unique_buffer
    return result


# ── 主流程 ───────────────────────────────────────────────────────────────────
async def process(files: list[str], mode: str, output_json: Path | None, output_report: Path | None) -> None:
    """执行处理:对每个文件调用 LLM,按 mode 输出 JSON 或 Markdown"""
    import aiohttp  # 懒加载
    if not API_KEY:
        print("❌ 环境变量 ASR_API_KEY 未设置。请 export ASR_API_KEY='sk-...'", file=sys.stderr)
        sys.exit(1)
    if not TRANSCRIPTS_DIR.is_dir():
        print(f"❌ 目录不存在: {TRANSCRIPTS_DIR}", file=sys.stderr)
        sys.exit(1)

    prompt_template = PROMPT_TEMPLATES[mode]
    temperature = 0.2 if mode == "distill" else 0.5
    sources = []

    async with aiohttp.ClientSession() as session:
        for filename in files:
            filepath = TRANSCRIPTS_DIR / filename
            if not filepath.exists():
                print(f"⚠️ 跳过 {filename},文件不存在")
                continue

            print(f"🔍 处理中 ({mode}): {filename} ...")
            mtime, fhash = get_file_metadata(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                numbered_lines = "".join([f"{i+1}: {line}" for i, line in enumerate(lines)])

            raw_output = await call_llm(session, numbered_lines, prompt_template, temperature)

            entry = {
                "filename": filename,
                "sha256": fhash,
                "mtime": datetime.fromtimestamp(mtime).isoformat(),
            }

            if mode == "distill":
                entry.update(parse_dimensions(raw_output))
            else:
                entry.update(parse_summary(raw_output))

            entry["_raw"] = raw_output  # 保留原始 LLM 输出
            sources.append(entry)
            print(f"  ✅ 完成 ({len(raw_output)} chars)")

    if not sources:
        print("⚠️ 没有成功处理任何文件,跳过输出")
        return

    # 输出 JSON
    if output_json:
        result = {
            "version": "1.1",
            "mode": mode,
            "processed_at": datetime.now().isoformat(),
            "model": MODEL,
            "sources": sources
        }
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✅ JSON 已保存 -> {output_json}")

    # 输出 Markdown 报告
    if output_report:
        report_lines = [f"# 小饭语料处理报告 ({mode})\n", "---\n"]
        for src in sources:
            report_lines.append(f"\n## 语料来源: {src['filename']}\n")
            report_lines.append(f"- **SHA256**: `{src['sha256']}`\n")
            if mode == "distill":
                for dim in ["recurring_ideas", "decision_rules", "mental_models", "vocabulary"]:
                    if src.get(dim):
                        report_lines.append(f"\n### {dim}\n\n{src[dim]}\n")
            else:
                if src.get("summary"):
                    report_lines.append(f"\n### 核心主题\n\n{src['summary']}\n")
                for section, label in [("key_points", "主要观点"), ("key_info", "关键信息"), ("unique_perspectives", "独特视角")]:
                    items = src.get(section, [])
                    if items:
                        report_lines.append(f"\n### {label}\n")
                        for item in items:
                            report_lines.append(f"- {item}\n")
            report_lines.append("\n---\n")
        output_report.parent.mkdir(parents=True, exist_ok=True)
        output_report.write_text("".join(report_lines), encoding="utf-8")
        print(f"✅ 报告已保存 -> {output_report}")


# ── CLI 入口 ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="小饭语料处理 — 蒸馏 / 总结 / 笔记整理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
环境变量:
  ASR_API_KEY    硅基流动 API Key (必填)
  ASR_BASE_URL   API 地址 (默认: https://api.siliconflow.cn/v1/chat/completions)
  ASR_MODEL      模型名 (默认: Qwen/Qwen2.5-7B-Instruct)

模式说明:
  distill   4 维度知识蒸馏(默认):Recurring Ideas / Decision Rules / Mental Models / Vocabulary
            输出 JSON 供 sync_distill_to_xiaofan.py 消费
  summary   内容总结:核心主题 + 主要观点 + 关键信息 + 独特视角
            输出 Markdown 报告(默认)或 JSON

示例:
  export ASR_API_KEY='sk-...'
  python3 scripts/distill_cognitive_model.py                    # 蒸馏(默认)
  python3 scripts/distill_cognitive_model.py --mode summary     # 总结
  python3 scripts/distill_cognitive_model.py --mode summary --files 京都风云录之黑金时代_extracted.txt
  python3 scripts/distill_cognitive_model.py --mode distill --report
  python3 scripts/distill_cognitive_model.py --mode summary --output-format json
  python3 scripts/distill_cognitive_model.py --list-transcripts
        """
    )
    parser.add_argument("--mode", choices=["distill", "summary"], default="distill",
                        help="处理模式: distill=知识蒸馏(默认), summary=内容总结")
    parser.add_argument("--files", nargs="*", default=None,
                        help="要处理的语料文件名(空格分隔,来自 transcripts/ 目录);不指定则使用默认三篇")
    parser.add_argument("--output", type=Path, default=None,
                        help="输出路径(JSON/MD 取决于 --output-format)")
    parser.add_argument("--output-format", choices=["json", "md", "auto"], default="auto",
                        help="输出格式: json/md/auto(dict 模式→json, summary 模式→md)")
    parser.add_argument("--report", action="store_true",
                        help="强制输出 Markdown 报告(默认: dict 模式仅 json, summary 模式仅 md)")
    parser.add_argument("--list-transcripts", action="store_true",
                        help="列出 transcripts/ 下所有可用语料文件并退出")

    args = parser.parse_args()

    if args.list_transcripts:
        list_transcripts()
        return

    files = args.files if args.files is not None else DEFAULT_FILES
    mode = args.mode

    # 确定输出格式
    fmt = args.output_format
    if fmt == "auto":
        fmt = "json" if mode == "distill" else "md"

    # 确定输出路径
    out_path = args.output
    if out_path is None:
        if fmt == "json":
            out_path = REPO_ROOT / "notes" / f"{mode}_output.json"
        else:
            out_path = REPO_ROOT / "notes" / f"{mode}_report.md"

    # 确定是否输出 JSON 和是否输出 MD
    output_json = out_path if fmt == "json" else None
    output_report = out_path if fmt == "md" else None
    if args.report and fmt == "json":
        # --report 强制额外输出 md
        output_report = REPO_ROOT / "notes" / f"{mode}_report.md"

    asyncio.run(process(files, mode, output_json, output_report))


if __name__ == "__main__":
    main()