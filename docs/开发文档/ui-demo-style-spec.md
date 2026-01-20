# UI Demo Style Spec (Sentinel Consensus Look)

## Table of Contents
- Overview
- User Scenarios and Requirements
- Decision Review Summary
- Design Targets and Constraints
- HUD Layout Mapping (Top Strip)
- Reference Demo (Image 2) Fidelity Notes
- Visual System (Tokens)
- Texture CSS Details
- Councilor Color Scope
- Component Mapping and Detailed Plan
- Optional UI Components (Not Required)
- Font Self-Hosting Plan (woff2)
- Tailwind Config Extension
- Background Texture Plan
- Deferred Ideas (Not Recommended)
- Technical Flow Diagram
- Affected Files and Key Changes (Planned)
- Non-Goals and Exclusions
- Risks and Open Questions
- Acceptance Checklist

## Overview
This document defines how to restyle the current "new system" UI in `frontend/src/*`
to match the demo look found in `tests/sentinel-consensus-system`. The change is
strictly visual: no logic, controls, interactions, or animations are to be modified.
The demo's "System Time" module is explicitly excluded.

## User Scenarios and Requirements
### User Scenarios
1) Operator starts a session on the Welcome screen, selects councilors, and views
   Stage 1/2/3 outputs with a sci-fi HUD aesthetic.
2) Operator uses the top HUD strip (left mission logs, center tabs, right peer reviews)
   as the main navigation header while preserving existing interactions.
3) Operator tracks Stage progress in the bottom Tactical HUD with consistent neon
   styling and texture.

### Requirements (Confirmed)
| Item | Requirement |
|---|---|
| Scope | Only `frontend/src/*` (new system) |
| Visual | Match demo style (neon cyan + dark HUD) |
| Logic | No changes to logic, buttons, interactions, or animations |
| System Time | Remove / do not add |
| Fonts | Self-host Orbitron + Rajdhani woff2 |
| Background | Keep demo-like grid/scanline textures |
| Councilor colors | Use neon cyan palette globally; keep councilor colors only in small labels/dots |

## Decision Review Summary
This table captures the design decisions reviewed and agreed.

| Item | Assessment | Conclusion | Rationale |
|---|---|---|---|
| Top HUD layout mapping | Reasonable | Adopt Option A | Keep three independent headers; unify visual height/borders to avoid layout logic changes. |
| Background layer performance | Reasonable | Adopt with reduced motion | Perspective + animation may stutter on low-end devices; add `prefers-reduced-motion` handling. |
| Font fallback | Reasonable | Adopt | Rajdhani lacks CJK; add cross-platform CJK fallback chain. |
| TacticalHUD styling | Reasonable | Adopt (clear direction) | Unify cyan borders/textures while preserving stage semantic colors. |
| Tailwind extension | Reasonable | Adopt | Needed for `bg-hud-*` classes unless using `bg-[var(--...)]`. |
| NeonText/TechPanel components | Optional | Optional adoption | Utility classes are enough; components improve cleanliness without logic impact. |
| CSS consolidation | Disputed | Not recommended | Scope increases and risk is higher; prefer HUD utility classes in `index.css`. |
| Background component | Optional | Optional adoption | Separation of concerns; not required for visual changes. |
| Stage color semantics | Reasonable | Adopt | Stage colors communicate function; keep as non-cyan accents. |

## Design Targets and Constraints
- The existing top "HUD" area is the combination of:
  - `Sidebar` header (left)
  - `StageContentArea` tabs bar (center)
  - `DetailPanel` header (right)
- We will not add a new header; only restyle these existing sections.
- Approach: keep three independent headers but unify visual height, borders, and
  background so they read as one continuous HUD strip.
- Existing animations remain as-is; only color/spacing/texture/class changes.
- Only ASCII characters should be used in files unless existing file already uses non-ASCII.

## HUD Layout Mapping (Top Strip)
We will not introduce a new cross-column `<header>`. Instead, each of the three
existing headers will adopt the same HUD styling so they visually align.

```
[Sidebar Header] | [Tabs Bar] | [Detail Header]
  same height    | same bg    | same border rhythm
```

