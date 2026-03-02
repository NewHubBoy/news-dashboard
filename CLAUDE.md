# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A stock news dashboard that aggregates news, announcements, disclosures, broker reports, and financial data for stocks, then uses AI to provide comprehensive investment analysis.

**Tech Stack:**
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, OpenAI SDK
- **Background Jobs:** APScheduler for periodic data updates
- **Web Scraping:** Playwright for Eastmoney scraper

## Development Commands

### Backend (Python/FastAPI)
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server (runs on http://localhost:8000)
uvicorn app.main:app --reload

# Run with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (Next.js)
```bash
cd frontend

# Install dependencies
npm install

# Run development server (runs on http://localhost:3000)
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Lint code
npm run lint
```

## Architecture

### Backend Structure (`backend/app/`)

**Main Entry:** `main.py` - FastAPI application with lifespan management (starts/stops scheduler)

**API Routes:** `api/routes.py` - REST endpoints:
- `POST /api/search` - Integrated search for stock data
- `GET /api/news/{stock_code}` - Get cached news history
- `POST /api/agent/analyze` - AI analysis with daily caching

**Services Layer:**
- `news_service.py` - News search with SerpApi primary, web search fallback
- `financial_service.py` - Fetches announcements, disclosures, broker reports, market data
- `agent_service.py` - OpenAI-powered analysis, caches results by day
- `web_search_service.py` - Fallback web search (Brave API or simple search)
- `eastmoney_scraper.py` - Playwright-based scraper for eastmoney.com

**Data Layer:**
- `db/database.py` - SQLAlchemy session management
- `models/news.py` - ORM models: `NewsArticle`, `FinancialDocument`, `AIAnalysisResult`
- `models/schemas.py` - Pydantic request/response models

**Scheduler:** `scheduler.py` - APScheduler job that runs every 4 hours to:
1. Fetch all previously searched stocks from database
2. Refresh their news and financial data
3. Re-run AI analysis with fresh data

**Config:** `config.py` - Settings from environment variables (uses pydantic-settings)

### Frontend Structure (`frontend/src/`)

**App Router:** `app/page.tsx` - Main page that orchestrates search → fetch → analyze flow

**Components:**
- `SearchForm.tsx` - Stock code/name input form
- `NewsList.tsx` - Displays articles, announcements, disclosures, reports, financial data in sections
- `AIAnalysis.tsx` - Renders markdown AI analysis results

**Services:** `services/api.ts` - Frontend API client with TypeScript interfaces matching backend schemas

### Data Flow

1. User enters stock code/name → `POST /api/search`
2. Backend parallel-fetches from multiple sources (news, announcements, disclosures, reports, financial data)
3. Results stored in database, returned to frontend
4. Frontend automatically triggers `POST /api/agent/analyze` with fetched data
5. AI service:
   - Checks daily cache (returns if found)
   - Compiles multi-source data into structured prompt
   - Calls OpenAI API (default: `moonshotai/kimi-k2.5`)
   - Stores analysis in database
6. Frontend displays results in categorized sections

## Configuration

### Backend Environment (`.env`)

Required:
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

Optional:
```env
GOOGLE_NEWS_API_KEY=xxx        # SerpApi for Google News (primary news source)
BRAVE_API_KEY=xxx              # Brave Search API (fallback)
CORS_ORIGINS=http://localhost:3000
OPENAI_API_KEY=xxx             # For AI analysis
OPENAI_BASE_URL=https://api.openai.com/v1  # Or compatible endpoint
LLM_MODEL_NAME=moonshotai/kimi-k2.5
```

### Frontend Environment

```env
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API URL
```

## API Design Patterns

**Search Priority Fallback:**
1. SerpApi (Google News) → if configured and not 401
2. Brave Search API → if configured
3. Simple web search → always available but limited

**AI Caching:** Analysis results cached per-stock per-day to avoid redundant API calls

**Database Persistence:** All search results (articles, financial docs) stored for history and scheduler consumption

## Key Dependencies

- **playwright** - For Eastmoney scraper (requires browser installation: `playwright install chromium`)
- **openai** - For AI agent (compatible with OpenAI or custom endpoints)
- **fastapi** - Async web framework with automatic OpenAPI docs at `/docs`
- **sqlalchemy** - ORM with async support (database URL from env)
- **apscheduler** - Background job scheduling
