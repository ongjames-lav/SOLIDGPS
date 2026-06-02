"""Streamlit UI for Business Opportunity Finder."""
import streamlit as st
import os
import sys
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import SeekBusinessScraper
from ai.recommender import BusinessRecommender
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state for history and data retention
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'last_results' not in st.session_state:
    st.session_state.last_results = None
if 'last_scrape_time' not in st.session_state:
    st.session_state.last_scrape_time = None

# Page config
st.set_page_config(
    page_title="Business Opportunity Finder",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 Business Opportunity Finder")
st.markdown("Discover businesses for sale worth investigating as investment opportunities")

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

# Main action
if st.button("🚀 Start Discovery", type="primary"):
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Scrape
        status_text.text("Step 1/3: Scraping business listings...")
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
        
        scraper = SeekBusinessScraper(delay=1.0)
        result = scraper.scrape_listings(
            days_back=days_back,
            max_pages=5,
            min_price=min_price,
            max_price=max_price
        )
        
        progress_bar.progress(40)
        
        if result.errors:
            with st.expander("Scraping Warnings", expanded=False):
                for error in result.errors[:10]:
                    st.warning(error)
        
        if not result.listings:
            st.error("No listings found. Try adjusting filters.")
            progress_bar.empty()
            status_text.empty()
        else:
            st.success(f"Found {len(result.listings)} businesses matching basic criteria")
            
            # Step 2: AI Analysis
            if use_ai:
                status_text.text("Step 2/3: AI analyzing business opportunities...")
                progress_bar.progress(60)
                
                recommender = BusinessRecommender()
                recommendations = recommender.score_businesses(
                    result.listings,
                    min_price=min_price,
                    max_price=max_price,
                    target_states=target_states if target_states else None,
                    focus_industry=None if focus_category == "All" else focus_category
                )
                
                progress_bar.progress(80)
                
                if recommendations:
                    st.success(f"AI identified {len(recommendations)} high-priority opportunities")
                else:
                    st.info("No high-priority recommendations from AI. Showing all matches.")
                    recommendations = result.listings
            else:
                # Manual filtering
                recommendations = result.listings
                if target_states:
                    recommendations = [l for l in recommendations if l.state in target_states]
                if focus_category != "All" and focus_category:
                    recommendations = [l for l in recommendations if l.category and focus_category.lower() in l.category.lower()]
            
            # Step 3: Display
            status_text.text("Step 3/3: Building dashboard...")
            progress_bar.progress(100)
            
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
            
            # All Listings Table (Demo Mode - Show All 100)
            # Store results in session state for history
            st.session_state.last_results = result
            st.session_state.last_scrape_time = datetime.now()
            
            # Add to history
            history_entry = {
                'time': datetime.now().strftime('%H:%M:%S'),
                'filters': f"{days_back}d, ${min_price or '0'}-${max_price or 'unlimited'}, {','.join(target_states) if target_states else 'All'}",
                'found': len(result.listings),
                'recommended': len(recommendations)
            }
            st.session_state.search_history.insert(0, history_entry)
            st.session_state.search_history = st.session_state.search_history[:10]  # Keep last 10
            
            # Section 1: AI-Powered Top Picks (clearly separated)
            ai_analyzed = [r for r in recommendations if getattr(r, 'ai_analyzed', False)]
            if ai_analyzed:
                st.subheader("🤖 AI-Powered Analysis (Top Investment Opportunities)")
                st.markdown(f"*{len(ai_analyzed)} businesses received detailed AI investment analysis*")
                
                # Create columns for AI picks
                cols = st.columns(min(len(ai_analyzed), 3))
                for idx, biz in enumerate(ai_analyzed[:6]):  # Show top 6 AI picks
                    with cols[idx % 3]:
                        score_color = "�" if biz.score >= 70 else "🟡" if biz.score >= 50 else "🔴"
                        with st.container():
                            st.markdown(f"<div style='padding: 10px; border-left: 4px solid #4CAF50; background: #f1f8e9; border-radius: 4px;'>", unsafe_allow_html=True)
                            st.markdown(f"**{biz.name[:40]}...**" if len(biz.name) > 40 else f"**{biz.name}**")
                            st.markdown(f"<h3 style='margin:0; color: {'green' if biz.score >= 70 else 'orange' if biz.score >= 50 else 'red'}'>{score_color} {biz.score:.0f}/100</h3>", unsafe_allow_html=True)
                            st.caption(f"{biz.location}, {biz.state} | {f'${biz.price:,}' if biz.price else 'P.O.A'}")
                            st.info(f"🤖 {biz.recommendation_reason[:100]}...")
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("---")
            
            # Section 2: All 100 Businesses Table
            st.subheader("� All Discovered Businesses (Complete List)")
            st.caption(f"Showing all {len(recommendations)} businesses sorted by investment score. 🤖 = AI-Analyzed | ⚡ = Algorithmic Score")
            
            if recommendations:
                # Prepare data for display - show ALL listings sorted by score
                all_listings_sorted = sorted(recommendations, key=lambda x: (getattr(x, 'ai_analyzed', False), x.score), reverse=True)
                
                display_data = []
                for i, r in enumerate(all_listings_sorted, 1):
                    price_str = f"${r.price:,}" if r.price else "P.O.A"
                    # Color code scores
                    score_color = "🟢" if r.score >= 70 else "🟡" if r.score >= 50 else "🔴"
                    # AI vs Fallback indicator
                    analysis_type = "🤖 AI" if getattr(r, 'ai_analyzed', False) else "⚡ Smart"
                    
                    display_data.append({
                        "Rank": i,
                        "Analysis": analysis_type,
                        "Score": f"{score_color} {r.score:.0f}",
                        "Business": r.name[:50] + "..." if len(r.name) > 50 else r.name,
                        "Category": r.category or "Unknown",
                        "Location": f"{r.location}, {r.state}",
                        "Price": price_str,
                        "Listed": f"{r.days_listed}d",
                        "Why": r.recommendation_reason[:40] + "..." if len(r.recommendation_reason) > 40 else r.recommendation_reason
                    })
                
                # Show all results with a clear message
                st.success(f"✅ Showing all {len(display_data)} businesses sorted by investment score")
                
                # Use st.table for better display of all rows
                st.dataframe(
                    display_data,
                    use_container_width=True,
                    hide_index=True,
                    height=800,
                    column_config={
                        "Rank": st.column_config.NumberColumn("#", width=50),
                        "Score": st.column_config.TextColumn("Score", width=80),
                        "Business": st.column_config.TextColumn("Business Name", width=250),
                        "Category": st.column_config.TextColumn("Category", width=120),
                        "Location": st.column_config.TextColumn("Location", width=150),
                        "Price": st.column_config.TextColumn("Price", width=100),
                        "Listed": st.column_config.TextColumn("Age", width=70),
                        "Why": st.column_config.TextColumn("Why", width=180)
                    }
                )
                
                # Detailed Profiles Section
                st.subheader("📋 Detailed Business Profiles")
                st.markdown("*Expand for full details and AI investment analysis*")
                
                # Show top 8 from the sorted list
                top_picks = all_listings_sorted[:8]
                
                for i, biz in enumerate(top_picks, 1):
                    # Score badge color
                    score_color = "green" if biz.score >= 70 else "orange" if biz.score >= 50 else "red"
                    
                    with st.expander(f"🎯 #{i} {biz.name}", expanded=i<=3):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**Location:** {biz.location}, {biz.state}")
                            st.write(f"**Category:** {biz.category or 'Unknown'}")
                            price_str = f"${biz.price:,}" if biz.price else "Price on Application"
                            st.write(f"**Asking Price:** {price_str}")
                            st.write(f"**Listed:** {biz.days_listed} days ago")
                            if biz.description:
                                st.write(f"**Description:** {biz.description[:200]}...")
                            if biz.url:
                                st.write(f"**Listing:** [{biz.url[:60]}...]({biz.url})")
                        
                        with col2:
                            st.markdown(f"<h2 style='color: {score_color}; text-align: center;'>{biz.score:.0f}/100</h2>", unsafe_allow_html=True)
                            # Show analysis type badge
                            analysis_badge = "🤖 AI-Powered Analysis" if getattr(biz, 'ai_analyzed', False) else "⚡ Smart Score"
                            st.caption(f"**{analysis_badge}**")
                            st.info(biz.recommendation_reason)
                            
                            if st.button("🔗 View Listing", key=f"view_{i}_{biz.dealer_id}"):
                                st.markdown(f"[{biz.url}]({biz.url})")
                            
                            # Action buttons - use index to ensure unique key
                            if st.button("📋 Copy Info", key=f"copy_{i}_{biz.dealer_id}"):
                                price_str = f"${biz.price:,}" if biz.price else "P.O.A"
                                info = f"{biz.name} | {biz.location}, {biz.state} | {price_str} | {biz.category or 'Unknown'}"
                                st.code(info)
            else:
                st.warning("No recommendations match your criteria. Try lowering filters.")
            
            # Export options
            if recommendations:
                import json
                
                st.subheader("📥 Export Data")
                col_export1, col_export2 = st.columns(2)
                
                # Full JSON export
                export_data = [
                    {
                        "rank": i+1,
                        "name": r.name,
                        "category": r.category,
                        "location": f"{r.location}, {r.state}",
                        "price": r.price,
                        "score": r.score,
                        "ai_analyzed": getattr(r, 'ai_analyzed', False),
                        "analysis_type": "AI-Powered" if getattr(r, 'ai_analyzed', False) else "Smart Score",
                        "ai_analysis": r.recommendation_reason,
                        "description": r.description,
                        "url": r.url,
                        "days_listed": r.days_listed
                    }
                    for i, r in enumerate(all_listings_sorted)
                ]
                
                with col_export1:
                    st.download_button(
                        "📥 Export Full Report (JSON)",
                        data=json.dumps(export_data, indent=2),
                        file_name=f"business_opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                # CSV export for spreadsheet
                import csv
                import io
                csv_buffer = io.StringIO()
                writer = csv.DictWriter(csv_buffer, fieldnames=["rank", "name", "category", "location", "price", "score", "analysis_type", "ai_analysis"])
                writer.writeheader()
                for item in export_data[:50]:  # Top 50 for CSV
                    writer.writerow({
                        "rank": item["rank"],
                        "name": item["name"],
                        "category": item["category"],
                        "location": item["location"],
                        "price": f"${item['price']:,}" if item['price'] else "P.O.A",
                        "score": item["score"],
                        "analysis_type": item["analysis_type"],
                        "ai_analysis": item["ai_analysis"][:100]
                    })
                
                with col_export2:
                    st.download_button(
                        "📊 Export Top 50 (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name=f"top_businesses_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            progress_bar.empty()
            status_text.empty()
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)
        progress_bar.empty()
        status_text.empty()

else:
    # Initial state or show cached results
    if st.session_state.last_results:
        st.info("📁 Showing cached results from previous search")
        st.write(f"Last updated: {st.session_state.last_scrape_time.strftime('%H:%M:%S') if st.session_state.last_scrape_time else 'Unknown'}")
        
        # Show history
        if st.session_state.search_history:
            with st.expander("📜 Search History (Last 10 searches)"):
                for i, entry in enumerate(st.session_state.search_history[:5], 1):
                    st.write(f"{i}. **{entry['time']}** — Found {entry['found']} businesses, AI recommended {entry['recommended']} | Filters: {entry['filters']}")
        
        st.markdown("---")
        st.markdown("👆 **Click 'Start Discovery' above to run a new search, or view previous results below**")
    else:
        st.info("👆 Configure filters in the sidebar, then click 'Start Discovery' to begin")
    
    st.markdown("""
    ### How It Works
    
    1. **Scrape** — Searches SeekBusiness.com.au for recent business-for-sale listings
    2. **Filter** — Applies your criteria (price range, location, category)
    3. **AI Score** — Uses AI to identify investment opportunities worth investigating
    4. **Recommend** — Displays ranked list with reasoning
    
    ### What Makes a Good Opportunity?
    
    - **Growth sectors** — Technology, healthcare, logistics, essential services
    - **Sweet spot pricing** — $100k-$500k range for accessible entry
    - **Metro locations** — Established customer bases and market access
    - **Fresh listings** — First-mover advantage for good deals
    """)
