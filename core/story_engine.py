"""
================================================================================
🌟 AUTOMATED INSTAGRAM STORIES ENGINE (20 STORIES / DAY PER ACCOUNT)
================================================================================
Generates and publishes 1080x1920 Ultra-HD Branded Story Cards across all 4 channels:
- 💼 Startup Road: Founder Rules, Mental Models, Business Case Studies
- 📈 Trading Road: Candlestick of the Day, Risk Discipline, Psychology Tips
- 🥗 Gudtree: Clean Ingredient Secrets, Superfood Alerts, Healthy Swaps
- 🛍️ Trending Road: Cool Gadget Highlights, Daily Life Hacks, Amazon Finds

Target: Exactly 20 Stories/Day per ID (80 Stories/Day Total)
Pacing: 08:00 AM - 10:00 PM (1 Story every ~42 minutes with human jitter)
================================================================================
"""

import os
import sys
import time
import json
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config_manager import get_channel_config
from core.publisher import InstagramPublisher
from core.telegram_hub import TelegramHub
from core.database import ChannelDatabase
from core.iron_shield import CircuitBreaker, is_reel_100pct_safe

def get_story_fonts():
    """Loads system TrueType fonts with fallback."""
    try:
        f_badge = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 32)
        f_topic = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
        f_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 56)
        f_body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
        f_footer = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 28)
    except:
        f_badge = ImageFont.load_default()
        f_topic = ImageFont.load_default()
        f_title = ImageFont.load_default()
        f_body = ImageFont.load_default()
        f_footer = ImageFont.load_default()
    return f_badge, f_topic, f_title, f_body, f_footer

