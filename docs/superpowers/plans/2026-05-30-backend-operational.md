# Backend Operational Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the OddsIQ backend fully operational — Postgres + Redis in Docker, SQLAlchemy models, real odds data from The Odds API, background polling + arb scanning, and all FastAPI endpoints reading from real data.

**Architecture:** The Odds API is polled on startup and every 2 minutes via APScheduler; results are written to Redis (30s TTL for fast reads) and Postgres (permanent snapshot). FastAPI endpoints read from Redis first, falling back to Postgres. The arb scanner runs immediately after each poll, writing detected opportunities to Redis.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic, asyncpg, Redis (redis-py), APScheduler, httpx, python-dotenv, Postgres 16, Redis 7.

---

## API Key Setup

Before any code, store the Odds API key:

1. Create `/Users/lucassimon/OddsIQ/backend/.env`:
```
DATABASE_URL=postgresql+asyncpg://oddsiq:oddsiq@localhost:5432/oddsiq
REDIS_URL=redis://localhost:6379
ODDS_API_KEY=your_key_here
ODDS_API_BASE=https://api.the-odds-api.com/v4
```

2. Replace `your_key_here` with the key from https://the-odds-api.com/account/

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `docker-compose.yml` | Modify | Add postgres + redis services |
| `backend/.env.example` | Create | Template for env vars |
| `backend/config.py` | Create | Pydantic settings from env |
| `backend/db/__init__.py` | Create | Package marker |
| `backend/db/session.py` | Create | Async SQLAlchemy engine + session factory |
| `backend/db/models.py` | Create | ORM: Game, OddsSnapshot, Bet, Alert |
| `backend/services/__init__.py` | Create | Package marker |
| `backend/services/redis_client.py` | Create | Redis connection + get/set helpers |
| `backend/services/odds_poller.py` | Create | Fetch Odds API → Redis + Postgres |
| `backend/services/arb_scanner.py` | Create | Scan polled odds → arb opportunities in Redis |
| `backend/alembic.ini` | Create | Alembic config |
| `backend/alembic/env.py` | Create | Alembic async env |
| `backend/alembic/versions/001_initial.py` | Create | Initial migration |
| `backend/api/v1/odds.py` | Modify | Read from Redis/Postgres instead of mock |
| `backend/api/v1/bets.py` | Modify | Persist to Postgres |
| `backend/api/v1/alerts.py` | Modify | Persist to Postgres |
| `backend/api/v1/arb.py` | Modify | Read opportunities from Redis |
| `backend/main.py` | Modify | Add lifespan, APScheduler, DB init |
| `backend/pyproject.toml` | Modify | Add all new dependencies |

---

## Task 1: Docker Compose — Add Postgres + Redis

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Replace docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: oddsiq
      POSTGRES_PASSWORD: oddsiq
      POSTGRES_DB: oddsiq
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    command: uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    env_file:
      - ./backend/.env
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

- [ ] **Step 2: Start just Postgres and Redis to verify**

```bash
cd OddsIQ
docker compose up postgres redis -d
docker compose ps
```

