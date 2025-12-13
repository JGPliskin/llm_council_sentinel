# AGENTS.md - Technical Architecture & workflows

This document provides a comprehensive technical reference for the LLM Council system, detailing the architecture, logic flows, state management, and operational rules.

## 1. System Overview

LLM Council is an asynchronous, multi-stage deliberation engine where a "Council" of diverse LLM personas debates a user query, peer-reviews each other's answers anonymously, and synthesizes a final consensus via a Chairman model.

### 1.1 Core Philosophy
- **Diversity**: Different models/personas avoid "echo chambers".
- **Anonymity**: Stage 2 reviews are blind to prevent model bias (e.g., favoring their own provider).
- **Safety**: Unhealthy models are strictly filtered out to prevent execution failures.
- **Transparency**: Every step (Raw answers, Peer reviews, Synthesis) is visible to the user.

---

## 2. Architecture & Components

### 2.1 Backend (`backend/`)

| Component | Functionality | Key Logic |
| :--- | :--- | :--- |
| **`main.py`** | FastAPI Entrypoint | - **Startup**: Preloads personas, validates initial health.<br>- **API**: `/api/councilors` (Health status), `/message` (Streaming).<br>- **Safety**: `resolve_target_councilors` enforces `healthy=True`. |
| **`council.py`** | Orchestration Engine | - Manages the 3-stage pipeline.<br>- implements `_bounded_query` with semaphores and retry logic.<br>- Handles anonymization maps. |
| **`validation.py`** | Health System | - **Probes**: Sends "Hello" to models.<br>- **Timeout**: 25s (relaxed for free tier).<br>- **Annotation**: Adds `healthy`, `health_error` to model objects. |
| **`config.py`** | Configuration | - Defines `COUNCILORS` list (ID, Name, Model, Persona Path).<br>- Defines `CHAIRMAN` definition.<br>- Sets timeouts and concurrency limits. |
| **`openrouter.py`** | LLM Client | - Async HTTP client for OpenRouter AI.<br>- Handles 429/500 retries.<br>- Normalizes responses. |
| **`storage.py`** | Persistence | - JSON-based flat file storage.<br>- Saves full conversation history.<br>- **Migration**: Handles schema updates (v1->v2 IDs). |

### 2.2 Frontend (`frontend/src/`)

| Component | Functionality | Key Logic |
| :--- | :--- | :--- |
| **`ChatInterface.jsx`** | Main UI | - Manages conversation stream.<br>- **State**: `selectedCouncilorIds` determines active participants.<br>- **Default**: Selects `active && healthy`. |
| **`CouncilAvatars.jsx`** | Member Display | - **Split Logic**: `available` vs `unavailable` (based on health).<br>- **Toggle**: "Show unavailable" allows inspecting dead models.<br>- **Visuals**: Checkmarks for selection, Grayscale for disabled. |
| **`Stage1.jsx`** | Proposal View | - Renders initial markdown answers side-by-side. |
| **`Stage2.jsx`** | Peer Review | - **Tabbed Interface**: Shows raw reviews.<br>- **Ranking**: Visualizes "Ranked 1st", "Ranked 2nd" etc.<br>- **Disclosure**: Shows real names but notes they were anonymous during review. |

---

## 3. Detailed Logic & Workflows

### 3.1 Health Check & Safety Workflow
The system ensures reliability by filtering out dead models *before* they cause errors.

1.  **Startup / Refresh**:
    -   `validate_council_health` iterates all defined models.
    -   **Probe**: Sends `{"role": "user", "content": "Hello"}` via `check_model_health`.
    -   **Timeout**: **25 seconds** (Accommodates cold starts on free tiers).
    -   **Result**: Returns full list annotated with `healthy: bool` and `health_error: str`.
2.  **API Exposure**:
    -   `/api/councilors` returns this annotated list.
