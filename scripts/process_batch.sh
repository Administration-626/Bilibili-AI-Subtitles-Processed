#!/bin/bash
# scripts/process_batch.sh — 小饭音频批量转写(兼容 Shim)
# 已迁移至通用 scripts/audio_to_text.sh,此为兼容入口。
# 用法: 
#   scripts/process_batch.sh                          # 处理默认文件列表
#   scripts/process_batch.sh raw/xiaofan/*.mp4        # 处理指定文件
#   scripts/process_batch.sh --dry-run                # 预览默认文件列表

set -euo pipefail
cd "$(dirname "$0")/.."

INPUT_DIR="${INPUT_DIR:-raw/xiaofan}"

DEFAULT_FILES=(
  "$INPUT_DIR/【小饭聊二次元】小饭的网文往事_音频.mp4"
  "$INPUT_DIR/【小饭聊二次元】小饭聊巅峰之智游戏_音频.mp4"
  "$INPUT_DIR/【小饭聊二次元】聊聊自己写过的网文_音频.mp4"
  "$INPUT_DIR/【小饭聊二次元】闲聊网文、废案、地狱乐_音频.mp4"
)

# 检查参数中是否有文件(非选项参数)
has_files=false
for arg in "$@"; do
  [[ "$arg" != -* ]] && has_files=true && break
done

if [[ "$has_files" == false ]]; then
  exec scripts/audio_to_text.sh --segment-time 1800 --reencode "$@" "${DEFAULT_FILES[@]}"
else
  exec scripts/audio_to_text.sh --segment-time 1800 --reencode "$@"
fi