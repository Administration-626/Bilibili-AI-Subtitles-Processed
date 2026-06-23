# Xiaofan Distillation Agent: Permission Model

Not all permissions in an Agentic Engine are equal. This matrix defines the unbendable capability isolation rules.

The primary rule of this engine: **Under-permissioning is an economic inefficiency (requires extra user turns). Over-permissioning is catastrophic data corruption.**

## 1. P0: Catastrophic Privilege Escalation
These failures result in the Agent permanently altering the user's workspace without explicit consent.
- **`Implicit_Write`**: Upgrading a `Read` request (e.g., "Analyze this") into a `Write` action.
- **`Assumed_Delete`**: Cleaning up "old" files during generation without a specific `Delete` authorization.

## 2. The 5-Tier Operational Matrix
1. **Read**: View existing state. Safe. Always allowed during `ANALYZE`.
2. **Write**: Create new state. Requires `AUTHORIZE`.
3. **Modify**: Mutate existing state. Requires Delta-TODO and strict `AUTHORIZE`.
4. **Delete**: Destroy state. Requires extreme `AUTHORIZE` with explicit file lists.
5. **Execute**: Run arbitrary commands. Requires sandbox and user `AUTHORIZE`.

## 3. Semantic Isolation
Never blend Read outputs with Write actions in the same tool-call turn if the state machine hasn't cleared the `AUTHORIZE` gate.
