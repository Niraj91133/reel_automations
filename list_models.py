import google.generativeai as genai

api_key = "AQ.Ab8RN6IEkFyg8_cpZqPGg8_f8zP01KggxmR9ON9odxohMjoG6w"
genai.configure(api_key=api_key)
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
