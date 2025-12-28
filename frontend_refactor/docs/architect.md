# 🏗️ System Architecture

## 1. High-Level Overview
**LLM Parliament** is a modular, client-side React application designed to simulate a multi-agent "Committee" workflow. It demonstrates the UX of collaborative AI (Ensemble Intelligence) with a high-fidelity "Tactical Sci-Fi" interface.

The app follows a **unidirectional data flow** driven by a custom simulation engine hook, separating business logic from the "Tactical UI" presentation layer.

## 2. Technical Stack
*   **Core**: React 18, TypeScript.
*   **State Management**: Custom React Hooks (`useParliamentEngine`).
*   **Styling**: Tailwind CSS (via CDN) + Custom Animations.
*   **Icons**: Lucide React.
*   **Build System**: Zero-build runtime using ES Modules (`<script type="importmap">`).

## 3. Directory Structure
```
/
├── index.html              # Entry Point & Global CSS
├── index.tsx               # Main App Assembly & Layout
├── types.ts                # Shared TypeScript Interfaces
├── mockData.ts             # Simulation Data (Static "Brains")
├── hooks/
│   └── useParliamentEngine.ts  # Core State Machine & Simulation Logic
└── components/
    ├── WelcomeScreen.tsx   # Agent Selection & Staging Logic
    ├── StageContentArea.tsx# Main View (Terminal & Markdown Rendering)
    └── TacticalHUD.tsx     # Bottom Status Bar & Visualization
```

## 4. Component Architecture

### 4.1. `useParliamentEngine` (The Brain)
A custom hook that manages the complex state transitions of the 3-stage pipeline.
*   **Responsibilities**:
    *   Manages `stage` ('idle' -> 'stage1' -> 'stage2' -> 'stage3').
    *   Tracks individual agent progress (`agentProgress`) and global stage progress.
    *   Handles data injection timing for `thinkingSteps` and `evaluations`.
    *   **Smart State**: Tracks `hasViewedConsensus` to manage UI notification noise.

### 4.2. `WelcomeScreen` (Setup)
*   **Squad Assembly**: Handles the selection of agents.
*   **Visuals**: Features a "Staging Area" concept where selecting an agent immediately creates a "Standby" slot in the HUD, preventing visual emptiness.

### 4.3. `StageContentArea` (Main Display)
*   **Tactical Tabs**: Top navigation bar with active state "pop-up" styling.
*   **Terminal View**: Renders agent content in a structured, terminal-like display.
*   **Smart Beacon**: A floating action button for the Consensus stage that stops pulsing once the user has acknowledged the report.

### 4.4. `TacticalHUD` (Status & Visualization)
The heavy-duty status container fixed to the bottom of the viewport.
*   **Stage Indicator**: Explicitly displays `STAGE [0X / 03]` with stage-specific color coding.
*   **Agent Slices**: Self-contained cards that morph based on state:
    *   *Standby*: Low-light, locked state (during selection).
    *   *Generating*: Orange pulse animations.
    *   *Review*: Blue/Red targeting states.
    *   *Consensus*: Purple completion state.
*   **Overlay Logic**: Handles the "Connection Beam" visualization (SVG) and the initial "Consensus Ready" modal overlay.

## 5. Data Flow
1.  **User Input**: User selects agents and sends a prompt in `WelcomeScreen`.
2.  **Initialization**: `App.tsx` triggers `engine.startSession()`.
3.  **Simulation Loop**: `useParliamentEngine` ticks through simulated delays, updating `agentProgress`.
4.  **Reactive UI**: `TacticalHUD` and `StageContentArea` reactively update based on the engine's state, rendering animations and text streams.

## 6. Future Integration Strategy (Phase 2)
To move from Simulation to Real Inference:
1.  **Service Layer**: Replace the `setInterval` logic in `useParliamentEngine` with `GoogleGenAI` API calls.
2.  **Streaming**: The UI is already designed to handle incremental updates (`thinkingSteps`). Real streaming will simply feed this state faster.
