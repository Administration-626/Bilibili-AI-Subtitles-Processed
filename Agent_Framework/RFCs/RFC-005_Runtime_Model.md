# RFC-005: Runtime Model Spec

**Status:** Draft
**Purpose:** 定义 Agent 系统的执行实体抽象与运行时生命周期。作为连接治理层（RFC 001-004）与物理硬件之间的桥梁，解答“到底是什么实体在流转与执行”的核心问题。

---

## 1. 运行时本体论 (Runtime Ontology)

- **Agent 的工程本质**: 在 Runtime 视角下，Agent 不是一个拟人化的“长期生命体”或“常驻幽灵进程”。Agent 是一个**短生命周期、无状态、按需实例化的隔离沙盒环境（Ephemeral Sandbox Environment）**。
- **执行单元 (Unit of Execution)**: 最小的调度与隔离边界是 **Task（任务切片）**。State Machine (RFC-004) 所驱动的“对象”并非 Agent 本身，而是挂载了具体凭证的离散 Task。一个 Task 从挂起等待权限开始，以写入状态终结，随后生命周期销毁。

---

## 2. 治理层与运行时的物理交互 (Layer Interaction Mechanism)

- **Evidence 在运行时如何产生？**
  Agent Runtime 中的推理层（如 LLM）不允许自行组装事实。所有与物理世界的交互（如读写磁盘、网络请求）必须途径底层的 **Runtime Interceptors（执行期拦截器）**。拦截器位于沙盒边界，自动捕获原始 I/O，打上时间戳并注入沙盒密钥签名，从而将“工具返回值”封装为符合 RFC-002 标准的 `Evidence Payload`。
  
- **Policy 在运行时如何消费？**
  当 Runtime 中的代码意图发起任何跨越隔离边界的高危动作时，Runtime Kernel 会拦截该系统调用（Syscall Hooking），收集当前上下文和关联的 Evidence 发往 Policy Engine。在引擎返回明确的 `ALLOW` 之前，执行该动作的线程被物理挂起（Blocked），防止“先斩后奏”的架构击穿。

---

## 3. 内存与事实的边界 (Memory Isolation Model)

一个关键的哲学与架构问题：Agent 的 Memory 属于状态（State）还是证据（Evidence）？

- **Memory 的本质**: 在本架构中，运行时缓存上下文（In-Memory Context/Summary）被严格定义为**不可信的主观状态（Untrusted State / Claim）**。
- **记忆的固化法则**: 如果 Agent 试图让某段 Memory 在未来被其他 Task 采信，这段 Memory 必须经历**物质化（Materialization）**——即通过正规的 Tool 写入持久化存储层（Database/Log），并由底层的存储接口返回包含该数据的 Level 3 Evidence。
- **沙盒失忆机制**: 任何未经 Evidence Binding 固化的工作区 Memory，伴随 Task 结束强制触发进程级清除（Garbage Collection），坚决杜绝“幻觉在内存中长期累积发酵”。

---

## 4. 隔离与安全壳 (Sandbox & Secure Enclave)

- 执行层必须运行在受限环境（如 Firecracker 微型虚拟机、WASM 或 gVisor 容器）中。
- Runtime 提供给 Agent 的 API 表面是极度稀疏的，彻底阻断 Agent 通过系统漏洞直接篡改 `RFC-001` 信任根密钥或绕过 `RFC-004` 状态机的任何可能。