Expected: both services show `running`.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add postgres and redis to docker-compose"
```

---

## Task 2: Backend Dependencies + Config

**Files:**
- Modify: `backend/pyproject.toml`
- Create: `backend/config.py`
- Create: `backend/.env.example`

- [ ] **Step 1: Update pyproject.toml**

```toml
[project]
name = "backend"
version = "0.1.0"
description = "OddsIQ backend API"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.136.3",
    "pydantic>=2.13.4",
    "pydantic-settings>=2.0.0",
    "uvicorn[standard]>=0.48.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.0",
    "httpx>=0.27.0",
    "apscheduler>=3.10.0",
    "python-dotenv>=1.0.0",
]
```

- [ ] **Step 2: Install dependencies**

```bash
cd OddsIQ/backend
uv sync
```

Expected: all packages install without errors.

- [ ] **Step 3: Create backend/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://oddsiq:oddsiq@localhost:5432/oddsiq"
    redis_url: str = "redis://localhost:6379"
    odds_api_key: str = ""
    odds_api_base: str = "https://api.the-odds-api.com/v4"
    poll_interval_seconds: int = 120

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 4: Create backend/.env.example**

```
DATABASE_URL=postgresql+asyncpg://oddsiq:oddsiq@localhost:5432/oddsiq
REDIS_URL=redis://localhost:6379
ODDS_API_KEY=your_key_here
ODDS_API_BASE=https://api.the-odds-api.com/v4
POLL_INTERVAL_SECONDS=120
```

- [ ] **Step 5: Create backend/.env from the example and add your key**

```bash
cp backend/.env.example backend/.env
# then edit backend/.env and replace your_key_here with the real key
```

- [ ] **Step 6: Commit**

```bash
git add backend/pyproject.toml backend/config.py backend/.env.example
git commit -m "feat: add backend dependencies and settings config"
```

---

## Task 3: SQLAlchemy Models

**Files:**
- Create: `backend/db/__init__.py`
- Create: `backend/db/session.py`
- Create: `backend/db/models.py`

- [ ] **Step 1: Create backend/db/__init__.py**

```python
```
(empty file — package marker)

- [ ] **Step 2: Create backend/db/session.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 3: Create backend/db/models.py**

```python
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.session import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sport: Mapped[str] = mapped_column(String, index=True)
    sport_key: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    home_team: Mapped[str] = mapped_column(String)
    away_team: Mapped[str] = mapped_column(String)
    commence_time: Mapped[datetime] = mapped_column(DateTime)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    snapshots: Mapped[list["OddsSnapshot"]] = relationship(back_populates="game")


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), index=True)
    book: Mapped[str] = mapped_column(String)
    market: Mapped[str] = mapped_column(String)        # h2h, spreads, totals
    outcome: Mapped[str] = mapped_column(String)       # team name or Over/Under
    price: Mapped[int] = mapped_column(Integer)        # American odds
    point: Mapped[float | None] = mapped_column(Float, nullable=True)  # spread/total value
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    game: Mapped["Game"] = relationship(back_populates="snapshots")


class Bet(Base):
    __tablename__ = "bets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True, default="local")
    date: Mapped[str] = mapped_column(String)
    sport: Mapped[str] = mapped_column(String)
    game: Mapped[str] = mapped_column(String)
    bet_type: Mapped[str] = mapped_column(String)
    odds: Mapped[int] = mapped_column(Integer)
    stake: Mapped[float] = mapped_column(Float)
    result: Mapped[str] = mapped_column(String, default="pending")
    pnl: Mapped[float] = mapped_column(Float, default=0.0)
    closing_odds: Mapped[int] = mapped_column(Integer, default=0)
    clv: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True, default="local")
    game: Mapped[str] = mapped_column(String)
    bet_type: Mapped[str] = mapped_column(String)
    target_odds: Mapped[int] = mapped_column(Integer)
    book: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[str] = mapped_column(String)
```

- [ ] **Step 4: Commit**

```bash
git add backend/db/
git commit -m "feat: add SQLAlchemy async models for games, bets, alerts, odds snapshots"
```

---

## Task 4: Alembic Migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/001_initial.py`

- [ ] **Step 1: Initialise Alembic**

```bash
cd OddsIQ/backend
uv run alembic init alembic
```

- [ ] **Step 2: Replace backend/alembic/env.py**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models so Alembic can detect them
from db.session import Base
from db import models  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Set the DB URL in alembic.ini**

Open `backend/alembic.ini` and find:
```
sqlalchemy.url = driver://user:pass@localhost/dbname
```
Replace with:
```
sqlalchemy.url = postgresql+asyncpg://oddsiq:oddsiq@localhost:5432/oddsiq
```

