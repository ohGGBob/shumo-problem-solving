# 紧急模式（Emergency Mode）操作手册

> 场景：时间极紧（如只剩数小时）、团队某环节卡死、或用户明确要求"全自动/直接完成"时，进入紧急模式——**由 skill 自主拍板走完全流程，但每个决策留痕、每个阶段有产物、交稿前强制收口**。

## 一、与「强制确认门禁」的关系（重要）

- **默认模式**：强制确认门禁照常——模型/数据处理/论文三类决策先给 2–3 方案等用户拍板（这是质量护城河，不废除）。
- **紧急模式**：是门禁的**显式例外**，仅在**用户明确触发**时生效。触发后，skill 把"逐项等拍板"切换为"自主决策 + 记录理由"：每次选择自动写入 `decision_log`（谁/选了啥/为什么/取舍/风险），事后可完整追溯。
- **触发口令**（任一即可）："紧急模式" / "全自动" / "直接完成" / "时间不够了帮我走完" / 显式指定 `emergency_run.py`。
- **门禁底线不破**：即便紧急，也绝不编造文献、绝不放过野数字、绝不跳步骤产（`emergency_run.py` 的 checkpoint 护城河强制）。

## 二、流程（7 阶段，每阶段有必产物才能推进）

| # | 阶段 | 必产物 | 参考 |
|---|---|---|---|
| 1 | 读题拆解 | `report/problem_restatement.md` | topic-selection / cumcm-years |
| 2 | 选型定位 | `log/decisions.md`（选型决策+理由） | model-recipes / innovation-playbook |
| 3 | 模型假设 | `report/assumptions.md` | assumptions-justification / logic-rigor |
| 4 | 建模求解 | `out/results.json`（关键结果落盘） | code-templates |
| 5 | 模型检验 | `report/validation.md`（过 sanity_check） | validation-checklist |
| 6 | 论文成文 | `report/main.md`（摘要四要素+三件套） | paper-skeleton / bao-paper-writing |
| 7 | 交稿收口 | `report/ai_declaration.txt` + 支撑材料清单 | prize_gate / gen_ai_report |

## 三、一条命令管到底

```bash
# 初始化：骨架 + 看板（题干放入 data/）
python scripts/emergency_run.py <项目目录> init --source 题干.txt --deadline "2026-09-13 20:00"

# 随时看进度 / 推进阶段
python scripts/emergency_run.py <项目目录> status
python scripts/emergency_run.py <项目目录> advance --phase 建模求解 --note "..."

# 红警检查：时间 vs 进度，给"砍什么保什么"
python scripts/emergency_run.py <项目目录> guard

# 一键收口：全链路校验 + AI 使用报告 + 提交清单
python scripts/emergency_run.py <项目目录> finish --source 题干.txt
```

## 四、红警规则（时间 vs 进度）

| 情形 | 动作 |
|---|---|
| 剩余 <6h 且论文未成文 | 砍次要问题到一页；先保：摘要四要素 + 三件套 + 核心结论数字 + 真文献 |
| 剩余 <24h 且主问未求解 | 放弃炫技算法，改用已验证模板；先跑通主问拿结果落盘 |
| 剩余 <24h 求解已过、论文未成文 | 写作冲刺：按 paper-skeleton 逐节填，每节配数字 |
| 已过截止 | 按最小可交付原则提交已有内容 |

## 五、交付契约（紧急模式也必须做到）

1. **每个数字能回溯到代码**（`results.json` 单一来源，铁律二）。
2. **AI 使用如实披露**（`gen_ai_report.py`，2026 合规，见 `ai-usage-report.md`）。
3. **交稿前过 `prize_gate.py`**——紧急不等于带病提交。
4. 结束时交付：完整论文包 + 决策日志（`log/decisions.md`）+ AI 使用详情 + **待人工复核点清单**（哪些是紧急模式下快速决策、赛后要回看验证）。

## 六、边界

紧急模式压缩的是"等待与沟通"，不压缩"质量收口"。它产出的是一篇**结构完整、数值可回溯、合规披露**的论文；"创新亮点"的打磨（支柱二）在时间允许时应回补——这也是 `emergency_run finish` 后建议回看决策日志、把快速决策逐条验证的原因。
