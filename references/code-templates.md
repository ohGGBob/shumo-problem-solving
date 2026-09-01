# 常用模型 Python 代码模板（复制即用）

> 说明：以下是最高频模型的「最小可用」实现。**赛前 / 赛后先在本机跑通一遍，实战直接改参数**，别到赛场上再调试。依赖：`numpy` `scipy` `pandas` `scikit-learn` `statsmodels`；画图另加 `matplotlib`、图论另加 `networkx`、Excel 数据另加 `openpyxl`。凡涉及随机的一律固定 `seed=0`。
> 验证：下列模板在 **Python 3.10–3.12**（numpy 1.26 / scipy 1.11 / pandas 2.x / scikit-learn 1.3 / statsmodels 0.14）代表性环境可跑，**以 `init_project.py` 锁定的 requirements 为准**；凡随机一律 `seed=0`。用随机占位数据时 R² 为负属正常，换成真实数据即可；ARIMA 每次 fit 的预测值随数据不同而不同。

## 0. 通用预处理

```python
import numpy as np, pandas as pd
df = pd.read_csv('data.csv', encoding='utf-8')
df = df.dropna()                        # 缺失值；也可 df.fillna(df.median())
X = (df - df.mean()) / df.std()         # z-score 标准化（评价/聚类前常用）
# 正向化/负向化：期望越大越好→保持；期望越小越好→取负或倒数
```

## 1. 灰色预测 GM(1,1)（少样本时间序列）

```python
import numpy as np
def gm11(x0, n_forecast=3):
    """x0: 原始序列(≥4 点)；返回拟合+预测序列。用前先做级比检验。"""
    x0 = np.asarray(x0, dtype=float)
    x1 = np.cumsum(x0)
    z1 = (x1[1:] + x1[:-1]) / 2                 # 紧邻均值
    a, b = np.linalg.lstsq(np.c_[-z1, np.ones_like(z1)], x0[1:], rcond=None)[0]
    c = x0[0] - b / a
    m = len(x0) + n_forecast
    x1_hat = c * np.exp(-a * np.arange(m)) + b / a
    return np.r_[x0[0], np.diff(x1_hat)]        # 累减还原
print(gm11([2.87, 3.28, 3.34, 3.39, 3.68, 3.92, 4.11], 3))
```

## 2. ARIMA / 时间序列（趋势明显、样本较多）

```python
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
y = np.loadtxt('series.csv')                   # 先画时序图看趋势/周期/噪声
model = ARIMA(y, order=(1, 1, 1))              # (p,d,q) 依 ACF/PACF 定阶
res = model.fit()
print(res.summary())
print(res.forecast(5))                          # 预测后 5 期
```

## 3. 熵权法 + TOPSIS（客观赋权综合评价）

```python
import numpy as np
def entropy_topsis(X):
    """X: n 样本 × m 指标（已正向化、同向化）。返回贴近度 ci∈[0,1]，越大越优。"""
    X = np.asarray(X, dtype=float)
    P = X / X.sum(axis=0)
    P = np.where(P <= 0, 1e-12, P)              # 防 log(0)
    e = -(P * np.log(P)).sum(axis=0) / np.log(len(X))    # 信息熵
    w = (1 - e) / (1 - e).sum()                 # 熵权
    Z = X / np.sqrt((X**2).sum(axis=0))         # 归一化决策矩阵
    V = Z * w
    d_pos = np.sqrt(((V - V.max(axis=0))**2).sum(axis=1))
    d_neg = np.sqrt(((V - V.min(axis=0))**2).sum(axis=1))
    return d_neg / (d_pos + d_neg), w
```

## 4. 层次分析 AHP（主观赋权，需一致性检验）

```python
import numpy as np
def ahp(A):
    """A: 判断矩阵(1-9 标度)。返回权重 w 与一致性比 CR（CR<0.1 才可用）。"""
    A = np.asarray(A, dtype=float); n = len(A)
    w = A.prod(axis=1) ** (1/n); w = w / w.sum()
    lam = (A.dot(w) / w).mean()
    CI = (lam - n) / (n - 1)
    RI = {1:0, 2:0, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45}
    return w, CI / RI[n]
```

