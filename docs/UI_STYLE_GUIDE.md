# UI_STYLE_GUIDE.md - LLM Council Sentinel HUD Visual System (As-Built)

This document defines the canonical, non-ambiguous UI style rules. All UI changes must conform to this HUD system unless explicitly scoped otherwise.

---

## 1. Visual Direction
- Style: dark sci-fi HUD, neon cyan, high contrast.
- Keywords: grid, scanline, chamfered panels, cyan glow, minimal noise.
- Constraint: visuals only; do not change logic or interaction behavior unless explicitly requested.

---

## 2. Color System

### 2.1 Core Tokens (`frontend/src/index.css`)
```css
:root {
  --hud-bg: #050a14;
  --hud-bg-soft: #0a0f1e;
  --hud-cyan: #06b6d4;
  --hud-cyan-soft: rgba(6, 182, 212, 0.2);
  --hud-amber: #f59e0b; /* allowed only for tiny status dots */
  --hud-text: #e0f2fe;
  --hud-muted: #5b6b7a;
}
```

### 2.2 Usage Rules
- Primary UI color: cyan only.
- Councilor-specific colors are allowed **only** for small badges or micro-accents (e.g., selection check badge background).
- Do not introduce purple or other accents for major UI regions.

---

## 3. Typography

### 3.1 Fonts
- Body: Rajdhani
- HUD titles/labels: Orbitron
- Mono: system mono stack

### 3.2 Source
Fonts are self-hosted in `frontend/src/assets/fonts/` and imported by `frontend/src/index.css`.

---

## 4. Background & Texture

### 4.1 Always-On Layers
Background layers must be visible in all states (Welcome + Stage1/2/3):
1) Perspective grid floor
2) Flat grid
3) Vignette
4) Scanline + cyan sweep

Implementation: `frontend/src/components/ui/Background.jsx`

### 4.2 Reduced Motion
Respect `prefers-reduced-motion` for scanline/sweep animation.

---

## 5. Layout Rules

### 5.1 Desktop
- Sidebar fixed on the left (≈ 260px).
- Right panel fixed on the right (≈ 400px).
- Center content fluid.

### 5.2 Mobile
- Sidebar becomes overlay drawer.
- Right panel becomes bottom sheet.

---

## 6. Avatar System

### 6.1 Asset Location
- Static assets: `frontend/public/avatars/`
- Avatar URL is supplied by backend (`/avatars/*.png`).

### 6.2 Cropping & Shape
- Avatars are displayed as **circular**.
- Use `object-cover` to avoid stretching.
- Outer selection ring **must not** be clipped by image masking.

**Recommended DOM layering**
```
[Outer Ring (no overflow-hidden)]
  [Inner Mask (overflow-hidden, circle)]
    [IMG object-cover]
```

---

## 7. Welcome Screen Selection Style

File: `frontend/src/components/WelcomeScreen.jsx`

Selection state is represented by:
- Full cyan ring (outer glow)
- Check badge on top-right
- Slight brightness increase

Non-selected state:
- Dimmed avatar
- Thin low-contrast ring

**No half-ring artifacts**: ensure the ring is not intersecting the masked avatar edge.

---

## 8. HUD Watermark

File: `frontend/src/components/TacticalHUD.css`
- `.agent-avatar-bg` is a watermark avatar used in cards.
- Opacity: 20% (0.2)
- `filter: grayscale(1)` to reduce distraction

---

## 9. Component Style Rules

### 9.1 Sidebar (`frontend/src/components/Sidebar.jsx`)
- Mission Logs strip with cyan glow
- Active conversation: cyan border + corner indicator

### 9.2 Tabs (`frontend/src/components/StageContentArea.jsx`)
- Uniform top/left/right borders
- Consensus tab uses cyan (no purple)

### 9.3 Right Panel (`frontend/src/components/DetailPanel.jsx`)
- Cyan border + dark fill
- Review headers use cyan

### 9.4 Bottom HUD (`frontend/src/components/TacticalHUD.jsx`)
- Card borders uniform (1px)
- No purple accents

---

## 10. Non-Goals
- Do not introduce System Time module.
- Do not change API or logic as part of styling.
- Avoid multi-color theme elements.

---

## 11. Verification Checklist
- [ ] Background grid visible in Welcome + Stage1/2/3.
- [ ] No purple elements in UI.
- [ ] Selection ring shows full circle with no clipping.
- [ ] HUD watermark opacity is 20%.

---

Last updated: 2026-01-23

