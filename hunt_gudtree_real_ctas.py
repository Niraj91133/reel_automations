import os, sys, re, json, time
sys.path.insert(0, 'reel_automations-main')
from core.niche_hunter import get_channel_cookies, parse_views_count
from playwright.sync_api import sync_playwright
import yt_dlp

ydl_opts = {'quiet': True, 'skip_download': True, 'cookiefile': 'reel_automations-main/cookies.txt'}

# Popular Indian diet, nutrition and fat loss creators who use comment DM automations (ManyChat)
target_profiles = [
    'fiteloapp',
    'dietitian_mac_singh',
    'gunjan_shouts',
    'dietitianshreya_official',
    'simrun.chopra',
    'dietitian.priyanka',
    'dt.lavleen'
]

cookies = get_channel_cookies('healthy_diet')

found_reels = []
cta_reels = []

chromium_args = [
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu",
    "--mute-audio"
]

print("Starting Instagram scan for real diet comment CTAs...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=chromium_args)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900}
    )
    if cookies:
        ctx.add_cookies(cookies)
    page = ctx.new_page()

    for profile in target_profiles:
        if len(cta_reels) >= 3:
            break
        url = f"https://www.instagram.com/{profile}/reels/"
        print(f"\nChecking @{profile} reels...")
        try:
            page.goto(url, timeout=25000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            
            # Extract reel links
            links = page.eval_on_selector_all("a[href*='/reel/']", "els => els.map(e => e.href)")
            print(f"  Found {len(links)} reels on profile")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for l in links[:8]:
                    m = re.search(r'/reel/([^/?]+)', l)
                    if not m:
                        continue
                    code = m.group(1)
                    reel_url = f"https://www.instagram.com/reel/{code}/"
                    
                    try:
                        info = ydl.extract_info(reel_url, download=False)
                        desc = info.get('description', '') or ''
                        creator = info.get('uploader', profile)
                        comments = info.get('comment_count', 0)
                        
                        # Check for strict comment CTA
                        cta_match = re.search(r'(comment\s+[\'\"][a-zA-Z0-9_\s]+[\'\"]|comment\s+[A-Z]{3,}|comment\s+karo|comment\s+mein|comment\s+below|comment\s+karein)', desc, re.IGNORECASE)
                        if cta_match:
                            cta_trigger = cta_match.group(0)
                            cta_reels.append({
                                'url': reel_url,
                                'creator': creator,
                                'comments': comments,
                                'cta': cta_trigger,
                                'desc': desc[:300].replace('\n', ' ')
                            })
                            print(f"🎯 MATCH FOUND on @{profile}: {reel_url} | CTA: '{cta_trigger}' | Comments: {comments}")
                            if len(cta_reels) >= 3:
                                break
                    except Exception as ex:
                        pass
        except Exception as e:
            print(f"Error accessing @{profile}: {e}")

    browser.close()

with open('gudtree_exact_ctas.json', 'w', encoding='utf-8') as f:
    json.dump(cta_reels, f, indent=2, ensure_ascii=False)

print(f"\nCompleted! Found {len(cta_reels)} exact Comment-CTA reels for Gudtree.")

