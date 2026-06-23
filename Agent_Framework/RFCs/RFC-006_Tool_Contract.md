# RFC-006: Tool Contract Spec

**Status:** Draft
**Purpose:** 定义 Agent 内部信任域（Internal Trust Domain）与外部不可信世界（External Trust Domain）的唯一交互界面。确保所有跨边界动作受到严格的权限验证、副作用隔离与证据自动化捕获。

---

## 1. 跨域隔离与工具本体论 (Cross-Domain Isolation & Tool Ontology)

- **边界设定**: `RFC-001` ~ `RFC-005` 构成了受控的内部信任域；而文件系统、数据库、外部 API 乃至人类，全部属于外部不可信域。
- **Tool 的本质**: Tool 不是 Agent 功能的延伸，而是**连接两个信任域的双向受控代理协议 (Bidirectional Proxy Protocol)**。
- 任何越过 Tool Contract、试图从 Runtime 内部直接发起原生 System Call 的尝试，均视为严重架构违规（Architectural Violation）。

---

## 2. 工具调用的四段式防御流水线 (4-Stage Defense Pipeline)

当 Agent 发起一次 Tool 调用时，执行流必须强行穿透以下防线：

### 2.1 Intent Verification (意图验证)
- Agent 输出的 Tool 参数本质上是一个 `Claim`（"我想修改文件"）。
- 该 Claim 被拦截并送入 `RFC-003: Policy Engine` 进行严格过滤（防止 Shell 注入、路径穿越等越权行为）。

### 2.2 Side-Effect Sandboxing (副作用沙盒化)
- 获得 `ALLOW` 的 Tool 必须在独立的细粒度沙盒（如限制特定路径挂载、切断公网权限的容器）内被唤起执行。
- Tool 永远只被赋予完成该动作所需的**最小特权（Least Privilege）**。

### 2.3 Observation Boundary (观察边界与证据捕获)
在 Tool 结束时，必须划定绝对的观察边界以生成 `RFC-002 Evidence`：
- **Level 2.5 基础事实**: `Exit Code` 决定状态走向；`stdout`/`stderr` 原生输出（未经 LLM 转述）。
- **Level 3 强校验事实**: 系统层面对目标文件 `stat` 变更的捕获，网络层对发包报文的审计。
- **拦截器原则**: Agent 无权自行总结 Tool 的执行结果。Runtime Interceptor 必须对上述 I/O 数据结构化打包，盖上内核签名后，才回传给 Agent 和状态机。

### 2.4 Transition (状态反馈)
被捕获并校验的 `Fact` 直接驱动 `RFC-004 State Machine` 的下一步流转。

---

## 3. 副作用分类与红线 (Side-Effect Classification)

系统必须对所有 Tool 进行强制分级管控：
1. **Read-Only (只读型)**: 如 `view_file`, `grep_search`。默认不影响外部物理事实，风险最低。
2. **State-Mutating (状态变更型)**: 如 `write_to_file`, `POST API`。执行前必须评估 `Policy`，推荐绑定回滚策略（Compensating Transaction）。
3. **Unrestricted (无限制高危型)**: 如 `run_command` (Shell 执行)。必须依赖 `RFC-001` 的高级授权，强审计追踪，发生异常时极易触发系统级 `FREEZE`。

---

## 4. 人机交互的统一抽象 (Human-in-the-Loop Contract)

- 在该框架下，**人类被视为一种极其特殊的外部不可信实体 (External Entity)**。
- 向人类提问（Ask User）被严格定义为一次特殊的 Tool Call。
- Agent 发送的问题是参数，人类回复的文本是返回值。将人机交互强制纳入 Tool Contract 体系，意味着用户的每次授权与答复，同样会被封装为带时间戳的 Evidence，进入全局安全审计。
