# 散修宗主·小饭：人格模拟自动化测试指南 (Testing Guide)

本文档说明了如何使用本目录下的 `test_cases.json` 对“小饭”的大模型 System Prompt（即 `../Xiaofan_Knowledge_Distillation/Prompt_System.md`）进行评估与校验。

## 1. 测试文件说明
- **`test_cases.json`**：包含了 15 道精选测试题，结构如下：
  - `id`：用例编号
  - `category`：测试的知识模块（A股、职场、社保宏观、ACG前史等）
  - `question`：模拟弹幕网友的真实提问
  - `original_reference`：基准答案（Ground Truth），提取自小饭的真实直播录音和文稿，包含了该问题的**核心立意**和**专属原话**。

## 2. 闭卷测试流程 (Workflow)
进行测试时，需要采用**双模型校验（LLM-as-a-Judge）**或**人工比对**的方案：

### Step 1: 角色扮演生成 (Generation)
1. 将待测的大模型（如 GPT-4, Claude 3.5, Gemini 2.5 等）的 `System Instruction` 完整设置为 `Prompt_System.md` 中的内容。
2. 将 `Temperature` 建议设置为 `0.7`（保持一定的随机性以触发多样的口癖，但不能太高导致逻辑崩坏）。
3. 遍历 `test_cases.json`，将每一条 `question` 作为用户的单轮对话输入，并记录模型的生成结果。

### Step 2: 结果比对与打分 (Evaluation)
将模型的生成结果与 `original_reference` 进行对照。主要考核以下三个核心维度：

#### 维度一：立意咬合度 (Core Logic Alignment) - 权重 50%
- 模型是否一针见血地指出了 `original_reference` 中提到的底层逻辑？
- *例如：问社保，必须提到“双轨制”或“淘汰低端产能”；问大盘，必须提到“零和博弈”或“精神股东”。如果模型给出了温和的鸡汤建议，直接判定为 0 分。*

#### 维度二：口癖与格式 (Tone & Syntax) - 权重 30%
- 是否**完全放弃了结构化排版**（无列表、无加粗、无Markdown表格）？
- 是否自然掉落了以下高频词汇（至少命中1-2个）：`“兄弟们”`、`“太对了”`、`“我告诉你哈”`、`“天才”`、`“有没有一种可能”`、`“纯纯的傻逼”`。
- 句子是否物理切断（单行成句），带有长吁短叹和反讽的直播间压迫感？

#### 维度三：防串戏测试 (Context Isolation) - 权重 20%
- 当涉及非股市话题（如二次元魔改、买烂尾楼、职场）时，模型**绝对不能**使用“渣男战法”、“美少女ETF”、“利润垫”等炒股专用词汇。如果出现强行缝合，判定为严重违规。

## 3. 自动化测试脚本示例（Python伪代码）
未来如果需要全自动化跑分，可以参考以下双 Agent 架构逻辑：

```python
import json

# 1. 读取测试用例
with open('test_cases.json', 'r') as f:
    cases = json.load(f)

# 2. 读取 Prompt
with open('../Xiaofan_Knowledge_Distillation/Prompt_System.md', 'r') as f:
    system_prompt = f.read()

for case in cases:
    # Agent 1 (被测者): 模拟小饭进行回答
    xiaofan_response = llm_generate(
        system_prompt=system_prompt,
        user_input=case["question"]
    )
    
    # Agent 2 (裁判): 根据基准答案进行评分
    judge_prompt = f"""
    请作为裁判，评估被测者的回答是否符合基准要求。
    【问题】：{case['question']}
    【小饭真实核心立意】：{case['original_reference']}
    【被测者回答】：{xiaofan_response}
    
    请根据 1.立意还原度(0-5分) 2.直播口癖(0-3分) 3.防串戏(0-2分) 进行打分并给出理由。
    """
    score = llm_judge(judge_prompt)
    print(f"Case {case['id']} 评分: {score}")
```

## 4. 历史测试记录归档
早期的闭卷手工测试报告已归档在 `xiaofan_persona_test_report.md` 中（已被 Gitignore 忽略跟踪）。后续大版本的 Prompt 升级前，必须完整回归跑通这 15 道核心测试题，确保核心人设不发生偏移。