- [ ] **Step 4: Generate and run the initial migration**

```bash
cd OddsIQ/backend
uv run alembic revision --autogenerate -m "initial schema"
uv run alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade  -> <hash>, initial schema`

- [ ] **Step 5: Verify tables exist**

```bash
docker exec -it oddsiq-postgres-1 psql -U oddsiq -d oddsiq -c "\dt"
```

Expected: shows `games`, `odds_snapshots`, `bets`, `alerts` tables.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: alembic async migrations — initial schema"
```

---

## Task 5: Redis Client

**Files:**
- Create: `backend/services/__init__.py`
- Create: `backend/services/redis_client.py`

- [ ] **Step 1: Create backend/services/__init__.py**

```python
```
(empty)

- [ ] **Step 2: Create backend/services/redis_client.py**

```python
import json
import redis.asyncio as aioredis
from config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def cache_set(key: str, value: dict | list, ttl: int = 60) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))


async def cache_get(key: str) -> dict | list | None:
    r = await get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
```

- [ ] **Step 3: Commit**

```bash
git add backend/services/
git commit -m "feat: async Redis client with get/set/close helpers"
```

---

## Task 6: Odds Poller Service

**Files:**
- Create: `backend/services/odds_poller.py`

- [ ] **Step 1: Create backend/services/odds_poller.py**

```python
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select

from config import settings
from db.session import AsyncSessionLocal
from db.models import Game, OddsSnapshot
from services.redis_client import cache_set
from api.v1.odds import SPORT_KEYS, SPORT_CATEGORIES

# Markets to fetch on each poll
MARKETS = "h2h,spreads,totals"
REGIONS = "us"
ODDS_FORMAT = "american"

# Cache TTL — 90 seconds so frontend 30s polling always hits warm cache
CACHE_TTL = 90


def _find_category(sport_display: str) -> str:
    for category, sports in SPORT_CATEGORIES.items():
        if sport_display in sports:
            return category
    return "Other"


async def poll_sport(sport_display: str, sport_key: str, client: httpx.AsyncClient) -> list[dict]:
    """Fetch odds for one sport from The Odds API. Returns raw game dicts."""
    url = f"{settings.odds_api_base}/sports/{sport_key}/odds"
    params = {
        "apiKey": settings.odds_api_key,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }
    try:
        resp = await client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[poller] Failed to fetch {sport_display}: {e}")
        return []


async def _upsert_game(session: AsyncSession, raw: dict, sport_display: str) -> None:
    """Insert or update a game row."""
    stmt = pg_insert(Game).values(
        id=raw["id"],
        sport=sport_display,
        sport_key=raw["sport_key"],
        category=_find_category(sport_display),
        home_team=raw["home_team"],
        away_team=raw["away_team"],
        commence_time=datetime.fromisoformat(raw["commence_time"].replace("Z", "+00:00")),
        last_updated=datetime.utcnow(),
    ).on_conflict_do_update(
        index_elements=["id"],
        set_={"last_updated": datetime.utcnow()},
    )
    await session.execute(stmt)


async def _insert_snapshots(session: AsyncSession, raw: dict) -> None:
    """Insert one OddsSnapshot row per bookmaker + market + outcome."""
    now = datetime.utcnow()
    for bookmaker in raw.get("bookmakers", []):
        book = bookmaker["title"]
        for market in bookmaker.get("markets", []):
            mkey = market["key"]
            for outcome in market.get("outcomes", []):
                session.add(OddsSnapshot(
                    game_id=raw["id"],
                    book=book,
                    market=mkey,
                    outcome=outcome["name"],
                    price=outcome["price"],
                    point=outcome.get("point"),
                    captured_at=now,
                ))