## Reference Demo (Image 2) Fidelity Notes
This spec targets the look shown in the second reference image (full HUD grid, cyan
lines, bright headers). The goal is to replicate the visual language, not to copy
layout or text content.

Must-match visual cues:
- Full-width HUD atmosphere with cyan grid background across the main canvas.
- Thin cyan edge lines and subtle glowing borders on panels.
- HUD headers are uppercase, letter-spaced, and use the Orbitron font.
- Cards use near-black fill with cyan or teal accent lines.
- Status dots are small, color-coded accents (councilor colors only here).

Explicit exclusions:
- No "System Time" module anywhere.
- No text or copy changes; keep existing UI labels and wording.

## Visual System (Tokens)
All tokens are centralized in `frontend/src/index.css` and applied via Tailwind
classes + custom utility classes.

### Color Tokens (Planned)
| Token | Value | Usage |
|---|---|---|
| --hud-bg | #050a14 | Primary HUD background |
| --hud-bg-soft | #0a0f1e | Panel surfaces |
| --hud-cyan | #06b6d4 | Main accent |
| --hud-cyan-soft | rgba(6,182,212,0.2) | Borders/soft glow |
| --hud-amber | #f59e0b | Secondary accent |
| --hud-text | #e0f2fe | Primary text |
| --hud-muted | #5b6b7a | Secondary text |

### Typography Tokens (Planned)
| Layer | Font | Weight |
|---|---|---|
| HUD labels, tabs | Orbitron | 500 |
| Primary titles | Orbitron | 700/900 |
| Body text | Rajdhani | 400/500 |
| Secondary text | Rajdhani | 300 |
| Mono text | existing mono | 500 |

### Utility Classes (Planned)
- `.bg-grid-floor`: Perspective cyan grid (demo style)
- `.bg-scanline`: subtle scanline overlay
- `.clip-corner-both`: chamfered panel corners
- `.hud-glow`: cyan glow for key elements

## Texture CSS Details
These are the explicit texture definitions that should be used to match the demo.
Implement them in `frontend/src/index.css` and apply via overlay divs or utility classes.

```css
/* Grid floor (demo-like) */
.bg-grid-floor {
  background-image:
    linear-gradient(#06b6d4 1px, transparent 1px),
    linear-gradient(90deg, #06b6d4 1px, transparent 1px);
  background-size: 40px 40px;
  transform: perspective(500px) rotateX(20deg) scale(1.5);
  transform-origin: center 80%;
  opacity: 0.2;
}

/* Vignette */
.bg-vignette {
  background: radial-gradient(circle at center, transparent 0%, #000000 90%);
  opacity: 1;
}

/* Scanline */
.bg-scanline {
  background-image: linear-gradient(transparent 50%, #000 50%);
  background-size: 100% 4px;
  opacity: 0.03;
}

/* Soft cyan sweep */
.bg-cyan-sweep {
  background: linear-gradient(to bottom, transparent, rgba(6,182,212,0.05), transparent);
  animation: scanline 8s linear infinite;
}

@keyframes scanline {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}

@media (prefers-reduced-motion: reduce) {
  .bg-cyan-sweep {
    animation: none;
  }
  .bg-scanline {
    background-image: none;
  }
}
```

## Councilor Color Scope
Councilor colors are preserved only in small indicators to keep a unified neon-cyan
system. Everything else uses the cyan palette.

Allowed councilor color usage:
- `DetailPanel` judge dot (4-8px) and small rank dot in review cards.
- `TacticalHUD` tiny indicator dots (if any) but not full card borders or fills.

Not allowed for councilor color:
- Tabs backgrounds or borders.
- Main content panel borders or titles.
- Agent slice full borders or progress fills in Tactical HUD.

## Component Mapping and Detailed Plan
### 1) Sidebar (`frontend/src/components/Sidebar.jsx`)
- Restyle header to match demo "MISSION LOGS" bar.
- Button "Initiate Session" uses demo clip-corner and cyan glow.
- Conversation list uses tech panel look with left border and subtle scanline.
- Keep logic unchanged (selection, delete, mobile overlay).
- Keep existing text; only apply HUD styling (uppercase, tracking, cyan).

