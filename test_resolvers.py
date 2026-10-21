import requests
import re
import json

def test_resolvers(reel_url):
    print("Testing resolvers for:", reel_url)
    
    # 1. Publer / SnapInsta style resolver
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Test v3 / fastdl
    try:
        r = requests.post("https://v3.fastdl.app/api/convert", json={"url": reel_url}, headers=headers, timeout=10)
        print("Fastdl status:", r.status_code)
        if r.status_code == 200:
            print("Fastdl response:", r.text[:200])
    except Exception as e:
        print("Fastdl error:", e)

    # Test Snapany / Saveig
    try:
        r = requests.get(f"https://api.vkrdown.com/instagram/?url={reel_url}", timeout=10)
        print("VKR status:", r.status_code)
        if r.status_code == 200:
            print("VKR response:", r.text[:200])
    except Exception as e:
        print("VKR error:", e)

test_resolvers("https://www.instagram.com/reel/DEvL721vd0b/")
