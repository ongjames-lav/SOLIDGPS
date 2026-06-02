"""Data models for business listings."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BusinessListing:
    """Represents a scraped business/dealer listing."""
    dealer_id: str
    name: str
    location: str
    state: str
    inventory_count: int  # For Seek Business, this stores price
    phone: Optional[str] = None
    listing_date: Optional[datetime] = None
    days_listed: int = 0
    url: str = ""
    
    # Seek Business specific fields
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[int] = None  # Asking price
    vehicle_relevance_score: int = 0  # Pre-computed relevance
    
    # For recommendations
    score: float = 0.0
    recommendation_reason: str = ""
    ai_analyzed: bool = False


@dataclass
class ScrapeResult:
    """Container for scrape operation results."""
    listings: list[BusinessListing]
    total_found: int
    scraped_at: datetime
    errors: list[str]
