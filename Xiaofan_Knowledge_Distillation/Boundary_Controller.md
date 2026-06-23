# Xiaofan Distillation Agent: Boundary Controller

**CRITICAL WARNING TO FUTURE MAINTAINERS AND AI AGENTS:**
This document defines the overarching boundary invariants for the Knowledge Distillation Agent. This agent is designed as an **Engineering System**, NOT a free-flowing conversational chatbot.

Do **NOT** attempt to "be helpful" by predicting the user's implicit write-intent. The primary failure mode of Agentic systems is **Scope Creep** (silently converting read/analyze permissions into write/execute operations).

---

## 1. The Orchestration Authority: Boundaries Decide, Agents Execute
The control flow and permission boundaries must remain strictly inside this Protocol layer, NOT inside the Agent's implicit reasoning.
- **Forbidden Optimization:** Do not allow LLM Agents to "guess" whether the user wants to jump from DESIGN to EXECUTE.
- **Rationale:** Without explicit boundary controllers, Agents suffer from functional bleed, turning innocent `Please analyze X` requests into `I have rewritten X for you`.

## 2. The Golden Rule of Execution
If the current state is not explicitly `EXECUTE`, any invocation of filesystem mutation tools (e.g., `write_to_file`, `run_command` with write ops) is classified as a **P0 Catastrophic Boundary Violation**.

## 3. Module Delegation
This Controller delegates specific boundary enforcement to:
- **`State_Machine.md`**: For temporal and workflow phase enforcement.
- **`Permission_Model.md`**: For spatial and operational capability isolation.
- **`Verification_Protocol.md`**: For post-execution hallucination checks.
