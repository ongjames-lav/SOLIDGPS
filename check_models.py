"""Check available models on the LiteLLM endpoint."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_BASE_URL')

print(f"Base URL: {base_url}")
print(f"API Key: {api_key[:15]}...")
print("\n" + "="*60)

# Try to get available models
try:
    response = requests.get(
        f"{base_url}/models",
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Available Models:")
        if 'data' in data:
            for model in data['data']:
                print(f"  - {model.get('id', 'unknown')}")
        else:
            print(f"  Response: {data}")
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

# Also try a simple chat completion test with different model names
print("\n" + "="*60)
print("Testing common model names...")

test_models = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4o",
    "claude-3-haiku",
    "claude-3-sonnet",
    "claude-3-opus"
]

for model in test_models:
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Say 'test'"}],
                "max_tokens": 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"  ✅ {model}: WORKING")
        else:
            error = response.json().get('error', {}).get('message', 'Unknown error')
            print(f"  ❌ {model}: {error[:60]}")
            
    except Exception as e:
        print(f"  ❌ {model}: {str(e)[:60]}")
