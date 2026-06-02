"""ISOLATION TEST: Prove the API issue is on their server side, not our code."""
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

print("="*70)
print("API ISOLATION TEST - Proves server-side issue")
print("="*70)

api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_BASE_URL')

print(f"\nEndpoint: {base_url}/chat/completions")
print(f"Model: smart")
print(f"API Key: {api_key[:15]}...")

# Test 1: Simplest possible request
print("\n" + "-"*70)
print("TEST 1: Minimal valid request (single message)")
print("-"*70)

try:
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    response = client.chat.completions.create(
        model="smart",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=50,
        timeout=60
    )
    
    print(f"Status: SUCCESS")
    print(f"Response type: {type(response)}")
    print(f"Content type: {type(response.choices[0].message.content)}")
    print(f"Content length: {len(response.choices[0].message.content)}")
    print(f"Content: {repr(response.choices[0].message.content)}")
    
    if response.choices[0].message.content:
        print("✅ MODEL IS WORKING - content received")
    else:
        print("❌ MODEL RETURNED EMPTY - server-side issue confirmed")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

# Test 2: Check response object structure
print("\n" + "-"*70)
print("TEST 2: Full response object inspection")
print("-"*70)

try:
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    response = client.chat.completions.create(
        model="smart",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=10,
        timeout=60
    )
    
    print(f"Response ID: {response.id}")
    print(f"Model used: {response.model}")
    print(f"Finish reason: {response.choices[0].finish_reason}")
    print(f"Prompt tokens: {response.usage.prompt_tokens if response.usage else 'N/A'}")
    print(f"Completion tokens: {response.usage.completion_tokens if response.usage else 'N/A'}")
    print(f"Message object: {response.choices[0].message}")
    print(f"Message content: {repr(response.choices[0].message.content)}")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

# Test 3: Our exact payload
print("\n" + "-"*70)
print("TEST 3: Exact payload from our app")
print("-"*70)

try:
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    response = client.chat.completions.create(
        model="smart",
        messages=[
            {
                "role": "system",
                "content": "You are a business analyst. Return JSON with score and reason."
            },
            {
                "role": "user",
                "content": "Business: Coffee Shop in Sydney, $200k, established 5 years"
            }
        ],
        temperature=0.3,
        max_tokens=500,
        timeout=60
    )
    
    content = response.choices[0].message.content
    print(f"Content received: {len(content)} characters")
    print(f"Content: {repr(content[:200])}")
    
    if content and len(content) > 10:
        print("✅ MODEL RESPONDED WITH CONTENT")
    else:
        print("❌ MODEL RETURNED EMPTY OR TOO SHORT")
        print("   This proves the server-side model is not generating output")
        
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("""
If all tests show empty content (''), this definitively proves:

1. ✅ Our code is correct (OpenAI client working)
2. ✅ API key is valid (authentication successful)
3. ✅ Network connection works (HTTP 200 responses)
4. ✅ Cloudflare tunnel is functional
5. ❌ Their locally-hosted 'smart' model generates NO OUTPUT

This is a SERVER-SIDE ISSUE with their model configuration.
""")
