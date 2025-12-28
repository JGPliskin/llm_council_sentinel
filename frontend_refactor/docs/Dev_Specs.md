# 📐 Engineering Specifications (v1.0 Refactor)

**Objective**: Transition the "LLM Parliament" from a monolithic single-file prototype (`index.tsx`) into a modular, scalable, and type-safe React application ready for Google GenAI integration.

---

## 1. Architectural Patterns

### 1.1 Separation of Concerns
We will move from a "God Component" architecture to a layered approach:
*   **Presentation Layer (`/components`)**: Pure UI components with no business logic (e.g., `AgentSlice`, `TacticalHUD`).
*   **Container Layer (`/containers`)**: Handles state orchestration (e.g., `StageController`).
*   **Service Layer (`/services`)**: Abstraction for LLM API calls. Allows switching between "Mock" and "Real" providers easily.
*   **Domain Layer (`/types`, `/constants`)**: Shared truth (Interfaces, Enums, Configuration).

### 1.2 State Management
*   **Current**: Scattered `useState` and `setTimeout`.
*   **Target**: A custom `useParliament` hook utilizing `useReducer`. This is necessary to handle the complex state transitions of the 3-stage pipeline safely without race conditions.

---

## 2. Directory Structure (Proposed)

We will migrate the flat structure to a standard feature-based React structure:

```
src/
├── components/
│   ├── tactical/           # The specialized Sci-Fi UI kit
│   │   ├── AgentSlice.tsx
│   │   ├── ConnectionOverlay.tsx
│   │   └── DataBeacon.tsx
│   ├── layout/
│   │   ├── StageContentArea.tsx
│   │   └── UnifiedDetailPanel.tsx
│   └── shared/             # Generic atomic components
│       ├── Button.tsx
│       └── Icons.tsx
├── hooks/
│   └── useParliamentEngine.ts  # The core simulation logic
├── services/
│   ├── llm/
│   │   ├── types.ts        # Input/Output interfaces
│   │   ├── gemini.ts       # Google GenAI SDK Implementation
│   │   └── mock.ts         # The current static data (fallback)
│   └── prompts/            # System Instructions
│       ├── personas.ts     # Kant, Kojima, etc.
│       └── protocols.ts    # "Review" and "Consensus" logic
├── types/
│   └── index.ts            # Global Type Definitions
├── App.tsx
└── main.tsx
```

---

## 3. Core Type Definitions

To ensure type safety when parsing JSON responses from Gemini, we will strictly enforce these interfaces:

### 3.1 The Agent Entity
```typescript
export type AgentId = 'kant' | 'kojima' | 'nietzsche' | 'confucius' | 'chair';

export interface AgentProfile {
  id: AgentId;
  name: string;
  fullName: string;
  avatar: string; // Emoji or URL
  role: string;   // e.g., "Deontologist"
  color: string;  // UI theme color
  systemPrompt: string; // The "Brain" configuration
}
```

### 3.2 Simulation State
```typescript
export type SimulationStage = 'idle' | 'stage1_generation' | 'stage2_review' | 'stage3_consensus';

export interface ParliamentState {
  stage: SimulationStage;
  globalProgress: number; // 0-100
  activeAgentId: AgentId;
  
  // Data Containers
  opinions: Record<AgentId, AgentResponse>;
  reviews: PeerReview[];
  consensus: ConsensusReport | null;
  
  // Operational Flags
  isStreaming: boolean;
  error: string | null;
}
```

### 3.3 API Response Models
```typescript
// Stage 1 Output
export interface AgentResponse {
  title: string;
  markdownContent: string;
  timestamp: number;
}

// Stage 2 Output (Structured Generation)
export interface PeerReview {
  fromId: AgentId;
  toId: AgentId;
  score: number; // 1-10
  critique: string;
  suggestion: string;
}

// Stage 3 Output
export interface ConsensusReport {
  title: string;
  executiveSummary: string;
  finalVerdict: string;
  rankings: Array<{ agentId: AgentId; score: number }>;
}
```

---

## 4. Service Layer Strategy (The "Brain")

We will implement a **Strategy Pattern** for the AI Service.

### 4.1 Interface `LLMProvider`
```typescript
interface LLMProvider {
  // Stage 1: Parallel generation
  generateOpinion(agent: AgentProfile, userPrompt: string): Promise<AgentResponse>;
  
  // Stage 2: N*N Complexity (or subsets)
  reviewOpinion(reviewer: AgentProfile, target: AgentResponse): Promise<PeerReview>;
  
  // Stage 3: Synthesis
  synthesizeConsensus(opinions: AgentResponse[], reviews: PeerReview[]): Promise<ConsensusReport>;
}
```

### 4.2 Implementation: `GeminiService`
*   **SDK**: `@google/genai`
*   **Model**: `gemini-2.5-flash` (Ideal for low latency and committee tasks).
*   **Prompting Strategy**:
    *   **System Instruction**: Injected with the `AgentProfile.role` and `AgentProfile.systemPrompt`.
    *   **Format**: Use `responseSchema` (JSON mode) for Stage 2 (Reviews) and Stage 3 (Consensus) to ensure the UI can parse scores and rankings reliably. Stage 1 can remain free-form text or Markdown.

---

## 5. UI/UX "Tactical" Standards

Refactoring must **preserve** the current aesthetic. The following rules apply to new components:

1.  **Chamfered Edges**: Do not use `rounded-lg`. Use `clip-path` or SVG borders for containers.
2.  **Palette**:
    *   Primary: `zinc-950` (Background)
    *   Accents: `orange-500` (Processing), `teal-500` (Success), `purple-500` (Consensus).
3.  **Typography**:
    *   Headers: `Inter` (Black/Bold), Uppercase, Tracking-wide.
    *   Meta/Status: `JetBrains Mono` or `Fira Code`.
    *   Content: `Merriweather` (Serif) for long-form text reading comfort.
4.  **Motion**:
    *   All panels must enter via `fade-in` + `slide-in`.
    *   Active processes must have a generic "pulse" or "scanline" effect.

---

## 6. Implementation Roadmap

### Phase 2.1: Foundation (Days 1-2)
1.  Set up the folder structure.
2.  Extract `MOCK_DATA` into `services/llm/mock.ts`.
3.  Extract `AgentSlice` and `TacticalHUD` into strictly typed components.

### Phase 2.2: The Hook (Day 3)
1.  Build `useParliamentEngine` to replace the `useEffect` timers.
2.  Ensure UI behaves exactly the same as the prototype, but driven by the new hook.

### Phase 2.3: The Brain (Days 4-5)
1.  Implement `services/llm/gemini.ts`.
2.  Add `.env` support for `API_KEY`.
3.  Create the System Prompts for Kant, Kojima, Nietzsche, etc.
4.  **Switch the toggle**: Point the `useParliamentEngine` to use `GeminiService` instead of `MockService`.

---
*Document approved for Phase 2 kickoff.*
