# 🗺️ Project Roadmap

## Phase 1: MVP Simulation (✅ Completed)
*   [x] **UI Framework**: React + Tailwind setup.
*   [x] **Stage 1 (Generate)**: Tabbed views for agents, "Thinking" side panel.
*   [x] **Stage 2 (Evaluate)**: Peer review simulation, anonymous feedback UI.
*   [x] **Stage 3 (Synthesize)**: Chairperson persona, Final Consensus report generation.
*   [x] **Responsive Design**: Desktop Sidebar / Mobile Drawer split.
*   [x] **HUD**: Bottom status bar with leaderboard visualization.

## Phase 2: "Real Brains" Integration (🚧 Next Up)
*   [ ] **API Client**: Integrate `OpenRouter` or `OpenAI` SDK.
*   [ ] **Prompt Engineering**:
    *   Create System Prompts for specific personas (Kant, Kojima, etc.).
    *   Create "Judge" Prompts for Stage 2 (outputting JSON scores).
    *   Create "Synthesizer" Prompts for Stage 3.
*   [ ] **Streaming**: Implement token streaming for answers to replace the static text dump.

## Phase 3: Customization & Persistence
*   [ ] **User Config**: Allow users to swap council members (e.g., "Add Steve Jobs", "Remove Kant").
*   [ ] **Model Selection**: Allow assigning specific models (e.g., GPT-4o, Claude 3.5 Sonnet) to specific personas.
*   [ ] **History**: Save parliamentary sessions to `localStorage`.

## Phase 4: Advanced Mechanics
*   [ ] **Debate Mode**: Allow Agents to reply to specific critiques (Multi-turn Stage 2).
*   [ ] **Branching**: Allow user to intervene in Stage 2 and overrule a specific critique.
*   [ ] **Export**: Generate a PDF/Markdown report of the entire session.
