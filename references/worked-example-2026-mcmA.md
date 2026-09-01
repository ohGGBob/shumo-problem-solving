# 真题演练示例：2026 MCM A — 智能手机电池耗电建模（完整串链范本）

> 目的：把 skill 前几批的能力**串成一条可复现的完整链**——读题 → 假设 → 符号 → 建模 → 求解 → 检验 → 摘要，照这一步一步走，比赛时套用同一套路。代码用**合成演示数据**跑通（标注替换真实数据处），完整可运行；对应 `cases-2026-mcm.md` 的 MCM A 部分与 `advanced-methods-templates.md` §1/§4。**核心铁律：官方明确禁止纯 ML/离散拟合，必须有显式连续时间方程。**
> ⚠️ 教学简化说明：文中摘要用中文是为了展示「串链结构」，**美赛实际交付物是英文 Summary Sheet**——把下方的摘要大意套进 `english-writing-mcm.md` §一 句式即可；代码用合成数据，替换真实数据处已逐处标注。

## 1. 问题重述（不抄题，转述）

已知手机各使用场景的功耗特征，要求：① 建立 SOC 的连续时间模型；② 预测不同初始电量×场景下的 time-to-empty；③ 做敏感性与假设检验；④ 给出省电建议与 OS 策略。

## 2. 问题分析（数据→字段→方法→指标）

- 问① → 机理题：由功率守恒列 ODE `dSOC/dt = -P_total/(Q_nom·V_oc)`，把功耗拆成可加分项。
- 问② → 事件触发的积分：`solve_ivp` + 终止事件求 time-to-empty。
- 问③ → 灵敏度：分项功率 ±X% 摄动，看 time-to-empty 变化；可用 Sobol 找主导参数。
- 问④ → 决策：把"哪项省电救回多少续航"翻译成可执行建议。

## 3. 模型假设（三件套：理由 / 后果 / 验证）

| 假设 | 理由 / 后果 / 验证 |
|---|---|
| 功耗分项可加（屏幕/CPU/网络/GPS/后台） | 理由：各模块近似独立耗电；后果：忽略模块间热耦合；验证：分项总和 vs 实测总量误差 <5% |
| 开路电压 V_oc 近似常数 | 理由：常用电量区间内变化小；后果：低 SOC 时 SOC 速率会被低估；验证：保留 V_oc(SOC) 变体做对照 |
| 容量 Q_nom 恒定（先不老化） | 理由：48h 内老化可忽略；后果：长期预测会偏乐观；验证：讨论老化修正 |
| 场景功耗占空比给定（由数据统计） | 理由：场景定义明确；后果：实际使用波动大；验证：对占空比做 ±20% 摄动 |

## 4. 符号约定

| 符号 | 含义 | 单位 |
|---|---|---|
| SOC(t) | t 时刻荷电状态 | 0–1 |
| Q_nom | 标称容量 | Ah |
| V_oc | 开路电压 | V |
| P_idle, P_screen, P_cpu, P_net, P_gps | 各分项功率 | W |
| P_total(t) | 总功耗 | W |
| T_empty | time-to-empty | h |

## 5. 建模与求解（完整可运行）

