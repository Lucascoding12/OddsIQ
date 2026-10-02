"""
In-process odds store — the single source of truth for live odds.

Why in-memory instead of reading Redis per request:
  The poller runs inside the API process, so the freshest snapshot is already
  in memory the moment it's fetched. Serving from here skips a network hop
  and a multi-hundred-KB JSON parse on every request, and lets the arb scan
  run immediately on each new snapshot. Redis is kept only as a write-through
  copy so a restart can warm-start without spending API credits.

Every update bumps `version`. Derived views (normalized board, arb payloads,
sharp metrics) are memoized against that version, so each is computed at most
once per poll no matter how many clients ask. SSE listeners await `changed()`.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from config import settings
from services.arb_engine import ArbCandidate, arbs_from_grouped
from services.ev_engine import EvBet, ev_from_grouped
from services.markets import ScanConfig, group_game

logger = logging.getLogger(__name__)


@dataclass
class PollStats:
    credits_remaining: int | None = None
    credits_used: int | None = None
    last_call_cost: int | None = None
    sports: list[str] = field(default_factory=list)
    last_error: str | None = None
    fetch_ms: float = 0.0


class OddsStore:
    def __init__(self) -> None:
        self.games: list[dict] = []
        self.polled_at: str | None = None
        self.version = 0
        self.arbs: list[ArbCandidate] = []
        self.ev_bets: list[EvBet] = []
        self.scan_ms = 0.0
        self.stats = PollStats()
        # arb id → ISO time first observed; lets the UI show how long an arb has lived
        self.first_seen: dict[str, str] = {}
        self._memo: dict[Any, Any] = {}
        self._memo_version = -1
        self._changed = asyncio.Event()

    def default_scan_config(self) -> ScanConfig:
        return ScanConfig(
            max_quote_age_s=settings.arb_max_quote_age_seconds or None,
            include_live=settings.arb_include_live,
            min_return_pct=settings.arb_near_miss_pct,
        )

    def update(self, games: list[dict], polled_at: str | None = None) -> None:
        """Swap in a new snapshot and rescan. Synchronous: callers never see a half-updated store."""
        start = time.perf_counter()
        cfg = self.default_scan_config()
        now = time.time()
        arbs: list[ArbCandidate] = []
        ev_bets: list[EvBet] = []
        # Group once per game; both engines read the same grouping.
        for game in games:
            gm = group_game(game, now, cfg)
            if gm is None:
                continue
            arbs.extend(arbs_from_grouped(gm, cfg))
            ev_bets.extend(ev_from_grouped(gm, cfg, settings.ev_floor_pct))
        arbs.sort(key=lambda a: a.return_pct, reverse=True)
        ev_bets.sort(key=lambda b: b.ev_pct, reverse=True)
        self.scan_ms = (time.perf_counter() - start) * 1000

        now_iso = datetime.now(timezone.utc).isoformat()
        live_ids = {a.id for a in arbs} | {b.id for b in ev_bets}
        self.first_seen = {k: v for k, v in self.first_seen.items() if k in live_ids}
        for item in (*arbs, *ev_bets):
            self.first_seen.setdefault(item.id, now_iso)

        self.games = games
        self.arbs = arbs
        self.ev_bets = ev_bets
        self.polled_at = polled_at or now_iso
        self.version += 1

        profitable = sum(1 for a in arbs if a.return_pct > 0)
        logger.info(
            f"Store v{self.version}: {len(games)} games, {profitable} arbs "
            f"({len(arbs) - profitable} near-misses), {len(ev_bets)} +EV, scan {self.scan_ms:.1f}ms"
        )

        # Wake everyone waiting, then arm a fresh event for the next update.
        self._changed.set()
        self._changed = asyncio.Event()

    async def changed(self, timeout: float) -> bool:
        """Wait for the next update. False on timeout (callers use it to send keepalives)."""
        event = self._changed
        try:
            await asyncio.wait_for(event.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def memo(self, key: Any, compute: Callable[[], Any]) -> Any:
        """Compute once per snapshot version. Returned values are shared — treat as read-only."""
        if self._memo_version != self.version:
            self._memo.clear()
            self._memo_version = self.version
        if key not in self._memo:
            self._memo[key] = compute()
        return self._memo[key]

    def status(self) -> dict:
        return {
            "version": self.version,
            "polled_at": self.polled_at,
            "games": len(self.games),
            "arbs": sum(1 for a in self.arbs if a.return_pct > 0),
            "near_misses": sum(1 for a in self.arbs if a.return_pct <= 0),
            "ev_bets": len(self.ev_bets),
            "scan_ms": round(self.scan_ms, 2),
            "fetch_ms": round(self.stats.fetch_ms, 1),
            "credits_remaining": self.stats.credits_remaining,
            "credits_used": self.stats.credits_used,
            "credits_per_poll": self.stats.last_call_cost,
            "sports": self.stats.sports,
            "last_error": self.stats.last_error,
            "poll_interval_seconds": settings.poll_interval_seconds,
        }


store = OddsStore()
