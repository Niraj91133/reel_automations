from playwright.sync_api import sync_playwright
import re
import time
from dm_scraper import parse_cookie_file, COOKIE_FILE

cookies = parse_cookie_file(COOKIE_FILE)

def test_extract(thread_url, name):
    print(f"\n==========================================")
    print(f"Testing real extraction for {name}: {thread_url}")
    print(f"==========================================")
    reels = []
    seen = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        page.goto(thread_url, timeout=45000, wait_until="networkidle")
        time.sleep(3)
        
        # Scroll up first to load history
        print("Scrolling history upwards...")
        for _ in range(6):
            page.mouse.move(600, 400)
            page.mouse.wheel(0, -3000)
            time.sleep(0.4)
            
        # Now scroll downwards step by step and click any reel card
        print("Scanning cards downwards...")
        for s in range(10):
            # Find all clickable cards in right pane (x > 350)
            cards = page.query_selector_all("div[role='button']")
            for card in cards:
                try:
                    box = card.bounding_box()
                    if not box or box['x'] < 350 or box['width'] < 100 or box['height'] < 150:
                        continue
                    
                    card_text = card.inner_text().strip().replace('\n', ' ')
                    # Avoid message controls
                    if any(skip in card_text for skip in ['Message...', 'Search', 'Send message', 'Active']):
                        continue
                    
                    # Creator handle is usually the text of the card
                    creator = card_text.split()[0] if card_text else "creator"
                    
                    # Click the card directly
                    card.click(timeout=2000)
                    time.sleep(1.5)
                    
                    cur_url = page.url
                    m = re.search(r"/(?:reel|p)/([^/?]+)", cur_url)
                    if m:
                        code = m.group(1)
                        if code not in seen:
                            seen.add(code)
                            reels.append({
                                "shortcode": code,
                                "url": f"https://www.instagram.com/reel/{code}/",
                                "creator": creator
                            })
                            print(f"  [Found {len(reels)}] https://www.instagram.com/reel/{code}/ (By @{creator})")
                        
                        # Close modal
                        close_btn = page.query_selector("svg[aria-label='Close']")
                        if close_btn:
                            close_btn.click()
                            time.sleep(0.4)
                        else:
                            page.keyboard.press("Escape")
                            time.sleep(0.3)
                    else:
                        page.keyboard.press("Escape")
                        time.sleep(0.2)
                except Exception as e:
                    pass
            
            page.mouse.move(600, 400)
            page.mouse.wheel(0, 1500)
            time.sleep(0.5)
            
        browser.close()
        
    print(f"Total extracted for {name}: {len(reels)}")
    return reels

test_extract("https://www.instagram.com/direct/t/101996904536119/", "im_raaaj_ (Startup)")
test_extract("https://www.instagram.com/direct/t/17887646322533789/", "baatleaderki (Politics)")
