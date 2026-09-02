# 高级方法代码模板（2026 美赛实战工具落地，复制即用）

> 定位：`code-templates.md` 讲基础模型，本文件补 **2026 美赛六题用到的「高级/统计/因果/优化」工具**，全部落地成最小可复现代码。每段都用 `numpy`/`scipy`/`statsmodels` 为主，重库（`pymc`、`SALib`、`pvlib`、`pulp`）给最小用法并在首行标注依赖。**凡随机一律固定 seed，数值可回溯**（呼应铁律二）。跑通后再改参数，别到赛场调试。
> 环境建议：`requirements.txt` 锁版本，以下库版本为实测基线：numpy 2.x / scipy 1.x / statsmodels 0.14+ / pandas 2.x；pulp 2.x / SALib 1.5 / pymc 5.x / pvlib 0.11+。

## 1. 电池 SOC 连续模型 + 事件触发 time-to-empty（MCM A 核心）

```python
# 依赖 numpy scipy
import numpy as np
from scipy.integrate import solve_ivp

# 参数：C_nom 标称容量(Ah)，V_oc 开路电压(V)，P_f 各分项功率
def dSOC(t, soc, C_nom=3.8, V_oc=3.7, P_idle=0.2, P_screen=0.5,
         P_cpu=1.2, P_net=0.6, P_gps=0.4):
    # P_total 随时间/状态变化的占空比由外部 dict 传入更灵活；这里给常量示例
    P_total = P_idle + P_screen + P_cpu + P_net + P_gps
    return -P_total / (C_nom * 3600 * V_oc)   # A/s 换算：容量 Ah->C

# 事件：SOC 到 0.02（约耗尽）即终止，返回 time-to-empty
def hit_empty(t, y): return y[0] - 0.02
hit_empty.terminal = True; hit_empty.direction = -1

sol = solve_ivp(dSOC, [0, 3600*10], [1.0], method='RK45',
                events=hit_empty, max_step=60, dense_output=True)
print('time-to-empty (s):', sol.t_events[0][0] if sol.t_events[0].size else 'not reached')
```
> 要点：把每个分项写成独立函数参数，便于逐项做灵敏度（±X% 摄动看 time-to-empty 变化）。**官方要求必须有显式连续时间方程**——只做纯 ML/离散拟合、没有连续时间模型的，不满足本题要求。

## 2. ODE 参数辨识（最小二乘反演，A/B/E 类机理题通用）

```python
# 依赖 numpy scipy
import numpy as np
from scipy.optimize import least_squares
from scipy.integrate import solve_ivp

def model(t, y, k):
    d = -k[0]*y[0]                      # 例：一阶衰减 dx/dt = -k0*x
    return [d]

def residuals(k, t_obs, x_obs, x0):
    sol = solve_ivp(model, [t_obs[0], t_obs[-1]], [x0], t_eval=t_obs, args=(k,), method='RK45')
    return sol.y[0] - x_obs

t_obs = np.linspace(0, 10, 20); x_obs = 5*np.exp(-0.4*t_obs) + 0.05*np.random.default_rng(0).normal(0,1,20)
x0 = x_obs[0]
res = least_squares(residuals, [0.5], args=(t_obs, x_obs, x0))
print('辨识参数 k =', res.x, ' RMSE =', np.sqrt(np.mean(res.fun**2)))
```
> 关键：`least_squares` 返回 `res.x`（最优参数）、`res.fun`（残差）；RMSE 是必报的拟合优度。可对多个初值多跑，报告稳定性。

## 3. Difference-in-Differences（双重差分，F 类因果题核心）

