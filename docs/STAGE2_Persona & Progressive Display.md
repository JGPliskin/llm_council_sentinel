Implementation Plan - Stage 2 Persona & Progressive Display

Goal
Enhance Stage 2 with persona-driven judging, display real names in rankings, fix council member name display, and implement progressive streaming so responses appear as soon as they are ready (instead of waiting for an entire stage to finish).

Scope

1. Stage 2 persona-driven judging (Persona + Rubric + JSON contract)
2. Stage 2 ranking UI uses real councilor names (not anon labels)
3. Fix “Council Members” displaying model IDs instead of character/role names
4. Progressive streaming display for Stage 1 and Stage 2 (partial → complete)

User Review Required
IMPORTANT

Schema Enforcement & Persona Risk
We will stack prompts (Judge Persona + Judge Rubric + JSON Hard Constraint). While strict, a very strong persona could still drift. We will mitigate this by:

* Constraining persona expression to allowed fields only (e.g., rationale wording), never at the expense of ranking correctness.
* Enforcing a hard JSON-only contract: one JSON object, no markdown fences, no extra text, no emojis.
* Using an existing “retry with stricter instruction” repair path (one retry) if the response fails JSON parsing or fails coverage rules (e.g., missing/duplicate anon_ids). This is a second model call with a corrective instruction, not a local JSON patch.

Persona Output Boundary
Persona is allowed to influence:

* The phrasing and framing of rationale (if rationale is enabled)
* Optional scoring calibration (scores 1–10)
  Persona must NOT influence:
* The structural validity of the JSON response
* The requirement that ranking includes all candidate anon_ids exactly once
* Any text outside the JSON object

Proposed Changes

Backend

[MODIFY] council.py

1. Stage 2 Persona: Persona + Rubric + JSON Contract

* Update Stage 2 message construction so each judge uses its own judging identity and rubric.
* Data sources:

  * Prefer councilor.judge_persona_path for Stage 2 persona text; fallback to councilor.persona_path if judge persona is missing.
  * Always append councilor.judge_system_prompt (rubric/task definition) after persona text.
  * Always append JSON-only hard constraint last.

Implementation details:

* Update _collect_single_ranking_bounded to accept either:
  a) the full councilor dict, or
  b) explicit (persona_text, judge_rubric_text) parameters.
  Passing the councilor dict is preferred to avoid missing future fields.

* Update _build_ranking_messages to construct a system prompt like:

  SYSTEM:
  {judge_persona_text}

  {judge_rubric_text}

  HARD CONSTRAINTS:

  * Output exactly one JSON object and nothing else.
  * No markdown fences. No extra commentary. No emojis.
  * ranking must include ALL anon_ids exactly once.

* Keep the Stage 2 mechanism unchanged:

  * Each judge issues one request and ranks all candidates in a single response (no per-candidate review loops).

2. Stage 2 Candidate Payload & Real-Name Mapping

* Maintain anonymized evaluation inputs to judges (judges still see only anon_id labels).
* For UI de-anonymization, ensure the backend emits robust mapping metadata:

  * anon_to_councilor: { anon_id → councilor_id }
  * anon_to_name: { anon_id → councilor_name }  (derived from stage1_results or councilor config)
    This ensures Stage 2 ranking display can always render real names, even if the frontend lookup cache is not yet populated.

3. Progressive Streaming: Stage 1 (partial → complete)
   We want responses to appear as soon as each councilor finishes.

* Create stage1_stream_responses(user_query, councilors) as an async generator.

  * It schedules all Stage 1 tasks immediately.
  * It yields incremental updates whenever a councilor finishes.
* Yield payloads should be merge-friendly and stable:

  * Prefer emitting an update event with:

    * councilor_id
    * result object (or status/error)
    * done_count / total
  * Avoid sending only “current_results_list” if it causes UI replacement flicker or duplicates.
* Keep existing stage1_collect_responses for non-streaming contexts (if needed), but send_message_stream should use streaming generator.

4. Progressive Streaming: Stage 2 (partial → complete)
   We want judge reviews to appear as soon as each judge finishes.

* Create stage2_stream_rankings(user_query, stage1_results, councilors) as an async generator.

  * It schedules all Stage 2 judge tasks immediately (same mechanism as current stage2_collect_rankings).
  * It yields incremental updates when a judge completes (success or fail).
* Emit merge-friendly payloads:

  * judge_councilor_id (or judge model/name)
  * review result (ranking/scores/rationale/raw_response)
  * judge_failures updates
  * done_count / total
* Always include mapping metadata with every Stage 2 update event:

  * anon_to_councilor
  * anon_to_name
    This guarantees the UI can render real names continuously during partial updates.

5. Event Naming / Semantics (important for correctness)
   Avoid emitting “*_complete” multiple times.

