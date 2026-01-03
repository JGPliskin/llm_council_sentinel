# Stage2 Thinking Stream + Review Replace Plan

- Version: v0.3
- Scope: Stage2 DetailPanel thinking stream + review replace, Stage1/Stage3 thinking-to-content cross-fade, Stage2 thinking targeted to activeTab via `target_anon_id`
- Decision summary: reuse `thinking` event, Stage2 thinking uses title + detail (two-line display, Chinese), review replaces thinking with transition, realtime only, Stage1/Stage3 use the same cross-fade style, Stage2 thinking includes target mapping for activeTab filtering

## Table of Contents

1. Background and Goals
2. User Scenarios and Requirements
3. Current State Review
4. Proposed Solution (High Level)
5. Detailed Technical Plan
6. Flow Diagram
7. ASCII UI Mock
8. Files to Change and Key Edits
9. Edge Cases and Error Handling
10. Recommendations and Tradeoffs
11. Open Items (if any)

## 1. Background and Goals

Stage2 currently renders peer reviews in the DetailPanel and does not display Stage2 thinking. We want to show a live thinking stream per judge during Stage2, and then replace that stream with the final review content in the same visual region when the review arrives.

## 2. User Scenarios and Requirements

### 2.1 User Scenario

| Scenario | Description | Expected UX |
|---|---|---|
| Live Stage2 evaluation | User selects 3 councilors, Stage2 starts | Each judge shows a live thinking stream (title + detail) that updates line-by-line, auto-scrolls, and keeps only the latest entry visible |
| Review arrives | Stage2 judge finishes | The review content replaces the thinking stream in the same area with a smooth transition |
| Active tab switch | User switches activeTab | Thinking stream remains unchanged (not reset), review content remains correct for each judge |

### 2.2 Requirements (Confirmed)

| Requirement | Decision |
|---|---|
| Event type | Reuse `thinking` events (no new `thinking_delta`) |
| Stage2 thinking layout | Same as Stage1: title main line, detail second line |
| Stage2 thinking language | Require Chinese output in prompt |
| Stage2 thinking targeting | Add `target_anon_id` so UI can filter by activeTab |
| Thinking frequency | Keep current 2-3 steps (no extra enforcement) |
| History | Realtime only (no history view) |
| Thinking to review | Review replaces thinking in the same region with animation |
| Active tab change | Thinking stays as-is |
| Stage1/Stage3 thinking transition | Use the same cross-fade + slight upward slide (180-240ms) with background-aware blending |

## 3. Current State Review

### 3.1 Backend

| Item | Current Behavior |
|---|---|
| SSE event | Emits `thinking` with fields: `stage`, `title`, `detail`, `op`, `bullet_id` (no target binding yet) |
| Stage2 thinking | Stage2 judges can emit `emit_thinking` tool calls |
| Persistence | Thinking stored in `metadata.thinking` (stage1/2/3), but UI only consumes stage1/3 |

### 3.2 Frontend

| Component | Current Behavior |
|---|---|
| `useParliamentEngine` | Handles Stage1 and Stage3 thinking only |
| `DetailPanel` | Shows peer reviews OR chairman synthesis, no Stage2 thinking |
| Stage2 reviews | Displayed as cards in DetailPanel (by activeTab) |

## 4. Proposed Solution (High Level)

Reuse existing `thinking` SSE events for Stage2, but extend payload to include `target_anon_id` so each thinking step can be mapped to the current activeTab. Add a Stage2 thinking stream model in the frontend state. In DetailPanel, each judge card shows a live thinking block (two-line title+detail) for the current activeTab until its review arrives. When review arrives, the card transitions to final review content.

Apply the same cross-fade transition style to Stage1 and Stage3 thinking-to-content handoffs to keep the UI consistent, while ensuring the overlay blends with each background.

## 5. Detailed Technical Plan

### 5.1 Data and Event Flow

```
SSE: thinking (stage2 with target_anon_id)
  -> useParliamentEngine.handleThinking
     -> map target_anon_id via anon_map to targetId
     -> update stage2ThinkingByJudge[judgeId].stepsByTarget[targetId][]
        -> DetailPanel renders latest step for activeTab (title + detail)

SSE: stage2_item
  -> set stage2Results + evaluationComments
     -> DetailPanel replaces thinking with review content for that judge
```

### 5.2 Frontend State Design

Option recommended: separate map for Stage2 with target-aware steps

| State | Type | Purpose |
|---|---|---|
| `stage2ThinkingByJudge` | `{ [judgeId]: { status: 'idle'|'thinking'|'done'|'failed', error?: string, stepsByTarget: { [targetId]: steps[] } } }` | Store Stage2 thinking steps per judge and per target |
| `stage2LastStep` (optional) | `{ [judgeId]: { [targetId]: step } }` | Quick access for UI rendering |

Notes:
- Steps array supports append/update based on `bullet_id` + `op`.
- UI only shows the latest step for activeTab; list retained for auto-scroll semantics.

### 5.3 UI Behavior

1) Before review
- Show two-line thinking block (title + detail) in each judge card for the current activeTab.
- Auto-scroll to the latest step if multiple steps are appended.

2) On review arrival
- Replace thinking block with the final review text.
- Use a short cross-fade + slight upward slide for continuity.

3) Active tab switch
- Do not reset thinking state. Display remains consistent.

### 5.4 Animation Transition

Recommended transition (simple, readable):

| Element | Transition | Duration |
|---|---|---|
| Thinking -> Review | cross-fade + slight upward slide | 180-240ms |
| Stage1 thinking -> answer | cross-fade + slight upward slide | 180-240ms |
| Stage3 thinking -> chairman content | cross-fade + slight upward slide | 180-240ms |

