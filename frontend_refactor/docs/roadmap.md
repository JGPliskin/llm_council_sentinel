# 🗺️ Project Roadmap

## Phase 1: MVP Simulation (✅ Completed)
*   [x] **UI Framework**: React + Tailwind setup.
*   [x] **3-Stage Engine**: Generate -> Review -> Synthesize workflow.
*   [x] **Responsive Design**: Desktop Sidebar / Mobile Drawer split.

## Phase 1.5: Tactical UX Polish (✅ Completed - v1.2)
*   [x] **Modular Refactor**: Codebase split into `components/` and `hooks/`.
*   [x] **Squad Assembly**: "Staging Area" visual feedback in the Welcome Screen.
*   [x] **Compact Dashboard**: Redesigned Welcome Screen to fit Input & Agents on one screen ("Above the fold").
*   [x] **Smart Notifications**: "Consensus Ready" beacon tracks `hasViewedConsensus` to reduce annoyance.
*   [x] **Stage Indicators**: Explicit `STAGE [0X / 03]` tracking in the status bar.

## Phase 2: "Real Brains" Integration (🚧 Next Priority)
*   [ ] **API Client**: Integrate Google GenAI SDK (Gemini).
*   [ ] **Prompt Engineering**:
    *   Create System Prompts for specific personas (Kant, Kojima, etc.).
    *   Create "Judge" Prompts for Stage 2 (outputting JSON scores).
    *   Create "Synthesizer" Prompts for Stage 3.
*   [ ] **Streaming**: Implement true token streaming to replace simulated loading.

## Phase 3: Advanced Features (Backlog)
*   [ ] **User Configuration**: Ability to add custom Agents.
*   [ ] **Session History**: Persist logs to `localStorage`.
*   [ ] **Export**: Generate PDF reports of the consensus.
