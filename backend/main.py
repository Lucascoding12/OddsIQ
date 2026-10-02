"""
OddsIQ FastAPI application entry point.

Startup sequence (lifespan):
  1. Warm-start the in-memory store from Redis (no API credits spent)
  2. Run an initial poll if polling is enabled
  3. Start APScheduler — polls on POLL_INTERVAL_SECONDS; every poll rescans arbs

Shutdown: stop scheduler, close the HTTP client and Redis pool.
"""
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import secrets

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from api.v1 import odds, alerts, bets, arb, ev, sharp, tools
from config import settings
from services.odds_poller import close_client, poll_all_odds, snapshot_age_seconds, warm_start
from services.odds_store import store
from services.redis_client import get_redis, close_redis
from ui import routes as ui

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
# httpx logs every request URL at INFO, and the Odds API key travels as a
# query parameter — keep it out of the logs.
logging.getLogger("httpx").setLevel(logging.WARNING)

scheduler = AsyncIOScheduler()

# Sentinel meaning "never poll automatically" — protects free-tier credits in dev.
POLLING_DISABLED = 99999


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OddsIQ API...")
    await warm_start()

    polling = bool(settings.odds_api_key) and settings.poll_interval_seconds < POLLING_DISABLED
    if polling:
        age = snapshot_age_seconds()
        if age is not None and age < settings.poll_interval_seconds:
            logger.info(f"Warm snapshot is {age / 60:.0f} min old — skipping initial poll to save credits")
        else:
            try:
                await poll_all_odds()
            except Exception as exc:
                logger.warning(f"Initial poll failed (will retry on schedule): {exc}")
        scheduler.add_job(
            poll_all_odds,
            "interval",
            seconds=settings.poll_interval_seconds,
            id="poll",
            replace_existing=True,
            # A slow poll must not stack a second one behind it.
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()
        logger.info(f"Polling every {settings.poll_interval_seconds}s")
    else:
        logger.info(
            f"Polling disabled (POLL_INTERVAL_SECONDS={settings.poll_interval_seconds}, "
            f"key_set={bool(settings.odds_api_key)}) — use POST /api/v1/admin/poll"
        )

    yield

    if scheduler.running:
        scheduler.shutdown(wait=False)
    await close_client()
    await close_redis()
    logger.info("OddsIQ API shutdown complete")


app = FastAPI(title="OddsIQ API", version="0.2.0", lifespan=lifespan)

# Odds payloads are large, repetitive JSON — gzip cuts them to roughly a tenth.
# SSE responses are excluded by Starlette automatically.
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.add_middleware(
    CORSMiddleware,
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
app.include_router(ev.router, prefix="/api/v1")
app.include_router(tools.router, prefix="/api/v1")
app.include_router(ui.router)


@app.get("/health")
async def health():
    """Liveness check. Also reports Redis reachability and snapshot freshness."""
    try:
        redis = await get_redis()
        await redis.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unavailable"
    return {"status": "ok", "redis": redis_status, "polled_at": store.polled_at}


LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


@app.post("/api/v1/admin/poll", tags=["admin"])
async def trigger_poll(request: Request, x_admin_token: str | None = Header(default=None)):
    """
    Manually trigger an odds poll (and therefore an arb scan). Every poll
    spends API credits, so it's locked: ADMIN_TOKEN must match the
    X-Admin-Token header, or with no token set, only local requests work.
    """
    if settings.admin_token:
        if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.admin_token):
            raise HTTPException(403, detail="Missing or wrong X-Admin-Token")
    elif (request.client.host if request.client else "") not in LOCAL_HOSTS:
        raise HTTPException(403, detail="Set ADMIN_TOKEN to trigger polls remotely")
    await poll_all_odds()
    return store.status()