def _build_best_line(raw: dict) -> dict | None:
    """Derive the best available line per market across all books."""
    h2h: dict[str, tuple[str, int]] = {}   # outcome → (book, best_odds)
    spread: dict[str, tuple[str, int, float]] = {}
    totals: dict[str, tuple[str, int, float]] = {}

    for bm in raw.get("bookmakers", []):
        book = bm["title"]
        for market in bm.get("markets", []):
            mkey = market["key"]
            for o in market.get("outcomes", []):
                name = o["name"]
                price = o["price"]
                dec = price / 100 + 1 if price > 0 else 100 / abs(price) + 1

                if mkey == "h2h":
                    if name not in h2h or dec > (h2h[name][1] / 100 + 1 if h2h[name][1] > 0 else 100 / abs(h2h[name][1]) + 1):
                        h2h[name] = (book, price)

                elif mkey == "spreads":
                    if name not in spread or dec > (spread[name][1] / 100 + 1 if spread[name][1] > 0 else 100 / abs(spread[name][1]) + 1):
                        spread[name] = (book, price, o.get("point", 0.0))

                elif mkey == "totals":
                    if name not in totals or dec > (totals[name][1] / 100 + 1 if totals[name][1] > 0 else 100 / abs(totals[name][1]) + 1):
                        totals[name] = (book, price, o.get("point", 0.0))

    teams = list(h2h.keys())
    if len(teams) < 2:
        return None

    home = raw["home_team"]
    away = raw["away_team"]
    home_h2h = h2h.get(home, ("", 0))
    away_h2h = h2h.get(away, ("", 0))

    spread_vals = list(spread.values())
    total_vals = list(totals.values())

    return {
        "homeMoneyline": home_h2h[1],
        "awayMoneyline": away_h2h[1],
        "spread": spread_vals[0][2] if spread_vals else 0.0,
        "spreadOdds": spread_vals[0][1] if spread_vals else 0,
        "total": total_vals[0][2] if total_vals else 0.0,
        "overOdds": totals.get("Over", ("", 0, 0.0))[1],
        "underOdds": totals.get("Under", ("", 0, 0.0))[1],
        "book": home_h2h[0],
    }


async def poll_all_active_sports() -> list[dict]:
    """
    Poll all sports in SPORT_KEYS, write to Postgres and Redis.
    Returns all raw game dicts for the arb scanner to consume immediately.
    """
    if not settings.odds_api_key:
        print("[poller] No ODDS_API_KEY set — skipping poll")
        return []

    all_games: list[dict] = []

    async with httpx.AsyncClient() as client:
        async with AsyncSessionLocal() as session:
            for sport_display, sport_key in SPORT_KEYS.items():
                games = await poll_sport(sport_display, sport_key, client)
                for raw in games:
                    raw["_sport_display"] = sport_display
                    await _upsert_game(session, raw, sport_display)
                    await _insert_snapshots(session, raw)
                    all_games.append(raw)

                # Cache per-sport list for the odds board endpoint
                serialisable = []
                for raw in games:
                    bl = _build_best_line(raw)
                    if bl:
                        serialisable.append({
                            "id": raw["id"],
                            "sport": sport_display,
                            "sportKey": raw["sport_key"],
                            "category": _find_category(sport_display),
                            "homeTeam": raw["home_team"],
                            "awayTeam": raw["away_team"],
                            "commenceTime": raw["commence_time"],
                            "bestLine": bl,
                        })
                await cache_set(f"odds:{sport_key}", serialisable, ttl=CACHE_TTL)

            await session.commit()

    print(f"[poller] Polled {len(all_games)} games across {len(SPORT_KEYS)} sports")
    return all_games
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/odds_poller.py
git commit -m "feat: odds poller — fetches Odds API, upserts to Postgres, caches to Redis"
```

---

## Task 7: Arb Scanner Service

**Files:**
- Create: `backend/services/arb_scanner.py`

- [ ] **Step 1: Create backend/services/arb_scanner.py**

```python
from datetime import datetime
from services.redis_client import cache_set
from api.v1.odds import SPORT_KEYS, ARB_ELIGIBLE_SPORTS

