"""Mock data generator for demo purposes."""
from models.business import BusinessListing
from datetime import datetime, timedelta
import random

def generate_mock_listings(count: int = 15) -> list[BusinessListing]:
    """Generate realistic mock business listings for demo."""
    
    business_types = [
        ("Cafe & Coffee Shop", "Food/Hospitality"),
        ("Transport Company", "Transport/Logistics"),
        ("Auto Repair Business", "Automotive"),
        ("Online Retail Store", "Retail"),
        ("Cleaning Franchise", "Services"),
        ("Tech Startup", "Technology"),
        ("Medical Practice", "Healthcare"),
        ("Construction Business", "Construction"),
        ("Mobile Car Detailing", "Automotive"),
        ("Courier Service", "Transport/Logistics"),
        ("Restaurant", "Food/Hospitality"),
        ("Gym & Fitness Center", "Health/Fitness"),
        ("Real Estate Agency", "Professional Services"),
        ("Landscaping Business", "Services"),
        ("Import/Export Business", "Trade"),
    ]
    
    locations = [
        ("Sydney", "NSW"),
        ("Melbourne", "VIC"),
        ("Brisbane", "QLD"),
        ("Perth", "WA"),
        ("Adelaide", "SA"),
        ("Gold Coast", "QLD"),
        ("Newcastle", "NSW"),
        ("Canberra", "ACT"),
        ("Wollongong", "NSW"),
    ]
    
    listings = []
    
    for i in range(count):
        biz_type, category = random.choice(business_types)
        city, state = random.choice(locations)
        
        # Generate realistic price
        price = random.choice([
            95000, 150000, 245000, 380000, 520000, 
            750000, 1200000, 250000, 420000, 89000
        ])
        
        # Generate days listed (last 7 days)
        days_listed = random.randint(0, 7)
        
        listing = BusinessListing(
            dealer_id=f"BIZ{1000+i}",
            name=f"{biz_type} - {city}",
            location=city,
            state=state,
            inventory_count=price,  # Reuse field for price
            price=price,
            days_listed=days_listed,
            category=category,
            description=f"Established {biz_type.lower()} with strong customer base. Great opportunity for growth."
        )
        listings.append(listing)
    
    return listings

if __name__ == "__main__":
    listings = generate_mock_listings()
    print(f"Generated {len(listings)} mock listings:")
    for l in listings[:5]:
        print(f"  - {l.name}: ${l.price:,} ({l.location}, {l.state}) - {l.days_listed}d ago")
