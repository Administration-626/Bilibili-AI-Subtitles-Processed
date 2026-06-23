# RFC-003: Policy Engine Spec

**Status:** Draft
**Purpose:** 定义系统的权限与策略验证中枢。将主权者的意志（Values & Governance）转化为机器可执行的断言。Policy Engine 是一个严格的“无状态消费节点”，仅基于已确立的 Fact 进行裁决。

---

## 1. 核心边界原则 (Core Boundary Principles)

**Principle: Policy Engine Never Trusts Claims. Policy Engine Consumes Facts Only.**
- **职责严格隔离**: Policy Engine 绝对不负责“判断物理世界实际发生了什么”——那是 Evidence Engine（RFC-002）的专属职责。
- **禁止推导新事实 (MUST NOT derive new facts)**: Policy Engine 没有任何物理嗅探能力。它的唯一输入是已经经过 RFC-002 `Fact Derivation Rule` 计算完毕、带有独立签名的 **Fact** 对象。如果试图将未经验证的 `Claim` 送入引擎，将在预检阶段直接引发内核拒绝（Kernel Reject）。
- **纯函数特性**: Policy Engine 的运行机制类似于一个纯函数：`Decision = Evaluate(Trust Root Context, Fact, Target Action)`。它不主动改变任何环境状态。

---

## 2. 标准输入/输出定义 (I/O Specification)

### 2.1 强制输入要求 (Mandatory Inputs)
引擎的每次裁决必须齐备以下三个参数，缺失任意一项直接宕机：
1. **`Trust Root Context`**: 试图发起该动作的主权者/受托人身份证明（依赖 RFC-001 签发的 Delegation Token）。
2. **`Fact Payload`**: 描述当前环境客观状态的实体数据包（依赖 RFC-002 产出）。
3. **`Target Action`**: 意图执行的下游动作（如：DELETE /etc/config，或 INVOKE 某高危 API）。

### 2.2 绝对输出域 (Strict Output Domain)
引擎的最终裁决结果必须且只能是以下三个枚举值之一：
- **`ALLOW`**: 权限链合法，事实满足前置条件，且未触碰任何安全红线。放行至 Execution Plane。
- **`DENY`**: 权限不足、事实被证伪、或目标动作违反隔离策略（如越权访问）。直接阻断当前工作流，并将上下文作为“越权记录”写入 Audit Log。
- **`ESCALATE`**: 遇到策略文件未覆盖的“灰色地带（Edge Case）”，或当前 Fact 的置信等级（Trust Level）达不到该高危动作的底线要求。此时挂起状态机（进入 RFC-001 定义的 Pause 状态），向多签委员会（Sovereign）抛出人为介入提权请求。

---

## 3. 策略评估链路 (Evaluation Pipeline)

在给出 `ALLOW` 之前，请求必须穿透以下三道闸门（任何阶段拦截即终止）：

1. **Authority Gate (权力闸门)**
   - 验证：发起请求的 Token 签名是否合法？该身份是否已在撤销列表（CRL）中？
   - 依赖基础：`RFC-001`
2. **Fact Gate (事实闸门)**
   - 验证：支撑该请求的前提是否为已确证的 `Fact`？其附带的 `Trust Level` 是否大于等于当前 `Target Action` 的风险要求（例如：转账操作强制要求 Trust Level >= 4，仅有 Level 3 则直接退回）？
   - 依赖基础：`RFC-002`
3. **Constraint Gate (红线闸门)**
   - 验证：该操作是否试图修改系统的核心控制层（试图回写审计日志、修改宪法）？是否突破了预先定义的业务隔离沙盒？
   - 依赖基础：`RFC-000`
