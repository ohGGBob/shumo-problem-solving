#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_profiler.py —— 表格数据快速概览（Excel / CSV，C 题读数据第一件事）

用途：拿到数据附件（xlsx/csv）后，一条命令摸清所有表的结构和健康度，让 AI 在
建模前先"读懂数据"——哪些列是 ID、哪些缺值、哪些数值异常、多张表能不能关联。
比赛中手写 pd.read_excel + df.describe 快得多，也避免漏看脏数据。

依赖：pandas + openpyxl（xlsx 读取）。赛前配好：python -m pip install pandas openpyxl

用法:
    python data_profiler.py 数据.xlsx                  # 概览所有 sheet
    python data_profiler.py 数据.xlsx --sheet 供货表     # 只看指定 sheet
    python data_profiler.py 数据.csv                   # CSV（自动猜编码）
    python data_profiler.py 数据目录/                  # 批量概览目录下所有 xlsx/csv
    python data_profiler.py 数据.xlsx --head 5          # 每表多打几行样例

输出（每张表）:
    - 形状 (行 × 列)、列清单
    - 每列: 类型 / 缺失数+缺失率 / 唯一值数
    - 数值列: 均值 / 标准差 / min / max（含 max-min=0 的常量列提示）
    - 前 N 行样例
    - 疑点提示: 高缺失列、疑似 ID 列（全唯一）、常量列、异常大比例重复
    - 多表时提示同名可关联列（候选 join 键）
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    print("[err] 需要 pandas：python -m pip install pandas openpyxl", file=sys.stderr)
    sys.exit(2)

_CSV_ENC = ["utf-8-sig", "gb18030", "utf-8", "latin-1"]


def _read_csv(path):
    """自动尝试多种编码读 CSV，返回 DataFrame（带编码标注）。"""
    for enc in _CSV_ENC:
        try:
            return pd.read_csv(path, encoding=enc), enc
        except (UnicodeDecodeError, Exception):
            continue
    return pd.read_csv(path, encoding="latin-1"), "latin-1"


def _load(path):
    """按扩展名读取，返回 [(名称, DataFrame, 来源)]。"""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df, enc = _read_csv(path)
        return [(os.path.basename(path), df, f"CSV({enc})")]
    if ext in (".xlsx", ".xlsm"):
        xls = pd.ExcelFile(path)
        out = []
        for sh in xls.sheet_names:
            df = xls.parse(sh)
            out.append((sh, df, "Excel"))
        return out
    if ext == ".xls":
        df = pd.read_excel(path)
        return [(os.path.basename(path), df, "Excel(旧格式)")]
    return []


def _profile(name, df, src, head):
    lines = []
    lines.append(f"### 表「{name}」({src}) · {df.shape[0]} 行 × {df.shape[1]} 列")
    if df.shape[0] == 0:
        lines.append("  [警告] 空表（0 行）——检查是否读错 sheet/文件")
        return lines
    # 每列信息
    n_rows = max(df.shape[0], 1)
    lines.append("| 列 | 类型 | 缺失 | 缺失率 | 唯一值 | 样例 |")
    lines.append("|---|---|---|---|---|---|")
    const_cols, high_missing, id_cols = [], [], []
    for c in df.columns:
        col = df[c]
        miss = int(col.isna().sum())
        uniq = int(col.nunique(dropna=False))
        sample = str(col.dropna().iloc[0])[:24] if col.notna().any() else "(全空)"
        rate = miss / n_rows
        is_num = str(col.dtype).startswith(("float", "int"))
        lines.append(f"| {str(c)[:30]} | {str(col.dtype) if hasattr(col,'dtype') else ''} | {miss} | {rate:.0%} | {uniq} | {sample} |")
        if rate > 0.5:
            high_missing.append(str(c))
        # ID 列判定：非数值 + 全唯一（避免高精度数值列误报）
        if uniq == n_rows and n_rows > 5 and not is_num:
            id_cols.append(str(c))
    # 数值列 describe
    num = df.select_dtypes(include="number")
    num = num.dropna(axis=1, how="all")  # 全空列不进数值统计
    if len(num.columns):
        lines.append("")
        lines.append("数值列统计:")
        desc = num.describe().T
        for c in desc.index:
            if desc.loc[c, "max"] == desc.loc[c, "min"]:
                const_cols.append(str(c))
                lines.append(f"  · {str(c)[:30]}: 常量（全部 {desc.loc[c,'max']}）——建模意义有限，注意")
            else:
                lines.append(f"  · {str(c)[:30]}: 均值 {desc.loc[c,'mean']:.3g} | 标准差 {desc.loc[c,'std']:.3g} | 范围 [{desc.loc[c,'min']:.3g}, {desc.loc[c,'max']:.3g}]")
    # 疑点汇总
    warns = []
    if id_cols:
        warns.append(f"疑似 ID 列（全唯一，勿当特征）: {', '.join(id_cols[:5])}")
    if const_cols:
        warns.append(f"常量列（无信息量）: {', '.join(const_cols[:5])}")
    if high_missing:
        warns.append(f"高缺失列（>50%，需处理或剔除）: {', '.join(high_missing[:5])}")
    if warns:
        lines.append("")
        lines.append("⚠️ " + " | ".join(warns))
    # 样例行
    lines.append("")
    lines.append(f"前 {min(head, len(df))} 行样例:")
    lines.append(df.head(head).to_string(max_colwidth=18))
    return lines


