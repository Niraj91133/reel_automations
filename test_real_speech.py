import json
from ai_service import analyze_reel_content

# Test DemeBlbBOG- video audio listening
video_file = "temp_DemeBlbBOG-.mp4"
result = analyze_reel_content(video_file, creator_username="vaidant.jain")
print("==========================================")
print("REAL SPOKEN TOPIC ANALYSIS:")
print(json.dumps(result, indent=2))
print("==========================================")
