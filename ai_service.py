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
        "-b:a", "32k",
        output_audio_path
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if os.path.exists(output_audio_path):
        return output_audio_path
    return None

def analyze_reel_content(video_file_path, creator_username="creator", category="startup"):
    client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=180.0))
    audio_path = extract_audio_from_video(video_file_path, "reel_speech.mp3")


    category_context = """
    BRAND / CHANNEL: Startup Road • The Founder Mindset (@startup_road).
    NICHE: High-Growth Startups, Business Case Studies, Entrepreneurship, Zero-to-One, Founder Mindset, Revenue Breakdowns.
    SEO KEYWORDS THEME: High-margin business models, founder secrets, scalable startup systems, marketing breakdown, revenue formulas, business case study India, unit economics.
    TONE: Actionable, value-dense, high-curiosity, aspirational, practical masterclass for aspiring founders and business minds.
    """
    sample_tags = "#StartupRoad #FounderMindset #StartupIndia #BusinessCaseStudy #Entrepreneurship #BusinessIdeas #WealthBuilding #MarketingStrategy"

    prompt = f"""
    You are the Head of Viral Content & Reels Growth for @startup_road (Startup Stories, Founder Mindset & Business Insights).
    Listen to this audio track very carefully. The speaker is talking in Hindi, Hinglish, or English.
    The original creator/speaker is @{creator_username}.

    {category_context}

    YOUR MISSION: Craft a viral Instagram Reel metadata package based STRICTLY on what the speaker says:
    1. Watch Time & Retention: Extract the single most surprising fact, number, or business lesson in the audio for the hook.
    2. Instagram Search Engine Optimization (SEO): Weave high-search-intent keywords in the first 2 lines.
    3. Saves & Shares: Provide an actionable 3-point structured breakdown of the speaker's advice that viewers MUST save.
    4. Comment Velocity: Ask a sharp, discussion-provoking question at the end.

    STRICT JSON FIELD INSTRUCTIONS:

    1. "hook_pill":
       - 3 to 4 words ONLY (ALL CAPS).
       - High-contrast curiosity sticker badge (e.g. "₹82L REVENUE FORMULA", "ZERO TO 1 PLAYBOOK", "AVOID THIS MISTAKE", "SCALING TO 10X").

    2. "main_title":
       - Exactly 2 lines separated by \\n (maximum 7-9 words total).
       - Must capture the core idea of what is spoken in the audio in Title Case.
       - Ultra-specific to the topic spoken (DO NOT use generic titles like "Important Business Lesson").

    3. "sub_quote":
       - An authentic, powerful punchline actually spoken by the speaker in the audio, in double quotes.

    4. "caption":
       - Write a brutal, viral, high-converting Instagram SEO caption strictly structured as:
         
         [1-Sentence Scroll-Stopping Hook about the exact business topic in audio] 👇
         
         📌 The Founder Breakdown:
         • [Point 1: Specific execution step or mechanism explained by speaker]
         • [Point 2: Core business model, unit economics, or market insight]
         • [Point 3: Key takeaway or strategic advantage]
         
         💡 Golden Rule: [1 punchy quote or golden takeaway from the audio]
         
         Save this reel for later 📌 | What are your thoughts on this strategy? Drop them below 👇
         
         Credits & Speaker: @{creator_username}
         Follow @startup_road for daily founder playbooks & business insights.
         
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
        print(f"Passing speech audio ({os.path.getsize(audio_path)} bytes) to Gemini AI via Google Files API for @startup_road Viral SEO analysis...", flush=True)
        uploaded_file = None
        try:
            # Use Google GenAI Files API to prevent socket write timeouts on Windows
            uploaded_file = client.files.upload(file=audio_path)
            
            for model_name in ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[uploaded_file, prompt]
                    )
                    text = response.text.strip().replace("```json", "").replace("```", "").strip()
                    data = json.loads(text)
                    print(f"✅ Gemini successfully analyzed audio with {model_name} (Custom SEO formatted for @startup_road)!", flush=True)
                    break
                except Exception as e:
                    print(f"Audio analysis note with {model_name}: {e}", flush=True)
                    continue
        except Exception as e_upload:
            print(f"Google Files API upload error: {e_upload}, trying direct bytes fallback...", flush=True)
            if audio_path and os.path.exists(audio_path):
                try:
                    with open(audio_path, "rb") as f:
                        audio_bytes = f.read()
                    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp3")
                    for model_name in ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"]:
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=[audio_part, prompt]
                            )
                            text = response.text.strip().replace("```json", "").replace("```", "").strip()
                            data = json.loads(text)
                            print(f"✅ Gemini successfully analyzed audio via direct bytes with {model_name}!", flush=True)
                            break
                        except Exception as e_inner:
                            print(f"Direct bytes note with {model_name}: {e_inner}", flush=True)
                except Exception as e_direct:
                    print(f"Direct bytes fallback error: {e_direct}", flush=True)
        finally:
            if uploaded_file and hasattr(uploaded_file, "name"):
                try: client.files.delete(name=uploaded_file.name)
                except: pass
            if os.path.exists(audio_path):
                try: os.remove(audio_path)
                except: pass


    if not data:
        # Dynamic fallback tailored to creator and @startup_road
        data = {
            "hook_pill": "FOUNDER PLAYBOOK",
            "main_title": f"The Growth Blueprint\nFrom @{creator_username}",
            "sub_quote": f'"Disciplined execution beats raw talent every single day."',
            "caption": (
                f"High-impact business insights from @{creator_username} 👇\n\n"
                f"📌 The Founder Breakdown:\n"
                f"• Strategic Growth: Building scalable systems with strong unit economics.\n"
                f"• Practical Execution: Turning market insights into high-margin products.\n"
                f"• Long-Term Value: Cultivating customer trust and sustainable advantage.\n\n"
                f"💡 Golden Rule: Focus on retention and value creation first.\n\n"
                f"Save this reel for later 📌 | What are your thoughts on this strategy? Drop them below 👇\n\n"
                f"Credits & Speaker: @{creator_username}\n"
                f"Follow @startup_road for daily founder playbooks & business insights.\n\n"
                f"{sample_tags}"
            )
        }

    return data

if __name__ == '__main__':
    print("Speech AI ready.")