def _inventory(target, tables):
    """生成数据清单（data_inventory.md）：文件/表/行列/列清单，供逐项核对无遗漏。"""
    lines = ["# 数据清单（data_inventory）", ""]
    lines.append(f"- 数据源: {target} | 表数: {len(tables)} | 生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("| # | 文件/表 | 行 | 列 | 列清单 |")
    lines.append("|---|---|---|---|---|")
    for i, (name, df, src) in enumerate(tables, 1):
        cols = ", ".join(str(c)[:20] for c in df.columns[:12])
        if len(df.columns) > 12:
            cols += "…"
        lines.append(f"| {i} | {name} | {df.shape[0]} | {df.shape[1]} | {cols} |")
    lines.append("")
    lines.append("> 用途：登记全部数据文件/表，与 data/ 目录逐项对照、确认无遗漏后再建模（铁律四·数据完整性纪律）。")
    lines.append("> 数据里没登记的附件/表 = 还没读，禁止进入建模。")
    return "\n".join(lines)


def main():
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="表格数据快速概览（Excel/CSV）")
    ap.add_argument("target", help="xlsx/csv 文件或目录")
    ap.add_argument("--sheet", default="", help="只看指定 sheet（Excel）")
    ap.add_argument("--head", type=int, default=3, help="样例行数（默认 3）")
    ap.add_argument("--inventory", action="store_true", help="只输出数据清单（文件/表/行列/列），供登记 data_inventory.md")
    ap.add_argument("--out", help="把输出写入文件（配合 --inventory 生成 data_inventory.md）")
    args = ap.parse_args()

    paths = []
    if os.path.isdir(args.target):
        for f in sorted(os.listdir(args.target)):
            if f.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv")):
                paths.append(os.path.join(args.target, f))
        if not paths:
            print(f"[err] 目录 {args.target} 下没有 xlsx/csv 文件", file=sys.stderr)
            return 2
    else:
        if not os.path.exists(args.target):
            print(f"[err] 找不到 {args.target}", file=sys.stderr)
            return 2
        paths = [args.target]

    all_tables = []
    for p in paths:
        try:
            tabs = _load(p)
        except Exception as e:
            print(f"[err] 读取 {os.path.basename(p)} 失败: {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
            return 2
        for name, df, src in tabs:
            if args.sheet and name != args.sheet:
                continue
            all_tables.append((name, df, src))

    if not all_tables:
        print("[err] 没有匹配的表格", file=sys.stderr)
        return 2

    if args.inventory:
        text = _inventory(args.target, all_tables)
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text + "\n")
            print(f"[data_profiler] 数据清单已写出 -> {args.out}")
        else:
            print(text)
        return 0

    print(f"# 数据概览 · {args.target} · 共 {len(all_tables)} 张表\n")
    for i, (name, df, src) in enumerate(all_tables, 1):
        if i > 1:
            print()
        for ln in _profile(name, df, src, args.head):
            print(ln)

    # 多表关联键提示
    if len(all_tables) > 1:
        col2tables = {}
        for name, df, _ in all_tables:
            for c in df.columns:
                col2tables.setdefault(str(c), []).append(name)
        joins = {c: ts for c, ts in col2tables.items() if len(ts) > 1}
        if joins:
            print("\n# 候选关联键（多表同名列，可尝试 join）")
            for c, ts in joins.items():
                print(f"  · {c} → 出现在: {', '.join(ts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
