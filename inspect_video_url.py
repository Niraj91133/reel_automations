import re
import requests
from playwright.sync_api import sync_playwright

def inspect_page_source():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page.goto("https://www.instagram.com/reel/DdOg8G7zGfE/", wait_until="domcontentloaded")
        content = page.content()
        browser.close()

    # Search for video_url in JSON script tags
    matches = re.findall(r'"video_url"\s*:\s*"([^"]+)"', content)
    print("Found video_url matches:", len(matches))
    for m in matches[:3]:
        clean_url = m.replace(r"\u0026", "&")
        print("URL:", clean_url[:120])
        # Try downloading 1 chunk
        r = requests.get(clean_url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        print("Status:", r.status_code, "Content-Length:", r.headers.get("Content-Length"))

inspect_page_source()
