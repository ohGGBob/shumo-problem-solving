# 美赛英文写作强化（Summary Sheet / Policy Letter / 术语表 / 节奏）

> 定位：把「中文写对了」升级成「英文写得像 O 奖」。美赛评委会用英文快速扫 Summary Sheet、正文与图表，**语言本身的清晰度直接决定评委愿不愿意给你 O**。本文件给句式库、模板、术语表与 4 天写作节奏。配套 `mcm-icm-guide.md`（规则）、`bao-paper-writing.md`（写作动作）、`cases-2026-mcm.md`（六题）一起用。

## 一、Summary Sheet 英文句式库（单页定生死）

美赛 Summary Sheet **独立一页、可脱离正文读懂结论**。结构 = 总段 + 每题 bullet + 收尾。

### 1. 开头总段（4 个可用骨架，选一个）

> **S1·问题-思路型**：`We develop a <MODEL_NAME> to address the <PROBLEM>. We model <subject> as <abstraction>, then <key action>, yielding <headline result>.`
> 例：`We develop a continuous-time SOC dynamics model to predict smartphone battery time-to-empty. We treat discharge as a set of additive power components, then calibrate against public battery datasets, yielding median time-to-empty within 8% of measurement.`

> **S2·数据-规模型**（有数据时）：`Using <N> records of <DATA>, we identify <KEY PATTERN>, construct <MODEL>, and report <RESULT> with <CONFIDENCE>.`
> 例：`Using 34 seasons of contest votes, we identify a non-linear talent-vote mapping, build a latent-factor model, and rank dancers with a 95% credible interval of ±1.1 ranks.`

> **S3·决策型**（面向决策者，F/D 类题）：`To <GOAL>, we propose <MODEL> that trades off <A> and <B>. We recommend <ACTION>, projected to <OUTCOME>.`
> 例：`To manage a team under a salary cap, we propose an MDP that trades off win-now and rebuild phases, and recommend a three-year plan projected to +4 wins at constant cost.`

> **S4·机理型**（A/E/B 类物理题）：`We derive <EQUATION TYPE> from <FIRST PRINCIPLE>, parameterize with <DATA>, and predict <OUTPUT>.`
> 例：`We derive an energy-balance ODE from power conservation, parameterize it against NASA battery data, and predict time-to-empty under mixed usage with quantified uncertainty.`

### 2. 中间 bullet 句式（每题 1–2 句，务必带数字）

> **给出模型 + 关键结果**：`We build <MODEL>, achieving <METRIC> of <VALUE> (e.g., MAPE 6.2%).`
> **给出区间 / 置信**：`Our estimate is <VALUE> with a <X>% confidence interval of [a, b].`
> **给出灵敏度结论**：`Under ±10% perturbation of <PARAM>, the conclusion remains stable (<CHANGE>).`
> **诚实写负结果**：`Data augmentation fails to improve <METRIC>, so we <FALLBACK>.`

bullet 节奏：一个 bullet = 一个 sub-problem 的「方法 → 结果 → 验证」，别把整问塞进一句长难句。

### 3. 收尾（sensitivity / strengths / limitations 各一句）

> `Sensitivity analysis shows <PARAM> is most influential; conclusions are robust to <X>% perturbation.`
> `Our strengths are <CONCRETE> (e.g., physically grounded, reproducible).`
> `A limitation is <SPECIFIC> (e.g., we ignore <FACTOR>; extrapolation beyond <RANGE> is uncertain).`

### 4. 完整成稿示例（把骨架填成一段可抄的成品）

> **A 题（电池）Summary 大意**：
> `We develop a two-state ODE battery model to predict smartphone time-to-empty. We treat app usage as time-varying power draw, calibrate against NASA battery data (fit R²=0.97), and predict time-to-empty within a median error of 8% over 200 scenarios. A ±10% perturbation of screen brightness shifts estimates by <5 minutes, confirming robustness. We recommend OS-level background-task throttling, projected to extend battery life by 18%.`
> （要点：一句方法 + 一句模型/数据 + 一个量化结果 + 一句灵敏度 + 一句落地建议——**每句都带数字**。）

## 二、Policy Letter（给决策者的信，F/D 类题高频收尾）

面向非技术决策者（政府 / 管理层 / 利益相关方）。措辞去技术化，每条建议 = **对象 + 做什么 + 预期效果 + 证据/文献**。

- 结构：`Dear <Stakeholder>,` → 一句话背景 → 3–5 条建议（每条加粗一个动词短语开头）→ 一句落点。
- 句式：`We recommend <ACTION> for <GROUP>, which we project to <OUTCOME> (<EVIDENCE>).`
- 例：`We recommend funding a solar-shading retrofit for the low-latitude school first, which we project to cut summer cooling load by 31% (Section 4.2).`
- 别写成技术报告：不堆公式，用「把数学结果翻译成行动」。

### 补充：Memo / Letter-to-Agency（ICM D/B 类题要求给 owner/agency 时）

Memo 是**独立文体**、有固定抬头，别和 Policy Letter 混用。结构：

```text
MEMORANDUM
TO:      <Owner / League Commissioner / MCM Agency>
FROM:    <Team #2410xxx>
DATE:    <Feb 3, 20xx>
SUBJECT: <一句话点题：给谁解决什么>

1. PURPOSE（1 段）：本 memo 回答什么决策问题。
2. FINDINGS（3–5 条 bullet）：每条 = 量化结论 + 出处（见正文 §X）。
3. RECOMMENDATION（1–2 段）：明确建议 + 预期收益 + 关键假设/风险。
```

- 语气比 Policy Letter 更**公文化、更强调决策时效**；每条结论都要能被正文一个表/图编号回溯。

