import requests
from core.config_manager import get_channel_config

channels = ['startup_road', 'trading_pulse', 'healthy_diet', 'viral_finds']
for ch in channels:
    cfg = get_channel_config(ch)
    token = cfg['credentials']['page_access_token']
    acc_id = cfg['credentials']['instagram_account_id']
    url = f'https://graph.facebook.com/v21.0/{acc_id}/media?fields=id,caption,like_count,comments_count,permalink,thumbnail_url&limit=50&access_token={token}'
    resp = requests.get(url).json()
    items = resp.get('data', [])
    uname = cfg.get('instagram_username')
    print(f'=== {ch} (@{uname}): {len(items)} media items found ===')
    if items:
        sorted_by_eng = sorted(items, key=lambda x: (x.get('like_count', 0) * 2 + x.get('comments_count', 0)), reverse=True)
        print('  Top Viral 3:')
        for x in sorted_by_eng[:3]:
            l = x.get('like_count', 0)
            c = x.get('comments_count', 0)
            p = x.get('permalink', '')
            print(f'    • Likes: {l}, Comments: {c}, Link: {p}')
        print('  Lowest Engagement 3:')
        for x in sorted_by_eng[-3:]:
            l = x.get('like_count', 0)
            c = x.get('comments_count', 0)
            p = x.get('permalink', '')
            print(f'    • Likes: {l}, Comments: {c}, Link: {p}')
    print()

