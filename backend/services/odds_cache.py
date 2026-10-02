"""
In-process memoization for JSON payloads read from Redis.

The poller refreshes Redis only every POLL_INTERVAL_SECONDS (hours in
production), but every /odds and /sharp request was re-running json.loads —
and re-deriving normalized views — over the same multi-hundred-KB payload.

Here the parse and any derived computation are memoized per Redis key:
as long as the raw payload string is unchanged, the cached result is reused.
Comparing the raw string is a C-level memcmp (microseconds); re-parsing and
re-normalizing is milliseconds per request at this payload size.

Returned values are shared between requests — treat them as read-only.
"""
from typing import Any, Callable

import json

from services.redis_client import get_redis

# redis key → (raw payload, parsed value)
_parse_cache: dict[str, tuple[str, Any]] = {}
# (redis key, tag) → (raw payload, derived value)
_derived_cache: dict[tuple[str, str], tuple[str, Any]] = {}


async def _get_raw_and_parsed(key: str) -> tuple[str, Any] | None:
    redis = await get_redis()
    raw = await redis.get(key)
    if raw is None:
        _parse_cache.pop(key, None)
        return None

    cached = _parse_cache.get(key)
    if cached is not None and cached[0] == raw:
        # Return the cached tuple so the raw string object stays stable
        # across calls — keeps derived-cache comparisons cheap.
        return cached

    parsed = json.loads(raw)
    _parse_cache[key] = (raw, parsed)
    return raw, parsed


async def get_json(key: str) -> Any | None:
    """Fetch and parse a JSON payload from Redis, memoizing the parse."""
    entry = await _get_raw_and_parsed(key)
    return entry[1] if entry is not None else None


async def get_derived(key: str, tag: str, compute: Callable[[Any], Any]) -> Any | None:
    """
    Fetch a JSON payload and return `compute(parsed)`, recomputing only when
    the underlying payload changes. `tag` namespaces independent derivations
    of the same key (e.g. "normalized:all" vs "normalized:Baseball").
    """
    entry = await _get_raw_and_parsed(key)
    if entry is None:
        _derived_cache.pop((key, tag), None)
        return None

    raw, parsed = entry
    cached = _derived_cache.get((key, tag))
    if cached is not None and cached[0] == raw:
        return cached[1]

    value = compute(parsed)
    _derived_cache[(key, tag)] = (raw, value)
    return value


def clear() -> None:
    """Drop all memoized entries (used by tests)."""
    _parse_cache.clear()
    _derived_cache.clear()
