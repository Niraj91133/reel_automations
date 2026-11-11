import json
from datetime import datetime
from collections import defaultdict

with open('startup_road_media_audit.json', encoding='utf-8') as f:
    media = json.load(f)

print(f"Total posts analyzed: {len(media)}")

daily_stats = defaultdict(lambda: {'count': 0, 'likes': 0, 'comments': 0, 'items': []})
all_items = []

for it in media:
    ts = it.get('timestamp')
    if not ts: continue
    dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S%z')
    date_str = dt.strftime('%Y-%m-%d')
    likes = it.get('like_count', 0)
    comments = it.get('comments_count', 0)
    cap = it.get('caption', '')
    perm = it.get('permalink', '')
    first_line = cap.split('\n')[0] if cap else 'NO TITLE'
    
    daily_stats[date_str]['count'] += 1
    daily_stats[date_str]['likes'] += likes
    daily_stats[date_str]['comments'] += comments
    daily_stats[date_str]['items'].append((likes, comments, first_line, perm, dt))
    all_items.append((likes, comments, dt, first_line, perm))

sorted_dates = sorted(daily_stats.keys())
print(f"Timeline: {sorted_dates[0]} to {sorted_dates[-1]} ({len(sorted_dates)} unique dates)")

total_likes = sum(d['likes'] for d in daily_stats.values())
total_comments = sum(d['comments'] for d in daily_stats.values())
print(f"Total Likes across account: {total_likes:,}")
print(f"Total Comments across account: {total_comments:,}")
print(f"Overall Avg Likes/Post: {total_likes/len(media):.1f}")
print(f"Overall Avg Comments/Post: {total_comments/len(media):.1f}\n")

print("=" * 80)
print("📅 COMPLETE TIMELINE EVOLUTION (By Date)")
print("=" * 80)
for d in sorted_dates:
    st = daily_stats[d]
    avg_l = st['likes'] / st['count'] if st['count'] else 0
    avg_c = st['comments'] / st['count'] if st['count'] else 0
    print(f"{d} | Posts: {st['count']:3d} | Total Likes: {st['likes']:7,d} | Avg Likes: {avg_l:7.1f} | Comments: {st['comments']:6,d} | Avg Comm: {avg_c:5.1f}")

print("\n" + "=" * 80)
print("🏆 TOP 15 ALL-TIME VIRAL REELS")
print("=" * 80)
sorted_by_likes = sorted(all_items, key=lambda x: (x[0] * 2 + x[1]), reverse=True)
for i, (l, c, dt, title, perm) in enumerate(sorted_by_likes[:15], 1):
    d_str = dt.strftime('%Y-%m-%d')
    print(f"#{i:02d} | Likes: {l:6,d} | Comments: {c:5,d} | Date: {d_str} | Link: {perm}")
    print(f"     Title: {title[:75]}")

print("\n" + "=" * 80)
print("⚠️ LOWEST 15 PERFORMING REELS (Recently or Fallback)")
print("=" * 80)
sorted_lowest = sorted(all_items, key=lambda x: (x[0] * 2 + x[1]))
for i, (l, c, dt, title, perm) in enumerate(sorted_lowest[:15], 1):
    d_str = dt.strftime('%Y-%m-%d')
    print(f"#{i:02d} | Likes: {l:4d} | Comments: {c:4d} | Date: {d_str} | Link: {perm}")
    print(f"     Title: {title[:75]}")

print("\n" + "=" * 80)
print("📊 ENGAGEMENT BREAKDOWN BY TOPIC / NICHE")
print("=" * 80)

topics = {
    'Containers & Scrap': ['container', 'scrap', 'steel boxes', 'garage'],
    'Micro Capital (Under ₹50k)': ['10,000', '20,000', '50,000', 'low investment', 'budget', '70,000', 'paisa'],
    'Physical Machines & Manufacturing': ['machine', 'manufacturing', 'chappal', 'packaging', 'factory', 'plant', 'paper bag'],
    'Franchise & Dealerships': ['petrol pump', 'dealership', 'franchise', 'agency'],
    'AI Tools & Digital Income': ['ai tool', 'chatgpt', 'digital product', 'stickers', 'claude', 'app idea', 'ai se'],
    'Generic Advice / Motivation': ['lesson', 'strategic playbook', 'growth blueprint', 'relationships', 'mindset', 'valuable']
}

topic_stats = defaultdict(lambda: {'count': 0, 'likes': 0, 'comments': 0})

for it in media:
    cap = (it.get('caption') or '').lower()
    likes = it.get('like_count', 0)
    comms = it.get('comments_count', 0)
    
    matched = False
    for t_name, kws in topics.items():
        if any(kw in cap for kw in kws):
            topic_stats[t_name]['count'] += 1
            topic_stats[t_name]['likes'] += likes
            topic_stats[t_name]['comments'] += comms
            matched = True
            break
    if not matched:
        topic_stats['Other Business Cases']['count'] += 1
        topic_stats['Other Business Cases']['likes'] += likes
        topic_stats['Other Business Cases']['comments'] += comms

for t, st in sorted(topic_stats.items(), key=lambda x: x[1]['likes']/max(1, x[1]['count']), reverse=True):
    avg_l = st['likes'] / st['count'] if st['count'] else 0
    avg_c = st['comments'] / st['count'] if st['count'] else 0
    print(f"{t:35s} | Reels: {st['count']:3d} | Total Likes: {st['likes']:7,d} | Avg Likes: {avg_l:7.1f} | Avg Comm: {avg_c:5.1f}")
