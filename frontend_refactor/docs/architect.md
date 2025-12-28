# 🏗️ System Architecture & Engineering Guide

## 1. High-Level Design
**LLM Parliament** follows a **Unidirectional Data Flow** pattern. The `App` component acts as the orchestrator, connecting the "Engine" (Business Logic) to three distinct UI regions: the Sidebar, the Stage Content, and the Tactical HUD.

## 2. Component Structure

```text
/
├── index.tsx               # Root & Orchestrator (App Component)
│   ├── TacticalSidebar     # Left: Mission Logs / Admin Controls / Reset
│   ├── StageContentArea    # Center: Tabbed Interface for Agent Answers
│   ├── UnifiedDetailPanel  # Right: Context-aware Info Panel (Logs/Evals)
│   ├── TacticalHUD         # Bottom: Fixed Status Bar & Visualization
│   └── WelcomeScreen       # Center (Stage 0): Setup Dashboard
│
├── hooks/
│   └── useParliamentEngine.ts  # State Machine & Simulation Logic
│
└── components/
    ├── WelcomeScreen.tsx
    ├── StageContentArea.tsx
    └── TacticalHUD.tsx
```

## 3. Core Components Specification

### 3.1. `App.tsx` (The Layout Controller)
*   **Responsibility**: Manages the responsive grid and visibility of side panels.
*   **Logic**:
    *   **Desktop**: Renders `UnifiedDetailPanel` as a side column that shrinks the central content width.
    *   **Mobile**: Renders `UnifiedDetailPanel` as a fixed `bottom-0` overlay (Drawer) with backdrop blur.
    *   **Panel Toggle**: Automatically opens the panel when the simulation starts (Desktop only).

### 3.2. `UnifiedDetailPanel` (Context Aware)
A single component that morphs based on the current `stage`:
*   **Stage 1**: Renders `ThinkingProcess` (List of `LogStep`).
*   **Stage 2**: Renders `EvaluationList` (List of `PeerReview` with `from` -> `to` arrows).
*   **Stage 3**: Renders `ThinkingProcess` (Chairperson's synthesis logs).
*   **Behavior**: Includes a close button (`X`) which updates `isPanelOpen` in the App state.

### 3.3. `StageContentArea.tsx` (Main View)
*   **Navigation**: Uses a horizontal Tab strip.
*   **Consensus Logic**: The "Consensus" tab is disabled/locked until `engine.consensusUnlocked` is true.
*   **Beacon**: Renders a floating "Consensus Ready" button if the user is currently looking at an agent tab but consensus is available.
*   **Rendering**: Renders full Markdown text blocks (currently simulated via `MOCK_ANSWERS`).

### 3.4. `TacticalHUD.tsx` (Visualizer)
*   **Props Contract**: `stage`, `agentProgress`, `evaluations`, `rankings`.
*   **Stage 2 Logic**: Uses `ConnectionOverlay` to draw SVG Bezier curves between `AgentSlice` components based on real-time `PeerReview` data.
*   **Completion**: Displays ranking badges (e.g., "🥇 9.2") on agent cards once Stage 3 finishes.
*   **Overlay**: Shows a full-screen "Consensus Ready" modal if `hasViewedConsensus` is false.

## 4. State Machine (`useParliamentEngine.ts`)

The engine manages the transition lifecycle:

### States
*   `'idle'`: User is configuring the squad.
*   `'stage1'`: **Parallel Execution**. Multiple `setInterval` timers run concurrently to fill `agentProgress`.
*   `'stage2'`: **Linear Execution**. A global `stageProgress` fills up, injecting `PeerReview` objects at 20%, 40%, 60%, 80%.
*   `'stage3'`: **Linear Execution**. Global progress fills, injecting `LogStep` for the Chairperson.

### Transitions
1.  **Start**: `idle` -> `stage1` (Triggered by user).
2.  **Auto-Forward**:
    *   `stage1` -> `stage2`: Triggered when **ALL** selected agents reach 100% progress.
    *   `stage2` -> `stage3`: Triggered when Stage 2 global progress hits 100%.
    *   `stage3` -> `Complete`: Triggered when Stage 3 hits 100%, sets `consensusUnlocked = true`.

### UX Flags
*   `hasViewedConsensus`: A one-time flag.
    *   **False**: HUD shows a large "Click Me" overlay when ready. Beacon pulses.
    *   **True**: Set when user clicks the Consensus Tab. HUD overlay is permanently removed for this session.

## 5. Data Models (Types)

*   **`AgentResponse`**: Static content blocks (Title + Paragraphs).
*   **`PeerReview`**: `{ from: AgentId, to: AgentId, comment: string }`.
*   **`LogStep`**: `{ agentId, text, time, status }`.

## 6. Future Considerations (API Integration)
To move from Simulation to Production:
1.  **Replace Intervals**: In `useParliamentEngine`, replace `setInterval` with `fetch`/`stream` readers.
2.  **Streaming Text**: Currently, `StageContentArea` renders the full text immediately. For LLM integration, this should receive a `streamedContent` prop to show text appearing token-by-token.
