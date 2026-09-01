# 真题演练示例：长江水质综合评价与预测（教学经典题）

> 目的：给你一份「照着做」的完整对照，走完 skill 的七步。所有数值均为**占位示例**，真正比赛时用官方数据替换；代码骨架可直接套用。

## 1. 问题重述（简要，依公开题面改述）

- 已知若干观测站点、若干水质指标（溶解氧、高锰酸盐指数、氨氮、pH 等）的时间序列。
- 问 1：对各站点水质做综合评价与分级；
- 问 2：对未来 1–2 年污染趋势做预测。

## 2. 问题分析

- 问 1 → 综合评价题：多个指标、多个对象，需「定权 + 集结」。
- 问 2 → 预测题：年度 / 月度序列、样本点不多 → 灰色 GM(1,1) 或指数平滑。

## 3. 模型假设

- 假设各站点指标统计口径一致、无系统性缺失（缺失用均值 / 插值补齐并说明）。
- 假设短期内水文条件平稳，历史趋势可外推（若放松，预测需引入季节性 / 突变项）。
- 假设指标间相关性用熵权处理即可（若强相关，先用 PCA 去冗余）。

## 4. 符号约定（节选）

| 符号 | 含义 |
|---|---|
| n, m | 评价对象数、指标数 |
| x_ij | 第 i 对象第 j 指标原始值 |
| z_ij | 标准化后的值 |
| w_j | 第 j 指标权重（熵权法） |
| y(k) | 时间序列第 k 期 |

## 5. 建模与求解（Python 可运行骨架）

### 问 1：熵权法 + TOPSIS 综合评价

```python
import numpy as np
import pandas as pd

# ===== 1. 原始数据：n 个站点 × m 个指标（用官方数据替换）=====
# 约定：列已处理成正向指标；负向/区间型先转正向
df = pd.read_csv("data/water_quality.csv", index_col=0)  # 行为站点
Z = df.to_numpy()
n, m = Z.shape

# ===== 2. 极差标准化（正向指标）=====
Z_norm = (Z - Z.min(axis=0)) / (Z.max(axis=0) - Z.min(axis=0) + 1e-12)

# ===== 3. 熵权法确定权重 =====
P = Z_norm / Z_norm.sum(axis=0)              # 比重
k = 1.0 / np.log(n)
e = -k * (P * np.log(P + 1e-12)).sum(axis=0) # 信息熵
d = 1 - e                                     # 差异系数
w = d / d.sum()                               # 权重
print("权重 w =", np.round(w, 4))

# ===== 4. TOPSIS 求贴近度 =====
Pv = Z_norm * w                               # 加权标准化
best  = Pv.max(axis=0); worst = Pv.min(axis=0)
Dp = np.sqrt(((Pv - best)  ** 2).sum(axis=1))
Dn = np.sqrt(((Pv - worst) ** 2).sum(axis=1))
C = Dn / (Dp + Dn)                            # 贴近度 C∈[0,1]，越大越优
rank = pd.Series(C, index=df.index).sort_values(ascending=False)
print(rank.round(4))  # 各站点排序（示例输出，非真实结果）
```

### 问 2：灰色 GM(1,1) 预测

```python
import numpy as np

def gm11(x0: np.ndarray, predict_n: int):
    """x0: 非负原始序列（长度≥4）；predict_n: 预测期数"""
    x0 = np.asarray(x0, dtype=float)
    # 级比检验（理想区间近似 e^(-2/(k+1)) ~ e^(2/(k+1))）
    lb, ub = np.exp(-2/(len(x0)+1)), np.exp(2/(len(x0)+1))
    ratio = x0[1:] / x0[:-1]
    if not ((ratio > lb).all() and (ratio < ub).all()):
        print("提示：级比检验未通过，可做平移变换 x0+k")
    x1 = x0.cumsum()                                   # 1-AGO
    B = np.column_stack([-0.5*(x1[1:] + x1[:-1]), np.ones(len(x1)-1)])
    Y = x0[1:]
    a, b = np.linalg.lstsq(B, Y, rcond=None)[0]        # 发展系数 a、灰作用量 b
    def pred(k):  # 还原到原始序列（k 从 0 计）
        return (x0[0] - b/a) * (1 - np.exp(a)) * np.exp(-a*k)
    fit = np.array([pred(k) for k in range(len(x0))])  # 回代拟合
    mape = np.mean(np.abs(fit - x0) / (x0 + 1e-12)) * 100
    print(f"a={a:.4f}, b={b:.4f}, 拟合 MAPE={mape:.2f}%")  # 示例指标
    return np.array([pred(len(x0)-1 + t) for t in range(1, predict_n+1)])

seq = np.array([6.1, 6.3, 6.6, 7.0, 7.5])   # 占位示例，替换为官方某指标序列
print("未来预测值 =", np.round(gm11(seq, 2), 2))  # 示例输出
```

## 6. 模型检验

- 灵敏度（问 1）：把每个指标权重 ±10%，重算贴近度排序，观察前几名是否变化（对比表或 Spearman 相关）。
- 误差（问 2）：留出最后 1–2 期不回代，用前段建模预测后段，算 MAPE / 相对误差。
- 稳定性：换一种定权（AHP 主观）或换一种预测（指数平滑）对比结论是否一致。

## 7. 论文骨架（照 `paper-skeleton.md` 填）

- 摘要：用了熵权法 + TOPSIS 给出站点水质排序；用 GM(1,1) 预测未来两年趋势，拟合 MAPE 约 X%……
- 五、模型建立与求解：问 1（熵权 + TOPSIS）、问 2（GM(1,1)）各一小节，贴上面代码 + 结果表。
- 六、模型检验：权重扰动结果 + 预测回测。

## 学完这道题，你会复用的三件事

1. 熵权 + TOPSIS 是**评价题通用配方**，几乎每年都有。
2. GM(1,1) 是**小样本预测首选**，任何"预测"题先试它。
3. 「权重扰动 + 留出验证」是**检验环节的标准动作**。