import os
import sys
import json
import subprocess
from google import genai
from google.genai import types

DEFAULT_GEMINI_KEY = "AQ.Ab8RN6Jr6PeTkcHjbHdcXpRsOV-2tkC3UNhNod8kAn-6_4acWw"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", DEFAULT_GEMINI_KEY)

def extract_audio_from_video(video_path, output_audio_path="temp_audio.mp3"):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ar", "16000",
        "-ac", "1",
        "-b:a", "64k",
        output_audio_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(output_audio_path):
        return output_audio_path
    return None

def analyze_reel_content(video_file_path, creator_username="creator", category="startup"):
    client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=25000))
    audio_path = extract_audio_from_video(video_file_path, "reel_speech.mp3")

    if category == "politics":
        category_context = """
        CATEGORY: Politics / National Affairs / Legal / Geopolitics / Deshhit (India).
        SEO KEYWORDS THEME: Indian politics, constitutional rights, governance analysis, Supreme Court, economic policy, national issues, parliament debates.
        TONE: Hard-hitting, analytical, patriotic, investigative, highly engaging.
        """
        sample_tags = "#IndianPolitics #CurrentAffairs #Bharat #DeshHit #SupremeCourt #LegalRights #Constitution #NationalNews"
    else:
        category_context = """
        CATEGORY: Startup / Business / Entrepreneurship / Case Studies / Wealth Building.
        SEO KEYWORDS THEME: High-margin business ideas, founder playbook, marketing breakdown, no-code AI, profitable side hustles, startup case study, revenue models.
        TONE: Actionable, value-dense, high-curiosity, aspirational, practical masterclass.
        """
        sample_tags = "#StartupIndia #BusinessCaseStudy #Entrepreneurship #BusinessIdeas #WealthBuilding #MarketingStrategy #FounderPlaybook"

    prompt = f"""
    You are an elite Instagram Reels Viral Content Strategist & Growth Hacker who has scaled multiple pages to 10M+ reach.
    Listen to this audio track very carefully. The speaker is talking in Hindi / Hinglish / English.
    The original creator/speaker is @{creator_username}.

    {category_context}

    YOUR MISSION: Craft a viral Instagram Reel metadata package designed to maximize:
    1. Watch Time & Retention (Open loops & scroll-stopping hook)
    2. Instagram Search Engine Optimization (SEO) (Weaving in high-search-intent keywords in the first 2 lines)
    3. Saves & Shares (Actionable structured breakdown that viewers must save)
    4. Comment Velocity (Polarizing or discussion-provoking closing question)

    STRICT JSON FIELD INSTRUCTIONS:

    1. "hook_pill":
       - 3 to 4 words ONLY (ALL CAPS or Title Case).
       - Extreme high-contrast curiosity badge for the top sticker (e.g. "₹82L REVENUE FORMULA", "DON'T START BEFORE THIS", "SUPREME COURT VERDICT", "3 NO-CODE AI TOOLS").

    2. "main_title":
       - Exactly 2 lines separated by \\n (maximum 8-10 words total).
       - Must contain the highest-volume search phrase spoken by the speaker in Title Case.
       - Ultra-specific (Never use vague titles like "Important Life Lesson").

    3. "sub_quote":
       - An authentic, memorable punchline actually spoken by the speaker in the audio, enclosed in double quotes.

    4. "caption":
       - Write a brutal, viral, high-converting Instagram SEO caption strictly structured as:
         
         [1-Sentence Scroll-Stopping Hook containing high-volume search keywords and an open loop] 👇
         
         📌 The Core Breakdown:
         • [Actionable Point 1 - Specific fact, number, or business/policy mechanic from audio]
         • [Actionable Point 2 - The exact execution step or core insight explained]
         • [Actionable Point 3 - The outcome, consequence, or strategic takeaway]
         
         💡 Key Takeaway: [1 punchy contrarian sentence or golden rule from the speaker]
         
         Save this reel for later 📌 | What are your thoughts on this? Tell us below 👇
         
         Credits & Speaker: @{creator_username}
         
         {sample_tags}

    Return strict valid JSON ONLY. No markdown quotes, no backticks, no commentary:
    {{
        "hook_pill": "...",
        "main_title": "Line 1\\nLine 2",
        "sub_quote": "\\"Spoken quote\\"",
        "caption": "Full formatted viral SEO caption text"
    }}
    """

    data = None
    if audio_path and os.path.exists(audio_path):
        print(f"Passing speech audio ({os.path.getsize(audio_path)} bytes) to Gemini AI for Viral SEO analysis ({category.upper()})...")
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type="audio/mp3"
        )

        for model_name in ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3-flash-preview"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[audio_part, prompt]
                )
                text = response.text.strip().replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                print(f"Gemini successfully analyzed spoken audio with {model_name} (Viral SEO formatted)!")
                break
            except Exception as e:
                print(f"Audio analysis error with {model_name}:", e)
                continue

        if os.path.exists(audio_path):
            try: os.remove(audio_path)
            except: pass

    if not data:
        # Dynamic fallback based on creator username so videos never share identical duplicate titles
        if category == "politics":
            data = {
                "hook_pill": "Desh Ki Awaz",
                "main_title": f"Badi Baat Deshhit Ki\nBy @{creator_username}",
                "sub_quote": f'"Rashtrahit aur loktantra me har nagrik ka jagruk hona zaroori hai."',
                "caption": (
                    f"Important perspectives and national discussion shared by @{creator_username} 👇\n\n"
                    f"📌 Key Highlights:\n"
                    f"• Civic Awareness: Understanding key issues shaping the nation today.\n"
                    f"• Public Interest: Why informed citizens drive positive reform.\n"
                    f"• National Perspective: Analyzing policies and their ground reality.\n\n"
                    f"💡 Core Takeaway: A vibrant democracy thrives on dialogue and awareness.\n\n"
                    f"Save this reel for later 📌 | What are your thoughts on this? Tell us below 👇\n\n"
                    f"Credits & Speaker: @{creator_username}\n\n"
                    f"{sample_tags}"
                )
            }
        else:
            data = {
                "hook_pill": "Founder Insights",
                "main_title": f"The Strategic Playbook\nFrom @{creator_username}",
                "sub_quote": f'"Execution and customer focus beat theory every single day."',
                "caption": (
                    f"Key business and entrepreneurial breakdown from @{creator_username} 👇\n\n"
                    f"📌 Key Breakdown:\n"
                    f"• Strategic Growth: Building scalable systems with strong unit economics.\n"
                    f"• Practical Execution: Turning market insights into high-margin products.\n"
                    f"• Long-Term Value: Cultivating customer trust and sustainable advantage.\n\n"
                    f"💡 Core Takeaway: Real success comes from disciplined execution.\n\n"
                    f"Save this reel for later 📌 | Would you try this strategy? Drop your thoughts below 👇\n\n"
                    f"Credits & Speaker: @{creator_username}\n\n"
                    f"{sample_tags}"
                )
            }

    return data

if __name__ == '__main__':
    print("Speech AI ready.")