```python
# 依赖 pandas statsmodels
import numpy as np, pandas as pd
from statsmodels.formula.api import ols

rng = np.random.default_rng(0)
n_per = 200
df = pd.DataFrame({
    'treat': np.r_[np.zeros(n_per), np.ones(n_per)],   # 0=对照组,1=处理组
    'post':  np.tile([0, 1], n_per),                    # 0=前,1=后
    'id':    np.arange(2*n_per),
})
# 生成 y：处理组在 post 后多 +1.5（真实效应）
df['y'] = 3.0 + 0.5*df['treat'] + 0.3*df['post'] + 1.5*(df['treat']*df['post']) + rng.normal(0, 0.5, 2*n_per)

model = ols('y ~ treat + post + treat:post', data=df).fit()
did = model.params['treat:post']
p = model.pvalues['treat:post']
print(f'DiD 效应 = {did:.3f}, p = {p:.3f}')   # 应≈1.5 且显著
```
> 要点：`treat:post` 交互项系数 = DiD 效应（2×2 无面板）。若是**面板数据**（同一个体前后两期），再加个体/时间固定效应 `y ~ C(id) + C(period) + treat:post`——`period` 是时期列、`id` 是面板个体；本玩具是重复截面、`id` 仅行号，**别直接套 `C(id)`（会与 treat 共线）**，并做**平行趋势检验**（对比 pre 期两组走势）。F 类题可用在"2022-11 生成式 AI 发布前后 × 任务类型"上。

## 4. Sobol 全局敏感性分析（识别主导参数，A/C/E 类亮点）

```python
# 依赖 SALib  （pip install SALib）
import numpy as np
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze

# 定义参数空间（name/bounds）
problem = {'num_vars': 4, 'names': ['alpha','beta','gamma','delta'],
           'bounds': [[0.5,1.5],[0.5,1.5],[0.5,1.5],[0.5,1.5]]}
X = sobol_sample.sample(problem, 1024, seed=0)          # 采样
Y = np.array([np.sin(x[0]) + 2*x[1] - x[2]*x[3] for x in X])  # 模型输出
Si = sobol_analyze.analyze(problem, Y)
for n, s1, st in zip(problem['names'], Si['S1'], Si['ST']):
    print(f'{n}: S1={s1:.3f} ST={st:.3f}')   # ST 总效应，>0.5 即主导参数
```
> 优势：比单点 ±10% 灵敏度更全面，能捕捉交互效应。美赛 A/E 类题用 Sobol 找"哪个参数对续航/遮阳影响最大"，是支柱二的"证据链"式检验。

## 5. 潜在变量 / 贝叶斯推断（MCMC，C 类"星舞"题通用）

```python
# 依赖 numpy scipy；重库可选 pymc
import numpy as np
from scipy import stats

# 最小可行：Gibbs/独立性采样估计潜在因子（无重库版）
rng = np.random.default_rng(0)
# 观测 = latent + 噪声
latent_true = np.linspace(0, 1, 10)
y = latent_true + rng.normal(0, 0.2, 10)

# 简单后验：latent ~ N(posterior_mean, posterior_var)
prior_var = 1.0; obs_var = 0.2**2
post_var = 1/(1/prior_var + len(y)/obs_var)
post_mean = (post_var) * (len(y)/obs_var) * y.mean()
samples = rng.normal(post_mean, np.sqrt(post_var), 5000)
print('latent posterior mean =', samples.mean(), '95%CI =', np.percentile(samples, [2.5,97.5]))
```
> 轻量思路：小问题用解析后验 / 简单采样；大问题用 `pymc`（`pm.Model` + `pm.Normal` 先验 + `pm.sample(draws=2000, random_seed=0)`）。**给置信区间**（可信区间）是 C 类题拿 O 的标配，别只报点估计。
> `pymc` 最小用法：
> ```python
> import pymc as pm
> with pm.Model() as m:
>     mu = pm.Normal('mu', 0, 1)
>     sigma = pm.HalfNormal('sigma', 1)
>     pm.Normal('obs', mu, sigma, observed=y)
>     trace = pm.sample(500, random_seed=0, progressbar=False)
> ```

## 6. CVaR 风险组合优化（D 类体育/金融风险决策）

