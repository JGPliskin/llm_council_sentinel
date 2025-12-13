
import unittest
from unittest.mock import MagicMock, patch, ANY
import asyncio
import sys
import os
import time

try:
    from unittest.mock import AsyncMock
except ImportError:
    class AsyncMock(MagicMock):
        async def __call__(self, *args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)

# Adjust path to include backend
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))

import council
from council import stage1_collect_responses, stage2_collect_rankings
import config


# Helper for Py3.7 Async Tests
class AsyncTestCase(unittest.TestCase):
    def run_async(self, coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


# Helper for Py3.7 Future creation
def create_future(value):
    f = asyncio.Future()
    f.set_result(value)
    return f

class TestConcurrencyLogic(AsyncTestCase):
    
    def setUp(self):
        # Reset config to defaults for each test
        config.DEFAULT_CONCURRENCY_STAGE1 = 6
        config.STAGE1_DEADLINE = None
        self.councilors = [
            {"id": f"c{i}", "name": f"Councilor {i}", "model": f"model_{i}", "persona_path": "dummy", 
             "stage_limits": {"stage1": {"timeout": 1.0}}} 
            for i in range(10)
        ]

    def test_concurrency_limit_stage1(self):
        async def _test():
            # Patch constants in council module
            with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.query_model") as mock_query, \
                 patch("council.DEFAULT_CONCURRENCY_STAGE1", 3):
                 
                # Scenario: 10 tasks, Limit 3.
                current_inflight = 0
                max_inflight = 0
                
                async def side_effect(*args, **kwargs):
                    nonlocal current_inflight, max_inflight
                    current_inflight += 1
                    max_inflight = max(max_inflight, current_inflight)
                    # Simulate work
                    await asyncio.sleep(0.1) 
                    current_inflight -= 1
                    return {"content": '{"judge_card": {"core_reasons":["a","b"]}}', "status_code": 200}
        
                mock_query.side_effect = side_effect
                
                # Run
                await stage1_collect_responses("query", self.councilors)
                
                # Verify
                self.assertTrue(max_inflight <= 3, f"Max inflight {max_inflight} exceeded limit 3")
                self.assertEqual(mock_query.call_count, 10)
        
        self.run_async(_test())

    def test_retry_mixed_failure(self):
        async def _test():
            with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.query_model") as mock_query, \
                 patch("asyncio.sleep", new_callable=AsyncMock): 

                # Scenario: Mixed failures
                councilors = [
                    {"id": "c1", "name": "C1", "model": "m_retry_net", "persona_path": "", "stage_limits": {}},
                    {"id": "c2", "name": "C2", "model": "m_retry_json", "persona_path": "", "stage_limits": {}},
                    {"id": "c3", "name": "C3", "model": "m_fail_mixed", "persona_path": "", "stage_limits": {}},
                ]
                
                # State tracking for mocks
                call_counts = {"m_retry_net": 0, "m_retry_json": 0, "m_fail_mixed": 0}
                
                async def side_effect(model, *args, **kwargs):
                    call_counts[model] += 1
                    count = call_counts[model]
                    
                    if model == "m_retry_net":
                        if count == 1:
                            return {"error": True, "status_code": 429, "content": "Rate Limit"}
                        return {"content": '{"status":"ok", "judge_card": {"core_reasons":["Access","Granted"]}}'}
                        
                    if model == "m_retry_json":
                        if count == 1:
                            return {"content": "Not JSON"}
                        return {"content": '{"status":"ok", "judge_card": {"core_reasons":["JSON","Fixed"]}}'}
                        
                    if model == "m_fail_mixed":
                        if count == 1:
                            return {"error": True, "status_code": 429}
                        # Second attempt fails with bad JSON
                        return {"content": "Still Not JSON"}
                        
                    return {}
        
                mock_query.side_effect = side_effect
                
                with patch("council.DEFAULT_CONCURRENCY_STAGE1", 10):
                    results = await stage1_collect_responses("q", councilors)
                
                # Assertions
                r1 = next(r for r in results if r["councilor_id"] == "c1")
                self.assertEqual(r1["status"], "ok")
                
                r2 = next(r for r in results if r["councilor_id"] == "c2")
                self.assertEqual(r2["status"], "ok")
                
                r3 = next(r for r in results if r["councilor_id"] == "c3")
                self.assertEqual(r3["status"], "failed")
                self.assertEqual(call_counts["m_fail_mixed"], 2)
        
        self.run_async(_test())


    def test_stage_deadline_partial_results(self):
        async def _test():
            with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.query_model") as mock_query, \
                 patch("council.STAGE1_DEADLINE", 0.5), \
                 patch("council.DEFAULT_CONCURRENCY_STAGE1", 10):

                councilors = [
                    {"id": "fast", "name": "Fast", "model": "m_fast", "persona_path": "", "stage_limits": {}},
                    {"id": "slow", "name": "Slow", "model": "m_slow", "persona_path": "", "stage_limits": {}},
                ]
                
                # Use side_effect with sleep
                async def side_effect(model, *args, **kwargs):
                    if model == "m_fast":
                         return {"content": '{"status":"ok", "judge_card": {"core_reasons":["Fast","Win"]}}'}
                    if model == "m_slow":
                        try:
                            await asyncio.sleep(2.0)
                        except asyncio.CancelledError:
                            raise
                        return {"content": "Too late"}
                
                mock_query.side_effect = side_effect
                
                results = await stage1_collect_responses("q", councilors)
                
                # Fast should succeed
                r_fast = next(r for r in results if r["councilor_id"] == "fast")
                self.assertEqual(r_fast["status"], "ok")
                
                # Slow should fail with STAGE_DEADLINE
                r_slow = next(r for r in results if r["councilor_id"] == "slow")
                # Wait, assertEqual failures help debug, but here checks structure
                self.assertEqual(r_slow["status"], "failed", f"Slow result unexpected: {r_slow}")
                self.assertEqual(r_slow["error"]["code"], "STAGE_DEADLINE")
                
        self.run_async(_test())

    def test_retry_after_header(self):
        async def _test():
            with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.query_model") as mock_query, \
                 patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                 
                councilors = [{"id": "c1", "model": "m1", "persona_path": "", "stage_limits": {}}]
                
                # Mock a 429 with Retry-After header
                # Use Futures
                mock_query.side_effect = [
                    create_future({
                        "error": True, 
                        "status_code": 429, 
                        "headers": {"retry-after": "10.5"},
                        "content": "Rate Limit"
                    }),
                    create_future({"content": '{"status":"ok", "judge_card": {"core_reasons":["Retry","Success"]}}'})
                ]
                
                results = await stage1_collect_responses("q", councilors)
                
                self.assertEqual(results[0]["status"], "ok")
                # Verify sleep called with ~10.5
                mock_sleep.assert_called_once()
                args, _ = mock_sleep.call_args
                self.assertAlmostEqual(args[0], 10.5, delta=0.1)
        
        self.run_async(_test())

    def test_fatal_error_no_retry(self):
        async def _test():
             with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.query_model") as mock_query:
                 
                councilors = [{"id": "c1", "model": "m1", "persona_path": "", "stage_limits": {}}]
                
                # Mock a 401 Fatal Error
                mock_query.side_effect = [
                     create_future({"error": True, "status_code": 401, "content": "Unauthorized"})
                ]
                
                results = await stage1_collect_responses("q", councilors)
                
                self.assertEqual(results[0]["status"], "failed")
                # Should NOT retry, so call count should be 1
                self.assertEqual(mock_query.call_count, 1)
        
        self.run_async(_test())

    def test_semaphore_released_during_backoff(self):
        async def _test():
            # We need to verify that while one task is "sleeping" for backoff, 
            # another task can acquire the semaphore.
            
            # Use a real semaphore behavior.
            from council import _request_stage1_bounded
            semaphore = asyncio.Semaphore(1) # Strict limit 1
            
            # Shared state
            sem_acquired_during_sleep = False
            
            async def mock_sleep(delay):
                # When the first task sleeps (backoff), we try to acquire semaphore
                nonlocal sem_acquired_during_sleep
                if not semaphore.locked():
                     # If not locked, it means it was released!
                     # Double check by trying to acquire
                     try:
                         await asyncio.wait_for(semaphore.acquire(), 0.1)
                         sem_acquired_during_sleep = True
                         semaphore.release()
                     except:
                         pass

            with patch("council.fetch_persona", return_value="System Prompt"), \
                 patch("council.query_model") as mock_query, \
                 patch("asyncio.sleep", side_effect=mock_sleep):
                 
                 councilor = {"id": "c1", "model": "m1", "persona_path": "", "stage_limits": {}}
                 
                 # Fail first, Succeed second
                 mock_query.side_effect = [
                     create_future({"error": True, "status_code": 429, "content": "Rate Limit"}),
                     create_future({"content": '{"status":"ok", "judge_card": {"core_reasons":["a","b"]}}'})
                 ]
                 
                 # Run single bounded query
                 await _request_stage1_bounded(semaphore, councilor, "q")
                 
                 self.assertTrue(sem_acquired_during_sleep, "Semaphore should be released during backoff sleep")
                 
        self.run_async(_test())



if __name__ == "__main__":
    unittest.main()
