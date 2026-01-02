import unittest
from unittest.mock import MagicMock, patch
import asyncio
import sys
import os

try:
    from unittest.mock import AsyncMock
except ImportError:
    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)

# Adjust path to include backend
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

from council import stage1_collect_responses, health_manager
import config


class AsyncTestCase(unittest.TestCase):
    def run_async(self, coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


class TestConcurrencyLogic(AsyncTestCase):

    def setUp(self):
        config.DEFAULT_CONCURRENCY_STAGE1 = 6
        config.STAGE1_DEADLINE = None
        self.councilors = [
            {
                "id": f"c{i}",
                "name": f"Councilor {i}",
                "model": f"model_{i}",
                "persona_path": "dummy",
                "stage_limits": {"stage1": {"timeout": 1.0}}
            }
            for i in range(6)
        ]
        health_manager._records = {}
        for councilor in self.councilors:
            health_manager.update_status(councilor["model"], True)

    def test_concurrency_limit_stage1(self):
        async def _test():
            with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.stream_model") as mock_stream, \
                 patch("council.DEFAULT_CONCURRENCY_STAGE1", 2):

                current_inflight = 0
                max_inflight = 0

                async def side_effect(*args, **kwargs):
                    nonlocal current_inflight, max_inflight
                    current_inflight += 1
                    max_inflight = max(max_inflight, current_inflight)
                    await asyncio.sleep(0.05)
                    current_inflight -= 1
                    return {"content": "ok", "model": "m"}

                mock_stream.side_effect = side_effect

                await stage1_collect_responses("query", self.councilors)

                self.assertTrue(max_inflight <= 2, f"Max inflight {max_inflight} exceeded limit 2")
                self.assertEqual(mock_stream.call_count, 6)

        self.run_async(_test())

    def test_stage_deadline_partial_results(self):
        async def _test():
            with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.stream_model") as mock_stream, \
                 patch("council.STAGE1_DEADLINE", 0.2), \
                 patch("council.DEFAULT_CONCURRENCY_STAGE1", 10):

                councilors = [
                    {"id": "fast", "name": "Fast", "model": "m_fast", "persona_path": "", "stage_limits": {}},
                    {"id": "slow", "name": "Slow", "model": "m_slow", "persona_path": "", "stage_limits": {}},
                ]
                health_manager.update_status("m_fast", True)
                health_manager.update_status("m_slow", True)

                async def side_effect(model, *args, **kwargs):
                    if model == "m_fast":
                        return {"content": "fast answer", "model": model}
                    if model == "m_slow":
                        try:
                            await asyncio.sleep(1.0)
                        except asyncio.CancelledError:
                            raise
                        return {"content": "slow answer", "model": model}

                mock_stream.side_effect = side_effect

                results = await stage1_collect_responses("q", councilors)

                r_fast = next(r for r in results if r["councilor_id"] == "fast")
                self.assertEqual(r_fast["status"], "ok")

                r_slow = next(r for r in results if r["councilor_id"] == "slow")
                self.assertEqual(r_slow["status"], "failed", f"Slow result unexpected: {r_slow}")
                self.assertEqual(r_slow["error"]["code"], "STAGE_DEADLINE")

        self.run_async(_test())

    def test_stage1_answer_delta_callback(self):
        async def _test():
            with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.stream_model") as mock_stream:

                captured = []

                async def side_effect(model, *args, **kwargs):
                    on_content = kwargs.get("on_content")
                    if on_content:
                        await on_content("Hello ")
                        await on_content("World")
                    return {"content": "Hello World", "model": model}

                async def on_delta(cid, delta):
                    captured.append((cid, delta))

                mock_stream.side_effect = side_effect
                health_manager.update_status("m1", True)

                await stage1_collect_responses(
                    "q",
                    [{"id": "c1", "name": "C1", "model": "m1", "persona_path": "", "stage_limits": {}}],
                    on_answer_delta=on_delta
                )

                self.assertEqual(captured, [("c1", "Hello "), ("c1", "World")])

        self.run_async(_test())


if __name__ == "__main__":
    unittest.main()
