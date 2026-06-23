import yt_dlp
import os

cookie_path = '/tmp/bili_cookie.txt'
try:
    with open(cookie_path, 'r') as f:
        cookie_str = f.read().strip()
except Exception as e:
    print(f"Failed to read cookie: {e}")
    exit(1)

ydl_opts = {
    'format': 'm4a/bestaudio/best',
    'outtmpl': 'raw/xiaofan_new_clips/%(title)s.%(ext)s',
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': cookie_str,
        'Referer': 'https://www.bilibili.com'
    },
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }],
    'quiet': False
}

with open('raw/xiaofan_new_clips/urls.txt', 'r') as f:
    urls = [line.strip() for line in f if line.strip()]

print(f"Starting download of {len(urls)} videos with secure cookies...")

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(urls)
finally:
    # Shred and delete the cookie file immediately for security
    os.system('shred -u /tmp/bili_cookie.txt')
    print("Cookie file securely shredded and deleted.")
