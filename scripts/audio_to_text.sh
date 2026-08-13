#!/bin/bash
# scripts/audio_to_text.sh — 音频文件批量转写文本(通用参数化版本)
#
# 用法:
#   scripts/audio_to_text.sh [选项] <文件1.mp4> [文件2.mp4 ...]
#   scripts/audio_to_text.sh --input-dir raw/xiaofan    # 处理目录下所有 *.mp4
#
# 选项:
#   --input-dir DIR     处理 DIR 下所有 *.mp4(默认: 无)
#   --output-dir DIR    输出目录(默认: 同输入文件目录)
#   --segment-time SEC  分段时长秒数(默认: 1800)
#   --reencode          重新编码音频为 mp3(默认: 不重编码,用 -c copy)
#   --skip-existing     跳过已存在的 _extracted.txt(默认: 重新转写)
#   --dry-run           只打印要执行的命令,不实际运行
#   --help              显示此帮助
#
# 环境变量:
#   ASR_API_KEY  硅基流动 API Key(必填)
#   ASR_MODEL    ASR 模型名(默认: TeleAI/TeleSpeechASR)
#
# 示例:
#   scripts/audio_to_text.sh raw/xiaofan/*.mp4
#   scripts/audio_to_text.sh --input-dir raw/xiaofan --segment-time 1500 --skip-existing

set -euo pipefail

# ── 默认值 ──────────────────────────────────────────────────────────────────
FFMPEG_BIN="${FFMPEG_BIN:-ffmpeg}"
SEGMENT_TIME=1800
REENCODE=false
SKIP_EXISTING=false
DRY_RUN=false
INPUT_DIR=""
OUTPUT_DIR=""
FILES=()

# ── 帮助 ────────────────────────────────────────────────────────────────────
show_help() {
  sed -n '/^# scripts\/audio_to_text.sh/,/^$/p' "$0" | sed 's/^# //; s/^#$//'
  exit 0
}

# ── 参数解析 ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --input-dir)    INPUT_DIR="$2"; shift 2 ;;
    --output-dir)   OUTPUT_DIR="$2"; shift 2 ;;
    --segment-time) SEGMENT_TIME="$2"; shift 2 ;;
    --reencode)     REENCODE=true; shift ;;
    --skip-existing) SKIP_EXISTING=true; shift ;;
    --dry-run)      DRY_RUN=true; shift ;;
    --help)         show_help ;;
    -*)
      echo "❌ 未知选项: $1" >&2
      echo "   使用 --help 查看用法" >&2
      exit 1
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

# ── 文件列表收集 ─────────────────────────────────────────────────────────────
if [[ -n "$INPUT_DIR" ]]; then
  if [[ ! -d "$INPUT_DIR" ]]; then
    echo "❌ 目录不存在: $INPUT_DIR" >&2
    exit 1
  fi
  # 收集 mp4/m4a 文件
  shopt -s nullglob
  for f in "$INPUT_DIR"/*.mp4 "$INPUT_DIR"/*.m4a; do
    [[ -f "$f" ]] && FILES+=("$f")
  done
  shopt -u nullglob
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "❌ 未指定输入文件。使用 --help 查看用法。" >&2
  exit 1
fi

# ── 核心处理函数 ─────────────────────────────────────────────────────────────
process_file() {
  local file="$1"
  local dir outdir base outfile

  dir=$(dirname "$file")
  outdir="${OUTPUT_DIR:-$dir}"
  base=$(basename "$file" .mp4)
  base=$(basename "$base" .m4a)
  outfile="${outdir}/${base}_extracted.txt"

  if [[ "$SKIP_EXISTING" == true && -f "$outfile" ]]; then
    echo "  ⏭️ 跳过(已存在): $outfile"
    return 0
  fi

  echo "  🔧 处理: $(basename "$file")"

  # 分段
  if [[ "$REENCODE" == true ]]; then
    # 重新编码为 mp3
    local seg_pattern="${outdir}/${base}_seg_%03d.mp3"
    local cmd=("$FFMPEG_BIN" -y -i "$file" -vn -ar 16000 -ac 1 -b:a 64k \
      -f segment -segment_time "$SEGMENT_TIME" -c:a libmp3lame \
      "$seg_pattern")
    echo "  📦 分段(重编码 mp3, ${SEGMENT_TIME}s): ${base}"
  else
    # 不重新编码,直接复制音轨
    local seg_pattern="${outdir}/${base}_seg_%03d.m4a"
    local cmd=("$FFMPEG_BIN" -y -i "$file" -vn -acodec copy \
      -f segment -segment_time "$SEGMENT_TIME" \
      "$seg_pattern")
    echo "  📦 分段(直接复制, ${SEGMENT_TIME}s): ${base}"
  fi

  if [[ "$DRY_RUN" == true ]]; then
    echo "    [DRY RUN] ${cmd[*]}"
  else
    "${cmd[@]}" -loglevel warning < /dev/null
  fi

  # ASR 转写
  local seg_glob
  if [[ "$REENCODE" == true ]]; then
    seg_glob="${outdir}/${base}_seg_*.mp3"
  else
    seg_glob="${outdir}/${base}_seg_*.m4a"
  fi

  echo "  🎙️  ASR 转写: ${base}"
  if [[ "$DRY_RUN" == true ]]; then
    echo "    [DRY RUN] python3 scripts/asr_transcribe.py --input \"$seg_glob\" --output \"$outfile\" --merge"
  else
    python3 scripts/asr_transcribe.py --input "$seg_glob" --output "$outfile" --merge
  fi

  # 清理分段
  if [[ "$DRY_RUN" == true ]]; then
    echo "    [DRY RUN] rm -f ${seg_glob}"
  else
    rm -f "$seg_glob"
  fi

  echo "  ✅ 完成: $outfile"
}

# ── 主循环 ───────────────────────────────────────────────────────────────────
echo "📂 共 ${#FILES[@]} 个文件"
for f in "${FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "  ⚠️ 文件不存在,跳过: $f"
    continue
  fi
  process_file "$f"
done
echo "🎉 全部处理完毕!"