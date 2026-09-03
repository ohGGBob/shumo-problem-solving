# shumo-problem-solving · 数学建模竞赛全流程解题 Skill

把一个数模赛题从「读不懂」推进到「可提交的论文」的 **Agent Skill**（供 DeepSeek Harness / 各类 agent preset 使用）。覆盖国赛 **CUMCM**、美赛 **MCM/ICM**，以及电工杯、华为杯、MathorCup、APMCM 等赛种。

> 与 `SKILL.md` 同步至 **v1.9.3**（2026-09-03）。以 `SKILL.md` 为准，本文件是给人看的导览。

## 一句话介绍

读题拆解 → 真题定位 → 模型假设 → 模型选型 → Python 求解 → 灵敏度/误差分析 → 论文与摘要，全程按「多方案先行、用户拍板」的教练式门禁推进，并用**三条铁律 + 质量三支柱**把论文从「能交」提到「国一」。

## 目录结构

```
shumo-problem-solving/
├── SKILL.md          # 技能入口：门禁 / 铁律 / 质量三支柱 / 路由表 / 标准流程 / 收口
├── references/       # 48 个专题文档（按需加载路由，勿一次全读）
├── tools/            # skill_audit.py —— A–G 七项体检器，升级后一键回归
└── scripts/          # 15 个脚本（14 个零第三方依赖 + plot_style 需 matplotlib + ref_search 需联网）
```

## 核心特性

- **强制确认门禁**：数据处理 / 模型选型 / 论文，都必须先给 2–3 个方案让用户选择，禁止一键生成全部成果；到达门禁须按「状态/动作/文件影响/备选/风险」五要素汇报，不许只问「是否继续」。
  - **「全自动」/「直接完成」只解锁连续执行，不解锁自主决策**——三类决策仍须给多方案。
  - 只有**显式点名「紧急模式」**（客观时间极紧）才切换为"自主决策 + 决策留痕"，详见 `references/emergency-mode.md`。
- **三条铁律**：参考文献严禁编造、先验证后引用 · 数值单一来源、可复现 · 赛种规则先核当年官方。
- **质量三支柱**：① 逻辑严密性（假设—模型双向自洽）② 解题创新性（有用 + 可检验 + 有贡献）③ 论文撰写质量（BAO 对标 + 逐节技法 + 改前改后对照）。每问初稿过 mini-gate、交稿过 full gate。
- **BAO 论文撰写对标**：从真实 O 奖/国奖范文（Baseline→Advanced→Outstanding）反推逐节写作动作与句式，含美赛 A/B/C 题型写法差异。
- **国赛 A/B/C 三题型端到端范本**：`worked-example-2023c.md`（数据）、`worked-example-2018a.md`（机理/热传导）、`worked-example-2020b.md`（优化/DP）。
- **美赛双范式范本**：`worked-example-2026-mcmA.md`（机理范式）、`worked-example-2026-mcmC.md`（统计逆问题范式，与 A 互补）。
- **亮点预埋**：`lightning-skeletons.md`——A/B/C 各 3 个可移植骨架（模型组合 + 证据链 + 论文落点模板 + 预写清单），赛前预写、赛中命中即套。
- **2026 AI 合规**：`gen_ai_report.py` 自动生成「AI工具使用声明」+ 支撑材料「AI工具使用详情」（四要素 + 匿名），见 `references/ai-usage-report.md`。
- **紧急模式**：`emergency_run.py` 7 阶段 checkpoint 不跳步 + 红警自动降级 + finish 一键收口。
- **错题本**：`pitfalls-cookbook.md`——20 条真实翻车实录（P1–P20），对照三支柱与铁律逐条自查。
- **排版双格式交付**：`typesetting-delivery.md`——国赛版式规范 + Word/LaTeX 双路线 + 交稿格式自查（对应百分制"排版 15 分"）；Figure Contract 见 `figure-polish.md` §9、百分制定稿评分见 `paper-quality-gate.md` 关卡六（≥85 才定稿）。
- **评委视角**：`judge-view.md`——历年评阅要点提炼的 8 条通用信号（快速算法/交叉验证/计算时间/协同鼓励…）+「看得懂找得到信得过用得上」四得自查 + 交稿前 30 分钟裁判预演。
- **防模型空转**：`sanity_check.py --distinct` 输出退化检查（预测全同值/解全一样当场抓住）+ `validation-checklist.md` 决策保持性检查（简化模型与完整模型最终决策必须一致）+ 图表用途四分类纪律（诊断图不入正文、每图必配解读）。

## 快速上手

把它放进你的 agent preset 的 skills 目录（以 DeepSeek Harness 为例）：

```
C:\Users\<你>\.dsh\.agent-presets\<preset>\skills\shumo-problem-solving\
```

保持 `SKILL.md` + `references/` + `scripts/` 结构即可，skill 加载器以 `SKILL.md` 为入口、按阶段路由读取 `references/`。之后在对话里直接发一道数模题（或「只写摘要」「只做灵敏度」），skill 即生效。

## references/ 导览（48 个，按阶段分组）

> 完整路由表见 `SKILL.md`「按需加载路由表」——**动手前先查那里，别一次全读**。

