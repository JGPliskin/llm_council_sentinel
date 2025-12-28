# 🏛️ LLM Parliament (The Committee)

> **Core Concept**: Why ask one LLM when you can consult a committee?

**LLM Parliament** is a local web application that simulates a "Committee of AI Agents." Instead of a single chatbot response, it orchestrates a debate among distinct personas (e.g., Kant, Kojima, Nietzsche, Confucius), followed by a peer review process, and finally synthesizes a consensus answer via a Chairperson.

## 🌟 Key Features

### The 3-Stage Workflow
1.  **Stage 1: Initial Opinions** 🧠
    *   The user's prompt is sent to 4 distinct AI personas simultaneously.
    *   Each persona answers based on their specific system prompt/philosophy.
    *   **UI**: Side "Thinking Panel" logs the generation process.

2.  **Stage 2: Peer Review** ⚔️
    *   Agents read each other's answers anonymously to prevent bias.
    *   They critique accuracy, insight, and alignment.
    *   **UI**: "Evaluation Panel" shows real-time feedback; HUD tracks progress.

3.  **Stage 3: Final Consensus** 🏆
    *   A "Chairperson" LLM weighs the ratings and critiques.
    *   A final, synthesized report is generated, resolving conflicts and offering a balanced solution.
    *   **UI**: Consensus Tab unlocks; HUD displays final rankings.

### UI Highlights
*   **Split-View Design**: Main content on the left, dynamic logs/details on the right.
*   **Responsive Layout**: Right panel becomes a "squeezing" sidebar on Desktop and a bottom drawer on Mobile.
*   **Heads-Up Display (HUD)**: A persistent bottom bar tracks stage progress and displays final rankings (visualized as a leaderboard).

## 🛠️ Tech Stack

*   **Framework**: React 18
*   **Styling**: Tailwind CSS
*   **Icons**: Lucide React
*   **Build**: ES Modules (No-build implementation via `importmap` for portability)

## 🚀 Getting Started

Since this is a client-side simulation demo:

1.  Open `index.html` in a modern browser (via a local server like Live Server).
2.  The simulation starts automatically in **Stage 1**.
3.  Click the buttons in the bottom-left or interact with the tabs to navigate the experience.

---
*Generated for the LLM Parliament Project.*
