import os
import sys
import time
import re
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

def inspect_reel_cards():
    cookies = parse_cookie_file(COOKIE_FILE)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900}
        )
        context.add_cookies(cookies)
        page = context.new_page()
        page.goto(CHAT_THREAD_URL, timeout=45000, wait_until="networkidle")
        time.sleep(4)

        # Inspect cards
        cards_info = page.evaluate("""
            () => {
                const results = [];
                const cards = document.querySelectorAll("div[role='button']");
                cards.forEach((card, idx) => {
                    const text = card.innerText || '';
                    const innerHTML = card.innerHTML;
                    // Check if it has creator handles or 'Watch again' or video thumbnail
                    const hasReelHint = text.includes('Reel') || text.includes('Watch') || innerHTML.includes('video') || innerHTML.includes('instagram.com/p/') || innerHTML.includes('instagram.com/reel/');
                    
                    // Extract all hrefs inside this card
                    const hrefs = Array.from(card.querySelectorAll('a')).map(a => a.href);
                    
                    results.push({
                        idx,
                        text: text.slice(0, 100),
                        hrefs,
                        hasReelHint
                    });
                });
                return results;
            }
        """)

        print(f"Total interactive cards examined: {len(cards_info)}")
        for c in cards_info:
            if c["hrefs"] or c["hasReelHint"]:
                print(f"Card {c['idx']}: Text: {c['text'][:40]} | Links: {c['hrefs']}")

        browser.close()

if __name__ == '__main__':
    inspect_reel_cards()
