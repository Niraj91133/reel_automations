from google import genai

key = "AQ.Ab8RN6Jr6PeTkcHjbHdcXpRsOV-2tkC3UNhNod8kAn-6_4acWw"
client = genai.Client(api_key=key)

for m in ["gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-3-flash-preview", "gemini-pro-latest"]:
    try:
        response = client.models.generate_content(
            model=m,
            contents="Say 'OK'!"
        )
        print(f"Model {m} SUCCESS: {response.text.strip()}")
        break
    except Exception as e:
        print(f"Model {m} failed: {e}")
