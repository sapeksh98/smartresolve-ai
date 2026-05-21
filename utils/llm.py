from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = None

def get_client():
    global client
    if client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set! Please configure it in the Render dashboard.")
        client = Groq(api_key=api_key)
    return client

def ask_llm(prompt: str) -> str:
    c = get_client()
    response = c.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content