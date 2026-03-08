"""
Run this script locally to see which Gemini models are available for your API key.
Usage: python check_models.py
"""
import os
from dotenv import load_dotenv
load_dotenv()

import google.genai as genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("Available models:")
for model in client.models.list():
    print(f"  - {model.name}")