ARB_CACHE_KEY = "arb:opportunities"
ARB_CACHE_TTL = 120


def _american_to_decimal(odds: int) -> float:
    if odds > 0:
        return odds / 100 + 1
    return 100 / abs(odds) + 1


async def scan_and_cache(all_games: list[dict]) -> int:
    """
    Scan all polled games for 2-way arb opportunities.
    Writes results to Redis. Returns count of opportunities found.
    """
    from api.v1.odds import SPORT_KEYS
    # Reverse map: sport_key → display name
    key_to_display = {v: k for k, v in SPORT_KEYS.items()}

    opportunities = []

    for raw in all_games:
        sport_key = raw.get("sport_key", "")
        sport_display = raw.get("_sport_display", key_to_display.get(sport_key, sport_key))

        if sport_display not in ARB_ELIGIBLE_SPORTS:
            continue

        # Index: market → outcome → list of (book, price)
        market_lines: dict[str, dict[str, list[tuple[str, int]]]] = {}
        for bm in raw.get("bookmakers", []):
            for market in bm.get("markets", []):
                mkey = market["key"]
                if mkey not in ("h2h",):  # Only moneyline for arb
                    continue
                market_lines.setdefault(mkey, {})
                for o in market.get("outcomes", []):
                    market_lines[mkey].setdefault(o["name"], []).append(
                        (bm["title"], o["price"])
                    )

        for mkey, outcomes in market_lines.items():
            if len(outcomes) != 2:
                continue

            outcome_names = list(outcomes.keys())
            best = []
            for name in outcome_names:
                best_book, best_price = max(
                    outcomes[name],
                    key=lambda x: _american_to_decimal(x[1])
                )
                best.append({"book": best_book, "odds": best_price, "name": name})

            decimals = [_american_to_decimal(b["odds"]) for b in best]
            total_prob = sum(1 / d for d in decimals)

            if total_prob < 1.0:
                legs = [
                    {
                        "book": best[i]["book"],
                        "odds": best[i]["odds"],
                        "impliedProb": round(1 / decimals[i], 6),
                    }
                    for i in range(len(best))
                ]
                opportunities.append({
                    "id": f"{raw['id']}_{mkey}",
                    "sport": sport_key,
                    "category": raw.get("sport_title", sport_display),
                    "homeTeam": raw["home_team"],
                    "awayTeam": raw["away_team"],
                    "commenceTime": raw["commence_time"],
                    "betType": "Moneyline",
                    "legs": legs,
                    "totalImpliedProb": round(total_prob, 6),
                    "profitPct": round((1 / total_prob - 1) * 100, 4),
                    "detectedAt": datetime.utcnow().isoformat() + "Z",
                })

    opportunities.sort(key=lambda o: o["profitPct"], reverse=True)
    await cache_set(ARB_CACHE_KEY, opportunities, ttl=ARB_CACHE_TTL)
    print(f"[arb scanner] {len(opportunities)} opportunities found")
    return len(opportunities)
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/arb_scanner.py
git commit -m "feat: arb scanner — scans polled games for 2-way moneyline arbs, caches to Redis"
```

---

## Task 8: Update FastAPI Endpoints

**Files:**
- Modify: `backend/api/v1/odds.py`
- Modify: `backend/api/v1/bets.py`
- Modify: `backend/api/v1/alerts.py`
- Modify: `backend/api/v1/arb.py`

- [ ] **Step 1: Update backend/api/v1/odds.py — add real endpoint**

Add this import and endpoint to the existing file (keep SPORT_KEYS, SPORT_CATEGORIES, ARB_ELIGIBLE_SPORTS as-is):

```python
from services.redis_client import cache_get

