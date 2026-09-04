# 国一冲刺升级方案（UPGRADE_PLAN · v1.9.3）

> 目标：把本 skill 从"强助教"推到"国一助攻"——不是承诺保送国一，而是把**可避免的失分清零**、把**亮点命中率抬到最高**、把 **72h 节奏管住**。国一 = 逻辑严密 × 计算准确 × 创新有据 × 表述清晰 × 规则零违规，本方案逐项打。

## 一、已落地（v1.8.0 → v1.9.8，直接可用）

| 增量 | 对应失分点 | 用法 |
|---|---|---|
| `scripts/check_env.py` | 环境翻车：库没装/版本不锁/图变豆腐块/磁盘满 | 开赛前 10 分钟，在**建模用的那个 Python 环境**跑 `python check_env.py --strict` |
| `scripts/crosscheck.py` | "表述清晰"硬伤：摘要/正文/图注同一个数各写各的 | `python crosscheck.py report/main.md`——一次找出 19.43 vs 19.5 式矛盾 + 摘要孤立数字 + 四要素缺项 |
| `scripts/prize_gate.py` | 交稿前手忙脚乱漏项 | `python prize_gate.py <项目目录> --source 题干.txt`——一条命令聚合 7 项校验出 PASS/FAIL 计分板 |
| `scripts/decision_log.py` | 每次拍板流失（"为什么这么选"无据可依） | 拍板即 `add --phase … --decision … --why … --ai …`；`export --for design` 直出论文「设计意图」素材 |
| `scripts/gen_ai_report.py` | 2026 国赛 AI 合规：声明缺失/详情不合规/匿名漏洞 | 自动生成参考文献前声明 + 「AI工具使用详情」四要素 + 匿名，有 pandoc 转 PDF |
| `scripts/emergency_run.py` | 时间极紧时慌到跳步/漏项/带病提交 | 紧急模式：7 阶段 checkpoint 不跳步 + 红警自动降级 + finish 一键收口（prize_gate+AI报告+提交清单） |
| 修复（v1.4.1→1.5.0） | Windows BOM 崩溃 / 负数误报 / 6.2% 拆错 | `check_results`/`sanity_check` 等 5 脚本改 `utf-8-sig`；数字提取支持负数 + 原子组防拆 + 百分比去重 |
| 合规依据 | 规则未核先动笔 | 按官方原文核实 2026 AI 规定（cmathc.org.cn/mcm/tz/602.html），写入 `references/ai-usage-report.md` |
| 模型适配（v1.8.0 收敛） | 型号细分过度、维护负担 | 收敛为 `references/model-adaptation.md`（DeepSeek 系通用：不区分型号、脚本与型号无关、卡壳换更强型号），删除细分工具 `model_profile.py` |
| 亮点预埋（v1.8.0） | 赛中才现想创新、没证据链 | `references/lightning-skeletons.md`（A/B/C 三题型各 3 可移植骨架：模型组合 + 证据链 + 论文落点模板 + 预写清单，命中即套） |
| 体检器（v1.8.1） | 每次升级靠人肉回归；preset 根配置漂移没人查 | 仓库根 `tools/skill_audit.py`：A–G 七项一键体检（脚本可跑 / 路由孤儿 / README 覆盖 / 数量口径 / 死链 / 门禁一致性 / **preset 根计数**），零依赖；每次升级后 `python tools/skill_audit.py` 回归（部署在 preset 布局下时，G 项会连 `preset.yml`/`agent.cordis.yml` 的计数口径一起扫） |
| 社区对标升级（v1.9.0） | 排版无人管、文献靠人肉、图与结论脱钩、定稿凭感觉 | 对标 GitHub 同类 skill（math-modeling-skill 系 / MathModelAgent）后补强四件套：① `references/typesetting-delivery.md`（国赛版式规范 + Word/LaTeX 双路线 + 格式自查 10 条）；② `scripts/ref_search.py`（OpenAlex 检索真实文献 + DOI 核验，铁律一自动化）；③ `figure-polish.md` §9 Figure Contract（画图前四行合同 + SVG/PNG 双导出）；④ `paper-quality-gate.md` 关卡六百分制定稿评分（摘要 30/模型 20/创新 20/写作 15/排版 15，≥85 才定稿，≤3 轮循环） |
| 评委视角（v1.9.1） | 只知道自嗨式写作，从没站在评阅组角度自检 | 对标社区评阅要点资源（Math_Model 合集 / MathModelHub）+ 历年官方评阅要点原文，落地 `references/judge-view.md`：8 条通用评委信号（快速算法优于无脑智能算法/简化给依据/给计算时间/交叉验证/协同鼓励…）+ 四得自查 + 模型对比表与应用指南模板 + 30 分钟裁判预演；`mid-contest-warning.md` 补「论文完整>论文完美」应急心法 |
| 社区对标第三轮（v1.9.2） | 模型空转没护栏、门禁汇报太随意、图表数量无纪律 | 对标 zhnnky329/MathModeling-skills（risk-probe/frozen-numbers/figure-table-planner）+ Fynn-jx/MathModeling-skill（H0–H5 门禁）+ cumcm-step-review（数据图硬规范）：① `sanity_check.py` 新增 `--distinct` 输出退化/集中度检查（预测全同值=模型空转当场抓住）；② `validation-checklist.md` 新增四章「输出退化 + 决策保持性」（简化模型最终决策须与完整模型复核一致）；③ SKILL.md 门禁新增「汇报五要素」（状态/动作/文件影响/备选/风险，不许只问"是否继续"）；④ `figure-polish.md` 新增 §10 图表用途四分类（诊断图不入正文）+ 数量纪律（同类型≤3 张、每图必配解读） |
| 收官审视修复（v1.9.3） | v1.9.x 收尾漏的运行时假绿 + 内容口径漂移 | 脚本：sanity_check 缺文件退 1 / verify_refs 孤儿引用退 1（消灭假绿）；emergency_run finish 查 prize_gate+AI 报告退出码（防带病收口）；ref_search 补 GBK reconfigure；skill_audit 透传 PYTHONUTF8 + 导览裸计数正则。内容：judge-view 虚化无源评阅要点原文与硬数值、§五两把尺澄清；typesetting 美赛 AI 报告改「附正文后同 PDF（不计 25 页）」对齐 2026 COMAP、参考文献 3–5 条；README 计数 46→48、零依赖 13→14；figure-polish/paper-quality-gate 修交叉引用与「五张表」层级；合规依据域名改 cmathc.org.cn（官方，挂 2026 AI 规定） |
| 评估修复三连（v1.9.4） | plot_style 缺库连 --help 都崩 / judge-view 残留无源"国奖线"硬数值 / ref_search 中文核验提醒不足 | `plot_style.py` 改 matplotlib 惰性加载（缺库时 `--help`/import 正常，体检器 A 项 15/15 全绿）；`judge-view.md` §五彻底移除无官方依据的分值硬数字，仅留相对权重提示；`ref_search.py` verify 补中文文献人工核验常驻提醒（[存在]/[不存在] 分支） |
| 教练式交互升级（v1.9.5，用户实测反馈） | 一次抛多道选择题让用户懵 / AI 跳问推进失控 / 读题全靠人肉或遗漏 / 用户到后面不知道 AI 在干嘛 | 依据真实使用反馈改造交互：① **决策卡片制**（`references/decision-cards.md`）：一次只抛一张卡、候选 3–4 个讲清优劣、选定确认才走下一步，杜绝"一批选择题"；② **按小问推进**：第 N 问闭环确认后才进第 N+1 问，绝不提前抛后面小问决策（写进门禁铁律 + 标准流程节奏）；③ **先讲方法再求解**：每问先 3–4 个候选方法卡、确认明白再求解；④ **边做边教**：每卡附"为什么这么推荐"，进度永远可预期；⑤ **PDF 全文提取** `scripts/pdf_extract.py`（多后端 PyMuPDF→pypdf→pdftotext，逐页全文+页标记+元数据+空页/扫描件检测，防读题遗漏；本机已装 PyMuPDF） |
| 读数据/读图工具配齐（v1.9.6，用户反馈） | C 题读数据靠手写探索代码 / 赛中临时装库 / 图片靠肉眼或漏读 | ① `scripts/data_profiler.py`：xlsx/csv 快速概览（形状/列类型/缺失率/唯一值/数值统计/常量列/疑似 ID/高缺失/多表关联键），一条命令读懂数据结构；② `scripts/img_tools.py`：图片信息/放大看小字/裁剪局部/从 PDF 提取内图/扫描件整页渲染/批量，配合模型视觉模态读题；③ 依赖提前配好（pandas/openpyxl/pillow 已装），`check_env.py` 体检一键装齐，避免赛中临时装；④ 数量口径 16→18 脚本全量同步 |
| 数据完整性铁律（v1.9.7，用户反馈 AI 幻觉） | AI 没读完全部数据甚至漏数据就开始判断，凭印象报数、幻觉严重 | 新增**铁律四 · 数据完整性**（SKILL 四条铁律 + `references/data-reading-discipline.md`）：① 数据清单先行——`data_profiler.py --inventory` 生成 `report/data_inventory.md`，与 data/ 逐项对照，有文件没登记=还没读禁止建模；② 数字必有出处——论文每个数据数字能回溯到"哪文件/哪表哪列/什么口径"，说不出来=幻觉删除；③ 漏读自查——每问建模前过三条；④ 禁凭印象——"大概/我记得"一律回文件确认。配套：`init_project.py` 骨架生成 `report/data_inventory.md` 模板 + README 铁律4；`data_profiler.py` 增 `--inventory/--out`；收口清单加"数据完整性"一道（3→4 项铁律、7→8 道收口）；refs 49→50 |
| 远端仓库合并（v1.9.8，用户反馈"提交仓库"） | GitHub origin 分叉：远端独有 3 脚本 + init_project 模板增强（基于老版本，缺本地 v1.9.x 全部升级） | 以本地 v1.9.7 为权威 merge 远端历史（`-s ours` 保内容），再手动吸收远端 4 项资产：① `scripts/time_budget.py`（赛程时间预算看板，72h 红警 + --watch）；② `scripts/log_run.py`（极简实验追踪器，多版本对比留痕）；③ `scripts/gen_defense.py`（答辩 PPT 生成器，revealjs 零依赖 / pptx）；④ `init_project.py` 合并论文模板能力（`--template cumcm/mcm/both`：国赛 LaTeX / 美赛 DOCX 生成脚本 + 模板说明），并修复远端两处 bug（`\py{}` 占位改普通文本、`main(sys.argv[1)` 缺右括号）。SKILL/README/model-adaptation/preset 数量 18→21，路由表加"赛中实验追踪/答辩/时间红线"三行；version bump v1.9.8 |

