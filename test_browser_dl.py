import os
import sys
import base64
import time

sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

def download_reel_via_page_context(reel_url, output_path="downloaded_reel.mp4"):
    print(f"Downloading reel via in-browser context: {reel_url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        try:
            page.goto(reel_url, timeout=30000, wait_until="networkidle")
            time.sleep(3)
            
            # Extract video through browser javascript fetch
            print("Extracting video buffer from page...")
            video_b64 = page.evaluate("""
                async () => {
                    const video = document.querySelector('video');
                    if (!video || !video.src) return null;
                    const res = await fetch(video.src);
                    const blob = await res.blob();
                    return new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result.split(',')[1]);
                        reader.readAsDataURL(blob);
                    });
                }
            """)
            
            if video_b64:
                video_bytes = base64.b64decode(video_b64)
                with open(output_path, "wb") as f:
                    f.write(video_bytes)
                print(f"Successfully downloaded {len(video_bytes)} bytes to {output_path}!")
                return output_path
            else:
                print("Could not find video element or src.")
                return None
        except Exception as e:
            print("Download error:", e)
            return None
        finally:
            browser.close()

if __name__ == '__main__':
    download_reel_via_page_context("https://www.instagram.com/reel/DdOg8G7zGfE/", "test_reel.mp4")
