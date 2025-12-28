# 📜 Development Log

## v1.2.0 - The "Dashboard" Layout Update
**Date**: Current
**Status**: Stable

Addressed UX friction regarding the Welcome Screen layout and visual feedback.

### 🎨 Changes
1.  **Compact Welcome Screen**:
    *   Moved the **Input Field** *above* the Protocol Presets.
    *   Changed Protocol Presets from large cards to a compact **Quick Launch Bar**.
    *   Optimized spacing so the entire setup flow fits on a standard laptop screen without scrolling.
2.  **HUD Staging Logic**:
    *   The HUD now stays visible during the Welcome Screen.
    *   Selecting an agent adds a `STANDBY` card to the HUD immediately, providing instant visual confirmation of the squad composition.

---

## v1.1.0 - The Tactical HUD & Notifications
**Date**: Previous Release

Major improvements to the status visualization and notification system.

### 🎨 Changes
1.  **Smart Beacon**:
    *   Implemented `hasViewedConsensus` state.
    *   The large "Consensus Ready" overlay now permanently disappears after the user clicks it once, preventing it from blocking the view during subsequent analysis.
2.  **Stage Indicators**:
    *   Added explicit `STAGE [0X / 03]` text to the HUD status bar.
    *   Added stage-specific color coding (Orange -> Blue -> Purple).

---

## v1.0.0 - Modular Refactor
**Date**: Initial Architecture Shift

Transitioned from a monolithic prototype to a scalable component architecture.
*   Extracted `TacticalHUD`, `StageContentArea`, and `WelcomeScreen`.
*   Created `useParliamentEngine` hook.
*   Established strict TypeScript definitions.
