#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""科研图表一键美化（依赖 matplotlib；不同于 scripts/ 下零依赖的校验脚本）。

用途：全项目统一风格，避免"一图一风格"。用法：

    import plot_style as ps
    ps.apply_style()                 # 幂等：设 rcParams + 探测本机中文字体
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=ps.FULL_W)   # 通栏 / HALF_W 半栏
    ... 画图 ...
    ps.save_fig(fig, 'res_q1.png')   # 300dpi + bbox_inches='tight'

配色 / 尺寸 / 字号常量统一维护在本文件头，改一处全项目生效。
正交套件见 references/figure-polish.md、figures-and-abstract.md、code-templates.md §14。
"""
from __future__ import annotations

_MPL = None  # matplotlib 惰性加载：让 --help / import 在缺库时仍可用


def _mpl():
    """惰性导入 matplotlib；仅在真正画图/设样式时触发，缺库给明确报错。"""
    global _MPL
    if _MPL is None:
        try:
            import matplotlib as mpl
            import matplotlib.pyplot as plt
            from matplotlib import font_manager
            _MPL = (mpl, plt, font_manager)
        except ImportError as e:  # pragma: no cover
            raise ImportError("plot_style 需要 matplotlib：pip install matplotlib") from e
    return _MPL

# ── 配色（Okabe-Ito 色盲安全 8 色 + 强调色 + 灰）──────────────────────────
COLORS = ["#E69F00", "#56B4E9", "#009E73", "#F0E442",
          "#0072B2", "#D55E00", "#CC79A7", "#000000"]
ACCENT = "#D55E00"      # 强调色（朱红，给"结论指向"的那条曲线/柱）
GRAY = "#7F7F7F"        # 辅助线 / 次要序列
SEQ_CMAP = "viridis"    # 顺序色（数值低→高）
DIV_CMAP = "RdBu_r"     # 发散色（有零点，如相关 -1..1）

# ── 图尺寸（英寸；国赛 A4 单栏，1:1 嵌入不缩放）──────────────────────────
FULL_W = (6.0, 3.7)     # 通栏（占满一行）
HALF_W = (3.1, 2.3)     # 半栏（一行两图并排）
WIDE = (6.3, 4.5)       # 全景大图 / 建模总流程图

# 中文字体候选（跨平台，按命中顺序取第一个；找不到就不启中文，改英文标签）
_CJK_CANDIDATES = [
    "SimHei", "Microsoft YaHei", "Microsoft JhengHei",
    "Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC",
    "WenQuanYi Zen Hei", "WenQuanYi Micro Hei",
    "PingFang SC", "Hiragino Sans GB", "Arial Unicode MS", "Heiti SC",
]


def find_cjk_font():
    """返回本机可用的第一个中文字体名；找不到返回 None（图用英文标签即可）。"""
    _, _, font_manager = _mpl()
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in _CJK_CANDIDATES:
        if name in installed:
            return name
    return None


def apply_style(font_scale: float = 1.0):
    """一键设风格（幂等，可重复调用）。先探测中文字体，再统一 rcParams。

    返回命中的中文字体名（或 None）。字号统一 8–10pt，配合图 1:1 嵌入，
    评委在 PDF 里看到的字号就是这里设的字号——不要用 14pt 再缩放成蚂蚁字。
    """
    mpl, _, _ = _mpl()
    mpl.rcParams.update({
        'font.sans-serif': _CJK_CANDIDATES + ['DejaVu Sans'],
        'axes.unicode_minus': False,          # 负号不显示成豆腐块 □
        'font.size': 9 * font_scale,
        'axes.titlesize': 10 * font_scale,
        'axes.labelsize': 9 * font_scale,
        'xtick.labelsize': 8 * font_scale,
        'ytick.labelsize': 8 * font_scale,
        'legend.fontsize': 8 * font_scale,
        'figure.dpi': 110,
        'savefig.dpi': 300,
        'axes.linewidth': 0.7,
        'lines.linewidth': 1.6,
        'axes.grid': True,
        'grid.alpha': 0.28,
        'grid.linestyle': '--',
        'grid.linewidth': 0.5,
        'legend.frameon': False,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'axes.spines.top': False,             # matplotlib>=3.5 支持
        'axes.spines.right': False,
    })
    cjk = find_cjk_font()
    if cjk:
        # 探测命中则优先用一个确定可用的字体，避免回退时部分缺字
        mpl.rcParams['font.sans-serif'] = [cjk] + list(mpl.rcParams['font.sans-serif'])
    return cjk


def save_fig(fig, path, dpi: int = 300):
    """统一导出：默认 300dpi + 去白边。扩展名决定格式（png 光栅 / pdf|svg 矢量）。"""
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    print(f"[plot_style] 已导出 {path} (dpi={dpi})")
    return path


def demo():
    """三张抢分图的成品范式：拟合vs实测 / 灵敏度龙卷风 / 方法对比。

    仅作演示：图内 set_title 是为了本 demo 自明；真实交付图**去掉图内标题**，
    标题留给论文题注（三件套，见 figures-and-abstract.md §3）。
    """
    import numpy as np
    _, plt, _ = _mpl()
    apply_style()
    rng = np.random.default_rng(0)

    # 1) 拟合 vs 实测 + 误差带
    x = np.linspace(0, 10, 30)
    y_obs = 2.3 * x + 1.1 + rng.normal(0, 1.2, x.size)
    k, b = np.polyfit(x, y_obs, 1)
    y_fit = k * x + b
    fig, ax = plt.subplots(figsize=FULL_W)
    ax.plot(x, y_fit, color=ACCENT, lw=2.2, label='拟合')
    ax.fill_between(x, y_fit - 1.2, y_fit + 1.2, color=ACCENT, alpha=0.15, label='误差带')
    ax.scatter(x, y_obs, s=24, color=COLORS[0], zorder=3, label='实测')
    ax.set_xlabel('x'); ax.set_ylabel('y'); ax.legend()
    ax.set_title('拟合 vs 实测（含置信带）')
    save_fig(fig, 'demo_fit.png')

    # 2) 灵敏度龙卷风（正/负影响用不同色）
    names = ['参数 a', '参数 b', '参数 c', '参数 d']
    vals = [-3.1, 2.4, -1.2, 0.8]
    fig, ax = plt.subplots(figsize=FULL_W)
    colors = [COLORS[2] if v >= 0 else COLORS[5] for v in vals]
    ax.barh(names, vals, color=colors)
    ax.axvline(0, color=GRAY, lw=0.8)
    ax.set_xlabel('结果变化量'); ax.set_title('灵敏度（龙卷风图）')
    save_fig(fig, 'demo_tornado.png')

    # 3) 方法对比（柱状 + 误差棒 + 数值标签；柱高从 0 起）
    models = ['GM(1,1)', 'ARIMA', 'LSTM', '本文模型']
    mape = [12.4, 8.1, 6.4, 5.9]
    err = [1.1, 0.8, 0.6, 0.5]
    fig, ax = plt.subplots(figsize=FULL_W)
    bars = ax.bar(models, mape, yerr=err, capsize=3,
                  color=COLORS[:4], edgecolor='black', linewidth=0.4)
    ax.bar_label(bars, labels=[f'{v}%' for v in mape], padding=2, fontsize=8)
    ax.set_ylabel('MAPE (%)'); ax.set_title('各模型预测误差对比（越低越好）')
    save_fig(fig, 'demo_compare.png')


if __name__ == '__main__':
    import argparse
    _ap = argparse.ArgumentParser(description="论文图规范样式: 默认输出默认品配色/字号/DPI 常量; 加 --demo 生成示例图")
    _ap.add_argument("--demo", action="store_true", help="在当前目录生成 3 张示例图(demo_fit/tornado/compare)")
    _a = _ap.parse_args()
    if _a.demo:
        demo()
    else:
        print("本脚本是 matplotlib 样式库, 供 import 使用。加 `--demo` 生成示例图; `--help` 查看说明。")