import os
import sys
import json
import yt_dlp

def fetch_latest_reel(username):
    url = f"https://www.instagram.com/{username}/reels/"
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'playlist_items': '1-3'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info

if __name__ == '__main__':
    username = 'uxwithraaj'
    print(f"Fetching reels for {username}...")
    try:
        data = fetch_latest_reel(username)
        print("Success! Found entries:")
        entries = data.get('entries', [])
        for e in entries[:3]:
            print("ID:", e.get('id'), "URL:", e.get('url'))
    except Exception as err:
        print("Error:", err)