* Use:

  * stage1_update for partial updates
  * stage1_complete once at the end
  * stage2_update for partial updates
  * stage2_complete once at the end
    Alternatively, if reusing existing event names is mandatory, include a boolean field partial: true/false and done_count/total, but “update/complete” split is preferred.

6. Failure & Skipped Handling (must not break progressive UI)

* Stage 2 has a skipped path when there are fewer than 2 valid candidates.

  * Ensure the streaming endpoint emits a final stage2_complete with skipped=true and skipped_reason so the UI never hangs in “loading”.
* Ensure retries:

  * Keep existing behavior: one retry on JSON/usage errors or retryable network errors, then record failure.

[MODIFY] main.py

1. Update send_message_stream to use streaming generators

* Replace blocking calls:

  * stage1_collect_responses → stage1_stream_responses
  * stage2_collect_rankings → stage2_stream_rankings
* The streaming endpoint should:

  * Emit stage_start events (optional but useful)
  * Emit stage1_update events as each Stage 1 councilor finishes
  * Emit stage1_complete event after all Stage 1 tasks resolve
  * Emit stage2_update events as each Stage 2 judge finishes
  * Emit stage2_complete event after all Stage 2 tasks resolve or skipped is determined
* Ensure metadata:

  * resolved_councilor_ids are emitted early (existing behavior is good)
  * anon_to_councilor and anon_to_name are included with Stage 2 events (updates + complete)

Frontend

[MODIFY] ChatInterface.jsx

Council Members Name Bug (Model ID shown instead of Character/Role Name)
Problem
During the answer phase, “Council Members” UI shows model IDs rather than the assigned councilor names. This suggests CouncilAvatars is receiving insufficient councilor metadata and falling back to model strings.

Fix Approach

* Construct the councilors prop using stable councilor IDs resolved for the message, not model strings.
* Preferred data source order:

  1. msg.meta.resolved_councilor_ids (emitted early by backend stream)
  2. conversation-level active councilor list (if available)
  3. msg.stage1 result IDs (fallback for historical messages)
* Then map IDs through councilorLookup to produce objects containing:

  * id
  * name (character/role name)
  * model (optional)
    This ensures CouncilAvatars always has access to the display name.

[MODIFY] Stage2.jsx

Real Name Logic for Ranking Display
Goal
When showing extracted ranking (best → worst), display the real councilor names (character names), not anon labels.

Data Contract
Stage 2 events will include:

* anon_to_name: { anon_id → councilor_name }
* anon_to_councilor: { anon_id → councilor_id } (backup mapping)
  Stage2.jsx should:
* Prefer anon_to_name to render ranking labels.
* Fallback to anon_to_councilor + councilorLookup[id].name if anon_to_name is missing.
* If still missing, fallback to anon_id as a last resort (should be rare).

Anonymity Guarantee
UI de-anonymization is only for display. Judges must still evaluate anonymized candidates (anon_id only). Ensure no “real names” leak into judge inputs.

Verification Plan

Automated Tests
No existing automated tests for streaming interaction. Verification will be manual. (Optionally add a minimal integration test later.)

Manual Verification

1. Persona Check (Stage 2)

* Run a conversation.
* Inspect Stage 2 “Raw Evaluations”:

  * Rationale (if enabled) should reflect judge persona voice and values.
  * Output must remain valid JSON with required keys.
* Confirm ranking covers all anon_ids exactly once.

2. Progressive Display (Stage 1)

* Start a conversation.
* Observe Stage 1: response cards appear one by one as councilors finish.
* Unfinished councilors retain “thinking/loading” placeholders.
* No duplicate cards: each councilor slot is updated/filled once.

3. Progressive Display (Stage 2)

* Observe Stage 2: judge review tabs appear one by one.
* Confirm partial updates do not reset/flash previously completed tabs.

4. Real Names in Stage 2 Ranking

* In “Extracted Ranking”, confirm labels render real councilor names:

  * e.g., “Rank 1: The Pragmatist” (or configured name)
  * not “anon_1” and not raw model IDs
* Verify fallback behavior:

  * If anon_to_name exists, it is used.
  * If not, anon_to_councilor + councilorLookup resolves the name.

5. Council Members Name Bug

* During answer phase, confirm “Council Members” shows character names (not model IDs).
* Hover/labels and avatar names are consistent with configured councilor names.

6. Skipped / Failure Paths

* Force a case where <2 valid Stage 1 candidates exist (e.g., intentionally fail most models).
* Confirm Stage 2 shows skipped state promptly (no indefinite loading).
* Confirm judge failures are recorded and the UI remains stable.

Notes / Non-Goals

* We are not implementing anon_id shuffling or self-evaluation exclusion in this iteration.
* We are not changing the fundamental Stage 2 judging mechanism (still one request per judge, ranking all candidates at once).
* Token optimization is not prioritized; correctness, UX responsiveness, and persona-driven evaluation are the priorities.
