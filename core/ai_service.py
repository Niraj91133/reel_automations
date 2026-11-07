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
    "gemini-3-flash-preview",
    "gemini-flash-latest"
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

    if not api_key or api_key.startswith("YOUR_GEMINI"):
        print(f"⚠️ [AI Engine] No valid Gemini API key configured for {channel_config.get('channel_id')}. Using fallback metadata.")
        return fallback_data

    # Extract isolated audio
    audio_path = extract_audio_isolated(video_file_path, workspace_dir)
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

Listen carefully to the audio and extract the most compelling viral hook and punchline.
Ensure output matches the required JSON format exactly.
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
                        max_output_tokens=800
                    )
                )
                if response and response.text:
                    clean_txt = clean_json_response(response.text)
                    data = json.loads(clean_txt)
                    if "main_title" in data and "hook_pill" in data:
                        # Meta Policy Compliance Validation
                        from core.compliance_guard import is_reel_compliant
                        is_safe, reason = is_reel_compliant(data.get("main_title", ""), data.get("hook_pill", ""), data.get("caption", ""))
                        if not is_safe:
                            print(f"🛡️ [Compliance Guard] AI generated unsafe content ({reason}). Reverting to clean fallback.")
                            return fallback_data
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
