# shumo-problem-solving · 数学建模竞赛全流程解题 Skill

把一个数模赛题从「读不懂」推进到「可提交的论文」的 **Agent Skill**（供 DeepSeek Harness / 各类 agent preset 使用）。覆盖国赛 **CUMCM**、美赛 **MCM/ICM**，以及电工杯、华为杯、MathorCup、APMCM 等赛种。

## 一句话介绍

读题拆解 → 真题定位 → 模型假设 → 模型选型 → Python 求解 → 灵敏度/误差分析 → 论文与摘要，全程按「多方案先行、用户拍板」的教练式门禁推进，并用**三条铁律 + 质量三支柱**把论文从「能交」提到「国一」。

## 目录结构

```
shumo-problem-solving/
├── SKILL.md          # 技能入口：门禁 / 铁律 / 质量三支柱 / 路由表 / 标准流程 / 收口
├── references/       # 42 个专题文档（按需加载路由）
└── scripts/          # 8 个脚本（7 个零依赖校验 + plot_style 依赖 matplotlib）
```

## 核心特性

- **强制确认门禁**：数据处理 / 模型选型 / 论文，都必须先给 2–3 个方案让用户选择，禁止一键生成全部成果。
- **三条铁律**：参考文献严禁编造、先验证后引用 · 数值单一来源、可复现 · 赛种规则先核当年官方。
- **质量三支柱**：① 逻辑严密性（假设—模型双向自洽）② 解题创新性（有用 + 可检验 + 有贡献）③ 论文撰写质量（BAO 对标 + 逐节技法 + 改前改后对照）。每问初稿过 mini-gate、交稿过 full gate。
- **BAO 论文撰写对标**：从真实 O 奖/国奖范文（Baseline→Advanced→Outstanding）反推逐节写作动作与句式，含美赛 A/B/C 题型写法差异。
- **国赛 A/B/C 三题型端到端范本**：`worked-example-2023c.md`（数据）、`worked-example-2018a.md`（机理/热传导）、`worked-example-2020b.md`（优化/DP）——照着做＝出一份完整论文。
- **可复用脚本**：`init_project` / `check_results` / `verify_refs` / `figcheck` / `sanity_check` / `dedup_scan` / `review_survey`（交稿收口全自动化）+ `plot_style`（科研绘图一键美化）。

## 快速上手

把它放进你的 agent preset 的 skills 目录（以 DeepSeek Harness 为例）：

```
C:\Users\<你>\.dsh\.agent-presets\<preset>\skills\shumo-problem-solving\
```

保持 `SKILL.md` + `references/` + `scripts/` 结构即可，skill 加载器以 `SKILL.md` 为入口、按阶段路由读取 `references/`。之后在对话里直接发一道数模题（或「只写摘要」「只做灵敏度」），skill 即生效。

## references/ 精选

| 文件 | 作用 |
|---|---|
| `logic-rigor.md` | 逻辑严密性硬检查（支柱一） |
| `innovation-playbook.md` | 创新亮点打法（支柱二） |
| `bao-paper-writing.md`、`paper-quality-gate.md` | 论文撰写对标 + 交稿关卡（支柱三） |
| `writing-deai-dedup.md`、`deai-rewrite-bank.md` | 降 AI 味 / 降重规范 + 改写对照库 |
| `figure-polish.md`、`figures-and-abstract.md` | 科研图表美化手册 + 图表/摘要规范 |
| `worked-example-2023c.md`、`worked-example-2018a.md`、`worked-example-2020b.md` | 国赛 A/B/C 三题型端到端范本 |
| `model-recipes.md`、`code-templates.md` | 模型配方速查 + 代码模板 |
| `validation-checklist.md`、`sanity_check.py` | 检验硬清单 + 量级/量纲自动校验 |
| `rules-and-deadlines.md` | 赛程、规则与红线（动笔前核当年官方） |
| `cases-2026-mcm.md` | 2026 美赛六题深度解析 |
| `preprocessing-pipeline.md` | 数据清洗流水线（2025 C 题复盘教训） |

## scripts/ 一览

| 脚本 | 作用 |
|---|---|
| `init_project.py` | 生成目录骨架 + 锁版本 requirements + `export_results.py` 模板 |
| `check_results.py` | 论文数字 vs `results.json` 对账（抓野数字） |
| `verify_refs.py` | 参考文献核验清单 + 孤儿/悬空引用检测 |
| `figcheck.py` | 图表 DPI / 命名 / 引用 / 标题单位 |
| `plot_style.py` | 科研绘图一键美化（配色 / 字号 / 中文字体 / 300dpi 导出，需 matplotlib） |
| `sanity_check.py` | 量纲 / 量级 / 边界自动校验 |
| `dedup_scan.py` | 降 AI 味 + 降重自查（中/英词库 + 密度 + 题干 n-gram 比对） |
| `review_survey.py` | 赛后四维复盘（数据/模型/写作/协作） |

> 除 `plot_style.py` 需 matplotlib 外，脚本仅用标准库（PIL 可选、缺失时 `figcheck.py` 自动跳过 DPI 硬检），Python 3.8+ 直接跑。

## 数据来源与致谢

论文撰写技法提炼自公开整理的数模优秀论文（Baseline / Advanced / Outstanding 三档，见 [Math-Modeling-BAO 教程站](https://wxj630.github.io/Math-Modeling-BAO/)），仅用于学习、研究与复现对照；论文版权归原作者、参赛队与竞赛组织方所有。本 skill 只做「技法蒸馏」，不收录论文原文。

## License

Apache License 2.0，见 `LICENSE`。欢迎 fork / 提 issue / 提 PR。