### 2) Tabs Bar (`frontend/src/components/StageContentArea.jsx`)
- Convert tabs to demo HUD strip style (monospace/Orbitron, cyan borders).
- Active tab uses cyan outline; inactive uses muted slate.
- Consensus tab retains state logic; only visual changes.
- Keep existing tab labels; no copy changes.

### 3) Main Content (`frontend/src/components/StageContentArea.jsx`)
- Apply demo panel framing: border lines, corner brackets, neon title.
- Thinking section styled as "LOGIC_PROCESS" block (emerald/teal tone).
- Preserve existing thinking expansion and auto-fold logic.

### 4) Detail Panel (`frontend/src/components/DetailPanel.jsx`)
- Header uses demo HUD strip with cyan label.
- Judge cards updated to tech-card style (cyan lines, subtle glow).
- Peer review list uses demo card style with small status dots.
- Keep timers and review delay logic intact.
- Keep existing header text (no label renaming).

### 5) Tactical HUD (`frontend/src/components/TacticalHUD.jsx` + .css)
- Convert to demo-like bottom action bar appearance.
- Agent slices retain structure and hover, but colors/texture change.
- Progress fill uses cyan stripe pattern.
- Preserve stage semantic colors for the top border (stage1 orange, stage2 blue,
  stage3 purple). All other accents stay cyan.

### 6) Welcome Screen (`frontend/src/components/WelcomeScreen.jsx`)
- Apply demo font stack and cyan/amber accents.
- Preserve selection logic and input submission behavior.

## Optional UI Components (Not Required)
These components are optional for code cleanliness. They do not change logic.
If skipped, use utility classes instead.

### NeonText (optional)
Suggested location: `frontend/src/components/ui/NeonText.jsx`
- Purpose: consistent neon glow text styling.
- Use for HUD labels and section headers.

### TechPanel (optional)
Suggested location: `frontend/src/components/ui/TechPanel.jsx`
- Purpose: reusable chamfered panel wrapper with HUD borders.
- Use for Sidebar list items and DetailPanel cards.

### Background (optional)
Suggested location: `frontend/src/components/ui/Background.jsx`
- Purpose: encapsulate grid + vignette + scanline layers.
- Use in `App.jsx` root container to keep layout clean.

## Font Self-Hosting Plan (woff2)
### Files (Planned)
```
frontend/public/fonts/Orbitron-500.woff2
frontend/public/fonts/Orbitron-700.woff2
frontend/public/fonts/Orbitron-900.woff2
frontend/public/fonts/Rajdhani-300.woff2
frontend/public/fonts/Rajdhani-400.woff2
frontend/public/fonts/Rajdhani-500.woff2
frontend/public/fonts/Rajdhani-700.woff2
```

### CSS (Planned)
Add `@font-face` definitions in `frontend/src/index.css`, then apply:
- `body { font-family: Rajdhani, <platform fallback>, sans-serif; }`
- `.hud-title, .hud-label` set to Orbitron

### Font Source and Notes
- Source: Google Fonts (download woff2 files, then self-host).
- Format: woff2 only.
- CJK coverage: Orbitron/Rajdhani do not cover CJK; allow system fallback for CJK.

### @font-face Template (Planned)
```css
@font-face {
  font-family: "Orbitron";
  src: url("/fonts/Orbitron-500.woff2") format("woff2");
  font-weight: 500;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Orbitron";
  src: url("/fonts/Orbitron-700.woff2") format("woff2");
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Orbitron";
  src: url("/fonts/Orbitron-900.woff2") format("woff2");
  font-weight: 900;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Rajdhani";
  src: url("/fonts/Rajdhani-300.woff2") format("woff2");
  font-weight: 300;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Rajdhani";
  src: url("/fonts/Rajdhani-400.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Rajdhani";
  src: url("/fonts/Rajdhani-500.woff2") format("woff2");
  font-weight: 500;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Rajdhani";
  src: url("/fonts/Rajdhani-700.woff2") format("woff2");
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}

body {
  font-family:
    "Rajdhani",
    -apple-system,
    BlinkMacSystemFont,
    "PingFang SC",
    "Microsoft YaHei",
    "Segoe UI",
    sans-serif;
}
.hud-title, .hud-label {
  font-family: "Orbitron", "Rajdhani", sans-serif;
}
```

