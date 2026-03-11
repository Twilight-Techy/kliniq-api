import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def test_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}" if api_key else "No API Key found")
    
    if not api_key:
        return

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello, are you working?"
        )
        print("Response received successfully!")
        print(f"Text: {response.text}")
    except Exception as e:
        print(f"Gemini Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini()
