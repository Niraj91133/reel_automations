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

def analyze_reel_content(video_file_path, creator_username="creator"):
    client = genai.Client(api_key=GEMINI_API_KEY)
    audio_path = extract_audio_from_video(video_file_path, "reel_speech.mp3")

    prompt = f"""
    You are an expert Instagram reels transcriptionist and content editor.
    Listen to this audio track very carefully. The speaker is talking in Hindi / Hinglish / English.
    The original creator/speaker is @{creator_username}.

    CRITICAL INSTRUCTIONS:
    1. Understand the EXACT TOPIC and STORY the speaker is talking about in this specific audio.
    2. Extract the core insight they are explaining.
    3. Output must be in strict valid JSON format:
    {{
        "hook_pill": "3-4 words direct punchy hook in English/Hinglish summarizing their specific point",
        "main_title": "2-line headline in Title Case summarizing what the speaker actually explained (maximum 10 words, use \\n between lines)",
        "sub_quote": "A memorable punchline or quote actually spoken or concluded by the speaker in double quotes",
        "caption": "Short engaging Instagram caption summarizing the speaker's exact 2-3 points\\n\\nCredits & Speaker: @{creator_username}\\n\\n#relevant #hashtags #based #on #topic"
    }}
    Return raw JSON only.
    """

    data = None
    if audio_path and os.path.exists(audio_path):
        print(f"Passing speech audio ({os.path.getsize(audio_path)} bytes) to Gemini AI...")
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type="audio/mp3"
        )

        for model_name in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-pro"]:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[audio_part, prompt]
                )
                text = response.text.strip().replace("```json", "").replace("```", "").strip()
                data = json.loads(text)
                print(f"Gemini successfully analyzed the real spoken audio with {model_name}!")
                break
            except Exception as e:
                print(f"Audio analysis error with {model_name}:", e)
                continue

        if os.path.exists(audio_path):
            os.remove(audio_path)

    if not data:
        data = {
            "hook_pill": "Watch Till The End",
            "main_title": "Valuable Lesson You Need\nTo Hear Today",
            "sub_quote": '"True knowledge comes from relentless practice."',
            "caption": f"Great insights by @{creator_username}!\n\nCredits: @{creator_username}\n\n#reels #learning #growth"
        }

    return data

if __name__ == '__main__':
    print("Speech AI ready.")
