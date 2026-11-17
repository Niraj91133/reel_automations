import os
import sys
import json
import re
import uuid
import subprocess
from google import genai
from google.genai import types
from core.niche_prompts import get_niche_prompt

# Primary lightning-fast models with fallback
WORKING_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3-flash-preview"
]

def extract_audio_isolated(video_path, output_dir):
    """Extracts lightweight mono 16kHz audio with a unique UUID to prevent collision."""
    unique_id = uuid.uuid4().hex[:8]
    output_audio_path = os.path.join(output_dir, f"audio_{unique_id}.mp3")
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
    """Safely extracts clean JSON from model response text."""
    if not raw_text:
        return ""
    m = re.search(r'(\{.*\})', raw_text, re.DOTALL)
    if m:
        return m.group(1).strip()
    clean = raw_text.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    elif clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    return clean.strip()

def analyze_reel_for_channel(video_file_path, channel_config, creator_username="creator", original_description="", original_title=""):
    """
    Main Multi-Tenant AI synthesis pipeline.
    Uses the channel's dedicated Gemini Key and Niche Prompt.
    """
    creds = channel_config.get("credentials", {})
    api_key = creds.get("gemini_api_key")
    category = channel_config.get("category", "startup")
    workspace_dir = channel_config.get("runtime", {}).get("workspace_dir", ".")
    
    niche_info = get_niche_prompt(category)
    sys_instruction = niche_info["system_instruction"]

    # Default fallback data
    fallback_data = {
        "hook_pill": niche_info["default_pill"],
        "main_title": niche_info["default_title"],
        "sub_quote": niche_info["default_quote"],
        "caption": f"Valuable insights from @{creator_username}\n\nCredits: @{creator_username}"
    }

    if not api_key or api_key.startswith("YOUR_GEMINI") or api_key.startswith("$"):
        api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key or api_key.startswith("YOUR_GEMINI") or api_key.startswith("$"):
        print(f"⚠️ [AI Engine] No valid Gemini API key configured for {channel_config.get('channel_id')}. Using fallback metadata.")
        return fallback_data

    # Extract isolated audio
    audio_path = extract_audio_isolated(video_file_path, workspace_dir)
    if not audio_path or not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
        print(f"🛑 [Audio Guard] REJECTED reel for {channel_config.get('channel_id')}: Video has no valid audio stream.")
        return {"rejected": True, "reason": "no_audio_stream"}

    client = None
    uploaded_file = None

    try:
        client = genai.Client(api_key=api_key)
        
        # Prepare context prompt
        context_text = f"Creator: @{creator_username}\n"
        if original_title:
            context_text += f"Original Title: {original_title}\n"
        if original_description:
            context_text += f"Description: {original_description}\n"

        prompt = f"""
{sys_instruction}

Context Metadata:
{context_text}

🎯 CRITICAL AUDIT & TRANSCRIPTION DIRECTIVE (ZERO GENERIC FILLER):
1. Listen carefully to the entire audio track. Identify the EXACT business model, machine, physical product, raw material, or service being taught (e.g., shipping container cabins, glass recycling cullet, tire puncture machine, dumper truck logistics, petrol pump franchise, tape rewinding machine, amul franchise, vanilla farming).
2. Extract the EXACT figures and unit economics mentioned in the audio: investment amounts (e.g. ₹50,000), monthly/daily profits (e.g. ₹1 Lakh/month, ₹20,000/day), profit margins (e.g. 200% to 500%), and operational steps.
3. Ground the Title, Hook Pill, Sub Quote, and Caption 100% in this video's specific business and numbers!
   - NO generic entrepreneurship cliches (NEVER write "build systems that operate without you", "turn passion into profit", "hustle hard").
   - Title MUST name the specific business or numbers (e.g. "START THIS BUSINESS WITH JUST ₹50,000 INVESTMENT", "OWN CONTAINERS EARN PASSIVE RENT", "START A BUSINESS WITH 200% TO 500% PROFIT MARGIN").
   - Hook Pill MUST be 2-4 uppercase words naming the killer angle (e.g. "1 LAKH/MO RENT", "ZERO MARKETING COST", "ZERO COMPETITION BUSINESS", "12-TYRE DUMPER PROFIT").
   - Caption MUST use the 5-Part Founder Breakdown detailing the actual setup, unit economics, and steps from the audio.
   - Comment CTA MUST use a specific 1-word keyword matching this product (e.g. Comment "CONTAINER", Comment "GLASS", Comment "MACHINE").
4. ALL OUTPUT MUST BE 100% IN ENGLISH SCRIPT. NEVER USE DEVANAGARI HINDI SCRIPT (हिंदी लिपि).
"""

        contents = []
        if audio_path and os.path.exists(audio_path):
            try:
                uploaded_file = client.files.upload(file=audio_path)
                contents.append(uploaded_file)
            except Exception as e_up:
                print(f"Audio upload warning for {channel_config.get('channel_id')}: {e_up}")

        contents.append(prompt)

        # Try models in order
        for model_name in WORKING_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=800,
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    clean_txt = clean_json_response(response.text)
                    data = json.loads(clean_txt)
                    if "main_title" in data and "hook_pill" in data:
                        # Language, Speech & Niche Gatekeeper
                        is_hindi = data.get("is_hindi", True)
                        has_speech = data.get("has_speech", True)
                        is_niche_match = data.get("is_niche_match", True)
                        if is_hindi is False:
                            print(f"🛑 [Language Guard] REJECTED reel for {channel_config.get('channel_id')}: Audio is NOT in Hindi.")
                            return {"rejected": True, "reason": "non_hindi_audio"}
                        if has_speech is False:
                            print(f"🛑 [Audio Guard] REJECTED reel for {channel_config.get('channel_id')}: Audio has NO clear human speech (only music/silence).")
                            return {"rejected": True, "reason": "no_speech_music_only"}
                        if is_niche_match is False:
                            print(f"🛑 [Niche Guard] REJECTED reel for {channel_config.get('channel_id')}: Content does NOT match channel niche.")
                            return {"rejected": True, "reason": "wrong_niche"}

                        # Meta Policy Compliance Validation
                        from core.compliance_guard import is_reel_compliant
                        is_safe, reason = is_reel_compliant(data.get("main_title", ""), data.get("hook_pill", ""), data.get("caption", ""))
                        if not is_safe:
                            print(f"🛑 [Compliance Guard REJECTED] Unsafe content ({reason}). Trying next candidate...")
                            return {"rejected": True, "reason": f"compliance_{reason}"}

                        # 🛡️ UNBREAKABLE CHANNEL BRAND INTEGRITY AUDIT (ALL CHANNELS)
                        from core.brand_security_guard import audit_and_enforce_channel_brand
                        ch_id = channel_config.get("channel_id", "")
                        is_brand_ok, brand_reason, sanitized_data = audit_and_enforce_channel_brand(ch_id, data, creator_username)
                        if not is_brand_ok:
                            print(f"🛑 [Channel Brand Guard REJECTED] Violation: {brand_reason}. Trying next candidate...")
                            return {"rejected": True, "reason": brand_reason}
                        data = sanitized_data

                        return data
            except Exception as e_model:
                print(f"Model {model_name} attempt failed: {e_model}")
                continue

    except Exception as e_all:
        print(f"AI synthesis error for {channel_config.get('channel_id')}: {e_all}")
    finally:
        # Clean up uploaded audio on Google server
        if client and uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
            except:
                pass
        # Clean up local audio file
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass

    return fallback_data
