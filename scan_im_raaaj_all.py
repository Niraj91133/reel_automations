import json
from playwright.sync_api import sync_playwright
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    all_reels_captured = {}

    def on_response(response):
        if "graphql" in response.url or "direct_v2" in response.url or "items" in response.url:
            try:
                data = response.json()
                def search_clips(obj):
                    if isinstance(obj, dict):
                        # Reel or media signature
                        code = obj.get("code")
                        if code and 9 <= len(code) <= 13:
                            u = obj.get("user") or {}
                            creator = u.get("username") or "creator"
                            if code not in all_reels_captured:
                                all_reels_captured[code] = creator
                                print(f"CAPTURED REEL: https://www.instagram.com/reel/{code}/ (by @{creator})")
                        for k, v in obj.items():
                            search_clips(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            search_clips(item)
                search_clips(data)
            except:
                pass

    page.on("response", on_response)
    page.goto('https://www.instagram.com/direct/t/101996904536119/', timeout=45000, wait_until='networkidle')
    page.wait_for_timeout(3000)

    # Scroll up 15 times to paginate Instagram thread
    for i in range(15):
        page.mouse.wheel(0, -6000)
        page.keyboard.press("PageUp")
        page.wait_for_timeout(1000)

    print(f"\n==========================================")
    print(f"TOTAL REELS IN CHAT NETWORK PAYLOAD: {len(all_reels_captured)}")
    for code, cr in all_reels_captured.items():
        print(f"  • {code} (@{cr})")
    print(f"==========================================")

    page.screenshot(path='current_im_raaaj_full.png')
    browser.close()
