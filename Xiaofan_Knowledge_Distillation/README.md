# Xiaofan_Knowledge_Distillation — 小饭认知模型知识蒸馏

本目录是小饭数字分身项目的**知识蒸馏产出**与**Agent 框架设计文档**的集合。

## 目录结构说明

### 人格内容 (Persona Content)
这些文件定义小饭的人格本身,是**下游 Xiaofan-Digital-Clone `persona/` 模块的语料来源**。
新蒸馏的认知模型应优先补充到这些文件,再同步到下游。

| 文件 | 内容 | 对应下游模块 | 同步方向 |
|------|------|-------------|---------|
| `Prompt_System.md` | 手写版 System Prompt v2.0(含完整人设、世界观、价值观、输出风格) | `dist/Prompt_System.md`(编译版) | 手动→下游 `persona/01~05` 模块 |
| `Style_Profile.md` | 第一层:风格画像(表达风格、断句节奏、语气) | `persona/05_output_style.md` | 可合并 |
| `Thinking_Framework.md` | 第二层:认知框架(思维模式、分析框架) | `persona/05_output_style.md` §思维框架 | 可合并 |
| `Output_Patterns.md` | 第三层:输出模板库(典型回答范式) | `persona/05_output_style.md` | 可合并 |
| `Vocabulary.md` | 第四层:核心词汇库(黑话、口癖、专属词汇) | `persona/03_vocabulary.md` | 可合并 |

### Agent 框架设计 (Framework Design)
这些文件定义**蒸馏 Agent 本身的运行规则**和安全协议,是**给"蒸馏 Agent"看的,不是给小饭人设用的**。
下游消费者不应将这些文件误解为人格内容。
如果你在寻找"小饭应该以什么身份回答问题",这些文件不相关。

| 文件 | 内容 | 与下游关系 |
|------|------|-----------|
| `Boundary_Controller.md` | 蒸馏 Agent 的执行边界——何时该拒绝回答、何时该中止 | 类似下游 `constitution/immutable_rules.md` 但视角不同(Agent 运行规则 vs 人格底线) |
| `State_Machine.md` | 蒸馏 Agent 的 7 步生命周期(输入→分析→提取→验证→输出) | 下游无直接对应 |
| `Permission_Model.md` | 蒸馏 Agent 的权限矩阵——能做什么、不能做什么 | 与下游 `constitution/` 概念重叠但用途不同 |
| `Verification_Protocol.md` | 蒸馏 Agent 的防幻觉协议——如何验证提取结果的真实性 | 下游无直接对应 |

### 示例

| 路径 | 内容 |
|------|------|
| `Examples/Example_01_AI_Distillation.md` | 知识蒸馏操作示例:ASR 语音转文字→大模型 Prompt→完事 |

## 使用流程

```
音频/视频 → audio_to_text.sh → _extracted.txt
                                  ↓
                    distill_cognitive_model.py → notes/distill_output.json
                                                     ↓
                                        sync_distill_to_xiaofan.py
                                                     ↓
                              Xiaofan-Digital-Clone/persona/06_distilled_cognition.md
```

## 与下游的关系

本仓库(语料生产端)产出的是**未经编译的原材料**。
下游 Xiaofan-Digital-Clone(消费端)的 `scripts/pipeline.py` 会将这些原材料
(constitution/ + persona/ 模块)编译为最终分发的 `dist/Prompt_System.md`。

**不要直接编辑下游的 `dist/Prompt_System.md`**——它是编译产物,所有修改应在
`persona/01~05*.md` 或 `constitution/immutable_rules.md` 中完成。