import os
import sys
import sqlite3
from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto("https://www.instagram.com/direct/t/17887646322533789/", timeout=45000, wait_until="networkidle")
    
    # Check all messages text inside main chat pane
    messages = page.evaluate("""
        () => {
            const divs = Array.from(document.querySelectorAll("div[role='row'], div[role='listitem'], div[role='button']"));
            return divs.map(d => d.innerText.replace(/\\n/g, ' ')).filter(t => t.length > 0);
        }
    """)
    print("Messages count:", len(messages))
    for m in messages[:25]:
        print("MSG:", m[:80])

    browser.close()
