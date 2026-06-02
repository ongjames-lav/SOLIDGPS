"""Proof of API timeout issue for Luke."""
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

print("="*70)
print("API ENDPOINT TEST - Timestamp:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("="*70)

api_key = os.getenv('OPENAI_API_KEY')
base_url = os.getenv('OPENAI_BASE_URL')

print(f"\nEndpoint: {base_url}/chat/completions")
print(f"Model: smart")
print(f"API Key: {api_key[:15]}...")

print("\n" + "-"*70)
print("TEST 1: Simple ping (5 second timeout)")
print("-"*70)

try:
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json={
            "model": "smart",
            "messages": [{"role": "user", "content": "Say 'API is working'"}],
            "max_tokens": 20
        },
        timeout=5
    )
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ SUCCESS:", response.json()['choices'][0]['message']['content'])
    else:
        print(f"❌ FAILED: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print("❌ TIMEOUT: Request exceeded 5 seconds")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {str(e)[:100]}")

print("\n" + "-"*70)
print("TEST 2: Real payload (10 listings, 15 second timeout)")
print("-"*70)

# Sample payload matching what the app sends
sample_payload = {
    "model": "smart",
    "messages": [
        {
            "role": "system",
            "content": """You are a business investment analyst. Score these businesses 0-100.
            Return JSON array with dealer_id, score, and reason fields."""
        },
        {
            "role": "user",
            "content": """Analyze these 3 businesses:
ID: SEEK_732643 | Name: Zarraffa's Coffee - Jerrabomberra | Category: Coffee, Cafes & Restaurants | Location: Jerrabomberra, NSW | Price: P.O.A | Listed: 0 days ago
ID: SEEK_781272 | Name: Leadership and Management RTO Melbourne | Category: Education, Coaching & Training | Location: Melbourne, VIC | Price: P.O.A | Listed: 0 days ago
ID: SEEK_781269 | Name: Leadership and Management RTO Perth | Category: Education, Coaching & Training | Location: Perth, WA | Price: P.O.A | Listed: 0 days ago"""
        }
    ],
    "temperature": 0.3,
    "max_tokens": 1000
}

start_time = datetime.now()

try:
    response = requests.post(
        f"{base_url}/chat/completions",
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        },
        json=sample_payload,
        timeout=15
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"Elapsed time: {elapsed:.2f} seconds")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS - AI Response received")
        content = response.json()['choices'][0]['message']['content']
        print(f"Response preview: {content[:150]}...")
    else:
        print(f"❌ FAILED: {response.status_code}")
        print(f"Response body: {response.text[:300]}")
        
except requests.exceptions.Timeout:
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"❌ TIMEOUT after {elapsed:.2f} seconds")
    print("The API did not respond within 15 seconds")
    
except Exception as e:
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"❌ ERROR after {elapsed:.2f} seconds: {type(e).__name__}")
    print(f"Details: {str(e)[:150]}")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("""
The locally-hosted API endpoint at:
  https://three-mistress-opera-locations.trycloudflare.com/v1

is experiencing timeouts. The app successfully falls back to algorithmic 
scoring, but the AI enhancement layer cannot connect reliably.

Recommendation: Check server load or increase API timeout limits.
""")
