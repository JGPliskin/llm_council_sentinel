# 🏛️ LLM Parliament (The Committee)

> **Core Concept**: "Why ask one LLM when you can consult a Council of Philosophers?"

**LLM Parliament** is a client-side React application that simulates a **Multi-Agent Consensus System**. It visualizes the process of "Ensemble Intelligence" where distinct AI personas (e.g., Kant, Kojima) debate a user's prompt, peer-review each other, and synthesize a final trusted answer.

---

## 🌟 Key Features (Current Implementation)

### 1. The 3-Stage Tactical Workflow
The application orchestrates a unidirectional pipeline, visualized through a responsive dashboard:

*   **Stage 0: Squad Assembly (Welcome Screen)** 🛡️
    *   **Compact Dashboard**: A "Pilot Cockpit" interface. Select agents and input directives in a single view.
    *   **Visual Feedback**: Selecting an agent immediately "locks" them into the bottom HUD (`STANDBY` status).

*   **Stage 1: Parallel Generation** 🧠
    *   **Behavior**: Selected agents generate responses simultaneously.
    *   **UI**: 
        *   **Main Area**: Tabs allow switching between agent drafts.
        *   **Right Panel (Thinking)**: A dedicated sidebar shows real-time "Thinking Logs" (e.g., "Analyzing ethical framework...").
        *   **HUD**: Agent cards pulse Orange (`GENERATING`) with progress bars.

*   **Stage 2: Peer Review** ⚔️
    *   **Behavior**: Agents cross-examine each other's outputs.
    *   **UI**:
        *   **Right Panel (Evaluation)**: Automatically switches to show a feed of peer critiques (Criticism/Suggestion).
        *   **HUD**: Renders dynamic SVG "Connection Beams" connecting the *Reviewer* (Blue) to the *Target* (Red).

*   **Stage 3: Consensus Synthesis** 🏆
    *   **Behavior**: A "Chairperson" agent weighs reviews and synthesizes a final report.
    *   **UI**:
        *   **Consensus Tab**: Unlocks only after synthesis is complete.
        *   **Right Panel (Synthesis)**: Shows the Chairperson's logic (e.g., "Weighing Kant vs Nietzsche").
        *   **Smart Beacon**: A holographic "Consensus Ready" FAB (Floating Action Button) appears to guide the user.

### 2. Tactical HUD (Heads-Up Display)
A persistent, cinematic status bar fixed to the bottom of the screen.
*   **Stage Tracker**: Explicitly displays `STAGE [0X / 03]` with color coding.
*   **Agent Slices**: Cards that morph states (`Standby` -> `Generating` -> `Reviewing` -> `Complete`).
*   **Final Ranking**: Upon completion, displays the final score (e.g., 9.2) and rank (🥇) in the HUD.

### 3. Responsive Layout System
*   **Desktop**: 3-Column Layout (Sidebar Navigation | Main Content | Detail Panel). The Detail Panel "squeezes" the main content but can be toggled.
*   **Mobile**: The Right Panel transforms into a **Bottom Drawer** overlay to save screen space.

---

## 🛠️ Technical Stack

*   **Core**: React 18 (Functional Components + Hooks)
*   **State Management**: `useParliamentEngine` (Custom Finite State Machine).
*   **Styling**: Tailwind CSS + Custom Keyframe Animations (`animate-in`, `scanline`).
*   **Icons**: Lucide React.
*   **Runtime**: Zero-build ES Modules via `<script type="importmap">`.

---

## 🚀 Usage Guide

1.  **Start**: Open `index.html` in a local server (VS Code Live Server recommended).
2.  **Assemble**: Toggle Agent Avatars in the Welcome Screen.
3.  **Init**: Type a prompt or select a Protocol Preset.
4.  **Observe**: 
    *   Watch the **HUD** for global progress.
    *   Check the **Right Panel** for detailed logs.
    *   Switch **Tabs** to read individual drafts.
5.  **Finish**: When the "Consensus Ready" beacon appears, click it to read the final report.

---
*Current Version: v1.2.0*
