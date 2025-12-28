# 📜 Development Log

## v1.1.0 - The Tactical UX Upgrade
**Date**: Current
**Status**: Stable

Major improvements to the user experience and visual feedback loop, focusing on the "Staging" phase and "Consensus" notifications.

### 🎨 UX Enhancements
*   **Squad Assembly (Staging Area)**: Fixed the "Black Void" issue in the HUD during the Welcome Screen. Now, when a user selects an agent, a corresponding `STANDBY` card immediately slides into the HUD slots. This creates a cohesive "team building" feel.
*   **Smart Beacon Logic**: 
    *   The "Consensus Ready" pulsing button and HUD overlay now track `hasViewedConsensus`.
    *   Once the user clicks to view Stage 3, the aggressive animations (Ping) and overlays are permanently dismissed for that session, preventing visual clutter.
*   **Stage Indicators**: Added a dedicated `STAGE [0X / 03]` section to the HUD status bar with stage-specific color coding (Orange/Blue/Purple) for better orientation.

---

## v1.0.0 - Modular Refactor
**Date**: Previous Release

Transitioned from a monolithic prototype to a scalable component architecture.

### 🛠️ Architecture
*   **Split Codebase**: Extracted `TacticalHUD`, `StageContentArea`, and `WelcomeScreen` into dedicated files.
*   **Custom Hook**: Created `useParliamentEngine` to isolate the simulation state machine from the UI logic.
*   **Type Safety**: Enforced strict TypeScript interfaces for `AgentProfile`, `PeerReview`, and `SimulationStage`.

---

## v0.1.0 - The "Parliament" MVP Release
**Date**: October 26, 2023
**Status**: Legacy Demo

The first major milestone of the **LLM Parliament** is complete. We have successfully simulated the full "Committee" workflow in a client-side environment.

### 🚀 Features Shipped
*   **The 3-Stage Engine**: Transitions from *Generation* to *Peer Review* to *Consensus*.
*   **Responsive Split-View**: Squeezing Sidebar (Desktop) and Bottom Drawer (Mobile).
*   **Heads-Up Display (HUD)**: Persistent bottom bar with simulated data visualization.
*   **Visual Polish**: Integrated `Lucide React` and custom CSS keyframes for a Sci-Fi terminal aesthetic.