@router.get("/odds", response_model=list[Game])
async def get_odds(
    sport: str | None = Query(None),
    category: str | None = Query(None),
):
    all_games = []
    for display, key in SPORT_KEYS.items():
        if sport and display != sport:
            continue
        if category and SPORT_CATEGORIES.get(category) and display not in SPORT_CATEGORIES[category]:
            continue
        cached = await cache_get(f"odds:{key}")
        if cached:
            all_games.extend(cached)
    return all_games
```

- [ ] **Step 2: Update backend/api/v1/bets.py — persist to Postgres**

Replace the file:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models import Bet as BetModel

router = APIRouter(tags=["bets"])


class BetCreate(BaseModel):
    date: str
    sport: str
    game: str
    betType: str
    odds: int
    stake: float
    result: str


class BetOut(BetCreate):
    id: str
    pnl: float
    closingOdds: int
    clv: float


def _calc_pnl(odds: int, stake: float, result: str) -> float:
    if result == "pending":
        return 0.0
    if result == "loss":
        return -stake
    return (stake * odds / 100) if odds > 0 else (stake * 100 / abs(odds))


@router.get("/bets", response_model=list[BetOut])
async def list_bets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BetModel).order_by(BetModel.created_at.desc()))
    rows = result.scalars().all()
    return [
        BetOut(
            id=str(r.id), date=r.date, sport=r.sport, game=r.game,
            betType=r.bet_type, odds=r.odds, stake=r.stake, result=r.result,
            pnl=r.pnl, closingOdds=r.closing_odds, clv=r.clv,
        )
        for r in rows
    ]


@router.post("/bets", response_model=BetOut, status_code=201)
async def create_bet(body: BetCreate, db: AsyncSession = Depends(get_db)):
    pnl = _calc_pnl(body.odds, body.stake, body.result)
    bet = BetModel(
        date=body.date, sport=body.sport, game=body.game,
        bet_type=body.betType, odds=body.odds, stake=body.stake,
        result=body.result, pnl=pnl, closing_odds=body.odds, clv=0.0,
    )
    db.add(bet)
    await db.commit()
    await db.refresh(bet)
    return BetOut(
        id=str(bet.id), date=bet.date, sport=bet.sport, game=bet.game,
        betType=bet.bet_type, odds=bet.odds, stake=bet.stake, result=bet.result,
        pnl=bet.pnl, closingOdds=bet.closing_odds, clv=bet.clv,
    )
```

- [ ] **Step 3: Update backend/api/v1/alerts.py — persist to Postgres**

Replace the file:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.session import get_db
from db.models import Alert as AlertModel
from datetime import date

router = APIRouter(tags=["alerts"])


class AlertCreate(BaseModel):
    game: str
    betType: str
    targetOdds: int
    book: str


class AlertOut(AlertCreate):
    id: str
    status: str
    createdAt: str


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertModel).order_by(AlertModel.id.desc()))
    rows = result.scalars().all()
    return [
        AlertOut(id=str(r.id), game=r.game, betType=r.bet_type,
                 targetOdds=r.target_odds, book=r.book,
                 status=r.status, createdAt=r.created_at)
        for r in rows
    ]


@router.post("/alerts", response_model=AlertOut, status_code=201)
async def create_alert(body: AlertCreate, db: AsyncSession = Depends(get_db)):
    alert = AlertModel(
        game=body.game, bet_type=body.betType,
        target_odds=body.targetOdds, book=body.book,
        status="active", created_at=date.today().isoformat(),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertOut(
        id=str(alert.id), game=alert.game, betType=alert.bet_type,
        targetOdds=alert.target_odds, book=alert.book,
        status=alert.status, createdAt=alert.created_at,
    )


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertModel).where(AlertModel.id == int(alert_id)))
    alert = result.scalar_one_or_none()
    if alert:
        await db.delete(alert)
        await db.commit()
```

- [ ] **Step 4: Update backend/api/v1/arb.py — read from Redis**

Add this import and endpoint (keep `scan_for_arb` and models for reference):

```python
from services.redis_client import cache_get
from services.arb_scanner import ARB_CACHE_KEY

