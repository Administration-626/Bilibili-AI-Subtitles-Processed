#!/usr/bin/env python3
"""
字幕文件文本提取工具（Linux 版）
支持 .json / .srt / .txt
特性：去除滑动窗口重复行 + 按时间间隔/标点分段

用法：
  python extract_subtitles.py video.json              # → video_extracted.txt
  python extract_subtitles.py video.json --timestamp  # → video_timestamped.txt
  python extract_subtitles.py video.json -o out.txt
  python extract_subtitles.py                         # 批量处理当前目录
  python extract_subtitles.py --dir /path/to/dir
  python extract_subtitles.py video.json --force
  python extract_subtitles.py video.json --gap 3.0    # 调整分段时间间隔（秒）
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional


# ── 可调参数 ──────────────────────────────────────────────────────────────────

DEDUP_THRESHOLD = 0.8   # 相似度 ≥ 此值视为重复，保留后者（更新的 ASR 结果）
DEFAULT_GAP     = 2.0   # 时间间隔 > 此值（秒）时换段
PUNCT_ENDS      = set("。！？…")  # 标点分段用的句末标点


# ── 数据结构 ──────────────────────────────────────────────────────────────────

@dataclass
class Segment:
    text: str
    from_sec: Optional[float] = None
    to_sec:   Optional[float] = None


# ── 时间格式化 ────────────────────────────────────────────────────────────────

def fmt_time(sec: float) -> str:
    if sec is None:
        return "00:00"
    s = int(sec)
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def fmt_range(seg: Segment) -> str:
    if seg.to_sec is not None:
        return f"[{fmt_time(seg.from_sec)} --> {fmt_time(seg.to_sec)}]"
    return f"[{fmt_time(seg.from_sec)}]"


# ── 解析 ──────────────────────────────────────────────────────────────────────

TEXT_FIELDS = ("content", "text", "sentence", "value", "caption", "subtitle")
ARRAY_KEYS  = ("data", "body", "results", "segments", "captions")


def first_text(item: dict) -> Optional[str]:
    for f in TEXT_FIELDS:
        v = item.get(f, "")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def find_segments(node) -> Optional[list]:
    """递归搜索 B 站各种变体 JSON 中真正包含字幕内容的列表"""
    if isinstance(node, list):
        if node and isinstance(node[0], dict) and first_text(node[0]):
            return node
        for item in node:
            res = find_segments(item)
            if res: return res
    elif isinstance(node, dict):
        for v in node.values():
            res = find_segments(v)
            if res: return res
    return None

def parse_json(path: Path) -> list[Segment]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="gbk")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(f"  警告：JSON 解析失败，回退纯文本：{path.name}")
        return [Segment(l.strip()) for l in raw.splitlines() if l.strip()]

    items = data if isinstance(data, list) else find_segments(data)
    if items is None:
        items = [data]

    segs = []
    for item in items:
        if isinstance(item, str):
            if item.strip():
                segs.append(Segment(item.strip()))
        elif isinstance(item, dict):
            text = first_text(item)
            if text:
                segs.append(Segment(
                    text=text,
                    from_sec=float(item["from"]) if "from" in item else None,
                    to_sec=float(item["to"])   if "to"   in item else None,
                ))
    return segs


def parse_srt(path: Path) -> list[Segment]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="gbk")
    segs = []
    for block in re.split(r"\n{2,}", raw.strip()):
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        time_line = next((l for l in lines if "-->" in l), None)
        if not time_line:
            continue
        # 解析时间 HH:MM:SS,mmm --> HH:MM:SS,mmm
        m = re.match(
            r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)",
            time_line.strip()
        )
        from_sec = to_sec = None
        if m:
            h1,m1,s1,_,h2,m2,s2,_ = (int(x) for x in m.groups())
            from_sec = h1*3600 + m1*60 + s1
            to_sec   = h2*3600 + m2*60 + s2
        texts = [l for l in lines if not re.match(r"^\d+$", l) and "-->" not in l]
        if texts:
            segs.append(Segment(
                text=" ".join(texts),
                from_sec=from_sec,
                to_sec=to_sec,
            ))
    return segs


def parse_txt(path: Path) -> list[Segment]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="gbk")
    return [
        Segment(l.strip()) for l in raw.splitlines()
        if l.strip() and not re.match(r"^\d+$", l.strip())
    ]


def parse(path: Path) -> list[Segment]:
    ext = path.suffix.lower()
    if ext == ".json": return parse_json(path)
    if ext == ".srt":  return parse_srt(path)
    
    # 对 .txt 等进行内容嗅探，防止把真正的 SRT 文件当成纯文本误杀
    try:
        head = path.read_text(encoding="utf-8")[:1000]
    except UnicodeDecodeError:
        head = path.read_text(encoding="gbk")[:1000]
        
    if re.search(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,.]\d{3}", head):
        return parse_srt(path)
        
    return parse_txt(path)


# ── 去重 ──────────────────────────────────────────────────────────────────────

def sim(a: str, b: str) -> float:
    """两个字符串的相似度（0~1）。"""
    if not a or not b:
        return 0.0
    ratio = SequenceMatcher(None, a, b).ratio()
    # 如果是相互包含的关系且长度差异不大（避免短串覆盖长句），可视为重复
    if (a in b or b in a) and min(len(a), len(b)) / max(len(a), len(b)) > 0.5:
        return max(ratio, 0.9)
    return ratio


def dedup(segs: list[Segment]) -> list[Segment]:
    """
    去除连续近似重复行（B站滑动窗口产物）。
    相似度 >= DEDUP_THRESHOLD 时，用后者替换前者（ASR 持续修正，后者更准）。
    """
    result: list[Segment] = []
    for seg in segs:
        if result and sim(result[-1].text, seg.text) >= DEDUP_THRESHOLD:
            result[-1] = seg   # 用更新版本替换
        else:
            result.append(seg)
    return result


# ── 分段 ──────────────────────────────────────────────────────────────────────

def group_by_gap(segs: list[Segment], gap: float) -> list[list[Segment]]:
    """按时间间隔分段。"""
    if not segs:
        return []
    groups, cur = [], [segs[0]]
    for seg in segs[1:]:
        prev = cur[-1]
        if (prev.to_sec is not None and seg.from_sec is not None
                and seg.from_sec - prev.to_sec > gap):
            groups.append(cur)
            cur = [seg]
        else:
            cur.append(seg)
    groups.append(cur)
    return groups


def group_by_punct(segs: list[Segment]) -> list[list[Segment]]:
    """按句末标点分段（无时间戳时的兜底方案）。"""
    if not segs:
        return []
    groups, cur = [], []
    for seg in segs:
        cur.append(seg)
        if seg.text and seg.text[-1] in PUNCT_ENDS:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def segment(segs: list[Segment], gap: float) -> list[list[Segment]]:
    has_time = any(s.from_sec is not None for s in segs)
    if has_time:
        return group_by_gap(segs, gap)
    return group_by_punct(segs)


# ── 输出格式化 ────────────────────────────────────────────────────────────────

def render(groups: list[list[Segment]], keep_timestamp: bool) -> str:
    parts = []
    for group in groups:
        first_time_seg = next((s for s in group if s.from_sec is not None), None)
        if keep_timestamp and first_time_seg is not None:
            # 每行保留时间戳
            lines = [f"{fmt_range(s)} {s.text}" for s in group]
            parts.append("\n".join(lines))
        else:
            # 合并成一段（中文不加空格）
            parts.append("".join(s.text for s in group))
    return "\n\n".join(parts) + "\n"


# ── 主逻辑 ────────────────────────────────────────────────────────────────────

def output_path(src: Path, keep_timestamp: bool) -> Path:
    suffix = "_timestamped.txt" if keep_timestamp else "_extracted.txt"
    return Path.cwd() / (src.stem + suffix)


def process(src: Path, dst: Path, keep_timestamp: bool, force: bool, gap: float):
    if not src.exists():
        print(f"  错误：文件不存在：{src}", file=sys.stderr)
        sys.exit(1)
    if dst.exists() and not force:
        print(f"  跳过：{dst.name} 已存在（--force 可覆盖）")
        return

    segs   = parse(src)
    if not segs:
        print(f"  警告：提取内容为空，跳过文件：{src.name}")
        return
        
    segs   = dedup(segs)
    groups = segment(segs, gap)
    text   = render(groups, keep_timestamp)

    dst.write_text(text, encoding="utf-8")
    print(f"  完成：{src.name} → {dst.name}  ({len(segs)} 句 / {len(groups)} 段)")


def main():
    parser = argparse.ArgumentParser(description="字幕文件文本提取工具")
    parser.add_argument("input", nargs="?",    help="输入文件（.json/.srt/.txt）")
    parser.add_argument("-o", "--output",      help="指定输出路径")
    parser.add_argument("--dir",  default=".", help="批量处理目录（无 input 时生效）")
    parser.add_argument("--timestamp", action="store_true", help="保留时间戳")
    parser.add_argument("--force",     action="store_true", help="覆盖已存在文件")
    parser.add_argument("--gap", type=float, default=DEFAULT_GAP,
                        help=f"分段时间间隔（秒，默认 {DEFAULT_GAP}）")
    args = parser.parse_args()

    if args.input:
        src = Path(args.input)
        dst = Path(args.output) if args.output else output_path(src, args.timestamp)
        process(src, dst, args.timestamp, args.force, args.gap)
    else:
        directory = Path(args.dir)
        if not directory.is_dir():
            print(f"错误：目录不存在：{directory}", file=sys.stderr)
            sys.exit(1)
        files = sorted(
            f for f in directory.iterdir()
            if f.is_file()
            and f.suffix.lower() in (".json", ".srt", ".txt")
            and not f.stem.endswith(("_extracted", "_timestamped"))
        )
        if not files:
            print("未找到可处理的字幕文件（.json/.srt/.txt）")
            sys.exit(0)
        print(f"找到 {len(files)} 个文件，开始处理...")
        for f in files:
            process(f, output_path(f, args.timestamp), args.timestamp, args.force, args.gap)
        print("批量处理完成！")


if __name__ == "__main__":
    main()
