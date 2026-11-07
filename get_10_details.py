import requests
import re
import json
import time

shortcodes = [
    'DWzFpCsilRP', 'Da1uZcdzVdP', 'DUFzBIMksDy', 'DXo2O-SkhRu',
    'DZP97Uxycpf', 'DYwxmjYvPgu', 'DdjgKMQB12M', 'DfPW7VzSnhx',
    'DYuMCAZzJX6', 'DYpCgIEtiqc'
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

for i, code in enumerate(shortcodes, 1):
    url = f"https://www.instagram.com/reel/{code}/"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        html = resp.text
        title_m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        desc_m = re.search(r'<meta property="og:description" content="([^"]+)"', html)
        title = title_m.group(1) if title_m else 'No title'
        desc = desc_m.group(1) if desc_m else 'No description'
        print(f"#{i} | {url}")
        print(f"   Header: {title}")
        print(f"   Hook/Caption: {desc[:200]}...")
        print("----------------------------------------------------------------")
    except Exception as e:
        print(f"#{i} | {url} | Error: {e}")
