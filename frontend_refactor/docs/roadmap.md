# 🗺️ Project Roadmap

## Phase 1: MVP Simulation (✅ Completed)
*   [x] **UI Framework**: React + Tailwind setup.
*   [x] **3-Stage Engine**: Generate -> Review -> Synthesize workflow.
*   [x] **Responsive Design**: Desktop Sidebar / Mobile Drawer split.
*   [x] **HUD**: Bottom status bar with leaderboard visualization.

## Phase 1.5: Tactical UX Polish (✅ Completed)
*   [x] **Modular Refactor**: Split monolithic code into `components/` and `hooks/`.
*   [x] **Squad Assembly**: "Staging Area" logic in HUD during agent selection.
*   [x] **Smart Notifications**: "Consensus Ready" beacon that respects user attention (dismisses after viewing).
*   [x] **Stage Indicators**: Explicit `STAGE [0X / 03]` tracking in the status bar.

## Phase 2: "Real Brains" Integration (🚧 Next Up)
*   [ ] **API Client**: Integrate Google GenAI SDK (Gemini).
*   [ ] **Prompt Engineering**:
    *   Create System Prompts for specific personas (Kant, Kojima, etc.).
    *   Create "Judge" Prompts for Stage 2 (outputting JSON scores).
    *   Create "Synthesizer" Prompts for Stage 3.
*   [ ] **Streaming**: Implement true token streaming for answers.

## Phase 3: Customization & Persistence
*   [ ] **User Config**: Allow users to swap council members.
*   [ ] **Model Selection**: Assign specific models (e.g., Gemini 1.5 Pro vs Flash) to specific personas.
*   [ ] **History**: Save parliamentary sessions to `localStorage`.

## Phase 4: Advanced Mechanics
*   [ ] **Debate Mode**: Allow Agents to reply to specific critiques (Multi-turn Stage 2).
*   [ ] **Export**: Generate a PDF/Markdown report of the entire session.
