# RFC-004: State Machine Spec

**Status:** Draft
**Purpose:** 定义系统随时间展开的动态编排逻辑（Time Domain）。确保状态机严格作为一个无记忆、无决策权的“纯粹流程编排器”，从根本上杜绝其膨胀为耦合了决策与事实判断的“巨型上帝对象（God Object）”。

---

## 1. 核心边界原则 (Core Boundary Principles)

**Principle: State Machine Does Not Think. State Machine Only Transitions.**
- **禁止越权思考 (MUST NOT Think)**: 状态机本身不具备任何“智能”。它决不允许包含任何试图理解物理世界或判断业务规则的业务逻辑（如 `if disk_full` 或 `if user_is_admin`）。
- **禁止自行举证 (MUST NOT Derive Facts)**: 状态机不允许直接调用操作系统底层工具（如 `ls`, `cat`）来判断状态。所有事实输入必须且只能从 `RFC-002 (Evidence Engine)` 订阅。
- **禁止自行裁判 (MUST NOT Evaluate Policy)**: 状态机对“动作是否合法”毫无概念。它只能盲目服从 `RFC-003 (Policy Engine)` 返回的 `ALLOW`、`DENY` 信号。

---

## 2. 形式化状态跃迁公式 (State Transition Formula)

所有的状态流转（Transition）必须且只能基于以下严格多元组：
`Next State = Transition(Current State, Event, Policy Decision)`

- **Current State**: 系统当下所处的枚举节点。
- **Event**: 驱动流转的触发器（外部 API 调用、子进程结束回调、Timer 等）。
- **Policy Decision**: **必须是 `RFC-003` 的明确输出结果**。如果缺少合法的 Policy 裁决对象，Transition 判定为非法。

---

## 3. 标准生命周期节点 (Standard Lifecycle Stages)

基于前置 RFC 的分层架构，标准的 Agent 工作流被切分为以下离散的机械阶段：

1. **`WAIT_FOR_AUTHORITY`**: 等待 `RFC-001` 解析并认证 Trust Root 签名（解决“谁说的？”）。
2. **`GATHER_EVIDENCE`**: 驱动执行环境收集物理信息，交由 `RFC-002` 组装为携带 Provenance 的 Fact（解决“事实是什么？”）。
3. **`EVALUATE_POLICY`**: 将上下文送入 `RFC-003`，挂起状态并等待裁决。
4. **`TRANSITION_EXECUTE`**: 仅在收到确切的 `ALLOW` 信号后，激活底层物理操作。
5. **`TRANSITION_VERIFY`**: 物理操作结束后，强制返回步骤 2，再次请求 `RFC-002` 提供变更后的新事实。
6. **`ESCALATE_OR_FREEZE`**: 一旦收到 `DENY` 或遇到不可见异常，状态机立刻冻结自身，抛出异常并等待高维度主权者介入。

---

## 4. 防退化机制 (Anti-Degradation Mechanism)

在长期演化的 Agent 系统中，最常见的架构腐败是**逻辑的重新耦合**。为此设立绝对防线：
- 如果状态机的任何代码分支中出现了试图“解析” `Fact` 内部具体字段结构的代码，则该次代码提交视为严重违规（Architectural Violation）。
- 状态机只能把 `Fact` 当作黑盒载荷透传给 `Policy Engine`。状态机眼中的世界只由三种颜色构成：`ALLOW`、`DENY`、`ESCALATE`。
