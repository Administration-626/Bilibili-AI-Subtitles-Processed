#!/bin/bash
# process_new_audio.sh — 小饭新音频批量转写(兼容 Shim)
# 已迁移至通用 scripts/audio_to_text.sh,此为兼容入口。
# 采用不重新编码方式(快速),默认跳过已存在的转写结果。
# 用法:
#   ./process_new_audio.sh                          # 处理默认文件列表
#   ./process_new_audio.sh raw/xiaofan/*.mp4        # 处理指定文件
#   ./process_new_audio.sh --dry-run                # 预览默认文件列表

set -euo pipefail
cd "$(dirname "$0")"

INPUT_DIR="${INPUT_DIR:-raw/xiaofan}"
export ASR_MODEL="${ASR_MODEL:-FunAudioLLM/SenseVoiceSmall}"
export FFMPEG_BIN="${FFMPEG_BIN:-./scripts/ffmpeg}"

DEFAULT_FILES=(
  "$INPUT_DIR/【散修宗秘传】三年前饭总送给散修宗弟子的圣诞礼物_音频.mp4"
  "$INPUT_DIR/【散修宗秘传】弱关系 云工作 强感知_音频.mp4"
  "$INPUT_DIR/【股神来了】第二话 老蒋A股凯旋 对赌饭总 化身银魔！_音频.mp4"
  "$INPUT_DIR/【股神来了】第三话 葱姜饭再聚首 饭总与老蒋对赌实盘！_音频.mp4"
  "$INPUT_DIR/【股神来了】第四话 叽里呱啦说什么呢，本质赌徒！_音频.mp4"
  "$INPUT_DIR/【股神来了】第五话 天才老蒋假装清醒！_音频.mp4"
  "$INPUT_DIR/【葱姜饭后传】生日篇 老蒋&饭总&徐冲浪 时隔三年的葱姜饭_音频.mp4"
  "$INPUT_DIR/【酱拌饭】宗主饭拷打蒋副宗主_音频.mp4"
)

has_files=false
for arg in "$@"; do
  [[ "$arg" != -* ]] && has_files=true && break
done

if [[ "$has_files" == false ]]; then
  exec scripts/audio_to_text.sh --segment-time 1500 --skip-existing "$@" "${DEFAULT_FILES[@]}"
else
  exec scripts/audio_to_text.sh --segment-time 1500 --skip-existing "$@"
fi