#!/bin/bash
FILES=(
  "raw/xiaofan/小饭中年事件簿--2025.08.13--一辈子在工作_P1_小饭中年事件簿--2025.08.13--_音频.mp4"
  "raw/xiaofan/小饭中年事件簿--2025.08.13--一辈子在工作_P2_社保_音频.mp4"
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
