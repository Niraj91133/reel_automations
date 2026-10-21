import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
COOKIE_FILE = "cookies.txt"
CHAT_THREAD_URL = "https://www.instagram.com/direct/t/101996904536119/"

def parse_cookie_file(cookie_file):
    cookies = []
    with open(cookie_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                cookies.append({
                    'domain': parts[0],
                    'path': parts[2],
                    'secure': parts[3].lower() == 'true',
                    'expires': int(parts[4]) if parts[4].isdigit() else -1,
                    'name': parts[5],
                    'value': parts[6]
                })
    return cookies

def inspect_chat_dom():
    cookies = parse_cookie_file(COOKIE_FILE)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        context.add_cookies(cookies)
        page = context.new_page()
        
        print("Loading chat thread...")
        page.goto(CHAT_THREAD_URL, timeout=45000, wait_until="networkidle")
        time.sleep(5)
        
        # Take screenshot of the chat to verify visual state
        page.screenshot(path="chat_preview.png")
        print("Saved chat_preview.png screenshot!")

        # Print all anchors and their hrefs / data attributes
        data = page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a')).map(a => ({
                    href: a.href,
                    text: a.innerText,
                    role: a.getAttribute('role')
                }));
                const images = Array.from(document.querySelectorAll('img')).map(img => img.src).slice(0, 10);
                return { links, images };
            }
        """)
        
        print("Total links found on page:", len(data["links"]))
        for l in data["links"]:
            if "instagram.com" in l["href"] and not l["href"].endswith("/direct/inbox/"):
                print("Link:", l["href"], "| Text:", l["text"][:30])

        browser.close()

if __name__ == '__main__':
    inspect_chat_dom()
