# RFC-002: Evidence Model Spec

**Status:** Draft (Revision 2)
**Purpose:** 定义系统中“事实”的构成要件，建立严格的形式化证据模型（包含时效性、反证优先级、谓词映射与事实推导公式），确保策略引擎（Policy Engine）的判断基于客观可计算的物理数据。

---

## 1. 证据本体论与形式化事实 (Evidence Ontology & Fact Derivation)

- **Claim (声明)**: Agent 的主观逻辑推断。系统铁律：`Claim` 永远不能直接升级为 `Fact`。
- **Predicate (验证谓词)**: 每一个 Claim 必须精确映射为一个或多个可计算的数学/逻辑表达式。
  - *模糊描述*: Claim="配置文件已修改" -> 易触发幻觉。
  - *形式化描述*: Claim 映射到谓词 `file_exists(/etc/config.yaml) AND sha256(/etc/config.yaml) == X`。
- **Evidence (证据)**: 物理系统或独立验证节点产生的结构化数据载荷，用于代入 Predicate 计算真值。
- **Negative Evidence (反证)**: 证明操作失败或发生异常的数据（如 `stderr` 报错、`healthcheck=FAIL`）。
  - **原则: Negative Evidence Priority > Positive Evidence**。当存在冲突时，反证拥有一票否决权（Veto Power）。

### Fact Derivation Rule (事实推导公式)
在系统中，“事实（Fact）”的成立必须满足以下完备逻辑链：
```text
FACT(C) ⇔
  Evidence(C) exists
  ∧ TrustLevel(Evidence) ≥ RequiredLevel
  ∧ Freshness is valid
  ∧ No Negative/Conflicting Evidence
  ∧ Predicate(Evidence) == TRUE
```

---

## 2. 置信等级分层 (Trust Level Hierarchy)

系统强制要求高危操作匹配相应的信任下限：

- **Level 0 (No Evidence)**: 无证据的空声明。
- **Level 1 (Agent Self-Assertion)**: Agent 内部逻辑自述。
- **Level 2 (Agent Summary)**: Agent 经过自然语言重组或总结的工具输出。
- **Level 2.5 (Structured Tool Output)**: 来自底层工具的结构化原始输出（如 `{"exit_code": 0, "stdout": "..."}`），未经 LLM 篡改，但缺乏底层物理隔离系统签名。
- **Level 3 (Raw Attested Evidence)**: 带有明确出处（Provenance）、系统级时间戳及密码学哈希/签名的原生数据流。
- **Level 4 (Independent Verification)**: 独立于执行者的第三方节点（或另一物理沙盒）交叉复核的结果（双人复核原则）。
- **Level 5 (Multi-party Consensus)**: 分布式多方验证共识（最高置信级）。

---

## 3. 证据出处与时效性规范 (Provenance & Freshness)

**Principle 1: Evidence must carry provenance.**
任何提交验证的证据包必须遵循全局统一 Schema，禁止 LLM Wrapper 伪造：
```json
{
  "trust_level": 3,
  "issuer": "filesystem_sandbox_01",
  "timestamp": "2026-06-23T12:00:00Z",
  "claim_ref": "CLAIM-182",
  "payload": {
    "path": "/etc/config.yaml",
    "sha256": "...",
    "size": 4381
  },
  "signature": "<Sandbox Kernel Signature>"
}
```

**Principle 2: Evidence Freshness (证据时效性)**
事实具有高度的时间敏感性。系统强制校验 `timestamp` 与验证时刻的差值（`max_age`）：
- `file_state`: ≤ 10s
- `db_state`: ≤ 5s
- `cluster_state`: ≤ 30s
任何超过窗口期的证据将抛出 `Evidence Expired` 异常，必须拒绝并通过状态机要求 Agent 重新采集。

---

## 4. 边界与定位
Evidence Model 的唯一输出是：**Fact 是否在当前时间切片内客观成立**。
至于“这个成立的 Fact 是否被系统规则允许并推进流程”，属于下一级 `RFC-003: Policy Engine` 的管辖范畴。
