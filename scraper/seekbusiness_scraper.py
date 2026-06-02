"""SeekBusiness.com.au scraper for businesses for sale."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Optional
import re
import time
import json

from models.business import BusinessListing, ScrapeResult


class SeekBusinessScraper:
    """Scrapes business-for-sale listings from SeekBusiness.com.au."""
    
    BASE_URL = "https://www.seekbusiness.com.au"
    SEARCH_URL = "https://www.seekbusiness.com.au/businesses-for-sale"
    
    # Business categories to track for AI analysis
    BUSINESS_CATEGORIES = [
        'retail', 'service', 'manufacturing', 'technology', 
        'healthcare', 'education', 'food', 'hospitality',
        'transport', 'logistics', 'automotive', 'construction',
        'professional', 'personal', 'cleaning', 'maintenance',
        'accommodation', 'tourism', 'leisure', 'franchise'
    ]
    
    def __init__(self, delay: float = 1.5):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.delay = delay
        self.errors = []
    
    def scrape_listings(
        self,
        days_back: int = 7,
        max_pages: int = 10,
        category: str = "transport",
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> ScrapeResult:
        """
        Scrape business listings from last N days.
        
        Args:
            days_back: Number of days to look back
            max_pages: Max pages to scrape
            category: Business category filter
            min_price: Minimum price filter
            max_price: Maximum price filter
        """
        listings = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            for page in range(1, max_pages + 1):
                status_msg = f"Scraping page {page}..."
                print(status_msg)
                
                page_listings, has_more = self._scrape_page(
                    page=page,
                    cutoff_date=cutoff_date,
                    days_back=days_back,
                    category=category,
                    min_price=min_price,
                    max_price=max_price
                )
                
                listings.extend(page_listings)
                
                if not has_more:
                    print(f"  Found {len(page_listings)} listings, stopping (reached date cutoff)")
                    break
                
                if page < max_pages:
                    time.sleep(self.delay)
                
        except Exception as e:
            self.errors.append(f"Scraping failed: {str(e)}")
            import traceback
            self.errors.append(traceback.format_exc())
        
        # If no listings found and we have errors, try fallback to mock data for demo
        if not listings and self.errors:
            print("⚠️ Live scraping failed, using mock data for demonstration")
            listings = self._generate_mock_listings(days_back, min_price, max_price)
            self.errors.append("NOTE: Using mock data for demonstration (live site requires JavaScript)")
        
        return ScrapeResult(
            listings=listings,
            total_found=len(listings),
            scraped_at=datetime.now(),
            errors=self.errors
        )
    
    def _generate_mock_listings(
        self, 
        days_back: int = 7,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> List[BusinessListing]:
        """Generate realistic mock data for demonstration."""
        import random
        
        business_templates = [
            ("Cafe & Coffee Shop", "Food/Hospitality", 120000),
            ("Transport Company", "Transport/Logistics", 450000),
            ("Auto Repair Business", "Automotive", 180000),
            ("Online Retail Store", "Retail", 95000),
            ("Cleaning Franchise", "Services", 85000),
            ("Tech Startup", "Technology", 380000),
            ("Medical Practice", "Healthcare", 520000),
            ("Construction Business", "Construction", 320000),
            ("Mobile Car Detailing", "Automotive", 75000),
            ("Courier Service", "Transport/Logistics", 280000),
            ("Restaurant", "Food/Hospitality", 195000),
            ("Gym & Fitness Center", "Health/Fitness", 420000),
            ("Real Estate Agency", "Professional Services", 250000),
            ("Landscaping Business", "Services", 145000),
            ("Import/Export Business", "Trade", 380000),
        ]
        
        locations = [
            ("Sydney", "NSW"), ("Melbourne", "VIC"), ("Brisbane", "QLD"),
            ("Perth", "WA"), ("Adelaide", "SA"), ("Gold Coast", "QLD"),
            ("Newcastle", "NSW"), ("Canberra", "ACT"), ("Wollongong", "NSW"),
        ]
        
        listings = []
        for i, (biz_name, category, base_price) in enumerate(business_templates[:12]):
            city, state = locations[i % len(locations)]
            
            # Vary the price slightly
            price = int(base_price * random.uniform(0.8, 1.3))
            
            # Apply price filters
            if min_price and price < min_price:
                continue
            if max_price and price > max_price:
                continue
            
            # Days listed (last 7 days)
            days_listed = random.randint(0, min(days_back, 7))
            
            listing = BusinessListing(
                dealer_id=f"MOCK{i+1000}",
                name=f"{biz_name} - {city} Area",
                location=city,
                state=state,
                inventory_count=price,
                price=price,
                days_listed=days_listed,
                category=category,
                description=f"Established {biz_name.lower()} with strong customer base in {city}. Great opportunity for growth and expansion.",
                url=f"{self.BASE_URL}/listing/mock-{i}"
            )
            listings.append(listing)
        
        return listings
    
    def _scrape_page(
        self,
        page: int,
        cutoff_date: datetime,
        days_back: int,
        category: str,
        min_price: Optional[int],
        max_price: Optional[int]
    ) -> tuple[List[BusinessListing], bool]:
        """Scrape a single page of business listings."""
        listings = []
        
        try:
            # Build search URL with filters
            params = {
                'page': page,
            }
            
            # Add category if specified
            if category:
                params['search-code'] = category
            
            # Add price filters
            if min_price:
                params['price-from'] = min_price
            if max_price:
                params['price-to'] = max_price
            
            response = self.session.get(
                self.SEARCH_URL, 
                params=params, 
                timeout=30,
                allow_redirects=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find listing cards using exact selectors from inspected HTML
            listing_cards = soup.find_all('article', {'data-testid': 'search-listings-result-item'})
            
            if not listing_cards:
                # Fallback: try article tags
                listing_cards = soup.find_all('article')
            
            print(f"  Found {len(listing_cards)} cards on page {page}")
            
            has_more = len(listing_cards) > 0
            
            for card in listing_cards:
                try:
                    listing = self._parse_listing_card(card)
                    
                    if listing:
                        # Check if it's recent enough
                        if listing.days_listed <= days_back or listing.days_listed == 0:
                            listings.append(listing)
                        else:
                            # Too old, signal to stop
                            has_more = False
                            
                except Exception as e:
                    self.errors.append(f"Card parse error: {str(e)}")
                    continue
            
            return listings, has_more
            
        except requests.RequestException as e:
            self.errors.append(f"Request failed on page {page}: {str(e)}")
            return listings, False
        except Exception as e:
            self.errors.append(f"Unexpected error on page {page}: {str(e)}")
            return listings, False
    
    def _parse_listing_card(self, card) -> Optional[BusinessListing]:
        """Extract data from a business listing card."""
        try:
            # Get all text content for searching
            full_text = card.get_text(separator=' ', strip=True)
            
            # Title/Business name - from h2 > a or from data-testid
            title_elem = card.find('h2')
            if title_elem:
                link = title_elem.find('a')
                title = link.get_text(strip=True) if link else title_elem.get_text(strip=True)
            else:
                # Fallback to business name span
                name_elem = card.find('span', {'data-testid': 'serp-listing-business-name'})
                title = name_elem.get_text(strip=True) if name_elem else "Unknown Business"
            
            # Generate ID from URL or title
            url_elem = card.find('a', href=re.compile('/business-listing/'))
            url = url_elem.get('href') if url_elem else ""
            if url.startswith('/'):
                url = f"{self.BASE_URL}{url}"
            
            # Extract ID from URL
            listing_id = ""
            if url:
                match = re.search(r'/([^/]+)/(\d+)$', url)
                if match:
                    listing_id = f"SEEK_{match.group(2)}"
                else:
                    listing_id = self._generate_id(title)
            else:
                listing_id = self._generate_id(title)
            
            # Location - from breadcrumbs
            location_elem = card.find('span', {'data-testid': 'search-result-item-location-breadcrumbs'})
            location, state = self._extract_location_from_breadcrumbs(location_elem)
            
            # Price - look for pattern in spans
            price = self._extract_price_from_spans(card)
            
            # Listing date / days ago - seek doesn't show this clearly, default to 0
            days_listed = 0  # Will need to check listing page for actual date
            
            # Category - from industry breadcrumbs
            category_elem = card.find('span', {'data-testid': 'search-result-item-industry-breadcrumbs'})
            category = self._extract_category_from_breadcrumbs(category_elem)
            
            # Description - from text spans
            description = self._extract_description(card)
            
            return BusinessListing(
                dealer_id=listing_id,  # Reusing field for listing ID
                name=title,
                location=location,
                state=state,
                inventory_count=price if price else 0,  # Reusing for price
                phone=None,  # Usually not on list page
                days_listed=days_listed,
                url=url,
                description=description,
                category=category
            )
            
        except Exception as e:
            self.errors.append(f"Parse error: {str(e)}")
            return None
    
    def _extract_location(self, card, text: str) -> str:
        """Extract location from listing."""
        # Common patterns: "Sydney NSW", "Melbourne VIC 3000"
        patterns = [
            r'([^,\d]+),?\s*(NSW|VIC|QLD|WA|SA|TAS|ACT)',
            r'(Sydney|Melbourne|Brisbane|Perth|Adelaide|Canberra|Darwin|Hobart)(?:\s+-\s+\w+)?',
            r'(Gold Coast|Newcastle|Wollongong|Geelong|Cairns|Townsville)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        
        return "Location unknown"
    
    def _extract_state(self, text: str) -> str:
        """Extract state abbreviation."""
        states = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT']
        for state in states:
            if re.search(r'\b' + state + r'\b', text, re.I):
                return state.upper()
        return "Unknown"
    
    def _extract_price(self, text: str) -> Optional[int]:
        """Extract asking price from listing text."""
        # Look for patterns like "$150,000", "$1.2m", "Price: $450000"
        patterns = [
            r'\$([\d,\.]+)(?:\s*m(?:illion)?)?(?:\s*\+\s*SAV)?',
            r'price[:\s]*\$?([\d,\.]+)',
            r'([\d,\.]+)\s*(?:million|m)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                price_str = match.group(1).replace(',', '').replace('.', '')
                try:
                    price = int(price_str)
                    # If it's too small, might be in millions
                    if price < 1000 and 'm' in text.lower():
                        price *= 1000000
                    return price
                except:
                    pass
        
        return None
    
    def _extract_days_listed(self, card, text: str) -> int:
        """Extract how many days ago the listing was posted."""
        # Look for date patterns or "X days ago"
        patterns = [
            r'listed\s+(\d+)\s+days?\s+ago',
            r'(\d+)\s+days?\s+ago',
            r'(\d+)\s+hours?\s+ago',
            r'(\d+)\s+minutes?\s+ago',
            r'listed\s+yesterday',
            r'listed\s+today',
            r'added\s+(\d+)\s+days?\s+ago',
        ]
        
        text_lower = text.lower()
        
        if 'today' in text_lower or 'just now' in text_lower or 'minutes ago' in text_lower or 'hours ago' in text_lower:
            return 0
        if 'yesterday' in text_lower:
            return 1
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    # if the match is hours/minutes it will return 0 due to early checks,
                    # but just in case:
                    return int(match.group(1))
                except:
                    pass
        
        # Check for date format
        date_patterns = [
            r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*',
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',
        ]
        
        return 0  # Default to recent if can't determine
    
    def _extract_url(self, card, title_elem) -> str:
        """Extract listing URL."""
        # Find link in card
        link_elem = (
            card.find('a', href=re.compile('/business-listing/', re.I)) or
            (title_elem if title_elem and title_elem.name == 'a' else None) or
            card.find('a')
        )
        
        if link_elem:
            href = link_elem.get('href', '')
            if href.startswith('/'):
                return f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                return href
        
        return ""
    
    def _extract_category(self, card, text: str) -> str:
        """Extract business category."""
        # Look for category tags or labels
        category_elem = card.find(['span', 'div'], class_=re.compile('category|type|tag', re.I))
        if category_elem:
            return category_elem.get_text(strip=True)
        
        # Infer from keywords
        if 'franchise' in text.lower():
            return 'Franchise'
        elif any(k in text for k in ['transport', 'logistics', 'delivery']):
            return 'Transport/Logistics'
        elif any(k in text for k in ['mechanical', 'auto', 'car']):
            return 'Automotive'
        
        return 'Business'
    
    def _calculate_relevance(self, listing) -> int:
        """Calculate vehicle fleet relevance score (0-100)."""
        text = f"{listing.name} {listing.description or ''}".lower()
        score = 0
        
        # High relevance keywords
        high_keywords = ['fleet', 'trucking', 'transport company', 'logistics', 'delivery service']
        for kw in high_keywords:
            if kw in text:
                score += 30
        
        # Medium relevance
        med_keywords = ['truck', 'van', 'vehicle', 'courier', 'removal', 'rental', 'hire']
        for kw in med_keywords:
            if kw in text:
                score += 15
        
        # Low relevance
        low_keywords = ['car', 'auto', 'mechanical']
        for kw in low_keywords:
            if kw in text:
                score += 5
        
        # Cap at 100
        return min(score, 100)
    
    def _generate_id(self, name: str) -> str:
        """Generate a clean ID from business name."""
        clean = re.sub(r'[^\w\s]', '', name).strip()
        clean = re.sub(r'\s+', '_', clean)
        return clean[:40].upper()
    
    def _extract_location_from_breadcrumbs(self, location_elem) -> tuple[str, str]:
        """Extract location and state from breadcrumbs element."""
        if not location_elem:
            return "Unknown", "Unknown"
        
        # Get all links in breadcrumbs
        links = location_elem.find_all('a')
        if len(links) >= 2:
            # Last link usually has suburb + state
            last_link = links[-1].get_text(strip=True)
            match = re.search(r'([^,]+),\s*(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)', last_link, re.I)
            if match:
                return match.group(1).strip(), match.group(2).upper()
        
        # Fallback: search text
        text = location_elem.get_text(strip=True)
        match = re.search(r'([^,]+),\s*(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)', text, re.I)
        if match:
            return match.group(1).strip(), match.group(2).upper()
        
        # Try just state
        states = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT']
        for state in states:
            if state in text.upper():
                return "Unknown", state
        
        return "Unknown", "Unknown"
    
    def _extract_price_from_spans(self, card) -> Optional[int]:
        """Extract price from span elements in card."""
        # Look for spans with $ pattern
        spans = card.find_all('span', class_=re.compile('_1dmkaif'))
        for span in spans:
            text = span.get_text(strip=True)
            # Look for $XXX,XXX pattern
            match = re.search(r'\$([\d,]+(?:\.\d+)?)(?:\s*\+\s*\w+)?', text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return int(float(price_str))
                except:
                    pass
        
        # Fallback: search all text
        text = card.get_text(separator=' ', strip=True)
        match = re.search(r'\$([\d,]+(?:\.\d+)?)', text)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return int(float(price_str))
            except:
                pass
        
        return None
    
    def _extract_category_from_breadcrumbs(self, category_elem) -> str:
        """Extract category from industry breadcrumbs."""
        if not category_elem:
            return "Business"
        
        # Get all links
        links = category_elem.find_all('a')
        if len(links) >= 2:
            # Last link is the most specific category
            return links[-1].get_text(strip=True)
        elif len(links) == 1:
            return links[0].get_text(strip=True)
        
        # Fallback: just get text
        return category_elem.get_text(strip=True).replace('>', '/')
    
    def _extract_description(self, card) -> str:
        """Extract description from card text."""
        # Try to gather larger chunks of text
        full_text = card.get_text(separator=' | ', strip=True)
        parts = full_text.split(' | ')
        desc_candidates = []
        for part in parts:
            if (len(part) > 60 and
                not re.search(r'^\$', part) and
                part not in ['Featured', 'Franchise New', 'Enquire', 'Save', 'more\xa0››']):
                desc_candidates.append(part)

        if desc_candidates:
            # The longest candidate is likely the description
            longest = max(desc_candidates, key=len)
            return longest[:500].replace('more\xa0››', '').strip()
            
        return ""
