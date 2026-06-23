# RFC-001: Trust Root & Sovereignty Spec

**Status:** Draft (Revision 2)
**Purpose:** 定义系统的绝对权力来源（Root of Authority），明确系统主权拓扑结构、密钥生命周期管理以及紧急状态下的柔性降级治理机制。

---

## 1. 信任根定义 (Definition of Trust Root)

- **Trust Root (信任根)** 是整个 Agent OS 中唯一不可被内部推理（Reasoning）或策略引擎（Policy Engine）覆盖的密码学授权实体。
- **权力去中心化 (Decentralized Authority)**: Trust Root 严禁绑定单一密钥。系统的最高决策权必须建立在 **M-of-N 多签阈值架构 (Threshold Signature Scheme)** 之上，消除单点灾难故障。

---

## 2. 身份与控制权映射 (Identity & Control Mapping)

- **Sovereign (系统主权者)**: 满足多签阈值的联合物理实体。Agent 内核只认多重签名，不认社会学意义上的“人类身份”。
- **Delegated Authorities (受托实体)**: Sovereign 可下发短期、降权的子证书，授予操作员临时操作权。
- **Agent 身份本质**: Agent 不具备原生主权。其行动权本质上是对 Sovereign 权限在限定 Policy 下的时间片租赁。

---

## 3. 权力冲突与裁决机制 (Conflict Resolution)

- **指令冲突**: 并发指令严格按照密码学证书链层级裁决。
- **身份验真失败**: 签名无效时触发断路器（Circuit Breaker），回退至无状态只读模式并告警。

---

## 4. 主权拓扑结构 (Authority Topology)

- **拓扑形态**: 建议采用 `3 / 5`（或自定义的 M / N）多签结构代表系统最高主权，避免 Bus Factor = 1。
- **主权继承与转移**: 任何对多签阈值或成员公钥集合的修改，必须由当前的主权委员会（满足现有多签条件）发起并签名确认。
- **权限剥夺**: 主权委员会可即时颁发证书吊销列表（CRL），使特定节点或子模块的权限瞬间归零。

---

## 5. 根密钥生命周期 (Root Key Lifecycle)

- **Key Creation (生成)**: 根密钥碎片必须在硬件安全模块（HSM）中生成。
- **Key Storage (存储)**: 系统运行时内存与环境变量中绝对禁止加载根私钥。
- **Key Rotation (轮换)**: 系统必须支持周期性密钥轮换协议（Routine Rotation）及泄露时的紧急轮换（Emergency Rotation）。
- **Key Loss & Recovery (丢失与恢复)**: 定义满足最低阈值条件下的失效碎片重构与根证书迁移算法。

---

## 6. 紧急治理机制 (Emergency Governance)

为了防止简单粗暴的 `TERMINATE_ALL` 导致次生物理灾难（如 ICU 呼吸机宕机），系统提供四级柔性降级策略：

1. **Pause (挂起)**: 暂停当前状态机的状态推进，保持内存和网络连接，等待外部审计指令。
2. **Freeze (冻结)**: 彻底剥夺系统的物理 Write/Execute 权限，系统强制降级为只读监控模式。
3. **Permission Revocation (局部吊销)**: 精准吊销受损 Agent 的子证书，隔离故障域，其他未受影响节点继续运行。
4. **Graceful Shutdown (优雅终止)**: 触发安全停机序列，保存事务点、释放物理设备互斥锁后，安全关闭 Agent 进程。