```python
# 依赖 numpy scipy；演示用合成数据，比赛替换为真实数据
import numpy as np
from scipy.integrate import solve_ivp

# ---------- 参数（演示值；用 NASA/Oxford 电池数据集标定）----------
Q_nom = 3.8          # Ah
V_oc  = 3.7          # V
# 各场景功耗占空比字典：场景名 -> {screen, cpu, net, gps} 占空比(0~1)
# idle 是基础功耗，始终存在
P_idle = 0.15        # W
P_max = dict(screen=0.6, cpu=1.5, net=0.7, gps=0.5)   # 各模块最大功率 W

def dSOC(t, soc, duty):
    """duty: {screen,cpu,net,gps} 占空比(0~1)。返回 dSOC/dt (1/s)。"""
    P_total = P_idle + sum(P_max[k]*duty[k] for k in P_max)
    return -P_total / (Q_nom*3600*V_oc)      # Ah·s -> SOC/s

def time_to_empty(duty, soc0=1.0):
    """事件触发：SOC 到 0.02 即终止，返回耗时(小时)。
    注意：dSOC 传了 args=(duty,)，事件函数也要接收 duty。"""
    def hit_empty(t, y, duty): return y[0] - 0.02
    hit_empty.terminal = True; hit_empty.direction = -1
    sol = solve_ivp(dSOC, [0, 3600*30], [soc0], args=(duty,),
                    events=hit_empty, max_step=60, dense_output=True)
    return sol.t_events[0][0]/3600 if sol.t_events[0].size else 30.0

# ---------- 场景定义 + 预测 ----------
scenes = {
    "轻度使用": dict(screen=0.2, cpu=0.1, net=0.1, gps=0.0),
    "中度使用": dict(screen=0.5, cpu=0.3, net=0.3, gps=0.1),
    "重度使用": dict(screen=0.8, cpu=0.7, net=0.5, gps=0.4),
}
for name, duty in scenes.items():
    t_empty = time_to_empty(duty)
    print(f"{name}: time-to-empty = {t_empty:.2f} h")
```
> 输出（合成数据示例，实测）：轻度约 28 h、中度约 12 h、重度约 6 h——量级合理（对照手机实际续航）。真实比赛用标定参数替换后重跑。

## 6. 模型检验（sanity + 灵敏度 + 结论稳健性）

```python
# ---------- 6a. sanity check：量级 / 边界 ----------
from sanity_check import check_number, summary
check_number("轻度 time-to-empty", time_to_empty(scenes["轻度使用"]), 0, 30, "应在 0–30h")
check_number("重度 time-to-empty", time_to_empty(scenes["重度使用"]), 0, 12, "重度应<12h")

# ---------- 6b. 灵敏度：占空比 ±20% 看 time-to-empty ----------
base = time_to_empty(scenes["中度使用"])
for k, pct in [("screen", 0.2), ("cpu", 0.2), ("net", 0.2), ("gps", 0.2)]:
    d = dict(scenes["中度使用"]); d[k] = min(1.0, d[k]*(1+pct))
    t1 = time_to_empty(d)
    print(f"{k} +20%: time-to-empty {base:.2f} -> {t1:.2f} h (Δ{t1-base:+.2f})")
summary()
```
> 解读：**对 time-to-empty 影响最大的模块就是最该优化的**（通常 CPU 或屏幕）。把"最敏感项"写进省电建议，是支柱一的证据链式检验，也是支柱二的"结果背后的为什么"。

## 7. 摘要（四要素，带数值）

> 针对智能手机电池续航问题，本文建立基于功率守恒的连续时间 SOC 模型，把功耗分解为屏幕/CPU/网络/GPS 四项可加分项，用事件触发的常微分方程求解不同场景下的 time-to-empty。在合成标定参数下，轻度使用续航约 28 h、中度约 12 h、重度约 6 h。灵敏度显示 CPU 与屏幕对续航影响最大：CPU 占空比 +20% 使续航缩短约 0.9 h、屏幕约 0.6 h，GPS 影响最小（约 0.1 h），据此建议优先限制后台 CPU 与降低屏幕亮度。模型在 ±20% 摄动下结论稳健，续航预测量级与主流机型实测一致。
> 注：上列数字与 §5/§6 代码输出逐位一致（铁律二：摘要数字必须能回溯到代码）。真实比赛用标定参数替换合成参数后，需重跑并同步更新摘要。

## 8. 对应 skill 资源（这套路从哪来）

| 环节 | 对应文件 |
|---|---|
| 题型定位 | `cases-2026-mcm.md`（MCM A：禁纯 ML，需连续时间方程） |
| ODE + 事件触发 | `advanced-methods-templates.md` §1/§9 |
| 量纲/量级/边界校验 | `scripts/sanity_check.py` |
| 灵敏度 | `validation-checklist.md`、`advanced-methods-templates.md` §4（Sobol） |
| 摘要 / 英文 | `paper-quality-gate.md`、`english-writing-mcm.md` |

## 学完这道题，你会复用的三件事

1. **连续时间方程 + 事件触发**：机理题（电池/传热/运动）通用，先列守恒方程再积分。
2. **分项可加 + 逐项灵敏度**：找"主导参数"→ 落到可执行建议，是 A 类题拿 O 的标配。
3. **sanity check 先行**：任何数值跑出来先过量级/边界校验，再进论文（支柱一）。
