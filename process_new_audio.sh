#!/bin/bash
set -e

cd /home/tan/Bilibili-AI-Subtitles-Processed

FILES=(
  "raw/xiaofan/【散修宗秘传】三年前饭总送给散修宗弟子的圣诞礼物_音频.mp4"
  "raw/xiaofan/【散修宗秘传】弱关系 云工作 强感知_音频.mp4"
  "raw/xiaofan/【股神来了】第二话 老蒋A股凯旋 对赌饭总 化身银魔！_音频.mp4"
  "raw/xiaofan/【股神来了】第三话 葱姜饭再聚首 饭总与老蒋对赌实盘！_音频.mp4"
  "raw/xiaofan/【股神来了】第四话 叽里呱啦说什么呢，本质赌徒！_音频.mp4"
  "raw/xiaofan/【股神来了】第五话 天才老蒋假装清醒！_音频.mp4"
  "raw/xiaofan/【葱姜饭后传】生日篇 老蒋&饭总&徐冲浪 时隔三年的葱姜饭_音频.mp4"
  "raw/xiaofan/【酱拌饭】宗主饭拷打蒋副宗主_音频.mp4"
)

export ASR_MODEL="FunAudioLLM/SenseVoiceSmall"

for FILE in "${FILES[@]}"; do
  if [ ! -f "$FILE" ]; then
    echo "File not found: $FILE"
    continue
  fi

  BASENAME=$(basename "$FILE" .mp4)
  OUTFILE="raw/xiaofan/${BASENAME}_extracted.txt"
  
  if [ -f "$OUTFILE" ]; then
    echo "Skip: $OUTFILE already exists."
    continue
  fi

  echo "Processing: $BASENAME"
  TMPDIR="raw/xiaofan/tmp_${BASENAME}"
  mkdir -p "$TMPDIR"
  
  echo "Splitting audio..."
  ./scripts/ffmpeg -y -i "$FILE" -f segment -segment_time 1500 -c copy "${TMPDIR}/segment_%03d.mp4" -loglevel warning
  
  echo "Running ASR..."
  python scripts/asr_transcribe.py --input "${TMPDIR}/segment_*.mp4" --output "$OUTFILE" --merge
  
  echo "Cleaning up..."
  rm -rf "$TMPDIR"
  echo "Done: $OUTFILE"
done
