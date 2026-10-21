import os
import sys
import time
import re
import yt_dlp

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

COOKIE_FILE = "cookies.txt"

def get_latest_reels_from_profile(username="uxwithraaj", max_count=10):
    """
    Fetches the latest reel links from the given profile using headless browser.
    """
    reels = []
    print(f"Checking latest reels for @{username}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        try:
            profile_url = f"https://www.instagram.com/{username}/reels/"
            page.goto(profile_url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(4)
            links = page.eval_on_selector_all("a[href*='/reel/']", "elements => elements.map(el => el.href)")
            
            seen = set()
            for l in links:
                m = re.search(r"/reel/([^/?]+)", l)
                if m:
                    shortcode = m.group(1)
                    if shortcode not in seen:
                        seen.add(shortcode)
                        reels.append({
                            "shortcode": shortcode,
                            "url": f"https://www.instagram.com/reel/{shortcode}/"
                        })
                        if len(reels) >= max_count:
                            break
        except Exception as e:
            print("Error finding reels:", e)
        finally:
            browser.close()

    print(f"Found {len(reels)} reels for @{username}")
    return reels

def download_reel_video(reel_url, output_path="downloaded_reel.mp4"):
    """
    Downloads highest quality reel video using yt-dlp with authenticated cookies.
    """
    print(f"Downloading reel via yt-dlp: {reel_url}")
    ydl_opts = {
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        'outtmpl': output_path,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'overwrites': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([reel_url])
        if os.path.exists(output_path):
            print(f"Successfully downloaded: {output_path} ({os.path.getsize(output_path)} bytes)")
            return output_path
    except Exception as e:
        print("Download error:", e)
    return None

if __name__ == '__main__':
    reels = get_latest_reels_from_profile("uxwithraaj", 5)
    print("Reels:", reels)
