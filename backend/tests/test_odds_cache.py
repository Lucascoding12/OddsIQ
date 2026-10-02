"""
Tests for services.odds_cache — the in-process memoization layer.

Run from backend/:  uv run python -m unittest discover -s tests
"""
import json
import unittest
from unittest.mock import AsyncMock, patch

from services import odds_cache


class FakeRedis:
    def __init__(self, store: dict[str, str]):
        self.store = store

    async def get(self, key: str) -> str | None:
        return self.store.get(key)


class OddsCacheTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        odds_cache.clear()
        self.store: dict[str, str] = {}
        patcher = patch(
            "services.odds_cache.get_redis",
            new=AsyncMock(return_value=FakeRedis(self.store)),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_get_json_parses_payload(self) -> None:
        self.store["odds:all"] = json.dumps([{"id": "g1"}])
        result = await odds_cache.get_json("odds:all")
        self.assertEqual(result, [{"id": "g1"}])

    async def test_get_json_returns_none_for_missing_key(self) -> None:
        self.assertIsNone(await odds_cache.get_json("odds:all"))

    async def test_parse_is_memoized_while_payload_unchanged(self) -> None:
        self.store["odds:all"] = json.dumps([{"id": "g1"}])
        first = await odds_cache.get_json("odds:all")
        second = await odds_cache.get_json("odds:all")
        self.assertIs(first, second)

    async def test_parse_refreshes_when_payload_changes(self) -> None:
        self.store["odds:all"] = json.dumps([{"id": "g1"}])
        first = await odds_cache.get_json("odds:all")
        self.store["odds:all"] = json.dumps([{"id": "g2"}])
        second = await odds_cache.get_json("odds:all")
        self.assertIsNot(first, second)
        self.assertEqual(second, [{"id": "g2"}])

    async def test_derived_computes_once_per_payload(self) -> None:
        self.store["odds:all"] = json.dumps([1, 2, 3])
        calls: list[int] = []

        def compute(parsed: list[int]) -> int:
            calls.append(1)
            return sum(parsed)

        first = await odds_cache.get_derived("odds:all", "sum", compute)
        second = await odds_cache.get_derived("odds:all", "sum", compute)
        self.assertEqual(first, 6)
        self.assertEqual(second, 6)
        self.assertEqual(len(calls), 1)

    async def test_derived_recomputes_when_payload_changes(self) -> None:
        self.store["odds:all"] = json.dumps([1, 2, 3])
        await odds_cache.get_derived("odds:all", "sum", sum)
        self.store["odds:all"] = json.dumps([10, 20])
        result = await odds_cache.get_derived("odds:all", "sum", sum)
        self.assertEqual(result, 30)

    async def test_derived_tags_are_independent(self) -> None:
        self.store["odds:all"] = json.dumps([1, 2, 3])
        total = await odds_cache.get_derived("odds:all", "sum", sum)
        count = await odds_cache.get_derived("odds:all", "len", len)
        self.assertEqual(total, 6)
        self.assertEqual(count, 3)

    async def test_derived_returns_none_and_evicts_for_missing_key(self) -> None:
        self.store["odds:all"] = json.dumps([1])
        await odds_cache.get_derived("odds:all", "sum", sum)
        del self.store["odds:all"]
        self.assertIsNone(await odds_cache.get_derived("odds:all", "sum", sum))


if __name__ == "__main__":
    unittest.main()
