# Mobile Review Drawer - E2E Test Scenarios

## Test Environment
- Device: Mobile viewport (<768px width)
- Browser: Chrome/Firefox DevTools Mobile Emulation

## Test Scenarios

### Scenario 1: Basic Drawer Functionality
**Steps:**
1. Open application on mobile viewport
2. Start a new conversation
3. Observe drawer behavior through stages

**Expected Results:**
- Stage 1: Drawer closed by default, can be opened manually
- Stage 2: Drawer opens, height increases as judges appear (debounced)
- Stage 3: Drawer shows with fullscreen button
- Clicking backdrop closes drawer
- Clicking X button closes drawer

---

### Scenario 2: Height Tier Transitions (Stage 2)
**Steps:**
1. Start conversation and enter Stage 2
2. Open detail panel
3. Observe height changes as judges start thinking

**Expected Results:**
- Initially: 30vh (1 judge)
- After 2nd judge appears (300ms delay): 45vh
- After 3rd judge appears (300ms delay): 60vh
- Height only increases, never decreases
- No jitter or rapid transitions

---

### Scenario 3: Mutual Exclusivity
**Steps:**
1. Open left sidebar (conversation list)
2. Click detail panel button
3. Verify sidebar closes
4. Close detail panel
5. Open left sidebar again
6. Verify detail panel is closed

**Expected Results:**
- Only one panel can be open at a time on mobile
- Opening one automatically closes the other
- Desktop: Both can be open simultaneously

---

### Scenario 4: Fullscreen Toggle (Stage 3)
**Steps:**
1. Navigate to Stage 3
2. Open detail panel
3. Click fullscreen button
4. Observe height change
5. Click minimize button

**Expected Results:**
- Initial height: 60vh
- After fullscreen click: 90vh
- After minimize click: back to 60vh
- Icon changes: Maximize2 ↔ Minimize2

---

### Scenario 5: Stage 1 Prompt Display
**Steps:**
1. Start a new conversation with question "What is AI?"
2. Enter Stage 1
3. Open detail panel manually

**Expected Results:**
- Drawer opens at 30vh
- User question "What is AI?" is displayed
- Content is scrollable if question is long

---

### Scenario 6: Desktop Compatibility
**Steps:**
1. Resize browser to desktop width (≥768px)
2. Start conversation
3. Observe panel behavior

**Expected Results:**
- Panel slides from right (not bottom)
- No drag handle visible
- Full height panel (not vh-based)
- Auto-opens on stage change
- Left sidebar and right panel can coexist

---

## Automated Test Commands

```bash
# Run unit tests
cd frontend
npm test

# Run build test
npm run build

# Visual regression (if available)
npm run test:visual
```

## Manual Testing Checklist

- [ ] Drawer appears from bottom on mobile
- [ ] Drag handle visible on mobile only
- [ ] Height tiers work (30/45/60vh)
- [ ] Fullscreen toggle works (Stage 3)
- [ ] Mutual exclusivity enforced
- [ ] User prompt displays (Stage 1)
- [ ] Smooth animations (no jitter)
- [ ] Content scrolls properly
- [ ] Desktop behavior unchanged
- [ ] All stages tested