## 5. 线性规划 / 整数规划（scipy）

```python
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
# 线性规划 min c·x  s.t. A_ub x <= b_ub
c = [-3, -4]                                   # 最大化则目标取负
res = linprog(c, A_ub=[[1, 1], [2, 1]], b_ub=[6, 8], bounds=[(0, None)]*2, method='highs')
print('最优解', res.x, '最优值', -res.fun)
# 0-1 / 整数规划
res2 = milp(c, integrality=[1, 1], bounds=Bounds([0, 0], [1, 1]))
print(res2.x, res2.fun)
```

## 6. 非线性规划（scipy）

```python
from scipy.optimize import minimize
f = lambda x: (x[0]-2)**2 + (x[1]+1)**2         # 目标
cons = {'type': 'ineq', 'fun': lambda x: 4 - x[0]**2 - x[1]**2}   # 约束 >=0
res = minimize(f, [0, 0], constraints=cons, method='SLSQP')
print(res.x, res.fun)
```

## 7. 常微分方程（机理题核心）

```python
from scipy.integrate import solve_ivp
import numpy as np
def sir(t, y, beta=0.3, gamma=0.1):             # 传染病 SIR
    S, I, R = y
    return [-beta*S*I, beta*S*I - gamma*I, gamma*I]
sol = solve_ivp(sir, [0, 100], [999, 1, 0], t_eval=np.linspace(0, 100, 200))
print(sol.y.T[-1])                               # 终态
# 改步长/换方法(rk45→BDF)验证收敛性是必做检验
```

## 8. 智能算法（全局寻优，先试现成的）

```python
from scipy.optimize import differential_evolution
import numpy as np
f = lambda x: np.sum((x - 3)**2)                # 多峰值/非凸目标
res = differential_evolution(f, bounds=[(-10, 10)]*2, seed=0)
print('全局最优', res.x, res.fun)
# 复杂问题再自写 GA/PSO/SA：编码 → 适应度 → 选择/交叉/变异 → 收敛曲线，并多跑取均值+方差
```

## 9. 蒙特卡洛仿真（随机/风险题）

```python
import numpy as np
rng = np.random.default_rng(0)
N = 100000
X = rng.normal(0, 1, (N, 2))                    # 随机输入
Y = np.sin(X[:, 0]) + X[:, 1]**2                # 模型输出
print('均值', Y.mean(), '置信区间', np.percentile(Y, [2.5, 97.5]))
# 改分布参数做敏感性，是必做检验
```

## 10. 机器学习（分类 / 回归 / 聚类，含交叉验证）

```python
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split, cross_val_score
import numpy as np
X = np.random.rand(200, 4); y = np.random.rand(200)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0)
rf = RandomForestRegressor(n_estimators=100, random_state=0).fit(Xtr, ytr)
print('R² =', rf.score(Xte, yte))               # 回归报 MAE/RMSE/R²
print('交叉验证', cross_val_score(rf, X, y, cv=5).mean())   # 防过拟合
km = KMeans(n_clusters=3, random_state=0, n_init=10).fit(X) # 聚类
print(km.labels_)
# 特征重要性 rf.feature_importances_，做可解释性
```

## 11. 按组切分防泄露（GroupKFold）

```python
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.ensemble import RandomForestRegressor
import numpy as np
X = np.random.rand(200, 4); y = np.random.rand(200)
groups = np.repeat(np.arange(20), 10)        # 每行归属的"组"（同一用户/同一赛事/同一地区）
gkf = GroupKFold(n_splits=5)
rf = RandomForestRegressor(n_estimators=100, random_state=0, n_jobs=1)
# 同一组不会同时出现在训练折与验证折 -> 杜绝组间信息泄露（P17）
scores = cross_val_score(rf, X, y, cv=gkf.split(X, y, groups))
print('GroupKFold CV R²:', round(scores.mean(), 3))
```
> 纵向/面板/同一主体有多条记录时**必用**：按行随机切分会让同组样本泄漏到测试集，指标虚高。详见 `pitfalls-cookbook.md` P17。

