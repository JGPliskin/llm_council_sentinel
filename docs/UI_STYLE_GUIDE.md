# UI_STYLE_GUIDE.md - LLM Council Sentinel HUD Visual System (As-Built)

This document defines the long-term visual style for the project. It is the canonical, non-ambiguous UI reference. All UI work should align to this HUD style.

---

## 1. Visual Direction
- Style: dark sci-fi HUD, neon cyan, high contrast, minimal color variance.
- Keywords: HUD, grid, scanline, chamfered panels, cyan glow.
- Constraint: visuals only; do not change logic or interaction behavior when applying styling.
- Explicit exclusion: System Time module is not used.

---

## 2. Color System
### 2.1 Core Tokens (frontend/src/index.css)
```css
:root {
  --hud-bg: #050a14;
  --hud-bg-soft: #0a0f1e;
  --hud-cyan: #06b6d4;
  --hud-cyan-soft: rgba(6, 182, 212, 0.2);
  --hud-amber: #f59e0b; /* allowed only for small status dots if needed */
  --hud-text: #e0f2fe;
  --hud-muted: #5b6b7a;

  /* Accent palette (only cyan is used for main UI) */
  --accent-cyan: #06b6d4;
  --accent-purple: #a855f7; /* legacy; do not use in UI */
}
```

### 2.2 Usage Rules
- Primary UI color is cyan only.
- Purple is not used in UI.
- Councilor colors are unified to cyan (avoid multi-color UI).
- Only small status dots may use secondary accents if absolutely required.

---

## 3. Typography
### 3.1 Fonts
- Body: Rajdhani
- HUD labels/titles: Orbitron
- Mono: existing system mono stack

### 3.2 Font Sources (self-hosted)
Location: `frontend/src/assets/fonts/`
- Orbitron: woff2 weights (400, 500, 700, 900)
- Rajdhani: woff2 weights (300, 500, 700)

Applied in `frontend/src/index.css` via:
```css
@import "./assets/fonts/fonts.css";

body {
  font-family:
    "Rajdhani",
    -apple-system, BlinkMacSystemFont,
    "PingFang SC", "Microsoft YaHei",
    "Segoe UI", sans-serif;
}

.font-hud, .hud-title, .hud-label {
  font-family:
    "Orbitron",
    "Rajdhani",
    -apple-system, BlinkMacSystemFont,
    "PingFang SC", "Microsoft YaHei",
    "Segoe UI", sans-serif;
}
```

---

## 4. Background and Texture
### 4.1 Layers (Always On)
Background is fixed and always visible in all states (Welcome + Stage 1-3):
1) Perspective grid floor
2) Flat grid
3) Vignette
4) Scanline + cyan sweep

Implementation: `frontend/src/components/ui/Background.jsx`

### 4.2 Reduced Motion
- Use `prefers-reduced-motion` to disable scanline/sweep animation.
- Grid and vignette remain visible.

### 4.3 Performance Hints
- Add `will-change: transform` to animated layers.

---

## 5. Layout Rules
### 5.1 Desktop
- Sidebar: fixed left column, width ~260px (`w-64`).
- Right Panel: fixed right column, width 400px; slides in/out horizontally.
- Center: flexible main content column.

### 5.2 Mobile
- Sidebar: overlay drawer.
- Right Panel: bottom sheet drawer (vertical slide), height tiers remain.

---

## 6. Component Style Rules

### 6.1 Sidebar
File: `frontend/src/components/Sidebar.jsx`
- Header: Mission Logs HUD strip with cyan text and small bar.
- Initiate Session button: solid translucent fill (no diagonal stripes).
- Active conversation: cyan border + small dot in top-right.

### 6.2 Tabs (StageContentArea)
File: `frontend/src/components/StageContentArea.jsx`
- Tabs border width is uniform (1px) on top/left/right.
- Consensus tab uses cyan, not purple.

### 6.3 Main Content
File: `frontend/src/components/StageContentArea.jsx`
- Panels use chamfered corners and cyan edge lines.
- Proposal header uses cyan only (no amber/purple).
- Logic process header text is always `LOGIC_PROCESS` to avoid overlap.

### 6.4 Right Panel (Peer Reviews)
File: `frontend/src/components/DetailPanel.jsx`
- Panels and cards use cyan border + dark fill.
- Review header and rank use cyan.

### 6.5 Bottom HUD (TacticalHUD)
Files: `frontend/src/components/TacticalHUD.jsx`, `frontend/src/components/TacticalHUD.css`
- Card borders must be uniform on all sides (1px).
- No purple accents; use cyan across all HUD elements.

### 6.6 Consensus Beacon
File: `frontend/src/components/ConsensusBeacon.css`
- Beacon uses cyan glow (no purple).

---

## 7. Utility Classes (frontend/src/index.css)
Required utilities for HUD style:
- `.bg-grid-floor`, `.bg-grid-pattern`
- `.bg-vignette`, `.bg-scanline`, `.bg-cyan-sweep`
- `.hud-panel`, `.hud-panel-soft`
- `.clip-corner-both`, `.clip-corner-top-right`
- `.hud-glow`, `.hud-label`, `.hud-title`

---

## 8. Non-Goals
- Do not introduce System Time.
- Do not change logic or API behavior.
- Do not use multi-color theme elements.

---

## 9. Verification Checklist
- [ ] Background grid visible in Welcome + Stage 1-3.
- [ ] No purple elements remain in UI.
- [ ] Tabs and bottom HUD borders have uniform widths.
- [ ] Right panel slides horizontally on desktop and vertically on mobile.
- [ ] Logic process header shows only `LOGIC_PROCESS`.

---

Last updated: 2026-01-22