## 二、建议后续（按优先级，赛前窗口内能做的排前面）

### P0 · 赛前 8 天（9/10 开赛前）
- [x] **环境体检**：在建模环境跑 `check_env.py`，缺库立刻装、版本锁进 `requirements.txt`。
- [x] **一键 smoke**：用 `init_project.py` 建个空项目跑 `prize_gate.py`，确认 21 个脚本在新机器全链通。
- [ ] **规则再核验**：`rules-and-deadlines.md` 已要求开题第一动作 web_search 核官网；赛前最后一天把当年页数/AI 披露/提交渠道/查重口径打印置顶。

### P1 · 赛中 72h
- [x] **决策日志**：`decision_log.py` 已落地，`export --for design` 直出论文「设计意图」素材；`export --for aireport` 喂给 AI 报告。
- [x] **紧急模式**：`emergency_run.py` 已落地——时间极紧时一条命令管到底（7 阶段不跳步 + 红警 + 一键收口），见 `references/emergency-mode.md`。
- [x] **AI 使用报告（2026 合规）**：`gen_ai_report.py` + `references/ai-usage-report.md` 已落地（声明 + 详情四要素 + 匿名 + 红线）。
- [x] **亮点预埋**：`lightning-skeletons.md` 已落地（v1.8.0）——A/B/C 三题型各 3 可移植亮点骨架（模型组合 + 证据链 + 论文落点模板 + 预写清单），赛前按"预写清单"备齐代码与图模板，赛中命中即套。
- [ ] **红警看板**：`timeline.md` 的红警线（D2 晚未跑通全部模型=砍复杂度）做成可勾选进度表，每问过 `sanity_check.py` 自动拦量级错。

### P2 · 交稿前 6h
- [x] **裁判预演（v1.9.1 落地）**：`references/judge-view.md`——官方评阅要点提炼的 8 条通用信号 +「看得懂/找得到/信得过/用得上」四得自查 + 模型对比表与「模型应用指南」模板 + 交稿前 30 分钟预演流程（原计划的 judge_rehearsal.md 以更完整形态落地）。
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
