---
trigger: always_on
description: Mandatory requirement grasping, checkpoint verification, and anti-drift protocols to prevent the AI from missing the mark.
---

# 🎯 Checkpoints & Grasping Protocol: Never Miss The Mark

This rule is **MANDATORY** for all tasks, plans, and implementations in this workspace.

---

## 1. Principle: Anti-Drift & Grounded Alignment
The AI assistant must NEVER rush into code generation, make ungrounded assumptions, or hallucinate project specifications. Every decision must align with the user's explicit vision, reference channels (e.g., `@GHIBLISTYLESTUDIO`), and existing project architecture.

---

## 2. Phase 0: The Mandatory Grasping Protocol (Before Any Code)

Before creating or heavily modifying code, pipelines, or architecture, the agent MUST execute the **Grasping Protocol**:

1. **Grasp Core Vision & Aesthetics**:
   - Explicitly identify the target aesthetic (e.g., Studio Ghibli painterly watercolor, 90s village nostalgia, ASMR audio, lo-fi piano).
   - State the target format (Shorts 9:16 vs Landscape 16:9, duration targets, target audience).
   - Clarify the publishing target and credentials (which channel profile, which Gmail account, OAuth requirements).

2. **Grasp Technical Constraints**:
   - Check local environment (Windows pwsh, Python 3.12, FFmpeg, available APIs like Gemini, Edge-TTS, Flux/SDXL, etc.).
   - Reuse existing utilities and conventions from `src/config.py`, `src/utils.py`, `src/evolution/learning_memory.py`.

3. **Active Clarification (No Guesswork)**:
   - If any core requirement is ambiguous or underspecified, the agent MUST use `ask_question` or present clear multiple-choice options to clarify BEFORE building.
   - Never substitute an assumption for a missing user preference.

4. **Grasping Summary**:
   - Present a concise 3-5 point summary of what was understood and confirm alignment.

---

## 3. The Mandatory Checkpoint Protocol (Phased Execution)

All multi-step implementations MUST be structured into discrete, verifiable **Checkpoints**:

1. **Partition into Numbered Milestones**:
   - Every plan must feature numbered checkpoints (e.g., `Checkpoint 1.1: Story Director`, `Checkpoint 1.2: Visual Generator`, `Checkpoint 1.3: Audio & ASMR`, etc.).
   - Each checkpoint must define:
     - **Goal & Target Files**
     - **Execution Action**
     - **Verification / Test Criteria** (proof of execution, e.g. dry-run command, test file, or render output).

2. **The "Stop & Verify" Gate**:
   - Execute ONE checkpoint at a time (or a tightly coupled atomic pair).
   - Run tests, dry-runs, or generate sample assets to prove correctness.
   - Report the status and tangible outcome to the user.
   - **STOP** and allow the user to review, test, or steer before moving to the next checkpoint.
   - Never execute entire weeks of work in a single turn without intermediate verification.

3. **Persistent Checkpoint Tracking**:
   - Track progress in `checkpoints.md` or a dedicated status artifact.
   - Use clear statuses: `[x] COMPLETE`, `[-] IN PROGRESS`, `[ ] PENDING`.

---

## 4. Programmatic Quality Gatekeeping ("The Mark-Avoidance System")

To prevent the pipeline from producing low-quality or off-target videos autonomously:
- Every generation pipeline must route content through a **Gatekeeper / Evaluator** before rendering or publishing.
- The gatekeeper must check:
  - **Narrative Hook & Emotional Tone**: Does it evoke the intended feeling (e.g. cozy nostalgia, curiosity)?
  - **Audio-Visual Synchrony**: Do scene durations match voice cues and ASMR sound layers?
  - **Resolution & Aspect Ratio**: 1080x1920 for Shorts, 1920x1080 for landscape.
  - **Anti-Repetition & Stealth**: Ensure variation in titles, pacing, and visual transitions.
- If a check fails, the pipeline must log the failure, self-correct, or pause rather than publishing flawed content.