## 12. 混合效应 / 纵向模型（GAMM，statsmodels）

```python
import statsmodels.formula.api as smf
import pandas as pd, numpy as np
rng = np.random.default_rng(0)
n_sub, n_rep = 30, 5
subj = np.repeat(np.arange(n_sub), n_rep)        # 重复测量个体
time = np.tile(np.arange(n_rep), n_sub)
re   = rng.normal(0, 0.5, n_sub)                  # 个体随机效应
y = 1.0*time + re[subj] + rng.normal(0, 0.2, n_sub*n_rep)
df = pd.DataFrame({'y': y, 'time': time, 'subj': subj})
# 随机截距模型：纵向/面板数据的标配，控制个体异质性
m = smf.mixedlm('y ~ time', df, groups=df['subj'])
res = m.fit()
print(res.summary().tables[1])                    # 看 time 的固定效应与显著性
```
> 同类个体重复观测（多期/多场次）别用普通 OLS——个体异质性会污染估计。随机截距/斜率是美赛 E/F、国赛 longitudinal 题的加分项。

## 13. 概率校准（分类器别只看准确率）

```python
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import numpy as np
X = np.random.rand(400, 4); y = (X[:,0] + X[:,1] > 1).astype(int)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0)
clf = LogisticRegression().fit(Xtr, ytr)
prob = clf.predict_proba(Xte)[:,1]
# 校准曲线：预测概率 vs 实际频率，越贴近 y=x 越好
frac_pos, mean_pred = calibration_curve(yte, prob, n_bins=10)
print('未校准 Brier 近似:', round(((prob - yte)**2).mean(), 4))
cal = CalibratedClassifierCV(clf, cv=3, method='isotonic').fit(Xtr, ytr)
prob_c = cal.predict_proba(Xte)[:,1]
print('校准后 Brier 近似:', round(((prob_c - yte)**2).mean(), 4))
```
> 评委要的是"概率可信"而非"点分类对"。给出预测概率时务必画校准曲线或报 Brier 分数（见 `advanced-methods-templates.md` §5 贝叶斯对照）。

## 14. 相关性热力图 / 分面图（matplotlib，交稿前 figcheck）

```python
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
rng = np.random.default_rng(0)
# 相关性热力图
M = rng.normal(0, 1, (6, 6)); M = np.corrcoef(M)
fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(M, cmap='coolwarm', vmin=-1, vmax=1)
ax.set_xticks(range(6)); ax.set_yticks(range(6))
fig.colorbar(im, ax=ax, fraction=0.046)
fig.savefig('heatmap.png', dpi=300, bbox_inches='tight')   # dpi 必须≥300 过 figcheck
# 分面图（按组别画子图）
fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
for i, ax in enumerate(axes):
    ax.hist(rng.normal(i, 1, 200), bins=20); ax.set_title(f'Group {i}')
fig.tight_layout(); fig.savefig('facets.png', dpi=300, bbox_inches='tight')
print('已输出 heatmap.png / facets.png (dpi=300)')
```
> 凡画图一律 `dpi=300` + `bbox_inches='tight'` 过 `scripts/figcheck.py`；图注独立可读、正文必须引用（见 `bao-paper-writing.md` 图表三件套）。
>
> **图要更好看 / 全项目统一风格**：文件头 `import plot_style as ps; ps.apply_style()`（`scripts/plot_style.py`，含配色/中文字体探测/300dpi 导出），完整美化规范见 `figure-polish.md`（配色/字号/图类型决策/出彩细节/难看反模式）。

> 抄完先确认「数值对得上、种子固定、结果可复现」，这是评审硬标准；每段代码的检验步骤（灵敏度/误差/交叉验证）不要省。**数值进论文前先过 `scripts/sanity_check.py` 做量纲/量级/边界校验**（权重和=1、概率∈[0,1] 等），高级统计/因果/优化题型再接 `advanced-methods-templates.md`（DiD、Sobol、MCMC、CVaR、MILP、GAMM 纵向建模、pvlib）。