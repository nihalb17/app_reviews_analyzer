"""Simple test to verify Gemini API connectivity"""
import os
from dotenv import load_dotenv

load_dotenv(".env")

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {api_key[:10]}..." if api_key else "No API key found")

try:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    print("Testing simple prompt...")
    response = model.generate_content("Say 'Hello World' and nothing else.")
    print(f"Response: {response.text}")
    print("✓ Gemini API is working!")
    
except Exception as e:
    print(f"✗ Error: {e}")