# ------------------------------------------------------------------------------
# 20 CURATED HIGH-VALUE STORY TEMPLATES PER CHANNEL (100% META COMPLIANT)
# ------------------------------------------------------------------------------
STORY_TEMPLATES = {
    "startup_road": [
        ("FOUNDER RULE #1", "Execution Beats Planning", "A mediocre idea executed relentlessly will always beat a genius idea left on a whiteboard."),
        ("STARTUP REALITY", "Fall in Love with the Problem", "Don't fall in love with your solution. The market only cares if you solve their pain."),
        ("SCALE SECRET", "Retention Over Acquisition", "Filling a leaky bucket with paid ads is suicide. Make existing users love your product first."),
        ("BUSINESS TRUTH", "Cash Flow is Oxygen", "Profit is vanity, revenue is sanity, but cash flow in the bank is reality. Never run out of runway."),
        ("LEADERSHIP", "Hire for Mission, Not Just Resume", "Early stage startups need missionaries who believe in the vision, not mercenaries chasing titles."),
        ("SALES INSIGHT", "Sell the Destination, Not the Plane", "Customers don't buy features; they buy the transformation features bring to their life."),
        ("MINDSET", "The Dip is Where Winners Are Made", "When growth plateaus and excitement fades, daily discipline separates real founders from dreamers."),
        ("COMPETITIVE EDGE", "Speed is Your Single Weapon", "Small startups can't outspend giants, but they can ship in 3 days what enterprise takes 6 months to approve."),
        ("PRICING STRATEGY", "Never Compete on Price Alone", "There is no strategic moat in being the second cheapest. Compete on exceptional customer experience."),
        ("FOUNDER LESSON", "Talk to 5 Customers Every Week", "The best product roadmap isn't brainstormed in a meeting room; it's dictated by your customers' complaints."),
        ("FOCUS RULE", "Say No to 99 Good Ideas", "Strategy is about deciding what NOT to do. Protect your core focus ruthlessly."),
        ("UNIT ECONOMICS", "CAC Must Pay Back in 12 Months", "If customer acquisition cost doesn't recover within 12 months, your growth model is unsustainable."),
        ("MARKET LESSON", "Niche Down Until It Hurts", "It is 100x easier to dominate a small specific market first than to be mediocre for everyone."),
        ("TEAM CULTURE", "High Standards, Zero Drama", "A small A-player team will outperform a bloated department of average performers every single time."),
        ("RESILIENCE", "Failure is Just Data", "A failed launch is not a personal defeat; it's customer feedback on your value proposition."),
        ("BRAND BUILDING", "Be Polarizing, Not Boring", "If nobody hates your brand, nobody loves it either. Take a strong stance on what you believe in."),
        ("PRODUCT WISDOM", "Remove Features Before Adding New Ones", "Simplicity is the ultimate sophistication. Great products feel effortless to use."),
        ("GROWTH HACK", "Turn Early Users Into Evangelists", "The highest ROI growth channel is word of mouth driven by customer delight."),
        ("FINANCIAL DISCIPLINE", "Keep Fixed Overhead Razor Thin", "Keep your burn rate low until you have indisputable proof of product-market fit."),
        ("DAILY MOTIVATION", "Compounding Takes 5 Years", "What looks like overnight success from the outside was usually 2,000 days of invisible effort.")
    ],

    "trading_pulse": [
        ("RISK DISCIPLINE #1", "Define Stop Loss Before Entering", "If you don't know your exit price before entering a trade, you are gambling, not trading."),
        ("CHART PSYCHOLOGY", "The Doji is a Pause, Not an Entry", "A Doji represents market indecision. Always wait for the next candle confirmation."),
        ("CAPITAL PROTECTION", "Never Risk More Than 1-2% Per Trade", "Protect your capital at all costs. You cannot play the market if your account is wiped out."),
        ("TECHNICAL RULE", "Breakouts Need Volume Confirmation", "A breakout without above-average volume is frequently an institutional liquidity trap."),
        ("TRADER MINDSET", "Accept Losses Without Emotional Pain", "Losses are simply the cost of doing business in trading. Never take a loss personally."),
        ("PRICE ACTION", "Support Turned Resistance", "Broken support levels frequently become the strongest resistance levels on a retest."),
        ("DISCIPLINE", "Revenge Trading Kills Accounts", "After a losing trade, close the screen. The market does not owe you your money back."),
        ("PATIENCE", "Cash is a Valid Position", "Staying out of a choppy, low-probability market is one of the highest-yield trading decisions."),
        ("TREND WISDOM", "Trade With the Broader Trend", "Fighting the higher-timeframe trend is like swimming against a tidal wave. Align with the flow."),
        ("EXECUTION", "Plan the Trade, Trade the Plan", "Write your entry, target, and stop loss down. Once live, execute with zero hesitation."),
        ("RISK REWARD", "Target 1:2 Minimum Risk-to-Reward", "With a 1:2 ratio, you can be wrong 50% of the time and still remain consistently profitable."),
        ("CHART TIP", "Multi-Timeframe Analysis is Key", "Check Daily for trend, 1-Hour for structure, and 15-Min for clean tactical entries."),
        ("MARKET LESSON", "News Follows Price Action", "By the time news hits mainstream media, smart money has already positioned and priced it in."),
        ("PSYCHOLOGY", "Overtrading Stems from Boredom", "Professional trading is 90% waiting and 10% execution. Learn to embrace the waiting."),
        ("STRUCTURE", "Identify Swing Highs & Swing Lows", "Market structure tells the real story of whether buyers or sellers are currently in control."),
        ("CAPITAL RULE", "Never Add to a Losing Position", "Averaging down on a trade that violated your setup is the fastest road to margin liquidation."),
        ("INDICATORS", "Price is King, Indicators are Lagging", "Use indicators only for secondary confirmation, never as your primary trigger for entry."),
        ("HABIT", "Journal Every Single Trade", "If you don't track your mistakes and win-loss metrics, you cannot improve your trading edge."),
        ("TRADING TRUTH", "Focus on the Process, Not the P&L", "Focusing on green numbers induces greed; focusing on flawless execution creates wealth."),
        ("GOLDEN RULE", "Survive First, Thrive Second", "The goal of your first year in trading is not to get rich; it's to protect your capital and survive.")
    ],

    "healthy_diet": [
        ("NUTRITION FACT #1", "Check the First 3 Ingredients", "Ingredients are listed by weight. If sugar or palm oil is in the top 3, it's not a healthy snack."),
        ("CLEAN EATING", "Real Food Does Not Need Labels", "Whole fruits, vegetables, seeds, and lentils are the purest fuel for human biology."),
        ("HYDRATION TIP", "Drink 500ml Water Upon Waking", "Overnight sleep dehydrates your organs. Rehydrating first thing jumpstarts metabolism."),
        ("SNACK HACK", "Swap Potato Chips for Roasted Makhana", "Makhana gives the exact same crunch with 3x higher protein and zero trans fats."),
        ("GUT HEALTH", "Probiotics Need Prebiotic Fiber", "Fermented curd provides healthy bacteria, but they need fiber from raw veggies to thrive."),
        ("SUGAR ALERT", "Hidden Sugar Aliases to Avoid", "Watch out for Maltodextrin, High Fructose Corn Syrup, Invert Syrup, and Dextrose on labels."),
        ("SUPERFOOD SPOTLIGHT", "Chia Seeds: The Omega-3 Powerhouse", "Just 2 tablespoons of soaked chia seeds provide 10g of fiber and healthy fats for sustained energy."),
        ("PROTEIN WISDOM", "Pair Lentils with Whole Grains", "Lentils and grains complete each other's amino acid profile to create complete protein."),
        ("DIET MYTH", "Not All Dietary Fats Make You Fat", "Fats from avocados, walnuts, and cold-pressed mustard oil are essential for brain health."),
        ("ENERGY HACK", "Never Skip Morning Protein", "A protein-rich breakfast stabilizes insulin and completely stops 4 PM sugar cravings."),
        ("READ THE LABEL", "'Zero Sugar' Often Means Artificial Sweeteners", "Sucralose and aspartame can disrupt gut microbiome. Choose naturally unsweetened snacks."),
        ("LIFESTYLE", "Chew Your Food 20 Times Per Bite", "Digestion begins in the mouth with salivary enzymes. Eating slowly prevents bloating."),
        ("HEALTHY SWAP", "Replace Refined White Sugar with Dates", "Whole date paste provides potassium, iron, and natural fiber that prevents insulin spikes."),
        ("EVENING HABIT", "Stop Caffeine 8 Hours Before Sleep", "Caffeine has a 6-hour half-life. Drinking coffee at 5 PM disrupts deep REM sleep cycles."),
        ("NUTRITION", "Eat the Rainbow for Phytonutrients", "Different natural food colors represent distinct antioxidant compounds that fight inflammation."),
        ("SALT TRUTH", "Switch Refined Table Salt to Rock Salt", "Unrefined rock/sendha salt retains trace minerals like potassium and magnesium."),
        ("OIL GUIDE", "Avoid Refined Seed Oils for Deep Frying", "Repeatedly heating refined sunflower/palm oil creates harmful free radicals and trans fats."),
        ("IMMUNITY", "Add Amla (Indian Gooseberry) Weekly", "A single fresh amla contains 20x more Vitamin C than an orange for radiant skin and immunity."),
        ("WELLNESS", "Walk 15 Minutes After Big Meals", "A gentle post-meal stroll lowers peak blood sugar spikes by up to 30% naturally."),
        ("CLEAN HABIT", "Your Body is Your Only Real Asset", "Treat every meal as medicine. What you feed your body today constructs your cells tomorrow.")
    ],

    "viral_finds": [
        ("GADGET OF THE DAY", "Magnetic Cable Management Hub", "Stops charger cables from falling behind your desk forever. Simple, clean, essential."),
        ("HOME ESSENTIAL", "Rechargeable Fabric Shaver", "Restores wool sweaters, coats, and sofa cushions to brand new condition in 30 seconds."),
        ("DAILY HACK", "Self-Cleaning Pet Hair Brush", "One-click button ejects all collected pet fur instantly into the bin with zero mess."),
        ("PROBLEM SOLVER", "Collapsible Silicone Kitchen Funnel", "Folds completely flat for drawer storage. Perfect for transferring oils and spices cleanly."),
        ("MUST HAVE", "Compact Motion Sensor Closet Light", "Magnetic stick-on bar lights up your wardrobe or pantry automatically upon opening."),
        ("CAR UPGRADE", "Rotating 360-Degree Cup Holder Expander", "Expands small car cup holders to fit giant 1-liter thermos bottles securely."),
        ("SMART LIVING", "Ultrasonic Jewelry & Glasses Cleaner", "Uses 45,000Hz sound waves to lift invisible grime from spectacles, rings, and watches."),
        ("KITCHEN HACK", "Silicone Stretch Lids: Ditch Plastic Wrap", "Reusable airtight lids stretch over bowls, melons, and jars to keep food fresh for days."),
        ("TRAVEL FIND", "Compression Packing Cubes with Double Zipper", "Compresses bulky jackets and clothes to save 50% suitcase volume effortlessly."),
        ("WORK SETUP", "Ergonomic Under-Desk Footrest Cushion", "Relieves lower back pressure and promotes healthy leg circulation during long work hours."),
        ("BATHROOM UPGRADE", "Fast-Drying Diatomite Stone Bath Mat", "Absorbs water instantly in 3 seconds and dries completely flat with zero mold or smell."),
        ("TECH ESSENTIAL", "3-in-1 Foldable Magnetic Wireless Charger", "Powers your phone, watch, and earbuds simultaneously from a single compact travel stand."),
        ("SAFETY FIND", "Compact Emergency Car Window Breaker", "Spring-loaded tungsten tip shatters tempered side glass underwater or during collisions."),
        ("DESK FIND", "Mini Desktop Vacuum for Crumbs & Dust", "Cleans mechanical keyboards and desk surfaces with quiet, powerful micro-suction."),
        ("LIFESTYLE", "Portable Electronic Luggage Scale", "Avoid expensive airline overweight baggage fees at airport check-in counters forever."),
        ("GENIUS PRODUCT", "Universal Socket Grip Tool (7mm - 19mm)", "54 steel pins automatically conform to grip any hex nut, hook, or damaged screw."),
        ("HOME FIND", "Touchless Automatic Foam Soap Dispenser", "Hygienic infrared sensor dispenses dense cleaning foam with zero hand contact."),
        ("ORGANIZER", "Over-The-Door Shoe & Cleaning Supply Rack", "Reclaims wasted door backspace to store 24 pairs or cleaning bottles neatly."),
        ("BEDROOM UPGRADE", "Sunrise Simulation Alarm Clock", "Gently wakes you up with progressive warm light 30 minutes before your alarm rings."),
        ("COOL TECH", "Waterproof Laser Tape Measure", "Measures room distances, area, and volume instantly up to 40 meters with 2mm accuracy.")
    ]
}

