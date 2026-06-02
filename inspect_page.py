"""Diagnostic script to inspect Seek Business page structure."""
import requests
from bs4 import BeautifulSoup
import sys

def inspect_seek_business():
    """Download and analyze the page structure."""
    url = "https://www.seekbusiness.com.au/businesses-for-sale"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"Fetching {url}...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save HTML for inspection
        with open('page_sample.html', 'w', encoding='utf-8') as f:
            f.write(response.text[:50000])  # First 50KB
        print("✅ Saved page_sample.html (first 50KB)")
        
        # Find potential listing containers
        print("\n🔍 Analyzing page structure...\n")
        
        # Look for article tags
        articles = soup.find_all('article')
        print(f"Found {len(articles)} <article> tags")
        if articles:
            print(f"  First article classes: {articles[0].get('class', 'NO CLASS')}")
            print(f"  First article data attributes: {[k for k in articles[0].attrs.keys() if k.startswith('data')]}")
        
        # Look for divs with listing-related classes
        listing_divs = soup.find_all('div', class_=lambda x: x and any(kw in ' '.join(x).lower() for kw in ['listing', 'result', 'card', 'item', 'search']))
        print(f"\nFound {len(listing_divs)} divs with listing-related classes")
        if listing_divs[:3]:
            for i, div in enumerate(listing_divs[:3]):
                print(f"  Div {i+1} classes: {div.get('class')}")
        
        # Look for data-testid attributes
        testid_elements = soup.find_all(attrs={"data-testid": True})
        print(f"\nFound {len(testid_elements)} elements with data-testid")
        testid_values = set()
        for el in testid_elements[:20]:
            testid_values.add(el.get('data-testid'))
        if testid_values:
            print(f"  Sample testids: {list(testid_values)[:10]}")
        
        # Look for h3/h2 titles
        titles = soup.find_all(['h3', 'h2'])
        print(f"\nFound {len(titles)} h2/h3 tags (potential titles)")
        if titles[:5]:
            for i, t in enumerate(titles[:5]):
                text = t.get_text(strip=True)[:60]
                parent_classes = t.parent.get('class', 'NO CLASS') if t.parent else 'NO PARENT'
                print(f"  Title {i+1}: '{text}...' (parent: {parent_classes})")
        
        # Look for price patterns
        price_patterns = ['$']
        print(f"\n💰 Looking for price indicators...")
        text_content = soup.get_text()
        price_count = sum(1 for p in price_patterns if p in text_content)
        print(f"  Found '$' symbol {text_count} times")
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print("Check page_sample.html in your editor for full HTML structure")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(inspect_seek_business())