3.  **Execution Guard** (`resolve_target_councilors`):
    -   When a user sends a message, they send `councilor_ids`.
    -   **Strict Check**: The backend verifies `is_healthy(id)`.
    -   **Default Safety**: If an ID is unknown or map lookup fails, it defaults to **`False` (Unhealthy)**.
    -   **Filtering**: Only healthy IDs are passed to the Stage 1 engine. Unhealthy ones are returned in `ignored_ids`.

### 3.2 The 3-Stage Deliberation Pipeline

#### Stage 1: Proposal Generation
*   **Goal**: Gather diverse perspectives.
*   **Concurrency**: Max 6 parallel requests.
*   **Retry Logic**: 2 Attempts per model.
    *   **Network Failure**: Backoff and retry.
    *   **JSON Failure**: Updates prompt with "Your previous reply was invalid..." and retries.
*   **Output**: List of JSON objects containing `answer_markdown` and a structured `judge_card`.

#### Stage 2: Anonymized Peer Review
*   **Anonymization**:
    *   Inputs: Valid results from Stage 1.
    *   Process: Assigns `anon_1`, `anon_2` etc. randomly (or structurally).
    *   Map: Stores `anon_id -> real_councilor_id` for later de-anonymization.
*   **Review Process**:
    *   Each Councilor (Judge) executes a "Ranking Task".
    *   **Prompt**: "You are a judge. Strict JSON. Rank these anonymous responses...".
    *   **Constraint**: Must include ALL `anon_ids` exactly once.
*   **Fallback**:
    *   If fewer than 2 valid Stage 1 candidates exist, Stage 2 is **Skipped** (`insufficient_candidates`).
    *   If all judges fail, Stage 2 is marked skipped (`all_judges_failed`).

#### Stage 3: Chairman Synthesis
*   **Input**: User Query + Stage 1 Answers + Stage 2 Reviews (if successful) + Aggregate Rankings.
*   **Role**: The Chairman (usually a high-reasoning model) acts as a neutral synthesizer.
*   **Prompt**: "Review the debate. Note the consensus. Acknowledge the winner (if any). Provide a final, actionable answer."
*   **Output**: A comprehensive markdown response.

### 3.3 State Management (Frontend)

*   **Selection Persistence**:
    *   `ChatInterface` maintains `selectedCouncilorIds`.
    *   On "New Conversation", this resets to the default (All Active & Healthy).
    *   During a conversation, the participants are *locked* to the message history to ensure continuity.
*   **Visual States**:
    *   **Available**: `healthy === true`. Shown normally.
    *   **Unavailable**: `healthy !== true`. Hidden by default.
    *   **Selected**: Green badge overlay.
    *   **Disabled**: Opacity 0.4, Grayscale, blocked interaction.

## 4. Configuration Rules

### 4.1 Port & Network
*   **Backend Port**: **8010** (Development/Local).
*   **Frontend Port**: **5173** (Vite).
*   **Docker**: Backend maps internal 8008 -> Host 80 via Nginx.

### 4.2 Model Constraints
*   **JSON Enforcement**: System prompts aggressively demand JSON.
*   **Context Windows**: Models must support at least 4k context for Stage 2 (reading multiple inputs).
*   **Free Tier Models**: Timeouts are explicitly tuned (25s Stage 1, 75s Stage 2) to tolerate slower APIs.

## 5. Troubleshooting Logic

*   **"Unavailable" Status**:
    *   Cause: `check_model_health` failed (timeout or error).
    *   Action: Click "Show unavailable" -> Hover tooltip to see error.
    *   Fix: Check OpenRouter key or try `/api/councilors?refresh=1`.
*   **"Ghost" Models**:
    *   If a model appears in `config.py` but not in the UI, check if it was filtered by the `startup_event` logic or if the backend process is stale (check Port 8010).
*   **Missing Stage 2**:
    *   If only 1 model succeeds in Stage 1, Stage 2 is skipped by design to save tokens.

---
*Created by [Your Name/Agent] - Last Updated: 2025-12-13*
