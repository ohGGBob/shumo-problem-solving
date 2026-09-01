# 国一冲刺升级方案（UPGRADE_PLAN · v1.5.0）

> 目标：把本 skill 从"强助教"推到"国一助攻"——不是承诺保送国一，而是把**可避免的失分清零**、把**亮点命中率抬到最高**、把 **72h 节奏管住**。国一 = 逻辑严密 × 计算准确 × 创新有据 × 表述清晰 × 规则零违规，本方案逐项打。

## 一、已落地（v1.5.0，直接可用）

| 增量 | 对应失分点 | 用法 |
|---|---|---|
| `scripts/check_env.py` | 环境翻车：库没装/版本不锁/图变豆腐块/磁盘满 | 开赛前 10 分钟，在**建模用的那个 Python 环境**跑 `python check_env.py --strict` |
| `scripts/crosscheck.py` | "表述清晰"硬伤：摘要/正文/图注同一个数各写各的 | `python crosscheck.py report/main.md`——一次找出 19.43 vs 19.5 式矛盾 + 摘要孤立数字 + 四要素缺项 |
| `scripts/prize_gate.py` | 交稿前手忙脚乱漏项 | `python prize_gate.py <项目目录> --source 题干.txt`——一条命令聚合 7 项校验出 PASS/FAIL 计分板 |
| 修复（v1.4.1→1.5.0） | Windows BOM 崩溃 / 负数误报 / 6.2% 拆错 | `check_results`/`sanity_check` 等 5 脚本改 `utf-8-sig`；数字提取支持负数 + 原子组防拆 + 百分比去重 |

## 二、建议后续（按优先级，赛前窗口内能做的排前面）

### P0 · 赛前 8 天（9/10 开赛前）
- [x] **环境体检**：在建模环境跑 `check_env.py`，缺库立刻装、版本锁进 `requirements.txt`。
- [x] **一键 smoke**：用 `init_project.py` 建个空项目跑 `prize_gate.py`，确认 11 个脚本在新机器全链通。
- [ ] **规则再核验**：`rules-and-deadlines.md` 已要求开题第一动作 web_search 核官网；赛前最后一天把当年页数/AI 披露/提交渠道/查重口径打印置顶。

### P1 · 赛中 72h
- [ ] **决策日志（建议实现）**：把「强制确认门禁」的每次拍板自动追加到 `log/decisions.md`（谁/选了啥/理由/取舍）。这是论文"设计意图"段的直接素材——评委最吃的"为什么这么选"。
- [ ] **亮点预埋**：赛前按 `innovation-playbook.md` 给 A/B/C 三题型各预写 2–3 个**可移植亮点骨架**（多模型对照择优、理论点证明、蒙特卡洛证据链），赛中直接套——创新是设计出来的，不是赛后找的。
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