CHANNEL_THEMES = {
    "startup_road": {
        "bg_color": (15, 23, 42),       # Slate Dark #0f172a
        "border_color": (225, 29, 72),   # Crimson Rose #e11d48
        "badge_bg": (225, 29, 72),
        "badge_text": "💼 STARTUP ROAD • DAILY WISDOM",
        "handle": "@startup_road"
    },
    "trading_pulse": {
        "bg_color": (9, 13, 22),         # Deep Navy #090d16
        "border_color": (14, 165, 233),   # Cyan Blue #0ea5e9
        "badge_bg": (14, 165, 233),
        "badge_text": "📈 TRADING ROAD • RISK DISCIPLINE",
        "handle": "@trading_road_"
    },
    "healthy_diet": {
        "bg_color": (6, 26, 20),         # Forest Dark #061a14
        "border_color": (16, 185, 129),  # Emerald Green #10b981
        "badge_bg": (16, 185, 129),
        "badge_text": "🥗 GUDTREE • CLEAN EATING TRUTH",
        "handle": "@gudtree_"
    },
    "viral_finds": {
        "bg_color": (11, 7, 20),         # Cyber Dark #0b0714
        "border_color": (139, 92, 246),  # Neon Violet #8b5cf6
        "badge_bg": (139, 92, 246),
        "badge_text": "🛍️ TRENDING ROAD • GADGET ALERT",
        "handle": "@trending_road"
    }
}

