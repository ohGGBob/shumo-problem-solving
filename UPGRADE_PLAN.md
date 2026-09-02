# 国一冲刺升级方案（UPGRADE_PLAN · v1.9.0）

> 目标：把本 skill 从"强助教"推到"国一助攻"——不是承诺保送国一，而是把**可避免的失分清零**、把**亮点命中率抬到最高**、把 **72h 节奏管住**。国一 = 逻辑严密 × 计算准确 × 创新有据 × 表述清晰 × 规则零违规，本方案逐项打。

## 一、已落地（v1.8.0 → v1.9.0，直接可用）

| 增量 | 对应失分点 | 用法 |
|---|---|---|
| `scripts/check_env.py` | 环境翻车：库没装/版本不锁/图变豆腐块/磁盘满 | 开赛前 10 分钟，在**建模用的那个 Python 环境**跑 `python check_env.py --strict` |
| `scripts/crosscheck.py` | "表述清晰"硬伤：摘要/正文/图注同一个数各写各的 | `python crosscheck.py report/main.md`——一次找出 19.43 vs 19.5 式矛盾 + 摘要孤立数字 + 四要素缺项 |
| `scripts/prize_gate.py` | 交稿前手忙脚乱漏项 | `python prize_gate.py <项目目录> --source 题干.txt`——一条命令聚合 7 项校验出 PASS/FAIL 计分板 |
| `scripts/decision_log.py` | 每次拍板流失（"为什么这么选"无据可依） | 拍板即 `add --phase … --decision … --why … --ai …`；`export --for design` 直出论文「设计意图」素材 |
| `scripts/gen_ai_report.py` | 2026 国赛 AI 合规：声明缺失/详情不合规/匿名漏洞 | 自动生成参考文献前声明 + 「AI工具使用详情」四要素 + 匿名，有 pandoc 转 PDF |
| `scripts/emergency_run.py` | 时间极紧时慌到跳步/漏项/带病提交 | 紧急模式：7 阶段 checkpoint 不跳步 + 红警自动降级 + finish 一键收口（prize_gate+AI报告+提交清单） |
| 修复（v1.4.1→1.5.0） | Windows BOM 崩溃 / 负数误报 / 6.2% 拆错 | `check_results`/`sanity_check` 等 5 脚本改 `utf-8-sig`；数字提取支持负数 + 原子组防拆 + 百分比去重 |
| 合规依据 | 规则未核先动笔 | 按官方原文核实 2026 AI 规定（mcm.edu.cn），写入 `references/ai-usage-report.md` |
| 模型适配（v1.8.0 收敛） | 型号细分过度、维护负担 | 收敛为 `references/model-adaptation.md`（DeepSeek 系通用：不区分型号、脚本与型号无关、卡壳换更强型号），删除细分工具 `model_profile.py` |
| 亮点预埋（v1.8.0） | 赛中才现想创新、没证据链 | `references/lightning-skeletons.md`（A/B/C 三题型各 3 可移植骨架：模型组合 + 证据链 + 论文落点模板 + 预写清单，命中即套） |
| 体检器（v1.8.1） | 每次升级靠人肉回归；preset 根配置漂移没人查 | 仓库根 `tools/skill_audit.py`：A–G 七项一键体检（脚本可跑 / 路由孤儿 / README 覆盖 / 数量口径 / 死链 / 门禁一致性 / **preset 根计数**），零依赖；每次升级后 `python tools/skill_audit.py` 回归（部署在 preset 布局下时，G 项会连 `preset.yml`/`agent.cordis.yml` 的计数口径一起扫） |
| 社区对标升级（v1.9.0） | 排版无人管、文献靠人肉、图与结论脱钩、定稿凭感觉 | 对标 GitHub 同类 skill（math-modeling-skill 系 / MathModelAgent）后补强四件套：① `references/typesetting-delivery.md`（国赛版式规范 + Word/LaTeX 双路线 + 格式自查 10 条）；② `scripts/ref_search.py`（OpenAlex 检索真实文献 + DOI 核验，铁律一自动化）；③ `figure-polish.md` §9 Figure Contract（画图前四行合同 + SVG/PNG 双导出）；④ `paper-quality-gate.md` 关卡六百分制定稿评分（摘要 30/模型 20/创新 20/写作 15/排版 15，≥85 才定稿，≤3 轮循环） |

## 二、建议后续（按优先级，赛前窗口内能做的排前面）

### P0 · 赛前 8 天（9/10 开赛前）
- [x] **环境体检**：在建模环境跑 `check_env.py`，缺库立刻装、版本锁进 `requirements.txt`。
- [x] **一键 smoke**：用 `init_project.py` 建个空项目跑 `prize_gate.py`，确认 15 个脚本在新机器全链通。
- [ ] **规则再核验**：`rules-and-deadlines.md` 已要求开题第一动作 web_search 核官网；赛前最后一天把当年页数/AI 披露/提交渠道/查重口径打印置顶。

### P1 · 赛中 72h
- [x] **决策日志**：`decision_log.py` 已落地，`export --for design` 直出论文「设计意图」素材；`export --for aireport` 喂给 AI 报告。
- [x] **紧急模式**：`emergency_run.py` 已落地——时间极紧时一条命令管到底（7 阶段不跳步 + 红警 + 一键收口），见 `references/emergency-mode.md`。
- [x] **AI 使用报告（2026 合规）**：`gen_ai_report.py` + `references/ai-usage-report.md` 已落地（声明 + 详情四要素 + 匿名 + 红线）。
- [x] **亮点预埋**：`lightning-skeletons.md` 已落地（v1.8.0）——A/B/C 三题型各 3 可移植亮点骨架（模型组合 + 证据链 + 论文落点模板 + 预写清单），赛前按"预写清单"备齐代码与图模板，赛中命中即套。
- [ ] **红警看板**：`timeline.md` 的红警线（D2 晚未跑通全部模型=砍复杂度）做成可勾选进度表，每问过 `sanity_check.py` 自动拦量级错。

### P2 · 交稿前 6h
- [ ] **裁判预演**：按 `paper-quality-gate.md` 的 full gate 五张表跑完后，再以"评审老师挑刺"视角逐节读一遍（本问亮点是否有证据链？假设是否有裸奔项？）——可固化成 `judge_rehearsal.md`。
- [ ] **图表数字对账扩展**：`figcheck.py` 增加"图注/表注里的数字 vs `results.json`"自动对账，把 crosscheck 的范围扩到图和表。

### P3 · 长期资产
- [ ] **国一达标线量化**：从 BAO 教程站抽国一全文做"指纹"（摘要字数、图密度、灵敏度覆盖度、命名模型数），产出可量化的达标线，交稿前自动打分。
- [ ] **复盘回流闭环**：`review_survey.py` 已生成四维复盘；增强为"评委视角复盘"（哪部分最可能被质疑→回流到 pitfalls-cookbook）。

## 三、使用方式（三条命令撑起一稿）

```bash
# 开赛前 10 分钟（建模环境）
python scripts/check_env.py --strict

# 交稿前 30 分钟（项目目录）
python scripts/prize_gate.py <项目目录> --source 题干.txt

# 发现一致性红项后逐条修
python scripts/crosscheck.py <项目目录>/report/main.md
```

> 边界说明：脚本把"机械可判"的失分全部拦住（数字、文献、图表、降重、一致性、环境），把"需要判断"的部分（创新、逻辑链、写作质感）留给人和 AI 协作；两者结合才是国一概率的乘积。
