# OddsIQ — CLAUDE.md

## Project Overview

OddsIQ is a sports odds aggregation and analysis platform built for both casual bettors and sharp/professional bettors. It polls odds from 80+ US sportsbooks plus prediction markets (Kalshi, Polymarket), surfaces the best available lines, tracks user PnL, and identifies arbitrage opportunities.

This is a learning project — prioritize clean, well-structured code that builds SWE fundamentals. Prefer explicit over clever, and document non-obvious decisions.

---

## Tech Stack

### Frontend
- **Next.js 14** (App Router) — React framework with SSR, great ecosystem, industry-standard
- **Tailwind CSS** — utility-first styling
- **shadcn/ui** — accessible component library built on Radix
- **Recharts** — charting for PnL and odds movement graphs
- **SWR** — data fetching with auto-revalidation for live odds polling

### Backend
- **FastAPI** (Python) — async REST API, great for data-heavy work, easy to learn
- **PostgreSQL** — primary database (users, bets, PnL, historical odds)
- **Redis** — cache layer for live odds (30-second TTL), pub/sub for alerts
- **Celery + Redis** — background task queue for odds polling jobs
- **SQLAlchemy** — ORM for database models
- **Alembic** — database migrations

### Odds Data Sources (Free Tier Priority)
- **The Odds API** — primary source, free tier (500 req/month for dev; upgrade path exists)
  - Covers major US books: DraftKings, FanDuel, BetMGM, Caesars, PointsBet, etc.
  - At 30s polling in prod, will need paid tier (~$10/month) or scraping fallback
- **Kalshi API** — free, no key needed, prediction market contracts
- **Polymarket API** — free, no key needed, prediction market contracts
- **ESPN unofficial API** — free, used for game schedules and metadata

### Authentication
- **NextAuth.js** — session-based auth with email/password + Google OAuth

### Dev/Deployment
- **Local** for now; architecture should support Vercel (frontend) + Railway/Render (backend) later
- **Docker Compose** — local dev environment (Postgres + Redis + API + Next.js)
- **uv** — Python package manager (faster than pip)
- **pnpm** — JS package manager

---

## Sports Coverage (Phase 1)

- NFL
- NBA
- MLB
- NHL

Expand to college sports, soccer, tennis in later phases.

---

## Core Features

### 1. Odds Board
- Display best available line for any game across all tracked books
- Filter by sport, game, bet type (moneyline, spread, total, props)
- Sort by best odds, book, or line movement
- 30-second auto-refresh via SWR polling

### 2. Line Shopping
- For a selected game + bet type, show all books side-by-side ranked by odds
- Highlight best line in green, worst in red
- Show implied probability and juice/vig for each book

### 3. Price Alerts
- Users set a target line (e.g., "Chiefs ML when odds reach +150 at any book")
- Background Celery worker checks on each poll cycle
- Alert delivery: in-app notification + email (SendGrid free tier)

### 4. Arbitrage Calculator (Phase 2)
- **Auto-surface mode**: background job scans all polled odds for guaranteed-profit opportunities across books
- **Manual calculator**: user inputs two or more lines from different books, calculator shows stake distribution and guaranteed return
- Show EV%, required stake per book, and net profit

### 5. PnL Tracker
- Users log bets (book, sport, game, line taken, stake, result)
- Dashboard shows: total PnL, ROI%, win rate, average odds, CLV (closing line value)
- Charts: PnL over time, PnL by sport, PnL by book, bet frequency heatmap

### 6. Sharp Metrics
- **CLV (Closing Line Value)**: compare the odds user bet vs. closing odds — primary sharp metric
- **Line movement tracker**: show how a line moved from open to close
- **Steam move detector**: flag rapid line movement across multiple books (indicates sharp action)
- **Reverse line movement**: flag when line moves opposite to public betting %
- **Consensus %**: show public betting % on each side (sourced from available free data)

---

## Project Structure

```
OddsIQ/
├── frontend/                  # Next.js app
│   ├── app/                   # App Router pages
│   ├── components/            # Reusable UI components
│   ├── lib/                   # Utilities, API clients
│   └── hooks/                 # Custom React hooks
├── backend/                   # FastAPI app
│   ├── api/                   # Route handlers
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   │   ├── odds_poller.py     # Celery task: fetch + cache odds
│   │   ├── arb_scanner.py     # Celery task: find arb opportunities
│   │   └── alert_checker.py   # Celery task: check user alerts
│   └── db/                    # Database setup, migrations
├── docker-compose.yml
└── CLAUDE.md
```

---

## Data Flow

```
The Odds API / Kalshi / Polymarket
         |
   [Celery Poller] (every 30s)
         |
    [Redis Cache] ← serves frontend polls quickly
         |
   [PostgreSQL] ← stores historical odds snapshots
         |
   [FastAPI] ← REST endpoints consumed by Next.js
         |
   [Next.js] ← SWR polling every 30s, renders UI
```

---

## Key Constraints & Decisions

- **Free tier first**: The Odds API free tier (500 req/month) is fine for development. At 30s prod polling intervals, upgrade to $10/month tier or add a scraping fallback layer. Kalshi and Polymarket are always free.
- **Redis as odds cache**: Never hit the odds API on every user request. The Celery poller writes to Redis; FastAPI reads from Redis. This decouples user load from API rate limits.
- **No vendor lock-in on odds source**: Abstract odds fetching behind a `OddsProvider` interface so sources can be swapped or added without touching business logic.
- **Bet logging is self-reported**: OddsIQ does not connect to real sportsbook accounts. Users manually log their bets for PnL tracking.
- **No real money transactions**: This is an information/analytics tool only.

---

## Development Phases

### Phase 1 — Core (Build First)
- [ ] Docker Compose local environment
- [ ] FastAPI skeleton + PostgreSQL + Redis setup
- [ ] Odds poller (The Odds API + Kalshi + Polymarket)
- [ ] Next.js odds board with 30s auto-refresh
- [ ] Line shopping view
- [ ] User auth (NextAuth)
- [ ] Bet logging + basic PnL dashboard

### Phase 2 — Sharp Features
- [ ] Price alerts (Celery + email)
- [ ] CLV calculator
- [ ] Line movement tracker
- [ ] Steam move detector
- [ ] Arbitrage auto-scanner
- [ ] Manual arb calculator UI

### Phase 3 — Polish & Deploy
- [ ] Vercel frontend deploy
- [ ] Railway/Render backend deploy
- [ ] Scraping fallback for additional books
- [ ] College sports, soccer expansion
- [ ] Performance optimization

---

## Coding Conventions

- Python: follow PEP 8, use type hints everywhere, async/await for all I/O
- TypeScript: strict mode enabled, no `any` types
- Components: one component per file, named exports
- API routes: RESTful, versioned under `/api/v1/`
- Errors: always return structured `{ error: string, detail?: string }` JSON
- No comments explaining what code does — only why when non-obvious
- Tests: pytest for backend, Vitest for frontend — write tests for services and utilities
