"""Quick test of the API connection."""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("Testing API connection...")
print(f"Base URL: {os.getenv('OPENAI_BASE_URL')}")
print(f"API Key: {os.getenv('OPENAI_API_KEY')[:10]}...")

try:
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL')
    )
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'API connection successful' and nothing else."}
        ],
        max_tokens=20
    )
    
    print(f"\n✅ SUCCESS: {response.choices[0].message.content}")
    print(f"Model used: {response.model}")
    
except Exception as e:
    print(f"\n❌ FAILED: {e}")
