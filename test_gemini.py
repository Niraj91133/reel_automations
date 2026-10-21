import google.generativeai as genai

api_key = "AQ.Ab8RN6IEkFyg8_cpZqPGg8_f8zP01KggxmR9ON9odxohMjoG6w"
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello! Give a 1-word response: Success or Fail?")
    print("Gemini response:", response.text)
except Exception as e:
    print("Gemini error:", e)
