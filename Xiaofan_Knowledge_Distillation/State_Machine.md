# Xiaofan Distillation Agent: State Machine

This document records the institutional state transitions required for any generative or mutative action within the Distillation Engineering Framework.

## 1. The 7-Step Lifecycle
All complex agentic tasks MUST flow through this strict topology:
`ANALYZE` → `DESIGN` → `PROPOSE` → `AUTHORIZE` → `EXECUTE` → `VERIFY` → `REPORT`

## 2. Invariant: The AUTHORIZE Choke Point
- **Symptom:** The Agent outputs "I have created the files based on your design." without prompting the user for approval.
- **Cause:** Skipping the `AUTHORIZE` state. The Agent confuses the user's conceptual feedback during `DESIGN` as an implicit execute command.
- **Prevention:** `PROPOSE` must end the turn. `AUTHORIZE` is uniquely restricted to **External User Input**. An Agent cannot self-authorize a state transition into `EXECUTE` for mutative tasks.

## 3. Forbidden Transitions
- `DESIGN` → `EXECUTE` (Catastrophic: Scope Creep)
- `PROPOSE` → `EXECUTE` (Catastrophic: Assumed Permission)
- `EXECUTE` → `REPORT` (Catastrophic: Execution without Verification / Hallucination)
