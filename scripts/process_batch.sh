#!/bin/bash
FILES=(
  "raw/xiaofan/【小饭聊二次元】小饭的网文往事_音频.mp4"
  "raw/xiaofan/【小饭聊二次元】小饭聊巅峰之智游戏_音频.mp4"
  "raw/xiaofan/【小饭聊二次元】聊聊自己写过的网文_音频.mp4"
  "raw/xiaofan/【小饭聊二次元】闲聊网文、废案、地狱乐_音频.mp4"
)

for file in "${FILES[@]}"; do
  echo "==================================="
  echo "Processing $file..."
  base=$(basename "$file" .mp4)
  
  # Extract audio and segment into 30 min chunks
  echo "Extracting and segmenting audio..."
  ffmpeg -y -i "$file" -vn -ar 16000 -ac 1 -b:a 64k -f segment -segment_time 1800 -c:a libmp3lame "raw/xiaofan/${base}_seg_%03d.mp3" < /dev/null
  
  # Transcribe and merge
  echo "Transcribing segments for $base..."
  python3 scripts/asr_transcribe.py --input "raw/xiaofan/${base}_seg_*.mp3" --output "raw/xiaofan/${base}_extracted.txt" --merge
  
  # Cleanup segments
  rm "raw/xiaofan/${base}_seg_"*.mp3
done
echo "All files processed."
