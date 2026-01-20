# Mobile Review Drawer & Desktop Layout Implementation

**Status:** Implemented ✅
**Last Updated:** 2026-01-20

## 1. Overview
This document details the responsive layout implementation for the "Right Detail Panel" (Review Panel).
- **Mobile (< 768px)**: Bottom Drawer (Sheet) overlay.
- **Desktop (>= 768px)**: 3-Column Standard Layout (Sidebar - Content - RightPanel).

## 2. Interaction Specification (Mobile)

### 2.1 Opening Logic
- **Stage 2 Auto-Open**: The drawer automatically opens when the session transitions to `Stage 2` (Review Phase). Code: `useEffect` in `App.jsx`.
- **Manual Toggle**: Users can toggle the drawer via the `TacticalHUD` controls ("Toggle Detail Panel").
- **Tab Switching**: Clicking an Agent Card in the `TacticalHUD` bottom bar:
  - Switches the visible content.
  - **Keeps the drawer OPEN** (via `stopPropagation()`).
  - Highlights the active agent.

### 2.2 Closing Logic ("Tap-to-Stow")
- **Background Tap**: Tapping the **Content Background** (the scrollable area of `StageContentArea` or `WelcomeScreen`) closes the drawer.
- **Scroll Safe**: Scrolling the content background does **NOT** close the drawer.
- **HUD Safe**: Tapping the HUD bottom bar does **NOT** close the drawer (since HUD is visually distinct and event isolated).
- **Explicit Close**: Tapping the "X" button in the Drawer Header closes it.
- **Stage 1 Behavior**: In Stage 1, the drawer is typically closed unless manually opened.

### 2.3 Layout & Z-Index
- **Drawer (`DetailPanel.jsx`)**:
  - Position: `fixed bottom-0 left-0 right-0`.
  - Z-Index: `z-50`.
  - Height: Responsive (`30vh`, `45vh`, `60vh`, `90vh` full).
  - Dragging: Visual drag handle (top) indicates interactability but height change is state-driven.
- **HUD (`TacticalHUD.jsx`)**:
  - Position: `absolute bottom-0 left-0 ... z-30` (Mobile).
  - Layering: Visually sits *behind* the drawer if drawer is tall, but remains accessible when drawer is closed or partial.
- **Main Content (`StageContentArea.jsx`)**:
  - Position: `relative z-10`.
  - Interaction: `onClick` listener attached to the specific scrolling container `div`.

## 3. Interaction Specification (Desktop)

### 3.1 3-Column Layout
On screens wider than 768px, the layout shifts to a rigid 3-column system:
1.  **Left Sidebar (260px)**: Conversation History.
2.  **Middle Content (Flex-1)**: Chat/Stage Area + HUD.
3.  **Right Panel (400px)**: Review Details.

### 3.2 Behavior
- **Push Interaction**: Opening the Right Panel **compresses** the Middle Content width. It does **NOT** overlay content.
- **HUD Width**: The Tactical HUD is part of Middle Content, so it naturally shrinks to fit the available space, ensuring all controls remain visible.
- **Auto-Open**: Right Panel auto-opens on Stage 2/3 start.

## 4. Key Component Implementation Details

### 4.1 App.jsx
- Manages `isPanelOpen` state.
- Handles responsive logic (`window.innerWidth` checks).
- Passes `handleContentClick` (Tap-to-Stow logic) to content areas.
- Uses `flex-col` + `flex-row` nesting to achieve the 3-column structure.

### 4.2 TacticalHUD.jsx
- **Flex Layout**: Root container uses `flex flex-col` to allow inner content to fill min-height.
- **Dynamic Height**: Height adapts to content.
- **Consistency**: Used `whitespace-nowrap` on headers to prevent breaking lines on narrow screens.
- **Min-Height expansion**: When the "Consensus Ready" banner appears (Stage 3), the HUD height naturally expands (via flex) to ensure the banner is not clipped.

### 4.3 StageContentArea.jsx
- Contains the `onClick` listener for "Tap-to-Stow".
- Ensures listener is on the *background* container, not interactive buttons.

## 5. CSS & Styling
- **Tailwind CSS**: Primary styling engine.
- **Animations**: `transition-all duration-300` used for smooth drawer slide-in/out.
- **Backdrop**: Mobile does **not** use a full-screen backdrop blocker, allowing interaction with the top visible part of the content.
