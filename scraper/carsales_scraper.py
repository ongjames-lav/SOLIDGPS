"""Carsales.com.au dealer scraper."""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Optional
import re
import time

from models.business import BusinessListing, ScrapeResult


class CarsalesScraper:
    """Scrapes dealer listings from Carsales.com.au."""
    
    BASE_URL = "https://www.carsales.com.au/dealer"
    SEARCH_URL = "https://www.carsales.com.au/dealer/search"
    
    def __init__(self, delay: float = 1.0):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.delay = delay
        self.errors = []
    
    def scrape_dealers(
        self,
        days_back: int = 7,
        max_pages: int = 5,
        min_inventory: int = 5
    ) -> ScrapeResult:
        """
        Scrape dealer listings from last N days.
        
        Args:
            days_back: Number of days to look back
            max_pages: Max pages to scrape (safety limit)
            min_inventory: Minimum inventory to include
        """
        listings = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            for page in range(1, max_pages + 1):
                page_listings, has_more = self._scrape_page(
                    page, cutoff_date, min_inventory
                )
                listings.extend(page_listings)
                
                if not has_more:
                    break
                    
                time.sleep(self.delay)
                
        except Exception as e:
            self.errors.append(f"Scraping failed: {str(e)}")
        
        return ScrapeResult(
            listings=listings,
            total_found=len(listings),
            scraped_at=datetime.now(),
            errors=self.errors
        )
    
    def _scrape_page(
        self, 
        page: int, 
        cutoff_date: datetime,
        min_inventory: int
    ) -> tuple[List[BusinessListing], bool]:
        """Scrape a single page of dealer results."""
        listings = []
        
        try:
            # Construct search URL with pagination
            params = {
                'page': page,
                'sort': 'dateListed',
                'order': 'desc'
            }
            
            response = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find dealer cards - need to inspect actual HTML structure
            dealer_cards = soup.find_all('div', class_=re.compile('dealer|listing', re.I))
            
            if not dealer_cards:
                # Try alternative selectors
                dealer_cards = soup.find_all(['article', 'div'], {'data-testid': re.compile('dealer', re.I)})
            
            has_more = len(dealer_cards) > 0
            
            for card in dealer_cards:
                try:
                    listing = self._parse_dealer_card(card)
                    
                    if listing and listing.days_listed <= 7:
                        if listing.inventory_count >= min_inventory:
                            listings.append(listing)
                    else:
                        # Too old, stop scraping
                        has_more = False
                        break
                        
                except Exception as e:
                    self.errors.append(f"Parse error: {str(e)}")
                    continue
            
            return listings, has_more
            
        except requests.RequestException as e:
            self.errors.append(f"Request failed: {str(e)}")
            return listings, False
    
    def _parse_dealer_card(self, card) -> Optional[BusinessListing]:
        """Extract data from a dealer card element."""
        try:
            # Dealer name
            name_elem = (
                card.find('h3') or 
                card.find('h2') or 
                card.find('a', class_=re.compile('title|name', re.I))
            )
            name = name_elem.get_text(strip=True) if name_elem else "Unknown Dealer"
            
            # Generate dealer ID from name
            dealer_id = self._generate_id(name)
            
            # Location
            location_elem = card.find(text=re.compile(r'(NSW|VIC|QLD|WA|SA|TAS|ACT)', re.I))
            location = "Unknown"
            state = "Unknown"
            
            if location_elem:
                location_text = str(location_elem)
                # Extract location and state
                match = re.search(r'([^,]+),?\s*(NSW|VIC|QLD|WA|SA|TAS|ACT)', location_text, re.I)
                if match:
                    location = match.group(1).strip()
                    state = match.group(2).upper()
            
            # Inventory count
            inventory = self._extract_inventory_count(card)
            
            # Days listed
            days_listed = self._extract_days_listed(card)
            
            # Phone
            phone_elem = card.find('a', href=re.compile('tel:'))
            phone = phone_elem.get('href', '').replace('tel:', '') if phone_elem else None
            
            # URL
            url_elem = card.find('a', href=re.compile('/dealer/'))
            url = f"https://www.carsales.com.au{url_elem.get('href')}" if url_elem else ""
            
            return BusinessListing(
                dealer_id=dealer_id,
                name=name,
                location=location,
                state=state,
                inventory_count=inventory,
                phone=phone,
                days_listed=days_listed,
                url=url
            )
            
        except Exception as e:
            self.errors.append(f"Card parse error: {str(e)}")
            return None
    
    def _extract_inventory_count(self, card) -> int:
        """Extract vehicle inventory count from card."""
        # Look for patterns like "123 vehicles", "Stock: 45", etc.
        text = card.get_text()
        
        patterns = [
            r'(\d+)\s+vehicles?',
            r'(\d+)\s+cars?',
            r'Stock[:\s]*(\d+)',
            r'Inventory[:\s]*(\d+)',
            r'(\d+)\s+in\s+stock'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _extract_days_listed(self, card) -> int:
        """Extract how many days ago the dealer was listed."""
        text = card.get_text()
        
        # Look for patterns like "Listed 3 days ago", "1 day ago", "Today"
        patterns = [
            r'listed\s+(\d+)\s+days?\s+ago',
            r'(\d+)\s+days?\s+ago',
            r'listed\s+yesterday',
            r'listed\s+today'
        ]
        
        if re.search(r'listed\s+today', text, re.I):
            return 0
        if re.search(r'listed\s+yesterday', text, re.I):
            return 1
        
        match = re.search(r'listed\s+(\d+)\s+days?\s+ago', text, re.I)
        if match:
            return int(match.group(1))
        
        match = re.search(r'(\d+)\s+days?\s+ago', text, re.I)
        if match:
            return int(match.group(1))
        
        return 0
    
    def _generate_id(self, name: str) -> str:
        """Generate a clean ID from dealer name."""
        clean = re.sub(r'[^\w\s]', '', name).strip()
        clean = re.sub(r'\s+', '_', clean)
        return clean[:30].upper()
