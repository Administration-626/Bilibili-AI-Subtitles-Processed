import urllib.request
import xml.etree.ElementTree as ET
import os
import re
from datetime import datetime

# 小饭的微博 UID
UID = os.environ.get("WEIBO_UID", "6231346896")
RSS_URL = f"https://rsshub.app/weibo/user/{UID}"
OUTPUT_FILE = os.environ.get("WEIBO_OUTPUT", "local_file/小饭-微博-自动抓取.md")

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def fetch_weibo():
    print(f"正在通过 RSSHub 获取小饭 (UID: {UID}) 的最新微博...")
    try:
        req = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        # 解析 RSS items
        posts = []
        for item in root.findall('./channel/item'):
            title = item.find('title').text
            description = item.find('description').text
            pub_date = item.find('pubDate').text
            link = item.find('link').text
            
            # 清理 HTML 标签
            text_content = clean_html(description)
            posts.append({
                'date': pub_date,
                'content': text_content,
                'link': link
            })
            
        return posts
    except Exception as e:
        print(f"抓取失败 (可能是网络或 RSSHub 节点限制): {e}")
        return []

def save_to_markdown(posts):
    if not posts:
        return
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # 读取已有的链接避免重复
    existing_content = ""
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing_content = f.read()
            
    new_count = 0
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        for post in reversed(posts): # 倒序，让旧的在前面
            if post['link'] not in existing_content:
                f.write(f"\n### {post['date']}\n")
                f.write(f"{post['content']}\n")
                f.write(f"[微博链接]({post['link']})\n")
                f.write("-" * 40 + "\n")
                new_count += 1
                
    print(f"成功更新了 {new_count} 条新微博到 {OUTPUT_FILE}！")

if __name__ == "__main__":
    posts = fetch_weibo()
    save_to_markdown(posts)
