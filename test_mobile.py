from playwright.sync_api import sync_playwright
import re
import requests

def test_mobile_view():
    with sync_playwright() as p:
        # Emulate iPhone 14
        device = p.devices['iPhone 14']
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(**device)
        page = context.new_page()
        
        page.goto("https://www.instagram.com/reel/DdOg8G7zGfE/", wait_until="domcontentloaded")
        content = page.content()
        
        # Look for video src in dom
        videos = page.eval_on_selector_all("video", "elements => elements.map(e => e.src)")
        print("Videos found:", videos)
        
        # Look for og:video in meta tags
        og_video = page.eval_on_selector("meta[property='og:video']", "el => el ? el.content : null")
        print("og:video:", og_video)
        
        if og_video:
            r = requests.get(og_video, stream=True)
            print("Status:", r.status_code, "Size:", r.headers.get("Content-Length"))
            with open("test_reel.mp4", "wb") as f:
                for c in r.iter_content(chunk_size=1024*1024):
                    if c: f.write(c)
            print("Successfully saved via og:video!")
        
        browser.close()

test_mobile_view()