| 阶段 | 文件 |
|---|---|
| 开题 / 定题 / 节奏 | `topic-selection.md`、`timeline.md`、`rules-and-deadlines.md` |
| 真题定位（国赛） | `cumcm-years.md` → `cases-2021.md`…`cases-2025.md` |
| 真题定位（美赛） | `cases-2026-mcm.md`（六题解析 + O 奖率）、`mcm-icm-guide.md`（25 页硬上限 + 页面预算） |
| 其他赛种 | `contests-catalog.md`（电工杯 / 华为杯 / MathorCup / APMCM / 深圳杯…） |
| 数据 / 清洗 | `preprocessing-pipeline.md`、`data-science-playbook.md`、`bigdata-playbook.md` |
| 假设 / 选型 | `assumptions-justification.md`、`model-recipes.md`、`longitudinal-threshold.md` |
| 求解实现 | `code-templates.md`（基础）、`advanced-methods-templates.md`（DiD / Sobol / MCMC / CVaR / MILP / pvlib） |
| 检验 | `validation-checklist.md` + `scripts/sanity_check.py` |
| 逻辑 / 创新（支柱一二） | `logic-rigor.md`、`innovation-playbook.md`、`lightning-skeletons.md` |
| 论文（支柱三） | `paper-skeleton.md` → `bao-paper-writing.md` → `figures-and-abstract.md` → `figure-polish.md` → `paper-quality-gate.md` |
| 赛题范文 | `worked-example-2023c.md`、`worked-example-2018a.md`、`worked-example-2020b.md`（国赛 A/B/C）、`worked-example-2026-mcmA.md`、`worked-example-2026-mcmC.md`（美赛双范式） |
| 排版 / 交付 | `typesetting-delivery.md`（国赛版式规范 + Word/LaTeX 双路线 + 格式自查） |
| 写作打磨 | `chinese-writing-advanced.md`（中文）、`english-writing-mcm.md`（美赛英文 / Summary Sheet / Policy Letter） |
| 降 AI 味 / 降重 | `writing-deai-dedup.md` → `deai-rewrite-bank.md` |
| 赛中 / 收口 | `mid-contest-warning.md`、`emergency-mode.md`、`pitfalls-cookbook.md`、`reproducibility.md` |
| 评委视角 | `judge-view.md`（评阅要点 8 信号 + 四得自查 + 裁判预演） |
| 合规 | `ai-usage-report.md` |
| 赛后 | `defense-and-presentation.md`、`post-contest-review.md` |
| 模型适配 | `model-adaptation.md`（DeepSeek 系通用） |

## scripts/ 一览（15 个）

> 除 `plot_style.py` 需 matplotlib 外，脚本仅用标准库（PIL 可选、缺失时 `figcheck.py` 自动跳过 DPI 硬检），Python 3.8+ 直接跑。**脚本与模型型号无关。**

| 脚本 | 作用 |
|---|---|
| `init_project.py` | 生成目录骨架 + 锁版本 `requirements.txt` + `export_results.py` 模板 |
| `check_env.py` | **赛前环境体检**：Python/库版本/中文字体/磁盘/可写/seed 可复现（`--strict` 警告也计失败） |
| `check_results.py` | 论文数字 vs `results.json` 对账（抓"野数字"） |
| `crosscheck.py` | **跨文件数字一致性**：摘要/正文/图注同一数字各写各的（19.43 vs 19.5）一次找出 |
| `sanity_check.py` | 量纲 / 量级 / 边界 / 输出退化自动校验（权重和=1、概率∈[0,1]、`--distinct` 抓"预测全同值"的模型空转） |
| `verify_refs.py` | 参考文献核验清单 + 孤儿/悬空引用检测 |
| `ref_search.py` | **文献真实检索与核验**（需联网，OpenAlex API）：搜真实文献直出 GB/T 7714 草稿，`--verify DOI` 确认存在性 |
| `figcheck.py` | 图表 DPI / 命名 / 引用 / 标题单位 |
| `plot_style.py` | 科研绘图一键美化（配色 / 字号 / 中文字体 / 300dpi 导出，需 matplotlib） |
| `dedup_scan.py` | 降 AI 味 + 降重自查 v2（中英分层词库 + 密度 + 题干 n-gram 比对） |
| `decision_log.py` | **决策日志**：每次拍板留痕，可导出论文「设计意图」与 AI 使用详情素材 |
| `gen_ai_report.py` | **2026 国赛 AI 使用报告**：参考文献前声明 + 详情四要素 + 匿名 |
| `prize_gate.py` | **国一冲刺计分板**：交稿前一条命令聚合 7 项校验出 PASS/FAIL 表 |
| `emergency_run.py` | **紧急全流程编排器**：7 阶段 checkpoint 不跳步 + 红警 + finish 一键收口 |
| `review_survey.py` | 赛后四维复盘（数据/模型/写作/协作） |

### 三条命令撑起一稿

```bash
# 开赛前 10 分钟（在真正建模用的那个 Python 环境里）
python scripts/check_env.py --strict

# 交稿前 30 分钟（项目目录）
python scripts/prize_gate.py <项目目录> --source 题干.txt

# 发现一致性红项后逐条修
python scripts/crosscheck.py <项目目录>/report/main.md
```

> 计分板口径：`prize_gate` 默认把「警告」显示为 `WARN` 且**不计红项**（如 sympy/torch 等可选库未装属正常），只有真阻断项才判红——保证"红项 = 必须修"。想连警告一起清，加 `--strict`。

## 数据来源与致谢

论文撰写技法提炼自公开整理的数模优秀论文（Baseline / Advanced / Outstanding 三档，见 [Math-Modeling-BAO 教程站](https://wxj630.github.io/Math-Modeling-BAO/)），仅用于学习、研究与复现对照；论文版权归原作者、参赛队与竞赛组织方所有。本 skill 只做「技法蒸馏」，不收录论文原文。

## License

Apache License 2.0，见 `LICENSE`。欢迎 fork / 提 issue / 提 PR。