## 三、建模方法英汉术语表（写正文 / 图表不卡壳）

| 中文 | English（论文用） | 中文 | English |
|---|---|---|---|
| 常微分方程 | ordinary differential equation (ODE) | 求解器 | solver |
| 偏微分方程 | partial differential equation (PDE) | 收敛 | convergence |
| 灵敏度分析 | sensitivity analysis | 稳健 | robust |
| 全局敏感性 | global sensitivity analysis | 参数辨识 | parameter calibration / identification |
| 置信区间 | confidence interval | 可信区间（贝叶斯） | credible interval |
| 蒙特卡洛 | Monte Carlo | 期望 | expectation / expected value |
| 随机变量 | random variable | 概率分布 | probability distribution |
| 均值-方差 | mean–variance | 条件风险价值 | Conditional Value-at-Risk (CVaR) |
| 整数规划 | integer programming (IP) | 混合整数规划 | mixed-integer programming (MILP) |
| 动态规划 | dynamic programming (DP) | 马尔可夫决策过程 | Markov decision process (MDP) |
| 因果推断 | causal inference | 双重差分 | difference-in-differences (DiD) |
| 潜在变量 | latent variable | 反向问题 / 逆问题 | inverse problem |
| 排队论 | queueing theory | 图论 | graph theory |
| 综合评价 | comprehensive evaluation | 层次分析 | analytic hierarchy process (AHP) |
| 熵权法 | entropy weighting | 逼近理想解排序 | TOPSIS |
| 灰色预测 | grey prediction (GM(1,1)) | 时间序列 | time series |
| 假设 | assumption | 约束 | constraint |
| 目标函数 | objective function | 决策变量 | decision variable |
| 拟合 | fit | 残差 | residual |
| 过拟合 | overfitting | 交叉验证 | cross-validation |
| 太阳能几何 | solar geometry | 遮阳 | solar shading |
| 电池荷电状态 | state of charge (SOC) | 容量 | capacity |

> 用法：正文首次出现缩写给全称：`ordinary differential equation (ODE)`，之后只用 `ODE`。图表标题、坐标轴、表头统一用英文术语，别中英混用。

## 四、中式英语 / 高频语言错误（写完自查）

| ❌ 中式英语 | ✅ 更地道的写法 | 说明 |
|---|---|---|
| `make the model be more accurate` | `improve the model's accuracy` | 冗余 be |
| `we should consider...` | `we consider / we account for` | 论文不写 should |
| `the data is very big` | `the dataset contains X records` | 用具体数字 |
| `in this paper, we will...` | `in this paper, we ...` | 过去/现在时一致，少用 will |
| `very/quite/really` 堆叠 | 删掉或用具体量词 | 模糊程度词 |
| `and so on` | 省略或 `etc.`（正式） | 显得没数完 |
| 长定语从句堆叠 | 拆成短句 | 一句一个意思 |
| `firstly, secondly, finally` 每段开头 | 保留必要的，其余删 | 避免模板感 |
| `make a conclusion that...` | `we conclude that...` | 简洁 |
| 时态混乱 | 方法/结果用过去式，通用结论用现在式 | 保持一致性 |

## 五、4 天写作节奏（美赛，配合 `timeline.md`）

> 英文产出**从第 1 天就开始写词块**，别到最后一天才翻译。

- **第 1 天**：定题时顺带定「模型英文名 + 一句话总思路」（写进 Summary 草稿）。建术语表，把关键模型名写死，别中途换词。
- **第 2 天**：随模型跑通，把每问「方法→结果→验证」写成 bullet 英文草稿（不等论文）。
- **第 3 天**：打磨主打图 + 把 bullet 串成 Summary Sheet 草稿；检查中英一致。
- **第 4 天**：先写死 Summary Sheet（独立一页），再补正文；最后 2h 只做语言润色 + 25 页预算 + 参考文献 + AI Use Report，**不做新计算**。
- **每日英文产出小目标**：第 1 天 ≤0.5 页、第 2 天 ≤2 页、第 3 天 ≤8 页、第 4 天补足并 ≤25 页硬上限。

## 六、交稿前英文自查清单

- [ ] Summary Sheet 独立一页、单页内、能脱离正文读懂
- [ ] 每句带数字 / 区间 / 置信，无模糊程度词
- [ ] 模型名全文统一、首次给全称 + 缩写
- [ ] 术语表覆盖关键方法，图表标题 / 轴 / 表头全英文且一致
- [ ] 时态一致（方法过去式、通用结论现在式）
- [ ] 无「中式英语」表中的典型错误
- [ ] Policy Letter（若题需要）面向非技术读者、每条 = 对象+行动+效果+证据
- [ ] 全文 ≤25 页硬上限、AI Use Report 不计页数（`mcm-icm-guide.md`）

## 七、AI Use Report 模板（用了生成式 AI 必附，不计页数）

美赛要求：若队伍使用生成式 AI / 翻译 / 代码辅助工具，须在 PDF 末尾附一段如实说明。按此结构写，别写成免责声明：

```text
AI Use Report
1. Tools used: <工具名 + 用途，如 ChatGPT-4o（brainstorming）、DeepL（translation）、Copilot（code completion）>
2. How used: <在哪个阶段怎么用，例如：生成备选模型清单、润色英文措辞；未用其直接产出整篇论文>
3. Verification: <如何核验 AI 输出，例如：公式人工推导核对、数值用自有脚本重算、文献逐条人工查证>
4. Team statement: 本文核心建模、求解、结论由队员独立完成；AI 仅作工具，其输出均经队员校验。
```

- 用没用都如实写：**用了却不写属违规**；没用则不写也不打勾。
- 把「如何校验」写具体（呼应 `reproducibility.md` 与铁律二）——这是评委最看重的半句。
