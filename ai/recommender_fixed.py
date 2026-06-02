"""AI-powered business recommendation engine."""
import os
from typing import List, Optional
from openai import OpenAI
from models.business import BusinessListing


class BusinessRecommender:
    """Uses AI to recommend business opportunities worth investigating."""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=os.getenv('OPENAI_BASE_URL')
        )
    
    def score_businesses(
        self, 
        listings: List[BusinessListing],
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        target_states: Optional[List[str]] = None,
        focus_industry: Optional[str] = None
    ) -> List[BusinessListing]:
        """
        Score and rank business opportunities based on AI analysis.
        """
        if not listings:
            return []
        
        # Step 1: Apply basic filters to ALL listings
        filtered = listings.copy()
        
        if min_price is not None:
            filtered = [b for b in filtered if b.price and b.price >= min_price]
        
        if max_price is not None:
            filtered = [b for b in filtered if b.price and b.price <= max_price]
        
        if target_states:
            filtered = [
                b for b in filtered 
                if b.state.upper() in [s.upper() for s in target_states]
            ]
        
        if focus_industry:
            filtered = [
                b for b in filtered
                if b.category and focus_industry.lower() in b.category.lower()
            ]
        
        if not filtered:
            return []
        
        # Step 2: Score ALL listings with fallback algorithm
        all_scored = self._fallback_scoring(filtered)
        
        # Mark all as fallback initially
        for listing in all_scored:
            listing.ai_analyzed = False
        
        # Step 3: Select top 5 for AI enhancement
        ai_candidates = all_scored[:5]
        
        print(f"Selected top {len(ai_candidates)} candidates for AI analysis out of {len(all_scored)} total")
        
        # Step 4: Get AI analysis for top 5
        try:
            businesses_text = self._format_for_ai(ai_candidates)
            
            response = self.client.chat.completions.create(
                model="smart",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a business investment analyst. 
                        Your job is to identify which businesses-for-sale are worth investigating as investment opportunities.
                        
                        Consider:
                        - Industry attractiveness (growth sectors, essential services)
                        - Price point relative to market norms
                        - Location (major metro vs regional tradeoffs)
                        - Business type (franchise vs independent pros/cons)
                        - Revenue indicators mentioned in description
                        - Red flags in the listing
                        
                        Return a JSON array with ALL businesses analyzed.
                        
                        Format: [{"dealer_id": "ID", "score": 75, "reason": "explanation"}]
                        
                        Score every business 0-100. Include all results."""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these businesses-for-sale and score them as investment opportunities:\n\n{businesses_text}"
                    }
                ],
                temperature=0.3,
                max_tokens=1000,
                timeout=60,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}}
            )
            
            ai_content = response.choices[0].message.content
            ai_results = self._parse_ai_response(ai_content)
            
            # Step 5: Merge AI scores back into the full list
            for listing in all_scored:
                if listing.dealer_id in ai_results:
                    result = ai_results[listing.dealer_id]
                    listing.score = result.get('score', listing.score)
                    listing.recommendation_reason = result.get('reason', listing.recommendation_reason)
                    listing.ai_analyzed = True
                    
            print(f"Applied AI scores to {len(ai_results)} listings")
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            # Continue with fallback scores
        
        # Step 6: Sort by score descending and return ALL
        all_scored.sort(key=lambda x: x.score, reverse=True)
        return all_scored
    
    def _format_for_ai(self, listings: List[BusinessListing]) -> str:
        """Format listings for AI consumption - lightweight version."""
        lines = []
        for b in listings:
            price_str = f"${b.price/1000:.0f}k" if b.price else "P.O.A"
            short_desc = (b.description or 'N/A')[:80]
            lines.append(
                f"ID:{b.dealer_id}|"
                f"Name:{b.name[:50]}|"
                f"Cat:{b.category or 'Unknown'}|"
                f"Loc:{b.location},{b.state}|"
                f"Price:{price_str}|"
                f"Desc:{short_desc}"
            )
        return "\n".join(lines)
    
    def _parse_ai_response(self, content: str) -> dict:
        """Parse AI response to extract scores."""
        import json
        import re
        
        if not content or content == '[]':
            return {}
        
        # Remove markdown code blocks if present
        if '```json' in content:
            content = content.replace('```json', '').replace('```', '').strip()
        elif '```' in content:
            content = content.replace('```', '').strip()
        
        # Try 1: Look for JSON array
        try:
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, list):
                    return {item.get('dealer_id', item.get('id', f'item_{i}')): item 
                            for i, item in enumerate(data) if isinstance(item, dict)}
        except Exception:
            pass
        
        return {}
    
    def _fallback_scoring(self, listings: List[BusinessListing]) -> List[BusinessListing]:
        """Apply fallback algorithmic scoring."""
        growth_categories = [
            'coffee', 'cafe', 'restaurant', 'food', 'health', 'medical', 
            'technology', 'online', 'digital', 'e-commerce'
        ]
        major_cities = ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide']
        
        for listing in listings:
            score = 50  # Base score
            
            if listing.price and 100000 <= listing.price <= 500000:
                score += 15
            
            if listing.category and any(cat in listing.category.lower() for cat in growth_categories):
                score += 10
            
            if any(city in listing.location for city in major_cities):
                score += 10
            
            if listing.days_listed <= 2:
                score += 10
            
            listing.score = min(score, 100)
            
            reasons = []
            if listing.price and 100000 <= listing.price <= 500000:
                reasons.append("Good price point")
            if any(city in listing.location for city in major_cities):
                reasons.append("Metro location")
            if listing.days_listed <= 2:
                reasons.append("Fresh listing")
            
            listing.recommendation_reason = ", ".join(reasons) if reasons else "Standard opportunity"
        
        return sorted(listings, key=lambda x: x.score, reverse=True)
