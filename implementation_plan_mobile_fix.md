# Implementation Plan - Mobile Layout Optimization

Goal: Resolve the issue where mobile cards obscure the input box by reducing card size and adjusting layout.

## User Review Required
> [!NOTE]
> Reducing mobile card dimensions significantly (approx 20% smaller) to fit vertically. Font sizes inside cards will also be scaled down.

## Proposed Changes

### Frontend Components

#### [MODIFY] [CouncilorCard.jsx](file:///e:/project/llm_council_sentinel/frontend/src/components/welcome/CouncilorCard.jsx)
- Reduce mobile dimensions from `w-[240px] h-[320px]` to `w-[180px] h-[240px]` (approx).
- Scale down internal text sizes (name, role, status) for the smaller card.

#### [MODIFY] [WelcomeScreen.jsx](file:///e:/project/llm_council_sentinel/frontend/src/components/WelcomeScreen.jsx)
- Adjust the grid/flex layout to ensure the bottom container (InfoPanel + Input) has proper spacing.
- Ensure the card carousel has `mb-auto` or reduced bottom margin to pull it up.

## Verification Plan

### Manual Verification
- Resize browser window to mobile width (< 768px).
- Verify that the card carousel is smaller.
- Verify that the Input Box and InfoPanel are fully visible at the bottom and not covered by cards.
- Check that text inside the cards is still legible.
