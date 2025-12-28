# 📐 Development Specifications (v1.2)

**Objective**: Maintain strict type safety and consistent data structures across the application to facilitate the future switch from Mock Data to Real API.

---

## 1. Shared Types (`types.ts`)

The application relies on these specific string literals and interfaces. Any new feature must adhere to these.

### 1.1. Agent Identity
*   **Type**: `AgentId`
*   **Values**: `'kant' | 'kojima' | 'nietzsche' | 'confucius' | 'chair'`
*   **Rule**: All data maps (Progress, Answers) must be keyed by this type.

### 1.2. Simulation Stages
*   **Type**: `SimulationStage`
*   **Values**:
    *   `'idle'`: App is in Welcome Screen.
    *   `'stage1'`: Agents are generating (Parallel).
    *   `'stage2'`: Agents are reviewing (Peer-to-Peer).
    *   `'stage3'`: Chairperson is synthesizing (Final).

### 1.3. Structured Data Models
These models mimic what we expect to receive from the LLM JSON mode in Phase 2.

**Agent Response (Stage 1 Output)**
```typescript
interface AgentResponse {
  title: string;
  content: string[]; // Array of paragraphs for easier UI rendering
}
```

**Peer Review (Stage 2 Output)**
```typescript
interface PeerReview {
  id: number;
  from: AgentId; // The Reviewer
  to: AgentId;   // The Target
  comment: string;
  type: 'criticism' | 'suggestion' | 'rhetoric';
}
```

**Ranking (Stage 3 Output)**
```typescript
interface Ranking {
  id: AgentId;
  score: number; // 0.0 - 10.0
  rank: number;  // 1 - 4
}
```

---

## 2. Component Contract: `TacticalHUD`

The HUD is the most complex component. It requires specific props to function correctly without crashing.

```typescript
props: {
  stage: SimulationStage;
  agentProgress: Record<AgentId, number>; // Must handle missing keys gracefully (default to 0)
  evaluations: PeerReview[];              // Used for the SVG overlay
  selectedAgents: AgentId[];              // Determines which "Slots" are rendered
  consensusUnlocked: boolean;             // Triggers the "Ready" state
  hasViewedConsensus: boolean;            // If true, hides the "Click Me" overlay
  onConsensusClick: () => void;
}
```

## 3. Mock Data Strategy
Currently defined in `mockData.ts`.
*   **Protocol Presets**: Used in `WelcomeScreen`. Contains `id`, `title`, `icon`, `desc`.
*   **Logic**: The `useParliamentEngine` hook interpolates this static data.
    *   *Stage 1*: Fills progress bars to 100%.
    *   *Stage 2*: Pushes items from `STAGE2_EVALUATIONS` array one by one.
    *   *Stage 3*: Pushes items from `STAGE3_STEPS` array.

---

## 4. Future API Integration Strategy (Phase 2)
When replacing `useParliamentEngine` logic with real API calls:
1.  **Keep the Hook Interface**: Do not change the return signature of `useParliamentEngine`.
2.  **Replace `setInterval`**: Use `await gemini.generateContent()` inside the `useEffect`.
3.  **Streaming**: Map the API stream chunks to `thinkingSteps` state to maintain the "live typing" effect.
