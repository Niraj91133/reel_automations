import requests
import json
import re

def get_instagram_reel(reel_url):
    # Free public high-speed resolver
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    api_url = f"https://api.cobalt.tools"
    # Testing Cobalt / public endpoint
    try:
        r = requests.post(
            "https://api.cobalt.tools/",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json={"url": reel_url},
            timeout=10
        )
        print("Cobalt status:", r.status_code, r.text[:200])
    except Exception as e:
        print("Cobalt error:", e)

get_instagram_reel("https://www.instagram.com/reel/DEvL721vd0b/")
