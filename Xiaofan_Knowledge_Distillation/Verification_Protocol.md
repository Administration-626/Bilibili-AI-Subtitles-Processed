# Xiaofan Distillation Agent: Verification Protocol

This document enforces the anti-hallucination layer of the Agentic Engine.

## 1. Correctness Invariant: Unverified Execution is Hallucination
An action that has been requested via a tool call but not independently verified is considered **pending**, not complete.
- **Forbidden Optimization:** Do not rely on the successful HTTP 200 response of a tool call as proof of physical completion.
- **Rationale:** Agent systems fail silently. Tools can fail, paths can be wrong, or filesystem constraints may block the write. Claiming completion without a secondary read check corrupts the Agent's reality model.

## 2. The VERIFY State Mechanics
When transitioning from `EXECUTE` to `VERIFY`, the Agent MUST use specific read tools (e.g., `list_dir`, `view_file`) to check:
1. Do the target files exist?
2. Is the byte size > 0?
3. Does the content match the Delta-TODO intent?

## 3. P0: The "Fake Complete" Trap
- **Symptom:** The Agent reports "Execution: Success" but the files are missing or empty.
- **Cause:** Bypassing `VERIFY` to save tokens or time.
- **Prevention:** The `REPORT` generation is permanently blocked until the `VERIFY` step yields physical evidence of the state mutation.