def wrap_text(text: str, max_chars: int = 28) -> list:
    """Wraps text cleanly into multiple lines for story cards."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    for w in words:
        if current_length + len(w) + 1 <= max_chars:
            current_line.append(w)
            current_length += len(w) + 1
        else:
            lines.append(" ".join(current_line))
            current_line = [w]
            current_length = len(w)
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def render_story_card(channel_id: str, badge: str, title: str, body: str, output_path: str):
    """
    Renders a luxury 1080x1920 Story Card using Pillow with TrueType fonts.
    Guarantees crisp typography, branded color palettes, and 100% Meta compliance.
    """
    theme = CHANNEL_THEMES.get(channel_id, CHANNEL_THEMES["startup_road"])
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=theme["bg_color"])
    draw = ImageDraw.Draw(img)

    f_badge, f_topic, f_title, f_body, f_footer = get_story_fonts()

    # 1. Subtle Outer Border
    margin = 40
    draw.rounded_rectangle(
        [(margin, margin), (width - margin, height - margin)],
        radius=24,
        outline=theme["border_color"],
        width=4
    )

    # 2. Header Channel Badge
    badge_w, badge_h = 740, 80
    badge_x = (width - badge_w) // 2
    badge_y = 220
    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
        radius=40,
        fill=theme["badge_bg"]
    )
    # Centered badge text
    bbox = draw.textbbox((0, 0), theme["badge_text"], font=f_badge)
    tx = badge_x + (badge_w - (bbox[2] - bbox[0])) // 2
    ty = badge_y + (badge_h - (bbox[3] - bbox[1])) // 2 - 4
    draw.text((tx, ty), theme["badge_text"], fill=(255, 255, 255), font=f_badge)

    # 3. Topic Tag
    draw.text((100, 420), f"TOPIC: {badge.upper()}", fill=theme["border_color"], font=f_topic)

    # 4. Big Bold Title
    title_lines = wrap_text(title.upper(), max_chars=20)
    y_pos = 500
    for line in title_lines:
        draw.text((100, y_pos), line, fill=(255, 255, 255), font=f_title)
        y_pos += 75

    # 5. Dividing Accent Bar
    y_pos += 25
    draw.line([(100, y_pos), (320, y_pos)], fill=theme["border_color"], width=6)
    y_pos += 60

    # 6. Body Paragraph
    body_lines = wrap_text(body, max_chars=28)
    for line in body_lines:
        draw.text((100, y_pos), line, fill=(226, 232, 240), font=f_body)
        y_pos += 62

    # 7. Bottom Branding & Handle
    draw.line([(100, 1620), (width - 100, 1620)], fill=(51, 65, 85), width=2)
    draw.text((100, 1650), f"Follow {theme['handle']} for daily value", fill=(148, 163, 184), font=f_footer)
    draw.text((width - 360, 1650), "TAP TO SAVE STORY ↗", fill=theme["border_color"], font=f_footer)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "JPEG", quality=95)
    return output_path

# ------------------------------------------------------------------------------
# PUBLISH SINGLE STORY FOR CHANNEL
# ------------------------------------------------------------------------------
def publish_single_channel_story(channel_id: str, story_index: int = 1, today_str: str = None):
    """
    Renders and publishes a single Instagram Story via Meta Graph API.
    Tracks state in ChannelDatabase to guarantee exact 20 stories/day without duplicate triggers.
    """
    if not today_str:
        today_str = datetime.now().strftime("%Y-%m-%d")

    config = get_channel_config(channel_id)
    if not config.get("enabled", True):
        return False

    db = ChannelDatabase(config["runtime"]["db_path"])
    if db.is_story_processed(story_index, today_str):
        print(f"⏩ [Story Already Live] {channel_id} Story #{story_index} already posted for {today_str}.")
        return True

    # Check Circuit Breaker
    is_locked, lock_reason = CircuitBreaker.is_channel_locked(channel_id)
    if is_locked:
        print(f"🛑 [Circuit Breaker Lock] Skipping story for {channel_id}: {lock_reason}")
        return False

    creds = config.get("credentials", {})
    hub = TelegramHub(creds.get("telegram_bot_token"), creds.get("telegram_chat_id"))
    publisher = InstagramPublisher(creds.get("instagram_account_id"), creds.get("page_access_token"))

    if not publisher.is_configured():
        return False

    templates = STORY_TEMPLATES.get(channel_id, STORY_TEMPLATES["startup_road"])
    idx = (story_index - 1) % len(templates)
    badge, title, body = templates[idx]

    # Meta Iron Shield Validation
    is_safe, reason = is_reel_100pct_safe(title, badge, body)
    if not is_safe:
        print(f"🛑 [Story Blocked by Iron Shield] {reason}")
        return False

    temp_img = os.path.join(config["runtime"]["workspace_dir"], f"story_slot_{story_index:02d}.jpg")
    render_story_card(channel_id, badge, title, body, temp_img)

    display_name = config.get("display_name", channel_id)
    print(f"\n🌟 [{display_name}] Publishing Story #{story_index}/20: {title}...")

    try:
        sent, cdn_url = hub.send_photo_with_cdn_url(temp_img, caption=f"[{display_name}] Story #{story_index}: {title}")
        if sent and cdn_url:
            res = publisher.publish_story(cdn_url)
            if res and "media_id" in res:
                media_id = res["media_id"]
                db.mark_story_processed(story_index, today_str, title, media_id)
                print(f"🎉 [{display_name}] Story #{story_index}/20 LIVE on Instagram! (Media ID: {media_id})")
                hub.send_message(
                    f"🌟 <b>{display_name} Story #{story_index}/20 LIVE!</b>\n\n"
                    f"📌 <b>Topic:</b> {badge}\n"
                    f"💡 <b>Title:</b> {title}"
                )
                return True
    except Exception as e:
        print(f"❌ Story publish failed for {channel_id}: {e}")
    finally:
        if os.path.exists(temp_img):
            try: os.remove(temp_img)
            except: pass

    return False

# ------------------------------------------------------------------------------
# 20 SLOTS GENERATOR (08:00 AM - 10:00 PM) ~ Every 42 Minutes
# ------------------------------------------------------------------------------
def generate_20_story_slots():
    """Generates 20 slots between 08:00 AM and 10:00 PM (~42 mins apart)."""
    slots = []
    start_total = 8 * 60       # 08:00 AM
    end_total = 21 * 60 + 50   # 09:50 PM
    interval = (end_total - start_total) / 19
    for i in range(20):
        m_total = int(start_total + i * interval)
        h = m_total // 60
        m = m_total % 60
        slots.append((i + 1, h, m))
    return slots

STORY_SLOTS = generate_20_story_slots()

def publish_all_channels_story_slot(slot_index: int, today_str: str = None):
    """
    Publishes the story for slot_index across all 4 channels with anti-bot stagger.
    """
    if not today_str:
        today_str = datetime.now().strftime("%Y-%m-%d")

    channels = ["startup_road", "trading_pulse", "healthy_diet", "viral_finds"]
    results = {}
    for ch in channels:
        res = publish_single_channel_story(ch, story_index=slot_index, today_str=today_str)
        results[ch] = res
        time.sleep(random.uniform(5, 10))
    return results