```python
# 依赖 pulp （pip install pulp）
import numpy as np
from pulp import LpProblem, LpMaximize, LpMinimize, LpVariable, LpStatus, value

# 例：3 种资产，最大化 CVaR 调整后收益。标准 LP 分位点法（Rockafellar–Uryasev）：
#   max  mean(w) - kappa*CVaR,  CVaR = VaR + 1/((1-α)·S)·Σ loss[s]
#   损失 loss_s = -R_s·w ；超额损失 loss[s] >= -R_s·w - VaR 且 loss[s] >= 0
#   w ≥ 0, Σw=1 ；VaR 需给一个下界（否则目标含 -kappa*VaR 会无界）
assets = 3; S = 1000
rng = np.random.default_rng(0)
R = rng.normal(0.05, 0.15, (S, assets))     # 每行一个场景收益
alpha = 0.95
kappa = 2.0

prob = LpProblem("CVaR", LpMaximize)
w = [LpVariable(f'w{i}', 0, 1) for i in range(assets)]   # 权重
vaR = LpVariable('VaR', lowBound=-5.0)                  # 给下界，防无界
loss = [LpVariable(f'l{s}', 0) for s in range(S)]
prob += sum(np.mean(R,0)[i]*w[i] for i in range(assets)) \
        - kappa*(vaR + 1/((1-alpha)*S)*sum(loss))        # 目标：mean - kappa*CVaR
prob += sum(w) == 1
for s in range(S):
    prob += loss[s] >= - sum(R[s,i]*w[i] for i in range(assets)) - vaR  # 超额损失 (loss=-R·w)
prob.solve()
print('status:', LpStatus[prob.status], 'weights:', [round(value(w[i]),3) for i in range(assets)])
```
> 要点：这是「分位点 LP」形式，`loss[s]` 捕捉超过 VaR 的损失，`CVaR = VaR + 平均超额损失/(1-α)`。**务必给 `vaR` 设一个合理下界（如 -5）**，否则目标含 `-kappa*VaR` 会因 VaR 可无限负而无界。D 类"tank-or-contend"决策可用 CVaR 度量最坏情形成本；也可结合 MDP 描述多阶段决策。**小规模先用精确 LP，别一上来就启发式。**

## 7. MILP 深化：多目标 → ε-约束 / 加权（B/D 类优化）

```python
# 依赖 pulp
import numpy as np
from pulp import LpProblem, LpMinimize, LpVariable, LpStatus, value

# 例：双目标 min (cost, time)。先单解每个目标，得理想点，再用 ε-约束。
prob = LpProblem("bi_obj", LpMinimize)
x = LpVariable('x', 0, 10, cat='Integer'); y = LpVariable('y', 0, 10, cat='Integer')
cost = 3*x + 4*y; time = 2*x + y
prob += cost                     # 只优化 cost
prob += x + y >= 5
prob.solve()
cost_min, time_at_cost = value(cost), value(time)
print('cost-min 解: cost=', cost_min, 'time=', time_at_cost)

# ε-约束：固定 cost ≤ 上界，再最小化 time
prob2 = LpProblem("eps", LpMinimize)
x2 = LpVariable('x2', 0, 10, cat='Integer'); y2 = LpVariable('y2', 0, 10, cat='Integer')
cost2 = 3*x2 + 4*y2; time2 = 2*x2 + y2
prob2 += time2
prob2 += x2 + y2 >= 5
prob2 += cost2 <= cost_min + 5      # ε = 5，得到 Pareto 上的另一解
prob2.solve()
print('ε-约束解: cost=', value(cost2), 'time=', value(time2))
```
> 要点：多目标用**ε-约束法**比简单加权更规范（能避免权重标定问题）。扫多个 ε 得 Pareto 前沿图，是 B/D 类题的加分可视化。

## 8. 太阳位置 + 遮阳入射角（E 类被动式遮阳）

