#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论文数字对账：找出论文里、但不在 results.json 中的"野数字"。

用法:
    python check_results.py <论文.md|论文.tex|论文.docx> [--json out/results.json] [--tol 0.01]

原理:
    论文里出现的数字（百分比、小数、带单位数、整数、区间端点），凡不能在
    results.json 中找到"数值上一致"的对应项，就标为待核对——它可能是手抄、
    凭记忆、或来自未落盘的探索脚本（违反"数值单一来源"铁律）。

说明:
    - 只做"存在性"核对，不做语义核对；百分比会自动与小数互转比较(50% vs 0.5)。
    - 容忍误差 --tol（相对误差），默认 1%。
    - 区间端点(1.2~3.4)拆成两个数分别核对。
"""
import argparse
import json
import os
import re
import sys
import glob


def read_text(path):
    if path.lower().endswith(".docx"):
        try:
            import zipfile
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8", "ignore")
            return re.sub(r"<[^>]+>", " ", xml)
        except Exception as e:  # noqa
            print(f"[warn] 无法读 docx(需 python-docx 或手动导出文本): {e}", file=sys.stderr)
            return ""
    with open(path, encoding="utf-8-sig", errors="ignore") as f:
        return f.read()


def extract_numbers(text):
    """提取文本里的"实义数字"：整数/小数/科学计数/百分比/带千分位/区间端点（含负数）。

    修复说明（v1.4.1）：
    - 支持负数（-1.599 不再被提取成 1.599 导致对账误报）；
    - 百分比先单独提取并原位替换为空格，杜绝 "6.2%" 被普通数正则回退拆成 6 的重复/误报；
    - 普通数用原子组 (?>...) 锁定小数整体，避免小数后跟 % 时被拆出整数部分。
    """
    nums = []

    def eat_percent(m):
        nums.append(float(m.group(1)) / 100.0)
        return " " * len(m.group(0))

    # 百分比（先处理并原位占位，普通数正则不再重复提取）
    text = re.sub(r"(-?\d+(?:\.\d+)?)\s*%", eat_percent, text)
    # 科学计数
    for m in re.finditer(r"(-?\d+(?:\.\d+)?)(?:[eE][+-]?\d+)", text):
        nums.append(float(m.group(1) + m.group(0)[len(m.group(1)):]))
    # 普通数（带千分位 / 小数 / 整数，负号跟随数字），排除纯序号如 [1] 引用与年份疑似
    for m in re.finditer(r"(?<![\w.])(-?(?>(?:\d{1,3}(?:,\d{3})+|\d+\.\d+|\d+)))(?![\w%])", text):
        raw = m.group(1).replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            continue
        # 跳过像 2025/2026 这种疑似年份（>1950 且 <2100 的 4 位整数）
        if v.is_integer() and 1950 < v < 2100:
            continue
        nums.append(v)
    return nums


def load_json_numbers(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    out = []
    flat = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, (int, float)):
            flat.append(float(o))

    walk(data)
    # 也允许 json 顶层是数字列表
    if isinstance(data, list):
        for v in data:
            if isinstance(v, (int, float)):
                flat.append(float(v))
    return flat


def matches(value, ref_list, tol):
    for r in ref_list:
        if r == 0:
            if abs(value) < 1e-9:
                return True
            continue
        if abs(value - r) / max(abs(r), 1e-9) <= tol:
            return True
        # 百分比↔小数互转
        if abs(value - r * 100) / max(abs(r * 100), 1e-9) <= tol:
            return True
        if abs(value * 100 - r) / max(abs(r), 1e-9) <= tol:
            return True
    return False


def main():
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="论文数字 vs results.json 对账")
    ap.add_argument("paper", help="论文 .md/.tex/.docx")
    ap.add_argument("--json", default=None, help="results.json 路径；默认依次查 上级 out/、同级 out/（init_project 骨架）")
    ap.add_argument("--tol", type=float, default=0.01, help="相对误差容忍，默认 0.01")
    args = ap.parse_args()

    if not os.path.exists(args.paper):
        print(f"[err] 论文不存在: {args.paper}", file=sys.stderr)
        return 1

    paper_text = read_text(args.paper)
    # 去掉参考文献段，避免卷期/页码被误判为野数字
    ref_idx = -1
    for kw in ["参考文献", "References", "REFERENCES", "引用文献"]:
        m = re.search(rf"^#*\s*{kw}\s*$", paper_text, re.MULTILINE)
        if m:
            ref_idx = m.start()
            break
    body_text = paper_text[:ref_idx] if ref_idx >= 0 else paper_text
    # 去掉正文引用键 [1] [2-4]，它们不是结果数字
    body_text = re.sub(r"\[\d+(?:[-,]\d+)*\]", " ", body_text)
    paper_nums = extract_numbers(body_text)

    if args.json:
        jpath = args.json
    else:
        # init_project.py 骨架：<项目>/report/main.tex 配 <项目>/out/results.json（上级 out/）
        base = os.path.abspath(args.paper)
        cands = [
            os.path.join(os.path.dirname(os.path.dirname(base)), "out", "results.json"),
            os.path.join(os.path.dirname(base), "out", "results.json"),
        ]
        jpath = next((c for c in cands if os.path.exists(c)), None)

    ref = load_json_numbers(jpath) if jpath else None
    if ref is None:
        print(f"[warn] 未找到 results.json，仅统计论文数字分布（无对账）。路径: {jpath}", file=sys.stderr)

    print(f"论文数字（去重）: {len(set(round(n,6) for n in paper_nums))} 个")

    if ref is None:
        from collections import Counter
        c = Counter(round(n, 4) for n in paper_nums)
        print("出现最多的数字（核对是否有未落盘的关键值）:")
        for v, k in c.most_common(15):
            print(f"   {v}: {k} 次")
        return 0

    print(f"results.json 数字: {len(ref)} 个")
    wild = sorted({round(n, 6) for n in paper_nums if not matches(n, ref, args.tol)})
    print(f"\n[对账] 论文中存在、但 results.json 找不到对应项的数字（共 {len(wild)} 个）:")
    if not wild:
        print("   ✓ 全部命中，数值单一来源核对通过。")
    else:
        for v in wild[:60]:
            print(f"   ! {v}")
        if len(wild) > 60:
            print(f"   ... 其余 {len(wild)-60} 个略")
        print("\n处理建议: 这些数字要么补进 export_results.py 重新落盘，要么确认来自题面/文献（在文内标注来源）。")
    return 1 if wild else 0


if __name__ == "__main__":
    raise SystemExit(main())