## Tailwind Config Extension
If we want token-based class names such as `bg-hud-cyan`, extend Tailwind in
`frontend/tailwind.config.js` to map CSS variables to colors.

```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      hud: {
        bg: "var(--hud-bg)",
        "bg-soft": "var(--hud-bg-soft)",
        cyan: "var(--hud-cyan)",
        amber: "var(--hud-amber)",
        text: "var(--hud-text)",
        muted: "var(--hud-muted)",
      },
    },
  },
},
```

## Background Texture Plan
Implement demo textures in `frontend/src/index.css` and apply to root container:
- Grid floor effect (perspective transform)
- Vignette overlay
- Scanline overlay (light opacity)

### Layering and Placement
Apply textures at the root app wrapper (recommended `frontend/src/App.jsx`):
1) Grid floor (lowest)
2) Vignette (middle)
3) Scanline + cyan sweep (top)

All layers should be `position: absolute; inset: 0; pointer-events: none;`.
Ensure main UI content has higher z-index to keep text legible.

### Reduced Motion Handling
Respect `prefers-reduced-motion: reduce` by disabling scanline and cyan sweep
animations. The static grid + vignette should remain.

### Performance Hints (Optional)
If needed, add `will-change: transform;` to animated layers (`.bg-cyan-sweep`)
to hint GPU acceleration. Use sparingly to avoid excessive memory usage.

## Deferred Ideas (Not Recommended)
- Consolidating all component CSS files into a single file is out of scope.
  Use shared HUD utility classes in `frontend/src/index.css` instead.

## Technical Flow Diagram
```
User Action
    |
    v
Existing UI Logic (unchanged)
    |
    v
Restyled Visual Layers (CSS/Tailwind only)
    |
    v
Rendered HUD (neon cyan + textures)
```

## Affected Files and Key Changes (Planned)
| File | Planned Changes |
|---|---|
| frontend/src/index.css | Add fonts, tokens, background textures, utility classes |
| frontend/src/components/Sidebar.jsx | Apply HUD header + tech panels |
| frontend/src/components/StageContentArea.jsx | Tabs bar + main panel restyle |
| frontend/src/components/DetailPanel.jsx | HUD header + review cards restyle |
| frontend/src/components/TacticalHUD.jsx | HUD base + agent slice restyle |
| frontend/src/components/TacticalHUD.css | Update patterns and borders |
| frontend/src/components/WelcomeScreen.jsx | Cyan/amber accents and fonts |
| frontend/tailwind.config.js | Extend HUD token colors (if using token classes) |
| frontend/public/fonts/* | Add self-hosted woff2 files |
| frontend/src/components/ui/NeonText.jsx | Optional reusable neon text helper |
| frontend/src/components/ui/TechPanel.jsx | Optional reusable tech panel wrapper |
| frontend/src/components/ui/Background.jsx | Optional background layer component |

### Key Modification Examples (Pseudo)
| Area | Change Type |
|---|---|
| Tabs bar | Use `.hud-strip` classes, cyan border, Orbitron |
| Cards | Add `.clip-corner-both`, cyan edge lines |
| Background | `bg-grid-floor + scanline` overlay |
| Labels | Use neon cyan with subtle glow |

## Non-Goals and Exclusions
- No change to business logic or interaction behavior.
- No changes to `frontend_refactor/*`.
- No use of demo "System Time" module.
- No changes to backend or data flow.

## Risks and Open Questions
### Risks
- Overly strong background textures might reduce readability.
- Using Orbitron for too much body text may hurt legibility; keep it for labels/titles only.

### Open Questions
- None pending. All decisions confirmed by user.

## Acceptance Checklist
- Top HUD strip (Sidebar header + Tabs bar + Detail header) uses Orbitron and cyan borders.
- System Time module is not present anywhere.
- Global background shows grid floor + scanline + vignette without reducing text contrast.
- Councilor colors appear only in small dots/mini indicators; all major borders/fills are cyan.
- Mobile layout remains unchanged in behavior; only visuals update.
- No logic, controls, or animations were modified.
