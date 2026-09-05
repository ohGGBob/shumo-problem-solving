#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据洞察挖掘（insight_miner.py）——从数据里自动挖"可写进论文的候选发现"。

C 题（数据题）国一 vs 国二的差距常在数据挖掘深度：反直觉发现、隐藏结构、可解释规律。
本脚本把"挖发现"变成半自动：跑一遍出候选清单，人/AI 再判断哪个"反直觉且可解释"。

    python insight_miner.py 数据.xlsx [--target 目标列] [--top 10]
    python insight_miner.py 数据目录/ --target 价格 --top 15

输出候选发现（每条带数据来源，铁律四·数字必有出处）：
  1. 强相关特征对（|r|≥0.7，数值列）
  2. 偏态列（|skew|>1 → 提示 log 变换或分布假设）
  3. 类别列对 target 的分组差异 top（均值差大 → 业务含义候选）
  4. 时间趋势（检测日期列 → 首尾均值变化）
  5. 异常值占比（IQR 1.5×，>1% 提示检查）
  6. 高缺失列（≥20%，衔接 data_profiler）

配套手册见 references/data-storytelling.md（发现→证据→图→论文落点的四要素格式）。
"""
import argparse
import os
import re
import sys

try:
    import pandas as pd
    import numpy as np
except ImportError:  # pragma: no cover
    print("[err] 需要 pandas/numpy：python -m pip install pandas numpy", file=sys.stderr)
    sys.exit(2)

_TARGET_HINT = re.compile(r"(价格|销量|成本|利润|需求|供应|产量|评分|收入|支出|target|price|sales|cost|profit|demand|supply|score)", re.I)
_DATE_HINT = re.compile(r"(日期|时间|date|time|年月|month|year|day)", re.I)


def _console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass


def _load(path):
    """读取单文件，返回 (name, df)。"""
    if path.lower().endswith(".csv"):
        return os.path.basename(path), pd.read_csv(path)
    return os.path.basename(path), pd.read_excel(path, sheet_name=None) if path.lower().endswith((".xlsx", ".xls")) else None


def _num_cols(df):
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _cat_cols(df, max_card=12):
    out = []
    for c in df.columns:
        try:
            dt = df[c].dtype
            if (pd.api.types.is_object_dtype(dt) or pd.api.types.is_string_dtype(dt)
                    or isinstance(dt, pd.CategoricalDtype)):
                if df[c].nunique(dropna=True) <= max_card:
                    out.append(c)
        except Exception:
            pass
    return out


def _date_cols(df):
    out = []
    for c in df.columns:
        if _DATE_HINT.search(str(c)):
            try:
                s = pd.to_datetime(df[c], errors="coerce")
                if s.notna().mean() > 0.8:
                    out.append((c, s))
            except Exception:
                pass
    return out


def mine(df, name, target=None, top=10):
    out = []
    n_row = len(df)
    num_cols = _num_cols(df)
    cat_cols = _cat_cols(df)

    # 0) 基础信息
    out.append(f"【{name}】{n_row} 行 × {len(df.columns)} 列 | 数值列 {len(num_cols)} | 类别列 {len(cat_cols)}")

    # 1) 强相关对
    if len(num_cols) >= 2:
        try:
            corr = df[num_cols].corr()
            pairs = []
            for i, a in enumerate(num_cols):
                for b in num_cols[i + 1:]:
                    r = corr.loc[a, b]
                    if pd.notna(r) and abs(r) >= 0.7:
                        pairs.append((abs(r), a, b, r))
            pairs.sort(reverse=True)
            for _, a, b, r in pairs[:top]:
                out.append(f"  [强相关] {a} ↔ {b}  r={r:.3f} → 论文落点：共线性说明/特征选择依据/可写'协同关系'")
        except Exception:
            pass

    # 2) 偏态列
    for c in num_cols:
        try:
            sk = df[c].skew()
            if pd.notna(sk) and abs(sk) > 1:
                out.append(f"  [偏态] {c}  skew={sk:.2f} → 提示：log 变换 / 分布假设（论文可写'数据呈右偏，故取对数'）")
        except Exception:
            pass

    # 3) 分组差异（需 target 或自动挑一个数值目标）
    tgt = target or _pick_target(df, num_cols)
    if tgt and cat_cols:
        try:
            g = df.groupby(tgt).mean(numeric_only=True) if tgt not in cat_cols else None
            rows = []
            for c in cat_cols:
                try:
                    grp = df.groupby(c)[tgt].mean()
                    if grp.nunique() >= 2:
                        diff = grp.max() - grp.min()
                        rows.append((diff, c, grp.idxmax(), grp.max(), grp.idxmin(), grp.min()))
                except Exception:
                    pass
            rows.sort(reverse=True)
            for diff, c, hi, hv, lo, lv in rows[:top]:
                out.append(f"  [分组差异] 按 {c} 分组，{tgt} 最高组={hi}({hv:.3g}) vs 最低组={lo}({lv:.3g})，差 {diff:.3g} → 论文落点：业务可解释规律（为什么高/低）")
        except Exception:
            pass

    # 4) 时间趋势
    for c, s in _date_cols(df)[:1]:
        try:
            s2 = s.dt.to_period("M") if s.dt.day.nunique() > 3 else s.dt.to_period("D")
            if tgt and tgt in num_cols:
                ts = pd.Series(df[tgt].values, index=s).sort_index()
                first, last = ts.iloc[:3].mean(), ts.iloc[-3:].mean()
                chg = (last - first) / first * 100 if first else float("nan")
                out.append(f"  [时间趋势] {c} 上 {tgt}：早期均值 {first:.3g} → 末期均值 {last:.3g}（变化 {chg:+.1f}%）→ 论文落点：时间拐点/趋势段划分")
        except Exception:
            pass

    # 5) 异常值占比
    for c in num_cols:
        try:
            q1, q3 = df[c].quantile(0.25), df[c].quantile(0.75)
            iqr = q3 - q1
            if iqr and pd.notna(iqr) and iqr > 0:
                frac = ((df[c] < q1 - 1.5 * iqr) | (df[c] > q3 + 1.5 * iqr)).mean()
                if frac > 0.01:
                    out.append(f"  [异常值] {c} 超 IQR 1.5× 占比 {frac:.1%} → 论文落点：异常点识别/稳健性处理（Winsorize 或单独讨论）")
        except Exception:
            pass

    # 6) 高缺失列
    for c in df.columns:
        miss = df[c].isna().mean()
        if miss >= 0.2:
            out.append(f"  [高缺失] {c} 缺失 {miss:.0%} → 论文落点：缺失机制讨论 + 填补方案（衔接 data_profiler）")

    if len(out) == 1:
        out.append("  （未挖到明显候选——数据太干净或全为类别列；换 --target 或先跑 data_profiler 看结构）")
    return "\n".join(out)


def _pick_target(df, num_cols):
    """自动挑一个数值目标列：优先命中目标名关键词，否则取方差最大的数值列。"""
    for c in num_cols:
        if _TARGET_HINT.search(str(c)):
            return c
    if num_cols:
        try:
            return max(num_cols, key=lambda c: df[c].var() if df[c].nunique() > 2 else -1)
        except Exception:
            return num_cols[0]
    return None


def main():
    _console()
    ap = argparse.ArgumentParser(description="数据洞察挖掘（候选发现清单，每条带来源）")
    ap.add_argument("target", help="xlsx/csv 文件或目录")
    ap.add_argument("--target", dest="tgt", default="", help="数值目标列（不填则自动挑）")
    ap.add_argument("--top", type=int, default=10, help="每类最多列出的条数（默认 10）")
    args = ap.parse_args()

    files = []
    if os.path.isdir(args.target):
        for p in sorted(os.listdir(args.target)):
            if p.lower().endswith((".xlsx", ".xls", ".csv")):
                files.append(os.path.join(args.target, p))
    else:
        files = [args.target]

    if not files:
        print("[err] 没有可读的数据文件", file=sys.stderr)
        return 2

    any_out = False
    for p in files:
        try:
            loaded = _load(p)
        except Exception as e:
            print(f"[err] 读取 {os.path.basename(p)} 失败: {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            continue
        name, df = loaded
        if isinstance(df, dict):
            for sheet, sdf in df.items():
                print(mine(sdf, f"{os.path.basename(p)}::{sheet}", args.tgt or None, args.top))
                print()
                any_out = True
        else:
            print(mine(df, name, args.tgt or None, args.top))
            print()
            any_out = True

    if not any_out:
        print("[err] 没有匹配的表格", file=sys.stderr)
        return 2
    print("> 候选发现供人/AI 筛选：挑'反直觉且可解释'的 3–5 条深化，每条按'发现→证据→图→论文落点'四要素写进论文（references/data-storytelling.md）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
