"""Script to find the API endpoint used by Seek Business."""
import requests
import json

def test_api_endpoints():
    """Try common API patterns."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json',
        'Referer': 'https://www.seekbusiness.com.au/businesses-for-sale'
    }
    
    # Common API patterns to try
    endpoints = [
        'https://www.seekbusiness.com.au/api/search',
        'https://www.seekbusiness.com.au/api/listings',
        'https://www.seekbusiness.com.au/_next/data/businesses-for-sale.json',
        'https://www.seekbusiness.com.au/businesses-for-sale/api',
    ]
    
    for url in endpoints:
        try:
            print(f"\n🔍 Testing: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"   ✅ JSON Response!")
                    print(f"   Keys: {list(data.keys())[:5]}")
                    
                    # Save if it looks promising
                    with open('api_response.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"   Saved to api_response.json")
                    
                except:
                    print(f"   Not JSON (length: {len(response.text)})")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