@router.get("/arb/opportunities", response_model=list[ArbOpportunity])
async def get_arb_opportunities(sport: str | None = None, min_profit_pct: float = 0.0):
    cached = await cache_get(ARB_CACHE_KEY) or []
    results = cached
    if sport:
        results = [o for o in results if o["sport"] == sport or o["category"] == sport]
    if min_profit_pct > 0:
        results = [o for o in results if o["profitPct"] >= min_profit_pct]
    return results
```

- [ ] **Step 5: Commit**

```bash
git add backend/api/
git commit -m "feat: wire real Postgres + Redis into bets, alerts, odds, arb endpoints"
```

---

## Task 9: Update main.py — Lifespan + Scheduler

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Replace backend/main.py**

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import odds, alerts, bets, arb, sharp
from config import settings
from services.redis_client import close_redis
from services.odds_poller import poll_all_active_sports
from services.arb_scanner import scan_and_cache


async def run_poll_cycle():
    """Called by the scheduler: poll odds then scan for arb."""
    games = await poll_all_active_sports()
    await scan_and_cache(games)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run one poll immediately on startup so data is available right away
    await run_poll_cycle()

    # Schedule recurring polls
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_poll_cycle,
        "interval",
        seconds=settings.poll_interval_seconds,
        id="odds_poll",
    )
    scheduler.start()

    yield

    scheduler.shutdown()
    await close_redis()


app = FastAPI(title="OddsIQ API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(odds.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(bets.router, prefix="/api/v1")
app.include_router(arb.router, prefix="/api/v1")
app.include_router(sharp.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Commit**

```bash
git add backend/main.py
git commit -m "feat: lifespan startup — immediate poll on boot, APScheduler recurring poll"
```

---

## Task 10: Smoke Test the Full Stack

- [ ] **Step 1: Start all services**

```bash
cd OddsIQ
docker compose up postgres redis -d
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Watch the logs — you should see:
```
[poller] Polled N games across 55 sports
[arb scanner] X opportunities found
```

- [ ] **Step 2: Check the odds endpoint**

```bash
curl http://localhost:8000/api/v1/odds?sport=NFL | python3 -m json.tool | head -40
```

Expected: JSON array of NFL games with bestLine data.

- [ ] **Step 3: Check the arb endpoint**

```bash
curl http://localhost:8000/api/v1/arb/opportunities | python3 -m json.tool
```

Expected: JSON array (may be empty — arbs are rare on the free tier).

- [ ] **Step 4: Check the API docs**

Open http://localhost:8000/docs — all endpoints should be listed and testable.

- [ ] **Step 5: Log a test bet**

```bash
curl -X POST http://localhost:8000/api/v1/bets \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-05-30","sport":"NFL","game":"Chiefs vs Bills","betType":"Chiefs ML","odds":-150,"stake":100,"result":"pending"}'
```

Expected: `201` with the new bet including `id`.

- [ ] **Step 6: Final commit + push**

```bash
git add -A
git commit -m "feat(v3): backend operational — Postgres, Redis, Odds API poller, arb scanner"
git push origin main
```

---

## API Key Quick Reference

| Step | What to do |
|------|-----------|
| 1 | Go to https://the-odds-api.com/account/ |
| 2 | Sign up / log in |
| 3 | Copy the API key shown on the dashboard |
| 4 | Paste it into `backend/.env` as `ODDS_API_KEY=your_key` |
| 5 | Start the backend — it polls on first boot |

Free tier gives 500 credits/month. Each sport poll costs 1 credit. With 55 sports, one full poll cycle = 55 credits. You have ~9 full cycles before you hit the limit — use them for testing, not automated polling. Set `POLL_INTERVAL_SECONDS=99999` in `.env` to disable the scheduler and only poll on startup.
