#!/usr/bin/env python3
"""
test_persona.py — 小饭人格测试脚本

调用 Gemini 以小饭人格回答测试问题,验证人设是否偏移。

用法:
  python3 test_persona.py                                            # 默认问题
  python3 test_persona.py --question "你的问题"                       # 自定义问题
  python3 test_persona.py --test-file tests/test_cases.json           # 从基础 15 题选第 1 题
  python3 test_persona.py --test-file tests/test_cases.json --test-id 5  # 选第 5 题
  python3 test_persona.py --test-file tests/test_cases_extended.json --list  # 列出扩展集
  python3 test_persona.py --test-file tests/test_cases_extended.json --test-id 1  # 扩展集第 1 题
"""

import os
import sys
import json
import argparse
from pathlib import Path


# ── 参数 ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="小饭人格测试脚本")
parser.add_argument("--question", default="", help="测试问题(默认: 社保新规)")
parser.add_argument("--model", default="gemini-2.5-pro", help="Gemini 模型名(默认: gemini-2.5-pro)")
parser.add_argument("--test-file", type=Path, help="从测试用例 JSON 文件读取问题")
parser.add_argument("--test-id", type=int, default=None, help="选取指定 id 的测试题(搭配 --test-file)")
parser.add_argument("--list", action="store_true", help="列出测试文件中的用例(搭配 --test-file)")
args = parser.parse_args()


# ── 从测试文件加载问题 ────────────────────────────────────────────────────
def load_question_from_file():
    """从 --test-file 加载问题,支持 --test-id 和 --list"""
    if not args.test_file or not args.test_file.is_file():
        print(f"❌ 测试文件不存在: {args.test_file}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.test_file.read_text(encoding="utf-8"))

    # 平展为列表:可能是数组,也可能是带 cases 键的字典
    if isinstance(data, dict) and "cases" in data:
        cases = data["cases"]
    elif isinstance(data, list):
        cases = data
    else:
        print(f"❌ 无法解析测试文件格式: {args.test_file}", file=sys.stderr)
        sys.exit(1)

    # 过滤掉注释元素(含 _comment 键的元数据对象)
    real_cases = [c for c in cases if isinstance(c, dict) and "_comment" not in c]

    if not real_cases:
        print(f"⚠️ 测试文件中未找到有效测试用例: {args.test_file}", file=sys.stderr)
        sys.exit(1)

    # --list: 列出所有用例
    if args.list:
        print(f"📋 测试文件: {args.test_file} ({len(real_cases)} 题)\n")
        for c in real_cases:
            cid = c.get("id", "?")
            cat = c.get("category", "未分类")
            q = c.get("question", "")
            if len(q) > 50:
                q = q[:50] + "..."
            print(f"  #{cid:>3}  [{cat}] {q}")
        sys.exit(0)

    # 按 id 匹配
    if args.test_id is not None:
        matched = [c for c in real_cases if c.get("id") == args.test_id]
        if not matched:
            print(f"⚠️ 未找到 id={args.test_id} 的用例,可用 --list 查看所有", file=sys.stderr)
            sys.exit(1)
        return matched[0]["question"]

    # 默认取第 1 题
    return real_cases[0]["question"]


# ── Gemini 调用(懒加载 SDK) ──────────────────────────────────────────────
def call_gemini(question: str, model_name: str, system_prompt: str) -> None:
    """调用 Gemini API,支持新旧 SDK"""
    try:
        import google.genai as genai
        from google.genai import types
        client = genai.Client()
        response = client.models.generate_content(
            model=model_name,
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            )
        )
        print(response.text)
        return
    except ImportError:
        pass

    try:
        import google.generativeai as old_genai
        old_genai.configure()
        model = old_genai.GenerativeModel(
            model_name,
            system_instruction=system_prompt
        )
        response = model.generate_content(question)
        print(response.text)
        return
    except ImportError:
        pass

    print("❌ 未找到 Google Gemini SDK。请安装: pip install google-genai", file=sys.stderr)
    print("   或: pip install google-generativeai", file=sys.stderr)
    sys.exit(1)


# ── 主流程 ────────────────────────────────────────────────────────────────
def main():
    # 确定问题
    question = args.question

    if args.test_file:
        question = load_question_from_file()

    if not question:
        question = "【弹幕提问】：饭总，我看到有人说最近全面强制交社保的新规，其实有反内卷的意思。就是把那些付不起社保的、靠低成本人力的落后产能和小微企业淘汰掉，这样留下来的企业做出来的产品都能卖个好价钱，整体经济就会好起来。你觉得这么理解对吗？"

    # 加载系统 Prompt
    prompt_path = Path("Xiaofan_Knowledge_Distillation/Prompt_System.md")
    if not prompt_path.is_file():
        print(f"❌ 系统 Prompt 文件不存在: {prompt_path}", file=sys.stderr)
        print("   请确认仓库根目录下有 Xiaofan_Knowledge_Distillation/Prompt_System.md", file=sys.stderr)
        sys.exit(1)

    system_prompt = prompt_path.read_text(encoding="utf-8")

    # 执行测试
    print("QUESTION:", question)
    print("-" * 40)
    call_gemini(question, args.model, system_prompt)


if __name__ == "__main__":
    main()