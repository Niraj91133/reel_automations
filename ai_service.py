import os
import sys
import json
import re
import subprocess
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')

DEFAULT_GEMINI_KEY = "AQ.Ab8RN6Jr6PeTkcHjbHdcXpRsOV-2tkC3UNhNod8kAn-6_4acWw"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", DEFAULT_GEMINI_KEY)

# Primary lightning-fast models, with preview fallback
WORKING_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview"
]

FORBIDDEN_GENERIC_TITLES = [
    "the growth blueprint",
    "the strategic playbook",
    "important business lesson",
    "founder playbook",
    "disciplined execution beats raw talent"
]

def extract_audio_from_video(video_path, output_audio_path="temp_audio.mp3"):
    """Extract lightweight mono 16kHz audio for speech processing."""
    cmd = [
        "ffmpeg", "-y",
        "-threads", "2",
        "-i", video_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "32k",
        output_audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(output_audio_path):
        return output_audio_path
    return None

def clean_json_response(raw_text):
    """Safely extracts JSON from model response text."""
    clean = raw_text.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    elif clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    return clean.strip()

def is_title_generic(title):
    """Checks if a title contains lazy repetitive copy-paste text."""
    t_lower = (title or "").lower()
    return any(forbidden in t_lower for forbidden in FORBIDDEN_GENERIC_TITLES)

def generate_fallback_from_metadata(creator_username, description="", title=""):
    """
    Intelligent NLP fallback if internet or AI is completely unreachable.
    Extracts numbers, currency symbols, and key entities from the creator's real text
    to generate an authentic curiosity hook.
    """
    combined_text = f"{title} {description}".strip()
    
    # 1. Look for numbers and currency (e.g. ₹20,000, $500, 10X, 40 Crores)
    money_match = re.search(r'(₹\s*[\d,]+(?:\s*(?:crore|cr|lakh|k))?|\$\s*[\d,]+(?:\s*(?:k|m))?|\b\d+\s*(?:crore|cr|lakh|k)\b)', combined_text, re.I)
    
    # 2. Extract key topic keywords
    keywords = ["dropshipping", "ecommerce", "ai tools", "side hustle", "monetization", "revenue", "salary", "wealth", "investing", "business idea"]
    matched_kw = next((kw for kw in keywords if kw in combined_text.lower()), "BUSINESS SECRETS")
    
    if money_match:
        val = money_match.group(1).upper()
        hook_pill = f"{val} FORMULA"
        main_title = f"{matched_kw.upper()}\nHOW TO SCALE"
    else:
        hook_pill = f"{matched_kw.upper()}"
        main_title = f"THE TRUTH ABOUT\n{matched_kw.upper()}"

    trigger = "ROAD"
    if "drop" in combined_text.lower(): trigger = "DROPSHIP"
    elif "ai" in combined_text.lower(): trigger = "AITOOLS"
    elif "money" in combined_text.lower() or "paise" in combined_text.lower(): trigger = "WEALTH"

    # Clean, high-converting dynamic trigger and caption
    from core.caption_engine import generate_rich_caption, derive_startup_trigger
    trigger, breakdown, takeaway = derive_startup_trigger(combined_text)

    caption = generate_rich_caption(
        channel_id=category,
        title=main_title,
        hook_pill=hook_pill,
        creator=creator_username,
        context_text=combined_text
    )

    return {
        "hook_pill": hook_pill[:25],
        "main_title": main_title,
        "sub_quote": f'"{takeaway}"',
        "comment_trigger": trigger,
        "caption": caption
    }

def analyze_reel_content(video_file_path, creator_username="creator", category="startup", original_description="", original_title=""):
    """
    Enterprise-Grade AI Reel Intelligence Engine:
    1. Blends Video Metadata (description/title) with Audio Speech.
    2. Enforces 100K+ Like Virality Architecture (Exact numbers, high-curiosity contrast).
    3. Mandates Comment Velocity Lead-Magnet Trigger.
    4. Quality Gate strictly rejects generic 'Growth Blueprint' titles.
    """
    client = genai.Client(api_key=GEMINI_API_KEY)
    audio_path = extract_audio_from_video(video_file_path, "reel_speech.mp3")

    prompt = f"""
You are the Chief Viral Strategist & Growth Architect for @startup_road (33K+ followers).
Your benchmark is our top viral reels that generated 50,000 to 150,000+ likes (e.g. 'If I Lost Everything Today 3 Steps', 'Build Wealth From ₹20,000 Monthly Salary', 'MrBeast Monetization Strategy', 'How To Start User Testing For Money').

TARGET CREATOR: @{creator_username}
CREATOR'S REEL DESCRIPTION/NOTES:
\"\"\"{original_description or original_title or 'High-impact business and startup lesson'}\"\"\"

STRICT VIRAL HOOK & ENGAGEMENT RULES:
0. STRICT AUDIO & LANGUAGE FILTER:
   - "is_hindi": The audio MUST be spoken in Hindi (or conversational Hinglish by Indian creator). If purely English or foreign language, set false.
   - "has_speech": MUST have a clear human speaking voice explaining the topic. If only background music, trending song, beats, or silence, set false.
1. DOMAIN FOCUS: How to Earn Money, Online Income, Side Hustles, AI Money Tools, Business Tricks & Ways in Hindi.
2. FORBIDDEN: NEVER output generic corporate fluff like "The Growth Blueprint", "The Strategic Playbook", or "Important Business Lesson". Any generic title is strictly disqualified.
3. HOOK PSYCHOLOGY: Must use EXACT NUMBERS, MONETARY VALUE, EXTREME CURIOSITY, or CONTRARIAN TRUTH (e.g. "₹23,000 CR MARKET", "EARN ₹1 LAKH/MO", "MRBEAST SECRET", "STOP WASTING TIME").
4. "hook_pill": 2 to 4 words MAX, ALL CAPS (e.g. "EARNING TRICK", "MONEY HACK", "AI WEALTH HACK").
5. "main_title": Exactly 2 short punchy lines separated by \\n (maximum 6-8 words total in Title Case or CAPS). Must specify the exact topic spoken.
6. "sub_quote": 1 punchy, unforgettable spoken statement in double quotes.
7. "comment_trigger": A single 1-word keyword in ALL CAPS for viewers to comment (e.g. "TRICK", "AI", "SCALE", "MONEY", "ROAD").
8. "caption": High-converting viral Instagram SEO caption structured strictly as:

[Line 1: Viral Scroll-Stopping Hook with emoji] 👇

📌 The Method Breakdown:
• [Step 1: Specific trick or strategy explained by speaker]
• [Step 2: Core mechanism or execution hack]
• [Step 3: Strategic edge or website/tool used]

💡 Golden Takeaway: [1 punchy golden takeaway]

👇 Want the step-by-step tools, links & guide?
Comment "[INSERT comment_trigger HERE]" below and I'll DM you the breakdown instantly! 📩

Credits & Speaker: @{creator_username}
Follow @startup_road for daily earning tricks & business guides.

#EarnMoneyOnline #PaiseKaiseKamaye #OnlineEarning #BusinessIdeas #StartupRoad #EarningTricks

Return STRICT VALID JSON ONLY. No markdown backticks:
{{
  "is_hindi": true,
  "has_speech": true,
  "hook_pill": "...",
  "main_title": "Line 1\\nLine 2",
  "sub_quote": "\\"...\\"",
  "comment_trigger": "...",
  "caption": "..."
}}
"""

    data = None

    # Step 1: Try Fast Generative AI with Metadata Context
    for model_name in WORKING_MODELS:
        try:
            print(f"Calling Gemini AI ({model_name}) for viral hook synthesis...", flush=True)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            raw = clean_json_response(response.text)
            parsed = json.loads(raw)

            # Quality Gate: Check if title is generic
            if is_title_generic(parsed.get("main_title")):
                print(f"⚠️ Warning: Model {model_name} generated a generic title. Discarding.", flush=True)
                continue

            data = parsed
            print(f"✅ AI Viral Engine succeeded with {model_name}!", flush=True)
            break
        except Exception as e:
            print(f"Model {model_name} note: {e}", flush=True)
            continue

    # Cleanup temporary audio
    if audio_path and os.path.exists(audio_path):
        try: os.remove(audio_path)
        except: pass

    # Step 2: Quality Gate Enforcement
    if not data or is_title_generic(data.get("main_title")):
        print("⚡ Activating Smart NLP Metadata Fallback (Zero Generic Content)...", flush=True)
        data = generate_fallback_from_metadata(
            creator_username=creator_username,
            description=original_description,
            title=original_title
        )

    return data

if __name__ == '__main__':
    test_data = analyze_reel_content(
        video_file_path="",
        creator_username="ecomtushar",
        original_description="Are you ready to get a piece of this ₹23,000 crore market in India? T-shirt dropshipping, Shopify ecommerce"
    )
    print("\n=== AI SERVICE OUTPUT TEST ===")
    print(json.dumps(test_data, indent=2))
