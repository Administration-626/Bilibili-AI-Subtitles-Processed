import os
import json
import asyncio
import aiohttp
from pathlib import Path
import hashlib

API_KEY = os.environ.get("ASR_API_KEY", "sk-qmdnuoekvfhstkajxxlnlmggbstxhyhbovwkmacvnhrgkkue")
BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"
MODEL = "Qwen/Qwen2.5-7B-Instruct"

PROMPT_TEMPLATE = """
你是一个执行「小饭认知模型」知识蒸馏的 Agent。
请仔细阅读以下视频/文章的文本转录稿，并提取出其中属于“小饭”这个人的核心认知模型。

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
"""

async def call_llm(session, content):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a strict epistemology-driven knowledge extraction engine."},
            {"role": "user", "content": PROMPT_TEMPLATE.replace("{content}", content[:15000])} # Limit length to fit context
        ],
        "temperature": 0.2
    }
    try:
        async with session.post(BASE_URL, headers=headers, json=payload, timeout=60) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

def get_file_metadata(filepath):
    stat = os.stat(filepath)
    with open(filepath, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    return stat.st_mtime, file_hash

async def main():
    transcripts_dir = Path("transcripts")
    
    # 选取几篇核心的小饭语料进行蒸馏
    target_files = [
        "京都风云录之黑金时代_extracted.txt",
        "凡人炒股传_extracted.txt",
        "女神异闻录_extracted.txt"
    ]
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for filename in target_files:
            filepath = transcripts_dir / filename
            if not filepath.exists():
                print(f"Skipping {filename}, not found.")
                continue
                
            print(f"Processing {filename}...")
            mtime, fhash = get_file_metadata(filepath)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 加行号
                numbered_lines = "".join([f"{i+1}: {line}" for i, line in enumerate(lines)])
                
            summary = await call_llm(session, numbered_lines)
            
            result_block = f"## 语料来源: {filename}\n"
            result_block += f"- **SHA256**: `{fhash}`\n\n"
            result_block += summary + "\n\n---\n"
            results.append(result_block)
            
    # 写出到统一的 v1.0 模型中
    output_path = Path("notes/xiaofan_cognitive_model_v1.0.md")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Xiaofan Cognitive Model (v1.0)\n\n")
        f.write("**Status:** Automated Batch Distillation (Phase 2)\n\n---\n\n")
        for res in results:
            f.write(res)
            
    print(f"Distillation complete! Model saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
