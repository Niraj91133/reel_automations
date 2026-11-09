import sqlite3, yt_dlp, re, json

ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'cookiefile': 'reel_automations-main/cookies.txt'
}

cta_patterns = [
    r"comment\s+[\'\"][a-zA-Z0-9_\s]+[\'\"]",
    r"comment\s+[A-Z]{3,}",
    r"comment\s+karo",
    r"comment\s+below",
    r"comment\s+down",
    r"type\s+[\'\"][a-zA-Z0-9]+[\'\"]",
    r"comment\s+kar",
    r"link\s+chahiye\s+to\s+comment",
    r"comment\s+for\s+link",
    r"comment\s+me\s+batao",
    r"comment\s+karein"
]

def scan_channel(ch, limit=70):
    conn = sqlite3.connect(f'reel_automations-main/databases/{ch}_history.db')
    c = conn.cursor()
    c.execute('SELECT shortcode FROM hunted_reels ORDER BY id DESC LIMIT ?', (limit,))
    codes = [r[0] for r in c.fetchall()]
    
    matches = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for code in codes:
            url = f'https://www.instagram.com/reel/{code}/'
            try:
                info = ydl.extract_info(url, download=False)
                desc = info.get('description', '') or ''
                creator = info.get('uploader', '') or ''
                comments = info.get('comment_count', 0)
                
                matched_cta = None
                for p in cta_patterns:
                    m = re.search(p, desc, re.IGNORECASE)
                    if m:
                        matched_cta = m.group(0)
                        break
                        
                if matched_cta or comments >= 150:
                    matches.append({
                        'shortcode': code,
                        'url': url,
                        'creator': creator,
                        'comments': comments,
                        'cta': matched_cta if matched_cta else f"{comments} comments (High Engagement)",
                        'snippet': desc[:250].replace('\n', ' ')
                    })
                    print(f"[{ch}] MATCH: {url} | CTA: {matched_cta} | Comments: {comments}")
                    if len(matches) >= 3:
                        break
            except Exception as e:
                pass
    return matches

all_results = {}
for ch in ['healthy_diet', 'trading_pulse', 'viral_finds']:
    print(f"Scanning {ch}...")
    all_results[ch] = scan_channel(ch, 70)

with open('strict_cta_results.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)
print("ALL DONE!")

