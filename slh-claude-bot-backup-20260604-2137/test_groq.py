import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GROQ_API_KEY')
print('GROQ_API_KEY exists:', bool(key))
if key:
    import groq
    client = groq.Client(api_key=key)
    try:
        chat = client.chat.completions.create(
            messages=[{"role":"user","content":"hi"}],
            model="llama3-8b-8192",
            max_tokens=10
        )
        print("AI OK:", chat.choices[0].message.content)
    except Exception as e:
        print("Error:", e)
