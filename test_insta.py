import instaloader

L = instaloader.Instaloader()
print("Fetching profile uxwithraaj...")
try:
    profile = instaloader.Profile.from_username(L.context, "uxwithraaj")
    print(f"Profile found: {profile.username}, Full name: {profile.full_name}, Posts: {profile.mediacount}")
    count = 0
    for post in profile.get_posts():
        if post.is_video:
            print(f"Video Reel Shortcode: {post.shortcode}, Date: {post.date_utc}")
            print(f"URL: https://www.instagram.com/reel/{post.shortcode}/")
            count += 1
            if count >= 2:
                break
except Exception as e:
    print("Error:", e)
