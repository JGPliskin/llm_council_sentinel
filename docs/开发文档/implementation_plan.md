# Implementation Plan - Welcome Screen & UnitDeck Refactor (Final)

Refactor `WelcomeScreen` and `TacticalHUD` to strictly align with `neural-council-os` demo and `Welcome_UnitDeck_TacticalHUD_Spec.md`.
**Core Goal**: Refactor the Bottom Panel to be a unified **Bottom Panel Container (Status Bar + UnitDeckList)**. Welcome and Stage views will render **separate instances** of this container with different data sources.

## User Review Required
> [!IMPORTANT]
> - `CouncilorCard.jsx` will be repurposed as `StandingArtDisplay` for the central stage area.
> - `TacticalHUD.jsx` will be refactored to act as the shared **Bottom Panel Container**.

## Proposed Changes

### 1. Shared UI Components (New)

#### [NEW] `frontend/src/components/UnitDeckCard.jsx`
- **Purpose**: Pure visual component for a single card.
- **Props**:
  - `data`: `UnitDeckCardViewModel` (Contains `id`, `name`, `role`, `avatar`, `state` link/standby/skipped, `progress`, `rank`, `isActiveTab`).
  - `onClick`: `(id) => void`
  - `onHover`: `(id | null) => void`
- **Logic**: Visual state is derived entirely from `data`. No `isSelected` prop.

#### [NEW] `frontend/src/components/UnitDeckList.jsx`
- **Purpose**: Pure presentation container.
- **Props**: `items` (Array of ViewModels), `onItemClick`, `onItemHover`.
- **Responsive Layout**:
  - Controlled via CSS only (no layout props).
  - **Desktop**: Grid (`md:grid md:grid-cols-3`).
  - **Mobile**: Horizontal scroll (`flex overflow-x-auto snap-x snap-mandatory`).

### 2. Bottom Panel Container Logic

#### [MODIFY] `frontend/src/components/TacticalHUD.jsx`
- **Role**: `TacticalHUD` acts as **Bottom Panel Container** for Stage; Welcome renders a separate Bottom Panel Container instance with the same structure.
- **Structure**:
  - **Top**: `StatusBar` (Preserved, visible in both Welcome and Stage).
  - **Bottom**: `UnitDeckList` (Replaces old card list).
- **Stage Logic**:
  - **Data Mapping**: Map to `UnitDeckCardViewModel`.
  - **Filtering**: **Only** display resolved (participating) councilors.
  - **Badges**: Show "SKIPPED" badge (Stage 2), Rank Badge (Stage 3).
  - **Progress**: Horizontal progress fill (Stage 1/2). **Stage 3 does not show progress fill; rank badge only.**

### 3. Welcome Screen Refactor

#### [MODIFY] `frontend/src/components/WelcomeScreen.jsx`
- **Layout**:
  1.  **Center**: `StandingArtStage` (Container for `StandingArtDisplay`s).
  2.  **Top Layer (Overlay)**: `InfoPanel` + `CommandInput`.
  3.  **Bottom**: **Bottom Panel Container**: Welcome uses its own container (same markup as TacticalHUD) containing `Status Bar` + `UnitDeckList`.
- **Responsive Strategy**:
  - Use `100dvh` to handle mobile browser bars.
  - **Small Screens**: `<480px` clamp rules for card width, `safe-area` padding for bottom.
  - **Landscape**: Compression rules to ensure visibility.
  - **Keyboard Open**: Shrink `StandingArtStage` (e.g., to 20vh), ensure `CommandInput` remains visible.
- **Interaction Flow**:
  - **UnitDeck Click**: Toggle selection.
  - **Standing Art Click**: **Focus Lock** InfoPanel (No selection toggle).
  - **InfoPanel Button**:
    - Right-side button "LINK" / "UNLINK".
    - **Allow unlinking the last unit**: `CommandInput` becomes disabled (grayed out).
  - **Empty State**: Show "NO UNIT SELECTED" in **StandingArtStage + InfoPanel** (Welcome only).

### 4. Component Modifications

#### [MODIFY] `frontend/src/components/welcome/CouncilorCard.jsx` -> `StandingArtDisplay.jsx`
- **Role**: Refactor to be the "Standing Art" display only (no card frame).
- **Visuals**: Full-height standing art (3:5). Online (Hologram) vs Standby/Offline styles.

#### [MODIFY] `frontend/src/components/welcome/InfoPanel.jsx`
- **Features**:
  - Add LINK/UNLINK button.
  - Update priority: Hover (focused) > Focus Locked > Last Selected.

#### [MODIFY] `frontend/src/config/councilors.js`
- **Data**: Add `standing` image paths (mapped to `frontend/public/avatars/standing/).

## Verification Plan

### Manual Verification
- **Welcome Screen**:
  - [ ] **Status Bar** is visible above the Deck.
  - [ ] **Empty State** is shown when no units selected.
  - [ ] **LINK/UNLINK** button works in InfoPanel.
  - [ ] **Unlink Last Unit**: Input becomes disabled.
  - [ ] **Mobile Keyboard**: Input remains visible when keyboard is open.
- **Stage Views**:
  - [ ] **Resolved Only**: Only participating councilors appear in Deck.
  - [ ] **Badges**: Skipped badge (Stage 2), Rank badge (Stage 3) visible.
  - [ ] **Progress**: Horizontal fill works.
  - [ ] **Active Tab**: Highlight logic preserves.