```python
# 依赖 numpy；重库可选 pvlib
import numpy as np

# 简化太阳高度角：正午最大高度 h = 90 - |lat - decl|
def solar_elevation(lat, day, hour):
    # 太阳赤纬（近似）B 公式
    B = 2*np.pi*(day - 81)/365
    decl = 23.45*np.sin(B) * np.pi/180          # rad
    lat_r = np.radians(lat)
    hour_angle = np.radians((hour - 12) * 15)   # 正午=0，每小时15°
    sin_h = np.sin(lat_r)*np.sin(decl) + np.cos(lat_r)*np.cos(decl)*np.cos(hour_angle)
    return np.degrees(np.arcsin(np.clip(sin_h, -1, 1)))  # 高度角(°)

def shading_ratio(lat, day, hour, shade_depth, window_height):
    h = solar_elevation(lat, day, hour)
    if h <= 0: return 0.0                        # 夜间无遮阳
    # 入射角余弦决定遮阳投影：投影长 = shade_depth * cot(h)
    proj = shade_depth / np.tan(np.radians(h))
    return min(1.0, proj / window_height)        # 遮住比例

print('北京(39.9°)夏至正午高度角:', solar_elevation(39.9, 172, 12))
print('遮阳比(深度0.6m,窗高1.2m):', shading_ratio(39.9, 172, 12, 0.6, 1.2))
```
> 要点：E 类核心是**太阳几何 + 热传导**。`pvlib`（`pvlib.solarposition.get_solarposition`）可拿精确高度/方位角；本函数给无重库近似版用于快速原型。**夏季遮挡 / 冬季透射**的取舍用季节性（day 参数）体现。

## 9. 事件驱动 / 时间到耗尽（B 类太空电梯 186 年悖论等）

```python
# 依赖 numpy scipy
import numpy as np
from scipy.integrate import solve_ivp

# 例：某量随时间线性积累，达到阈值触发事件（如月球殖民地人口/物资阈值）
def dX(t, y, rate): return [rate]

def hit_threshold(t, y, rate): return y[0] - 100000   # 到 10 万触发；注意传 args 时事件函数也要收 rate
hit_threshold.terminal = True; hit_threshold.direction = 1

sol = solve_ivp(dX, [0, 365*200], [0], events=hit_threshold, args=(1000/365,), max_step=30)
years = sol.t_events[0][0]/365 if sol.t_events[0].size else None
print('到达 10 万所需年数 ≈', years)            # 若>200，就是"186年悖论"的反直觉点
```
> 亮点用法：把「目标所需时间 vs 现实约束时间」对照，做 sanity check（如 B 类 186 年悖论），并据此设计更可行的 ISRU / 多港口分阶段方案。

## 10. 反事实 / 模拟重放（C 类"34 赛季重放"等机制检验）

```python
# 依赖 numpy
import numpy as np
rng = np.random.default_rng(0)

# 例：给定选手 talent，模拟 34 赛季排名分布，检验某机制是否稳定
talent = rng.normal(0, 1, 10)                    # 10 名选手真实实力
n_seasons = 34
wins = np.zeros(10)
for s in range(n_seasons):
    obs = talent + rng.normal(0, 0.5, 10)        # 每赛季加噪声
    winner = int(np.argmax(obs))                 # 最高分夺冠
    wins[winner] += 1
print('34 赛季夺冠分布:', wins)
print('最强选手(talent最大)夺冠次数:', wins[int(np.argmax(talent))])
```
> 用途：C 类题用反事实重放检验「计分机制是否偏向运气 / 真实实力」。改噪声幅度看排序稳定性，就是机制设计的证据链。

---

## 选库速查（按题型）

| 题型 | 首选库 | 进阶 |
|---|---|---|
| ODE/机理 | `scipy.integrate.solve_ivp` | `odeint` |
| PDE/热传导 | `numpy` 差分离散 | `fipy` |
| 优化/LP/IP/MILP | `scipy.optimize`、`pulp` | `ortools`（大规模） |
| 非线性/全局优化 | `scipy.optimize.differential_evolution` | `optuna` |
| 统计/回归/ARIMA | `statsmodels` | `scipy.stats` |
| 因果推断 DiD | `statsmodels.formula.api.ols` | `linearmodels`（面板） |
| 贝叶斯/MCMC | `numpy` 手写后验 | `pymc`、`emcee` |
| 全局敏感性 | `SALib`（Sobol） | 手写 MC 摄动 |
| 风险/CVaR | `pulp`（LP 分位） | `scipy.optimize` |
| 太阳/地理 | `pvlib` | 手写太阳几何 |
| 图/网络 | `networkx` | `scipy.sparse.csgraph` |

> 抄完先确认「数值对得上、种子固定、可复现」，这是评审硬标准；每段的灵敏度/验证步骤不要省。所有"显著/敏感"结论都要能回溯到这里的输出（铁律二）。
