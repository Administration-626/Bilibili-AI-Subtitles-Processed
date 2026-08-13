#!/usr/bin/env python3
"""
scripts/sync_distill_to_xiaofan.py — 蒸馏产物 → Xiaofan persona 模块转换

读 distill_cognitive_model.py 产出的结构化 JSON,按维度映射为 Xiaofan-Digital-Clone
的 persona/ 模块格式,直接写入目标仓库。

用法:
  python3 scripts/sync_distill_to_xiaofan.py [--input notes/distill_output.json] [--dry-run]

环境变量:
  XIAOFAN_REPO  (可选) 目标仓库路径,默认 /home/tan/Xiaofan-Digital-Clone
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── 路径 ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "notes" / "distill_output.json"
DEFAULT_XIAOFAN_REPO = Path("/home/tan/Xiaofan-Digital-Clone")
XIAOFAN_PERSONA_DIR = Path(os.environ.get("XIAOFAN_REPO") or str(DEFAULT_XIAOFAN_REPO)) / "persona"


# ── 维度 → 模块映射 ──────────────────────────────────────────────────────────
# 每个维度对应 Xiaofan 的 persona 模块编号和内容模板
DIMENSION_MAP = {
    "recurring_ideas": {
        "title": "蒸馏补充:高频核心观点 (Recurring Ideas)",
        "section_header": "## 蒸馏补充:高频核心观点",
        "target_module": "06_distilled_cognition.md",
    },
    "decision_rules": {
        "title": "蒸馏补充:行为与判断准则 (Decision Rules)",
        "section_header": "## 蒸馏补充:行为与判断准则",
        "target_module": "06_distilled_cognition.md",
    },
    "mental_models": {
        "title": "蒸馏补充:底层心智模型 (Mental Models)",
        "section_header": "## 蒸馏补充:底层心智模型",
        "target_module": "06_distilled_cognition.md",
    },
    "vocabulary": {
        "title": "蒸馏补充:专属词汇与话语标记 (Vocabulary)",
        "section_header": "## 蒸馏补充:专属词汇与话语标记",
        "target_module": "06_distilled_cognition.md",
    },
}

MODULE_HEADER = """\
# [MODULE: distilled_cognition]
# 小饭认知模型蒸馏补充 — 从音频/视频语料自动提取
# ⚠️ 本文件由 scripts/sync_distill_to_xiaofan.py 自动生成,请勿手动编辑
# 生成时间: {timestamp}
# 源蒸馏文件: {source}

"""


def load_distill(path: Path) -> dict:
    """加载蒸馏 JSON 并验证结构"""
    if not path.is_file():
        print(f"❌ 蒸馏 JSON 文件不存在: {path}", file=sys.stderr)
        print(f"   请先运行: python3 scripts/distill_cognitive_model.py", file=sys.stderr)
        sys.exit(1)
    data = json.loads(path.read_text(encoding="utf-8"))
    if "sources" not in data or not isinstance(data["sources"], list):
        print(f"❌ {path} 中缺少 sources 字段或格式错误", file=sys.stderr)
        sys.exit(1)
    return data


def build_module_content(data: dict) -> str:
    """将蒸馏 JSON 的所有维度组装为 persona 模块格式的 Markdown"""
    lines = []
    lines.append(MODULE_HEADER.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        source=str(DEFAULT_INPUT),
    ))

    # 遍历所有维度
    for dim_key, dim_cfg in DIMENSION_MAP.items():
        lines.append(f"{dim_cfg['section_header']}\n")
        lines.append(f"来源语料: {len(data['sources'])} 篇\n\n")

        for src in data["sources"]:
            content = src.get(dim_key, "").strip()
            if not content:
                continue
            # 这里不用原文中的 `_raw` 整体,而是用 parse_dimensions 提取的干净文本
            lines.append(f"### 来自: {src['filename']}\n")
            lines.append(f"*SHA256: `{src['sha256']}`*\n\n")
            lines.append(content + "\n\n")

        lines.append("---\n\n")

    return "".join(lines)


def write_module(content: str, target: Path, dry_run: bool) -> Path:
    """写入到 Xiaofan 仓库的 persona/ 目录"""
    target.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"🔍 [DRY RUN] 将写入: {target} ({len(content)} chars)")
        print("--- 预览前 20 行 ---")
        for line in content.splitlines()[:20]:
            print(f"  {line}")
        print("---")
    else:
        target.write_text(content, encoding="utf-8")
        print(f"✅ 已写入: {target} ({len(content)} chars)")
    return target


def notify_user(target: Path) -> None:
    """提示用户下一步操作"""
    print(f"\n📌 下一步:如需将蒸馏补充加入编译链,请编辑 Xiaofan-Digital-Clone 的")
    print(f"   scripts/pipeline.py,在 MODULE_ORDER 列表末尾追加 `\"06_distilled_cognition.md\"`")
    print(f"   然后运行: python3 scripts/pipeline.py prompt (重新编译 Prompt_System.md)")


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="蒸馏产物 → Xiaofan persona 模块",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
环境变量:
  XIAOFAN_REPO  目标 Xiaofan 仓库路径 (默认: /home/tan/Xiaofan-Digital-Clone)

使用流程:
  # 1. 先蒸馏
  export ASR_API_KEY='sk-...'
  python3 scripts/distill_cognitive_model.py --report

  # 2. 再转换同步
  python3 scripts/sync_distill_to_xiaofan.py --dry-run   # 预览
  python3 scripts/sync_distill_to_xiaofan.py              # 实际写入
        """
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                        help=f"蒸馏 JSON 输入路径 (默认: {DEFAULT_INPUT})")
    parser.add_argument("--dry-run", action="store_true",
                        help="预览写入内容,不实际写入文件")
    parser.add_argument("--target", type=Path, default=None,
                        help="目标文件路径(默认: <XIAOFAN_REPO>/persona/06_distilled_cognition.md)")

    args = parser.parse_args()

    xiaofan_persona = Path(os.environ.get("XIAOFAN_REPO") or str(DEFAULT_XIAOFAN_REPO)) / "persona"
    if not xiaofan_persona.is_dir():
        print(f"❌ Xiaofan 仓库 persona 目录不存在: {xiaofan_persona}", file=sys.stderr)
        print(f"   请确认环境变量 XIAOFAN_REPO 或确保 {DEFAULT_XIAOFAN_REPO} 存在", file=sys.stderr)
        sys.exit(1)

    data = load_distill(args.input)
    content = build_module_content(data)
    target = args.target or xiaofan_persona / "06_distilled_cognition.md"
    write_module(content, target, args.dry_run)

    if not args.dry_run:
        notify_user(target)


if __name__ == "__main__":
    main()