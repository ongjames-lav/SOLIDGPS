"""Debug version of the app with verbose logging."""
import streamlit as st
import os
import sys
from datetime import datetime
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import SeekBusinessScraper
from ai.recommender import BusinessRecommender
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Business Opportunity Finder - DEBUG MODE",
    page_icon="🐛",
    layout="wide"
)

# Title
st.title("🐛 DEBUG MODE - Business Opportunity Finder")
st.markdown("Verbose logging enabled to show all background processes")

# Initialize debug log container
debug_log = st.empty()
log_messages = []

def log(msg, level="INFO"):
    """Add to debug log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_messages.append(f"[{timestamp}] {level}: {msg}")
    debug_log.code("\n".join(log_messages[-50:]), language="log")  # Show last 50

# Sidebar filters
st.sidebar.header("Search Filters")

days_back = st.sidebar.slider(
    "Days to Look Back",
    min_value=1,
    max_value=14,
    value=7,
    help="How many days of recent listings to analyze"
)

# Price range
price_range = st.sidebar.select_slider(
    "Price Range",
    options=["Any", "Under $100k", "$100k-$500k", "$500k-$1M", "$1M+"],
    value="Any",
    help="Filter by asking price"
)

target_states = st.sidebar.multiselect(
    "Target States",
    options=["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
    default=["NSW", "VIC", "QLD"],
    help="Focus on specific states (empty = all states)"
)

focus_category = st.sidebar.selectbox(
    "Business Category",
    options=["All", "Transport/Logistics", "Retail", "Services", "Technology", 
             "Food/Hospitality", "Healthcare", "Construction", "Franchise"],
    index=0,
    help="Filter by business type"
)

use_ai = st.sidebar.checkbox(
    "Use AI Recommendations",
    value=True,
    help="Use AI to score and recommend businesses (uncheck for basic filtering)"
)

show_debug = st.sidebar.checkbox(
    "Show Debug Log",
    value=True,
    help="Show detailed background processing logs"
)

# Debug log display
if show_debug:
    st.sidebar.subheader("Debug Output")
    debug_container = st.sidebar.container()

# Main action
if st.button("🚀 Start Discovery (Debug Mode)", type="primary"):
    
    log_messages.clear()
    log("Starting discovery process...")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Results", "Raw Data", "Debug Log"])
    
    try:
        # Step 1: Scrape
        status_text.text("Step 1/3: Scraping business listings...")
        log("Initializing scraper...")
        progress_bar.progress(10)
        
        # Parse price range
        min_price = None
        max_price = None
        if price_range == "Under $100k":
            max_price = 100000
        elif price_range == "$100k-$500k":
            min_price = 100000
            max_price = 500000
        elif price_range == "$500k-$1M":
            min_price = 500000
            max_price = 1000000
        elif price_range == "$1M+":
            min_price = 1000000
        
        log(f"Price filter: min={min_price}, max={max_price}")
        log(f"Target states: {target_states}")
        log(f"Days back: {days_back}")
        
        scraper = SeekBusinessScraper(delay=1.0)
        result = scraper.scrape_listings(
            days_back=days_back,
            max_pages=5,
            min_price=min_price,
            max_price=max_price
        )
        
        log(f"Scraping complete. Found {len(result.listings)} listings")
        log(f"Errors during scraping: {len(result.errors)}")
        if result.errors:
            for err in result.errors[:5]:
                log(f"  - {err}", "WARNING")
        
        # Log first few listings for debugging
        log("Sample listings found:")
        for i, listing in enumerate(result.listings[:3], 1):
            price_str = f"${listing.price:,}" if listing.price else "N/A"
            log(f"  {i}. {listing.name} | {listing.location}, {listing.state} | {price_str}")
        
        progress_bar.progress(40)
        
        if not result.listings:
            st.error("No listings found. Try adjusting filters.")
            log("ERROR: No listings found", "ERROR")
            progress_bar.empty()
            status_text.empty()
        else:
            st.success(f"Found {len(result.listings)} businesses matching basic criteria")
            
            # Step 2: AI Analysis
            if use_ai:
                status_text.text("Step 2/3: AI analyzing business opportunities...")
                log("Initializing AI recommender...")
                progress_bar.progress(60)
                
                recommender = BusinessRecommender()
                
                # Pre-apply fallback scoring first
                log("Applying fallback scoring as baseline...")
                for listing in result.listings:
                    score = 50
                    if listing.price:
                        if 100000 <= listing.price <= 500000:
                            score += 15
                        elif listing.price > 500000:
                            score += 10
                    
                    major_cities = ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide']
                    if any(city in listing.location for city in major_cities):
                        score += 10
                    
                    if listing.days_listed <= 2:
                        score += 10
                    
                    listing.score = min(score, 100)
                    log(f"  {listing.name[:40]}... fallback score: {listing.score}")
                
                # Only send top 5 to AI - 60s timeout configured for locally-hosted model
                ai_candidates = result.listings[:5]
                log(f"Sending top {len(ai_candidates)} candidates to AI (60s timeout, lightweight payload)...")
                
                try:
                    recommendations = recommender.score_businesses(
                        ai_candidates,
                        min_price=min_price,
                        max_price=max_price,
                        target_states=target_states if target_states else None,
                        focus_industry=None if focus_category == "All" else focus_category
                    )
                    # Combine AI-scored with remaining unscored listings
                    remaining = [l for l in result.listings[5:] if l not in recommendations]
                    recommendations = recommendations + remaining
                    
                    log(f"AI analysis complete. {len(recommendations)} recommendations with positive scores")
                    
                    # Log score distribution
                    score_counts = {}
                    for r in recommendations:
                        bucket = (r.score // 10) * 10
                        score_counts[bucket] = score_counts.get(bucket, 0) + 1
                    log("Score distribution:")
                    for bucket in sorted(score_counts.keys(), reverse=True):
                        log(f"  {bucket}-{bucket+9}: {score_counts[bucket]} businesses")
                    
                except Exception as e:
                    log(f"AI analysis failed: {e}", "ERROR")
                    import traceback
                    log(traceback.format_exc(), "ERROR")
                    recommendations = result.listings
                    recommendations.sort(key=lambda x: x.score, reverse=True)
                
                progress_bar.progress(80)
                
                if recommendations:
                    st.success(f"AI identified {len(recommendations)} high-priority opportunities")
                else:
                    st.info("No high-priority recommendations from AI. Showing all matches.")
                    recommendations = result.listings
            else:
                # Manual filtering only
                log("AI disabled, using manual filtering only")
                recommendations = result.listings
                if target_states:
                    recommendations = [l for l in recommendations if l.state in target_states]
                    log(f"After state filter: {len(recommendations)} listings")
                if focus_category != "All" and focus_category:
                    recommendations = [l for l in recommendations if l.category and focus_category.lower() in l.category.lower()]
                    log(f"After category filter: {len(recommendations)} listings")
            
            # Step 3: Display
            status_text.text("Step 3/3: Building dashboard...")
            progress_bar.progress(100)
            
            with tab1:
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Found", len(result.listings))
                with col2:
                    st.metric("Recommended", len(recommendations))
                with col3:
                    if recommendations:
                        avg_score = sum(r.score for r in recommendations) / len(recommendations)
                        st.metric("Avg Score", f"{avg_score:.1f}")
                    else:
                        st.metric("Avg Score", "N/A")
                with col4:
                    top_state = max(
                        set(r.state for r in recommendations),
                        key=lambda s: sum(1 for r in recommendations if r.state == s)
                    ) if recommendations else "N/A"
                    st.metric("Top State", top_state)
                
                # Recommendations table
                st.subheader("🎯 Top Recommendations")
                
                if recommendations:
                    # Prepare data for display
                    display_data = []
                    for r in recommendations[:20]:
                        price_str = f"${r.price:,}" if r.price else "P.O.A"
                        display_data.append({
                            "Score": f"{r.score:.0f}" if r.score > 0 else "N/A",
                            "Business": r.name,
                            "Category": r.category or "Unknown",
                            "Location": f"{r.location}, {r.state}",
                            "Price": price_str,
                            "Listed": f"{r.days_listed}d ago",
                            "Why": r.recommendation_reason[:80] + "..." if len(r.recommendation_reason) > 80 else r.recommendation_reason
                        })
                    
                    st.dataframe(
                        display_data,
                        use_container_width=True,
                        hide_index=True
                    )
                
            with tab2:
                st.subheader("Raw Business Data")
                for i, biz in enumerate(recommendations[:10], 1):
                    with st.expander(f"{i}. {biz.name} (ID: {biz.dealer_id})"):
                        st.json({
                            "dealer_id": biz.dealer_id,
                            "name": biz.name,
                            "location": biz.location,
                            "state": biz.state,
                            "price": biz.price,
                            "category": biz.category,
                            "days_listed": biz.days_listed,
                            "score": biz.score,
                            "recommendation_reason": biz.recommendation_reason,
                            "description": biz.description[:200] if biz.description else None,
                            "url": biz.url
                        })
            
            with tab3:
                st.subheader("Debug Log")
                st.code("\n".join(log_messages), language="log")
                
                # Export log button
                st.download_button(
                    "📥 Download Debug Log",
                    data="\n".join(log_messages),
                    file_name=f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
            
            progress_bar.empty()
            status_text.empty()
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        log(f"CRITICAL ERROR: {e}", "CRITICAL")
        import traceback
        log(traceback.format_exc(), "CRITICAL")
        progress_bar.empty()
        status_text.empty()

else:
    # Initial state
    st.info("👆 Click 'Start Discovery (Debug Mode)' to begin with verbose logging")
    
    st.markdown("""
    ### Debug Mode Features
    
    This mode shows:
    - **Real-time scraping logs** — Every HTTP request and HTML parsing step
    - **Data extraction details** — What fields are found for each listing
    - **AI processing logs** — What the AI receives and returns
    - **Scoring breakdown** — How each business gets its score
    - **Error details** — Full stack traces for debugging
    
    ### Tabs
    1. **Results** — Normal UI output with recommendations
    2. **Raw Data** — Complete extracted data for each business
    3. **Debug Log** — Step-by-step process log
    """)
