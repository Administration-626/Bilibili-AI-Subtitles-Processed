#!/bin/bash
# scripts/process_batch_2.sh — 小饭音频批量转写(兼容 Shim)
# 已迁移至通用 scripts/audio_to_text.sh,此为兼容入口。
# 用法:
#   scripts/process_batch_2.sh                          # 处理默认文件列表
#   scripts/process_batch_2.sh raw/xiaofan/*.mp4        # 处理指定文件

set -euo pipefail
cd "$(dirname "$0")/.."

INPUT_DIR="${INPUT_DIR:-raw/xiaofan}"

DEFAULT_FILES=(
  "$INPUT_DIR/小饭中年事件簿--2025.08.13--一辈子在工作_P1_小饭中年事件簿--2025.08.13--_音频.mp4"
  "$INPUT_DIR/小饭中年事件簿--2025.08.13--一辈子在工作_P2_社保_音频.mp4"
)

has_files=false
for arg in "$@"; do
  [[ "$arg" != -* ]] && has_files=true && break
done

if [[ "$has_files" == false ]]; then
  exec scripts/audio_to_text.sh --segment-time 1800 --reencode "$@" "${DEFAULT_FILES[@]}"
else
  exec scripts/audio_to_text.sh --segment-time 1800 --reencode "$@"
fi