# Business Opportunity Finder

AI-powered discovery tool for identifying businesses for sale worth investigating as investment opportunities.

## Overview

This application scrapes business-for-sale listings from SeekBusiness.com.au (last 7 days, up to 100 listings) and uses a hybrid AI + algorithmic approach to recommend the top opportunities. The UI presents a clean, demo-ready “Top 10 Recommendations” view prioritized by AI analysis.

## Quick Start

```bash
# 1) Install dependencies
pip install -r requirements.txt

# 2) Configure environment (copy the example and fill your values)
cp .env.example .env
# set OPENAI_API_KEY and OPENAI_BASE_URL in .env (do NOT commit .env)

# 3) (Optional) Test API connection
python test_api.py

# 4) Run the app
streamlit run ui/app.py
```

## Features

- **Time-sensitive scraping**: Extracts listings from the last 7 days (5 pages, ~100 listings)
- **AI + Algorithmic scoring**: AI-enhanced scoring on a capped subset for speed; algorithmic fallback for all
- **Top 10 Recommendations**: AI-analyzed results first, then best Smart scores
- **Professional UI**: Streamlit interface with dynamic tables and score bars
- **Filters**: Price range, target states, and robust category matching (name/category/description)
- **Exports**: JSON and CSV for the Top 10 set

## How It Works

1. **Scrape** — Searches SeekBusiness.com.au for recent business-for-sale listings (up to 100)
2. **Filter** — Applies criteria (price range, target states, business category)
3. **AI Score** — AI analyzes a capped shortlist (up to 10) for detailed reasoning; algorithmic scores applied to all
4. **Recommend** — Displays a clean “Top 10” table and detailed profiles with reasoning

## AI Integration

Uses a LiteLLM-compatible API with the OpenAI Python client.

- Configure via environment variables in `.env` (see `.env.example`).
- We disable provider “thinking” output to ensure content is returned in the normal `content` field (server-dependent):
  - `extra_body={"chat_template_kwargs": {"enable_thinking": False}}`
- If AI is slow/unavailable, the app gracefully falls back to algorithmic scoring so results are always shown.

## My Approach

### How I Used AI
- Designed and iterated on the AI prompt to output strict JSON with score/reason
- Implemented robust parsing (JSON-in-markdown, objects/arrays, text fallback)
- Tuned performance (cap AI batch to 10, moderate max_tokens, 60s timeout)
- Added graceful fallbacks and visibility in the debug logs

### Scoring Logic (Hybrid)
- Algorithmic baseline for all listings (base 50 + bonuses for metro, recency, price band)
- AI overlay on a capped shortlist (up to 10) with qualitative reasoning
- Final Top 10 prioritizes AI-analyzed entries, then highest Smart scores

### Filters & Categories
- Price range and states applied before or after scoring as appropriate
- Category filter uses robust keyword matching across name/category/description
  - Example: Transport/Logistics includes transport, delivery, freight, courier, warehouse, 3PL, fleet, shipping, etc.

### Exports
- JSON: full Top 10 with metadata (analysis type, reasoning)
- CSV: Top 10, condensed for spreadsheet review

### Troubleshooting
- If you see few results for a narrow category, the filter is strict by design; broaden category or states
- If the AI returns empty/markdown-wrapped JSON, the parser removes code fences and proceeds
- If the AI endpoint times out, fallback scoring is used automatically and the UI still renders

### One Thing I'd Add
- Contact enrichment pipeline — scraping broker/seller contact details from detail pages for direct outreach capability.

## Security
- Do not commit `.env` — use `.env.example` as a template
- API keys are read from environment variables only
