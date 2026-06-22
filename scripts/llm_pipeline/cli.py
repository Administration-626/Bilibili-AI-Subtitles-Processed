import argparse
import sys
import os
import asyncio
import re

from .config import load_config
from .prompts import PROMPTS
from .chunker import get_tokenizer, chunk_text_by_tokens
from .telemetry import TokenTelemetry
from .merger import run_pipeline

MAX_INPUT_CHARS = 300000

def preprocess_transcript(text: str, keep_timestamps: bool = False) -> str:
    """ASR 前置清洗器"""
    if not keep_timestamps:
        # 支持 [HH:MM:SS] 与 [MM:SS] 格式
        text = re.sub(r'\[\d{2}:\d{2}(?::\d{2})?\]', '', text)
        text = re.sub(r'\d{2}:\d{2}:\d{2}(?:,\d{3})?(?:\s*-->\s*\d{2}:\d{2}:\d{2}(?:,\d{3})?)?', '', text)
    # 取消激进的连续字符压缩，防止误伤弹幕与笑声等有意义的表达
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def main():
    parser = argparse.ArgumentParser(description="字幕/文字稿大语言模型异步整理管线（V4 专业级架构）")
    parser.add_argument("--input", required=True, help="输入文件路径，传入 '-' 则从 stdin 读取")
    parser.add_argument("--output", required=True, help="输出 Markdown 文件路径")
    parser.add_argument("--mode", default="general",
                        choices=["general", "livestream", "detail", "tech"],
                        help="摘要模式")
    parser.add_argument("--base-url", default="", help="API base URL")
    parser.add_argument("--api-key", default="", help="API Key (注意：生产环境推荐使用环境变量 LLM_API_KEY 防泄露)")
    parser.add_argument("--model", default="", help="LLM 模型")
    
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max-tokens", type=int, default=4000)
    parser.add_argument("--chunk-size", type=int, default=6000, help="物理 Token 切分上限（默认 6000）")
    parser.add_argument("--workers", type=int, default=5, help="全局异步并发协程数（默认 5）")

    args = parser.parse_args()

    try:
        config = load_config(args)
        
        if args.input == "-":
            import io
            text = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8').read()
        else:
            if not os.path.exists(args.input):
                raise RuntimeError(f"输入文件不存在：{args.input}")
            with open(args.input, "r", encoding="utf-8") as f:
                text = f.read()
                
        if len(text) > MAX_INPUT_CHARS:
            raise RuntimeError(f"输入文本长度({len(text)})超过 {MAX_INPUT_CHARS} 的安全阈值，防止 API 账单失控。")
            
        # stdin ("-") 时，如果在 detail 模式就保留时间戳，否则不保留
        keep_timestamps = (args.input != "-" and "_timestamped" in args.input) or (args.mode == "detail")
        text = preprocess_transcript(text, keep_timestamps)
        
        # 1. 初始化核心总线
        telemetry = TokenTelemetry()
        tokenizer = get_tokenizer()
        
        print(f"🚀 V4 Agent Pipeline 启动 | 模式: {args.mode} | 并发引擎: aiohttp ({config.workers}协程)")
        
        # 2. 精确 Token 级语义切片
        chunks = chunk_text_by_tokens(text, config.chunk_size, tokenizer)
        print(f"📦 物理级 Token 分析完成，精准切分为 {len(chunks)} 大块")

        system_prompt = PROMPTS[args.mode]
        
        # 3. 引爆全异步事件循环
        result = asyncio.run(run_pipeline(text, chunks, system_prompt, config, telemetry))

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)

        print(f"\n✅ Pipeline 运行结束，最终文档已生成于：{args.output}")
        
        # 4. 生成结算财报
        telemetry.print_report()

    except Exception as e:
        print(f"\n❌ Pipeline 崩溃退出：{e}", file=sys.stderr)
        sys.exit(1)
