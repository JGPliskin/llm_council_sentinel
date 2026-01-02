import json
from unittest.mock import patch

from fastapi.testclient import TestClient

import backend.main as main


def test_streaming_sse_includes_thinking_and_delta():
    client = TestClient(main.app)

    conversation = {
        "id": "conv_test",
        "messages": [],
        "active_councilor_ids": ["c1"],
        "active_chairman": main.CHAIRMAN.get("id"),
        "schema_version": 2
    }

    async def mock_stage1_collect_responses(
        user_query,
        councilors,
        on_result=None,
        on_thinking=None,
        on_answer_delta=None,
        on_answer_done=None,
        enable_thinking=True
    ):
        if on_thinking:
            await on_thinking("c1", "stage1", {"bullet_id": "b1", "title": "Analyze", "detail": "Detail", "op": "append"}, "m1")
        if on_answer_delta:
            await on_answer_delta("c1", "Hello")
        if on_answer_done:
            await on_answer_done("c1")
        result = {"councilor_id": "c1", "councilor_name": "C1", "model": "m1", "status": "ok", "answer_markdown": "Hello"}
        if on_result:
            await on_result(result)
        return [result]

    async def mock_stage2_collect_rankings(*args, **kwargs):
        return {"skipped": True, "skipped_reason": "insufficient_candidates", "reviews": [], "anon_map": {}}

    async def mock_stage3_synthesize_final(*args, **kwargs):
        return {"status": "ok", "model": "m3", "response": "Final"}

    with patch("backend.main.storage.get_conversation", return_value=conversation), \
         patch("backend.main.storage.add_user_message"), \
         patch("backend.main.storage.add_assistant_message"), \
         patch("backend.main.storage.update_conversation_title"), \
         patch("backend.main.resolve_target_councilors", return_value=([{"id": "c1", "name": "C1", "model": "m1"}], False, [])), \
         patch("backend.main.stage1_collect_responses", side_effect=mock_stage1_collect_responses), \
         patch("backend.main.stage2_collect_rankings", side_effect=mock_stage2_collect_rankings), \
         patch("backend.main.stage3_synthesize_final", side_effect=mock_stage3_synthesize_final):

        response = client.post(
            "/api/conversations/conv_test/message/stream",
            json={"content": "hi", "enable_thinking": True}
        )

        events = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                payload = json.loads(line[6:])
                events.append(payload)

        assert any(e.get("type") == "thinking" and e.get("bullet_id") == "b1" for e in events)
        assert any(e.get("type") == "stage1_answer_delta" and e.get("delta") == "Hello" for e in events)