CSS idea (non-code spec):
- thinking block fade out while review fades in
- optional small translateY (4-8px) to signal handoff
- blend on top of existing background (avoid harsh edges on dark panels)

### 5.5 Stage2 Thinking Content (Title + Detail)

Current Stage2 prompt does not explicitly require `detail`, Chinese output, or target binding. Update the Stage2 prompt so:

- It requires `detail` (1-2 lines)
- It explicitly requests Chinese output
- It requires `target_anon_id` to indicate which anon candidate the thinking step refers to
- If no detail, UI shows title only (second line hidden)

This improves visual consistency, language alignment, and activeTab filtering for the Stage2 stream.

### 5.6 Stage2 Thinking Targeting (target_anon_id)

Add `target_anon_id` to the Stage2 thinking payload so each step can be tied to a specific candidate.

Example payload (tool call arguments):

```
{
  "title": "评估逻辑一致性",
  "detail": "关注假设的可验证性与风险控制",
  "target_anon_id": "anon_2",
  "op": "append"
}
```

Frontend mapping:
- Use `stage2_start.anon_map` to map `anon_2` -> councilor_id
- Show only steps whose mapped target matches `activeTab`
- If `target_anon_id` is missing, treat the step as `global` and hide it by default (or show with a GLOBAL label if needed for debugging)

### 5.7 Stage2 Prompt Update Example

Add explicit instructions in Stage2 prompt:

```
在调用 emit_thinking 时，必须指定 target_anon_id，表示你当前正在评估哪个候选方案（如 anon_1、anon_2）。
title 与 detail 均需使用中文，detail 为 1-2 行说明。
```

If tooling schema is updated, include `target_anon_id` in the tool parameters (Stage2 only).

### 5.8 Judge Identity in SSE Payload

SSE `thinking` events already include `councilor_id` and `model`. Use `councilor_id` as `judgeId` in the frontend.

## 6. Flow Diagram

```
Stage2 Thinking Data Flow

  Stage2 LLM (TRUMP)
      |
      | emit_thinking({ title, detail, target_anon_id: "anon_2" })
      v
  Backend (council.py/main.py)
      | SSE: { type: "thinking", stage: "stage2",
      |        councilor_id: "trump", target_anon_id: "anon_2", ... }
      v
  Frontend (useParliamentEngine)
      | map anon_2 -> kant via anon_map
      | stage2ThinkingByJudge["trump"].stepsByTarget["kant"].push(step)
      v
  DetailPanel
      | if (activeTab === "kant") show latest step for "kant"
      | stage2_item -> replace thinking with review
```

## 7. ASCII UI Mock

```
DetailPanel (Stage2) - activeTab = KANT

┌──────────────────────────────────────────────────────────────────────────┐
│ 评审员          │ 状态      │ 内容                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ [TRUMP]        │ ⏳ Thinking│ 标题: 评估 KANT 论证的可行性...              │
│               │           │ 详情: 关注成本与时间权衡                     │
├──────────────────────────────────────────────────────────────────────────┤
│ [KOJIMA]       │ ⏳ Thinking│ 标题: 检验 KANT 叙事连贯性...                │
│               │           │ 详情: 匹配用户目标与语气                     │
├──────────────────────────────────────────────────────────────────────────┤
│ [KANT]         │ ⏳ Thinking│ 标题: 自评 KANT 方案的稳健性...             │
│               │           │ 详情: 校验假设与可执行性                     │
└──────────────────────────────────────────────────────────────────────────┘

(later: review replaces thinking block for TRUMP/KOJIMA)
```

## 8. Files to Change and Key Edits

| File | Change | Key Points |
|---|---|---|
| `frontend/src/hooks/useParliamentEngine.js` | Add Stage2 thinking handling | Capture `thinking` when `event.stage === 'stage2'`, append/update steps per judge ID |
| `frontend/src/components/DetailPanel.jsx` | Render thinking block before review | Each judge card shows latest thinking step, then replaces with review on arrival |
| `frontend/src/components/StageContentArea.jsx` | Add Stage1 cross-fade | Apply cross-fade transition for thinking-to-answer handoff |
| `frontend/src/App.jsx` | Pass new props | Provide `stage2ThinkingByJudge` to DetailPanel |
| `backend/council.py` | Enrich Stage2 thinking detail/language/target | Require `detail` lines, Chinese output, and `target_anon_id` in Stage2 thinking instructions |
| `backend/main.py` | Pass through target field | Extend thinking normalization to include `target_anon_id` for stage2 |

No changes required in SSE or event types (reuse `thinking`).

## 9. Edge Cases and Error Handling

| Case | Handling |
|---|---|
| Stage2 skipped (insufficient candidates) | No thinking expected; show existing skip message or empty state |
| Judge failure | Keep thinking (last known) or show fallback status text |
| Missing detail | Render title only; hide detail row |
| Missing target_anon_id | Treat as global and hide by default (optionally show with GLOBAL label) |
| Self review display | Self-review is allowed; display it like any other judge |
| enable_thinking = false | Skip thinking UI, show reviews only |

## 10. Recommendations and Tradeoffs

### Recommendation on replacing thinking with review

I agree with replacing thinking once the review arrives. For Stage2, users typically care about the final evaluation more than the intermediate thought stream. This keeps the panel clean and reduces noise. The only cost is losing transparency for debugging or trust-building.

If you ever want to re-enable visibility for debugging later, we can keep the data internally but still replace it in UI.

### Tradeoffs

| Option | Pros | Cons |
|---|---|---|
| Replace thinking with review | Cleaner UI, less noise | Less transparency after completion |
| Keep thinking visible | Auditability | Cluttered panel, harder to scan reviews |

## 11. Open Items (if any)

- None. All decisions confirmed.

---
End of document.
