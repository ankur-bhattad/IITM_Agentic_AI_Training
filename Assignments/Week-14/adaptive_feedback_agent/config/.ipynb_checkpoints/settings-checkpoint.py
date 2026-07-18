import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY. Please set it in your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)
