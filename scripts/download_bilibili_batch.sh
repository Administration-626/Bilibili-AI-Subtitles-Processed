#!/bin/bash

# Bilibili 批量音频下载与转录脚本
# 依赖：BBDown, python3 (带 asr_transcribe.py)

WORK_DIR="${WORK_DIR:-raw/xiaofan_clips}"
mkdir -p "$WORK_DIR"

# 检查 BBDown 是否安装
if [ ! -f "/tmp/bbdown/BBDown" ]; then
    echo "未检测到 BBDown，正在自动下载..."
    wget "https://github.com/nilaoda/BBDown/releases/download/1.6.3/BBDown_1.6.3_20240814_linux-x64.zip" -O /tmp/bbdown.zip
    unzip -o /tmp/bbdown.zip -d /tmp/bbdown
    chmod +x /tmp/bbdown/BBDown
fi

# 如果有命令行参数，则使用命令行参数，否则使用默认的 5 个 URL
if [ "$#" -gt 0 ]; then
    urls=("$@")
else
    urls=(
        "https://www.bilibili.com/video/BV1f98czFEA4"
        "https://www.bilibili.com/video/BV1NTunzrERT"
        "https://www.bilibili.com/video/BV1Jh81z9EJe"
        "https://www.bilibili.com/video/BV1aQg5zgEXR"
        "https://www.bilibili.com/video/BV1RznhzUECW"
    )
fi

echo "======================================"
echo "开始下载 Bilibili 音频切片..."
echo "======================================"

for url in "${urls[@]}"; do
    echo "Downloading $url..."
    /tmp/bbdown/BBDown "$url" --audio-only --work-dir "$WORK_DIR"
done

echo "======================================"
echo "下载完成。开始通过 SenseVoice 进行语音转文字..."
echo "======================================"

for file in "$WORK_DIR"/*.m4a; do
    if [ -f "$file" ]; then
        output="${file%.*}.txt"
        # 如果已经存在转写文件则跳过
        if [ ! -f "$output" ]; then
            echo "Transcribing $file -> $output"
            python3 scripts/asr_transcribe.py --input "$file" --output "$output"
        else
            echo "Skipping $file (already transcribed)"
        fi
    fi
done

echo "全部处理完毕！"
