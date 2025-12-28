# 💡 Idea Inbox & MVP Roadmap

**Product**: LLM Parliament (The "Committee" Approach)
**Status**: MVP Simulation Complete
**Date**: October 2023

---

## 1. The Core Problem
*   **Issue**: Users blindly trust single LLM responses. Single models have biases and blind spots.
*   **Solution**: "Ensemble Intelligence" visualized. By personifying different models/prompts (The "Parliament"), users get a spectrum of answers (Conservative, Creative, Analytical) and a synthesized truth.

## 2. What Works (Current MVP)
The current build successfully demonstrates the **UX flow** of a multi-agent interaction without the cost/latency of real inference.

*   **The "Squeeze" UI**: The side panel interacting with the main text area effectively solves the problem of "Where do I show the reasoning without hiding the answer?".
*   **The Narrative Flow**: Moving from *Divergence* (Stage 1: Many answers) to *Convergence* (Stage 3: One consensus) feels natural.
*   **The Chairperson**: Giving the final synthesizer a personality ("The Chair") makes the summarization step engaging rather than just a utility.

## 3. Architectural Decisions (Why we built it this way)

### Why Client-Side Simulation first?
*   **Latency Design**: LLM Chains (Generate -> Read -> Evaluate -> Synthesize) are slow. We needed to design a UI that keeps the user engaged during 30s+ wait times. The "Step Logs" and "Progress Bars" were tuned here before real API integration.
*   **Visual Hierarchy**: Determining how to display 4 different essays + 12 different reviews + 1 final essay required rapid iteration on the layout (Tabs vs. Grid vs. Column).

### Why the Bottom HUD?
*   We observed that users need to know "Who is winning?" during the evaluation phase. Placing this at the bottom creates a "Ticker Tape" feel that is informative but unobtrusive.

## 4. Backlog / Idea Inbox

### Short Term (Features)
*   **"Objection!" Button**: Allow the user to pause simulation and inject a constraint (e.g., "Kojima, focus less on cutscenes").
*   **Cost Estimator**: Show how many tokens the "Parliament" is consuming in real-time.

### Long Term (Vision)
*   **The "War Room" View**: A visualization mode that shows connections/edges between agents who agree with each other (Graph View).
*   **HuggingFace Spaces Integration**: One-click deploy for the community to create their own Parliaments.

---

*This document serves as a high-level scratchpad for product direction.*
