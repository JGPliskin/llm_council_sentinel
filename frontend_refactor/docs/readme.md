# 🏛️ LLM Parliament (The Committee)

> **Core Concept**: Why ask one LLM when you can consult a committee?

**LLM Parliament** is a local web application that simulates a "Committee of AI Agents." Instead of a single chatbot response, it orchestrates a debate among distinct personas (e.g., Kant, Kojima, Nietzsche, Confucius), followed by a peer review process, and finally synthesizes a consensus answer via a Chairperson.

## 🌟 Key Features

### The 3-Stage Workflow
1.  **Stage 1: Initial Opinions** 🧠
    *   The user's prompt is sent to 4 distinct AI personas simultaneously.
    *   **Parallel Processing**: Watch individual agents "think" and generate output in real-time.
    *   **UI**: "Thinking Panel" logs the generation process.

2.  **Stage 2: Peer Review** ⚔️
    *   Agents read each other's answers anonymously.
    *   **Connection Beams**: The HUD visualizes who is critiquing whom via dynamic SVG data beams.
    *   They critique accuracy, insight, and alignment.

3.  **Stage 3: Final Consensus** 🏆
    *   A "Chairperson" LLM synthesizes a final report.
    *   **Smart Beacon**: A holographic alert notifies the user when the consensus is ready, automatically silencing itself after the first view to reduce visual noise.

### UX Highlights (Tactical v2.1)
*   **Squad Assembly (Staging Area)**: Selecting agents in the Welcome Screen immediately "slots" them into the bottom HUD in a `STANDBY` state, giving the user a satisfying "Lock & Load" feeling before the simulation starts.
*   **Tactical HUD**: A persistent dashboard tracking `STAGE [0X / 03]`. It uses chamfered cards (`AgentSlice`) to display real-time status (Generating, Reviewing, Complete).
*   **Responsive Layout**: 
    *   **Desktop**: "Squeezing Sidebar" for logs.
    *   **Mobile**: Bottom Drawer + Floating Action Buttons.

## 🛠️ Tech Stack

*   **Framework**: React 18 (Modular Architecture)
*   **State**: Custom TypeScript Hooks
*   **Styling**: Tailwind CSS + Custom Keyframe Animations
*   **Icons**: Lucide React
*   **Build**: ES Modules (No-build implementation via `importmap`)

## 🚀 Getting Started

Since this is a client-side simulation demo:

1.  Open `index.html` in a modern browser (via a local server like Live Server).
2.  **Assemble your Council**: Click agent avatars to toggle them. Watch them appear in the HUD Staging Area.
3.  Type a prompt or select a **Protocol Preset** to begin.

---
*Generated for the LLM Parliament Project.*
