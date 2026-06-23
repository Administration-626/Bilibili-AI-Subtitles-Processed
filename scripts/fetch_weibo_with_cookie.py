import urllib.request
import json
import os
import re
import time
import random

# 替换为你抓取到的 Cookie
YOUR_COOKIE = "SCF=ArVSGXPI3Wn3cQi3QISzA8pN_NA5MPQtDBezdKYvNnrLZuTxXVjheEK_rdkL1T0tAPX3HhYVRjrqYF76ZSv7C7E.; SUB=_2A25HPqmbDeRhGeFH61EU9yjMwzuIHXVkNaNTrDV6PUJbktAbLW_MkW1NeCd9WRRE3PE18AraG4lGw2g1CnP4MSvR; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WhE5_HUWy6QWnFJEGA7mw-C5NHD95QN1K50SKMcehnNWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0.7e0-NSo5RS7tt; SSOLoginState=1782241739; ALF=1784833739; WEIBOCN_FROM=1110006030; MLOGIN=1; _T_WM=83429517315; XSRF-TOKEN=377d42; M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D231583%26launchid%3D10000360-page_H5%26uicode%3D10000011%26fid%3D1076036231346896"

UID = "6231346896"
BASE_URL = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={UID}&containerid=107603{UID}"
OUTPUT_FILE = "/home/tan/Bilibili-AI-Subtitles-Processed/local_file/小饭-微博-自动抓取.md"

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def fetch_weibo_pages(cookie, max_pages=10):
    print(f"开始批量抓取小饭的历史微博（最多抓取 {max_pages} 页）...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Cookie': cookie,
        'Accept': 'application/json, text/plain, */*',
        'MWeibo-Pwa': '1',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'https://m.weibo.cn/u/{UID}'
    }
    
    all_posts = []
    since_id = None
    
    for page in range(1, max_pages + 1):
        url = BASE_URL
        if since_id:
            url += f"&since_id={since_id}"
            
        print(f"正在抓取第 {page} 页...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if data.get('ok') != 1:
                print("API 返回异常，抓取终止。")
                break
                
            cards = data['data']['cards']
            for card in cards:
                if card.get('card_type') == 9: # 9表示普通微博
                    mblog = card['mblog']
                    date = mblog.get('created_at', '未知时间')
                    text = clean_html(mblog.get('text', ''))
                    link = f"https://m.weibo.cn/detail/{mblog.get('id')}"
                    
                    all_posts.append({
                        'date': date,
                        'content': text,
                        'link': link
                    })
            
            # 获取下一页的 since_id
            since_id = data['data']['cardlistInfo'].get('since_id')
            if not since_id:
                print("没有更多数据了。")
                break
                
            # 加上随机延时防止被微博封禁 (1 到 5 秒)
            delay = random.uniform(1, 5)
            print(f"随机停顿 {delay:.2f} 秒...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"抓取失败: {e}")
            break
            
    return all_posts

def save_to_markdown(posts):
    if not posts:
        return
        
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    existing_content = ""
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing_content = f.read()
            
    new_count = 0
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        # 翻转顺序，从最老的微博开始往文件末尾追加
        for post in reversed(posts):
            if post['link'] not in existing_content:
                f.write(f"\n### {post['date']}\n")
                f.write(f"{post['content']}\n")
                f.write(f"[微博链接]({post['link']})\n")
                f.write("-" * 40 + "\n")
                new_count += 1
                
    print(f"抓取结束，共成功更新了 {new_count} 条历史微博到 {OUTPUT_FILE}！")

if __name__ == "__main__":
    posts = fetch_weibo_pages(YOUR_COOKIE, max_pages=999) # 设置抓取上限为 999 页（几乎等于抓取全部）
    save_to_markdown(posts)
