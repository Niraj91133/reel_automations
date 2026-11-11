import json

with open('startup_road_media_audit.json', encoding='utf-8') as f:
    media = json.load(f)

print('=== TOP 5 POSTS (NOV 4-5 VIRAL PEAK) ===')
nov45 = [x for x in media if x.get('timestamp','').startswith(('2026-11-04', '2026-11-05'))]
nov45_sorted = sorted(nov45, key=lambda x: x.get('like_count', 0), reverse=True)

for m in nov45_sorted[:5]:
    print(f"LIKES: {m.get('like_count'):,d} | COMMENTS: {m.get('comments_count'):,d}")
    print(f"LINK: {m.get('permalink')}")
    print("CAPTION:")
    print(m.get('caption', '')[:350])
    print('='*70)

print('\n=== SLUMP POSTS (NOV 8-10) ===')
recent = [x for x in media if x.get('timestamp','').startswith(('2026-11-08', '2026-11-09', '2026-11-10'))]
recent_sorted = sorted(recent, key=lambda x: x.get('like_count', 0))

for m in recent_sorted[:5]:
    print(f"LIKES: {m.get('like_count'):,d} | COMMENTS: {m.get('comments_count'):,d}")
    print(f"LINK: {m.get('permalink')}")
    print("CAPTION:")
    print(m.get('caption', '')[:350])
    print('='*70)
