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
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        target_states: List[str] = None,
        focus_industry: Optional[str] = None
    ) -> List[BusinessListing]:
        """
        Score and rank business opportunities based on AI analysis.
        
        Args:
            listings: List of business listings to analyze
            min_price: Minimum asking price to consider
            max_price: Maximum asking price to consider
            target_states: Preferred states (NSW, VIC, QLD, etc.)
            focus_industry: Preferred industry/category
        """
        if not listings:
            return []
        
        # Filter by basic criteria first
        filtered = listings.copy()
        
        # Limit to top 10 for AI analysis (optimize for locally-hosted model)
        if len(filtered) > 10:
            print(f"Limiting AI analysis to top 10 of {len(filtered)} listings (60s timeout configured)")
            filtered = filtered[:10]
        
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
        
        # Prepare data for AI analysis
        businesses_text = self._format_for_ai(filtered)
        
        # Get AI recommendations
        try:
            response = self.client.chat.completions.create(
                model="smart-nothink",  # Try the other available model
                messages=[
                    {
                        "role": "system",
                        "content": """You are a business investment analyst. 
                        Your job is to identify which businesses-for-sale are worth investigating as investment opportunities.
                        
                        Evaluate each business practically to determine if it's a great fit for investment.
                        Consider:
                        - Explicitly mentioned revenue or net profit (High signal)
                        - Price point compared to potential returns or growth (P.O.A without context is a negative signal)
                        - Location advantages (metro vs regional - focus on profitability rather than penalizing one over the other)
                        - Essential services vs highly discretionary sectors
                        - Turn-key operations vs "shell" businesses without existing traction

                        Give higher scores to businesses that provide clear indicators of profitability and sustainable revenue.
                        
                        Return a JSON array with ALL businesses analyzed.
                        
                        Format: [{"dealer_id": "ID", "score": 75, "reason": "explanation"}]
                        
                        Score every business 0-100 based strictly on business fundamentals and clarity. Include all results."""
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
            
            # Parse AI response and update listings
            ai_content = response.choices[0].message.content
            
            print(f"\n{'='*60}")
            print(f"AI RAW RESPONSE:")
            print(f"{'='*60}")
            print(repr(ai_content))
            print(f"{'='*60}\n")
            ai_results = self._parse_ai_response(ai_content)
            print(f"Parsed {len(ai_results)} AI recommendations")
            
            if not ai_results:
                print("AI returned no scorable results, using fallback scoring")
                # Mark all as fallback (not AI analyzed)
                for listing in filtered:
                    listing.ai_analyzed = False
                return self._fallback_scoring(filtered)
            
            # Mark listings that got AI analysis
            for listing in filtered:
                listing.ai_analyzed = listing.dealer_id in ai_results
            
            # Apply AI scores to these listings
            return self._apply_scores(filtered, ai_results)
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            import traceback
            print(traceback.format_exc())
            # Fallback: basic scoring without AI
            # Mark all as fallback (not AI analyzed)
            for listing in filtered:
                listing.ai_analyzed = False
            return self._fallback_scoring(filtered)
    
    def _format_for_ai(self, listings: List[BusinessListing]) -> str:
        """Format listings for AI consumption - lightweight version."""
        lines = []
        for b in listings:
            price_str = f"${b.price/1000:.0f}k" if b.price else "P.O.A"
            # Truncate description to reduce payload size
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
        
        # Debug: show what we're trying to parse
        print(f"Cleaned content preview: {repr(content[:200])}")
        
        # Try 1: Look for JSON array
        try:
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, list):
                    return {item.get('dealer_id', item.get('id', f'item_{i}')): item 
                            for i, item in enumerate(data) if isinstance(item, dict)}
        except Exception as e:
            print(f"JSON array parse failed: {e}")
        
        # Try 2: Look for JSON object
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"JSON object parse failed: {e}")
        
        # Try 3: Parse text-based scoring (if AI returns plain text)
        results = {}
        lines = content.split('\n')
        current_id = None
        
        for line in lines:
            # Look for ID patterns
            id_match = re.search(r'(?:ID|Business)[:\s]+([A-Z_\d]+)', line, re.I)
            if id_match:
                current_id = id_match.group(1)
                results[current_id] = {'score': 0, 'reason': ''}
            
            # Look for score
            score_match = re.search(r'(?:score|rating)[:\s]+(\d+)', line, re.I)
            if score_match and current_id:
                results[current_id]['score'] = int(score_match.group(1))
            
            # Look for reason/explanation
            reason_match = re.search(r'(?:reason|because|why)[:\s]+(.+)', line, re.I)
            if reason_match and current_id:
                results[current_id]['reason'] = reason_match.group(1)
        
        if results:
            print(f"Parsed {len(results)} entries from text format")
            return results
        
        print("Warning: Could not parse any AI recommendations")
        return {}
    
    def _apply_scores(
        self, 
        listings: List[BusinessListing], 
        ai_results: dict
    ) -> List[BusinessListing]:
        """Apply AI scores to listings."""
        scored_count = 0
        for listing in listings:
            if listing.dealer_id in ai_results:
                result = ai_results[listing.dealer_id]
                listing.score = result.get('score', 0)
                listing.recommendation_reason = result.get('reason', '')
                scored_count += 1
            # If not in AI results, keep existing score (from fallback)
        
        print(f"Applied AI scores to {scored_count} listings")
        
        # Sort by score descending, include all with score > 0
        result_list = [l for l in listings if l.score > 0]
        if not result_list:
            print("Warning: No listings with positive scores, using all listings")
            result_list = listings
            for l in result_list:
                if l.score == 0:
                    l.score = 50  # Default minimum
                    l.recommendation_reason = "Standard listing"
        
        return sorted(result_list, key=lambda x: x.score, reverse=True)
    
    def _fallback_scoring(self, listings: List[BusinessListing]) -> List[BusinessListing]:
        """Basic scoring when AI is unavailable."""
        for listing in listings:
            score = 40  # Base score
            reasons = []
            
            # Price-based scoring (if available)
            if listing.price:
                if 50000 <= listing.price <= 500000:
                    score += 20  # Sweet spot for small-medium acquisitions
                    reasons.append("Accessible price point")
                elif listing.price > 500000:
                    score += 15  # Larger opportunity
                    reasons.append("Established scale")
            else:
                score -= 10  # Penalty for P.O.A as it lacks transparency
                reasons.append("Price on Application (lower transparency)")
            
            # Recency bonus
            if listing.days_listed <= 2:
                score += 10  # Fresh listing
                reasons.append("Fresh listing")
            
            # Category bonus
            growth_categories = ['technology', 'healthcare', 'logistics', 'e-commerce', 'education', 'food', 'hospitality']
            if listing.category and any(cat in listing.category.lower() for cat in growth_categories):
                score += 15
                reasons.append(f"In-demand category")

            # Description signals
            if listing.description:
                desc = listing.description.lower()
                if 'profit' in desc or 'net' in desc or 'takings' in desc or 'revenue' in desc:
                    score += 20
                    reasons.append("Financial indicators mentioned")
                if 'under management' in desc or 'staff managed' in desc:
                    score += 10
                    reasons.append("Under management")
            
            listing.score = min(max(score, 10), 100)
            listing.recommendation_reason = " | ".join(reasons) if reasons else "Standard opportunity without clear financial signals"
        
        return sorted(listings, key=lambda x: x.score, reverse=True)
