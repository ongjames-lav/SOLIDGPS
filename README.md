# Business Opportunity Finder

AI-powered discovery tool for identifying businesses for sale worth investigating as investment opportunities.

## Overview

This application scrapes business-for-sale listings from SeekBusiness.com.au (last 7 days) and uses AI to recommend investment opportunities worth investigating.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test API connection
python test_api.py

# Run the app
streamlit run ui/app.py
```

## Features

- **Time-sensitive scraping**: Extracts listings from last 7 days
- **AI-powered recommendations**: Uses LLM to score business opportunities
- **Interactive UI**: Streamlit interface with filters and export
- **Smart filtering**: Price range, location, category, and recency

## How It Works

1. **Scrape** — Searches SeekBusiness.com.au for recent business-for-sale listings
2. **Filter** — Applies criteria (price range, target states, business category)
3. **AI Score** — LLM analyzes each business as investment opportunity
4. **Recommend** — Displays ranked list with reasoning

## AI Integration

Uses LiteLLM-compatible API endpoint with OpenAI client:
- Base URL: `https://three-mistress-opera-locations.trycloudflare.com/v1`
- Model routing: Automatic
- Fallback: Basic algorithmic scoring if AI unavailable

## My Approach

### How I Used AI
- Generated scraper structure and HTML parsing logic for Seek Business
- Designed the AI recommendation prompt for investment analysis
- Created UI components with price filtering and export functionality
- Implemented graceful fallback when AI service unavailable

### Scoring Logic
- **High Score (80-100)**: Growth sector + good price point + metro location
- **Medium Score (50-79)**: Solid fundamentals with one or two advantages
- **Not Recommended (<50)**: Lacks clear investment merit or has red flags

### One Thing I'd Add
Contact enrichment pipeline — scraping broker/seller contact details from detail pages for direct outreach capability.
