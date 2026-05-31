"""
OddsIQ FastAPI application entry point.

Startup sequence (lifespan):
  1. Test Redis connection
  2. Run initial odds poll (so the board isn't empty on first load)
  3. Run initial arb scan
  4. Start APScheduler — polls odds + runs arb scan on POLL_INTERVAL_SECONDS

Shutdown: close Redis connection pool, stop scheduler.
"""
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import odds, alerts, bets, arb, sharp
from config import settings
from services.redis_client import get_redis, close_redis
from services.odds_poller import poll_all_odds
from services.arb_scanner import scan_for_arb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def poll_and_scan() -> None:
    """Combined task: poll odds then scan for arb."""
    await poll_all_odds()
    await scan_for_arb()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────────────────────
    logger.info("Starting OddsIQ API...")

    # Verify Redis is reachable
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connected")
    except Exception as exc:
        logger.warning(f"Redis not reachable at startup: {exc} — odds board will be empty until Redis is up")

    # Run one poll immediately so there's data on first request
    if settings.odds_api_key and settings.poll_interval_seconds < 99999:
        logger.info("Running initial odds poll...")
        await poll_and_scan()
    else:
        logger.info(
            f"Skipping initial poll "
            f"(POLL_INTERVAL_SECONDS={settings.poll_interval_seconds}, key_set={bool(settings.odds_api_key)})"
        )

    # Schedule recurring polls (only if a reasonable interval is set)
    if settings.poll_interval_seconds < 99999:
        scheduler.add_job(
            poll_and_scan,
            "interval",
            seconds=settings.poll_interval_seconds,
            id="poll_and_scan",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(f"Scheduler started — polling every {settings.poll_interval_seconds}s")
    else:
        logger.info("Scheduler not started (POLL_INTERVAL_SECONDS >= 99999 — dev/credit-save mode)")

    yield

    # ── Shutdown ─────────────────────────────────────────────────────────────
    if scheduler.running:
        scheduler.shutdown(wait=False)
    await close_redis()
    logger.info("OddsIQ API shutdown complete")


app = FastAPI(title="OddsIQ API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # Allow localhost in dev + any Vercel deployment URL in prod.
    # CORS_ORIGINS env var can override with a comma-separated list.
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
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
    """Quick liveness check. Also reports Redis reachability."""
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unavailable"
    return {"status": "ok", "redis": redis_status}


@app.post("/api/v1/admin/poll", tags=["admin"])
async def trigger_poll():
    """
    Manually trigger an odds poll + arb scan.
    Use this in dev to fetch live data without waiting for the scheduler.
    POST http://localhost:8000/api/v1/admin/poll
    """
    await poll_and_scan()
    return {"message": "Poll and arb scan triggered"}
