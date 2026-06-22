#!/usr/bin/env python3
"""
语音转文字脚本（OpenAI 兼容接口）
用法：
  python asr_transcribe.py --input audio.mp3 --output result.txt
  python asr_transcribe.py --input "**/*.mp3" --output result.txt --merge

环境变量（可选，命令行参数优先级更高）：
  ASR_BASE_URL   API base URL，默认 https://api.siliconflow.cn/v1
  ASR_API_KEY    API Key（必填）
  ASR_MODEL      模型名称，默认 TeleAI/TeleSpeechASR
"""

import argparse
import glob
import os
import sys
import time
from pathlib import Path
import requests


DEFAULT_BASE_URL = "https://api.siliconflow.cn/v1"
DEFAULT_MODEL = "TeleAI/TeleSpeechASR"
MAX_FILE_SIZE_MB = 50


def get_config(args) -> tuple[str, str, str]:
    base_url = args.base_url or os.environ.get("ASR_BASE_URL", DEFAULT_BASE_URL)
    api_url = base_url.rstrip("/") + "/audio/transcriptions"

    api_key = args.api_key or os.environ.get("ASR_API_KEY", "")
    if not api_key:
        print("错误：未提供 API Key", file=sys.stderr)
        print("请设置环境变量 ASR_API_KEY 或使用 --api-key 参数", file=sys.stderr)
        sys.exit(1)

    model = args.model or os.environ.get("ASR_MODEL", DEFAULT_MODEL)
    return api_url, api_key, model


def transcribe_file(file_path: Path, api_url: str, model: str, session: requests.Session) -> str:
    start_time = time.time()
    
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f)}
        data = {"model": model}
        response = session.post(api_url, files=files, data=data, timeout=300)

    if response.status_code == 401:
        print(f"\n错误：HTTP 401 (API Key 无效或未授权)", file=sys.stderr)
        sys.exit(1)
    if response.status_code != 200:
        print(f"\n错误：API 返回 {response.status_code}", file=sys.stderr)
        print(f"响应：{response.text}", file=sys.stderr)
        sys.exit(1)

    result = response.json()
    elapsed = time.time() - start_time
    print(f"  [完成] 耗时 {elapsed:.1f}s")
    return result.get("text", "")


def main():
    parser = argparse.ArgumentParser(description="语音转文字（OpenAI 兼容 ASR 接口）")
    parser.add_argument("--input", required=True, help="输入音频文件或 glob 模式（如 **/*.mp3）")
    parser.add_argument("--output", required=True, help="输出文本文件路径")
    parser.add_argument("--base-url", default="", help=f"API base URL（默认：{DEFAULT_BASE_URL}）")
    parser.add_argument("--api-key", default="", help="API Key (注意：生产环境推荐使用环境变量 ASR_API_KEY 防泄露)")
    parser.add_argument("--model", default="", help=f"ASR 模型（默认：{DEFAULT_MODEL}）")
    parser.add_argument("--merge", action="store_true", help="多文件时按文件名顺序合并输出")
    args = parser.parse_args()

    api_url, api_key, model = get_config(args)

    input_paths = [Path(p) for p in sorted(glob.glob(args.input, recursive=True))]
    if not input_paths:
        print(f"错误：未找到匹配文件：{args.input}", file=sys.stderr)
        sys.exit(1)

    # 预检所有文件大小，避免中途崩溃
    for p in input_paths:
        size_mb = p.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            print(f"错误：文件 {p.name} 大小为 {size_mb:.1f}MB，超过 {MAX_FILE_SIZE_MB}MB 限制", file=sys.stderr)
            print("请先使用 ffmpeg 分割文件：", file=sys.stderr)
            print(f"  ffmpeg -i {p.name} -f segment -segment_time 1500 -c copy segment_%03d.mp3", file=sys.stderr)
            sys.exit(1)

    print(f"找到 {len(input_paths)} 个文件，使用模型：{model}")

    all_texts = []
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})

    try:
        for i, f in enumerate(input_paths, 1):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"[{i}/{len(input_paths)}] 正在转写：{f.name} ({size_mb:.1f}MB)...", end="", flush=True)
            text = transcribe_file(f, api_url, model, session)
            all_texts.append(text)
    except KeyboardInterrupt:
        print("\n用户中断转写！", file=sys.stderr)
        if not all_texts:
            sys.exit(1)
        print("尝试保存已完成的部分进度...", file=sys.stderr)

    out_path = Path(args.output)
    if args.merge or len(input_paths) == 1:
        final_text = "\n".join(all_texts)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(final_text, encoding="utf-8")
        print(f"\n完成！输出已写入：{out_path}")
        print(f"总字数：{len(final_text)} 字符")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        for i, (f, text) in enumerate(zip(input_paths[:len(all_texts)], all_texts)):
            part_path = out_path.with_name(f"{out_path.stem}_part{i+1:03d}{out_path.suffix}")
            part_path.write_text(text, encoding="utf-8")
            print(f"  写入：{part_path}")
        print(f"\n完成！共输出 {len(all_texts)} 个文件")


if __name__ == "__main__":
    main()
