import os
from dotenv import load_dotenv

# Force load .env file
load_dotenv(dotenv_path=".env", override=True)

# Check if key is loaded
key = os.getenv("GROQ_API_KEY")
print(f"Key found: {key[:10]}..." if key else "ERROR: Key not found!")

from utils.llm import ask_llm
response = ask_llm("Say hello in one sentence!")
print(response)