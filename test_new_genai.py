from google import genai

key = "AQ.Ab8RN6Jr6PeTkcHjbHdcXpRsOV-2tkC3UNhNod8kAn-6_4acWw"
client = genai.Client(api_key=key)
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Give a 1-word response: Are you ready?"
)
print("SUCCESS GEMINI 3.8 FLASH! Response:", response.text)
