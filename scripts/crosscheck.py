#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨文件数字一致性核对（国一冲刺包 #2）。

国一论文"表述清晰"评分的硬伤高发区，不在建模，而在"同一个数字各写各的"：
摘要写 19.43、正文写 19.4、结论写 19.5——评委一眼看穿不严谨。本脚本一次性找出。

用法:
    python crosscheck.py <论文.md|.tex|.docx> [--json out/results.json] [--tol 0.02]

检查项:
    1. 摘要 / 正文分段提取数字，摘要里的数字必须在全文有同值支撑（摘要不可有孤立数字）；
    2. "近似但不同"数值共存检测：全文同时出现 19.43 与 19.5（容差内不同值）→ 疑似同一指标两种写法，提示核对；
    3. 每个数字的出现上下文片段输出，供人工快速扫一致性；
    4. 摘要四要素检测（问题/方法/结果/结论 + 至少 3 个数字），配合质量三支柱摘要要求。

仅标准库（Python 3.8+）；只做本地结构化检查，联网动作由人/AI 完成。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys


def read_text(path):
    if path.lower().endswith(".docx"):
        try:
            import zipfile
            with zipfile.ZipFile(path) as z:
                return re.sub(r"<[^>]+>", " ", z.read("word/document.xml").decode("utf-8", "ignore"))
        except Exception as e:  # noqa
            print(f"[warn] docx 读取失败: {e}", file=sys.stderr)
            return ""
    with open(path, encoding="utf-8-sig", errors="ignore") as f:
        return f.read()


def extract_numbers(text):
    """与 check_results.py 同款：含负数、百分比→小数、原子组防拆。"""
    nums = []

    def eat_percent(m):
        nums.append(float(m.group(1)) / 100.0)
        return " " * len(m.group(0))

    text = re.sub(r"(-?\d+(?:\.\d+)?)\s*%", eat_percent, text)
    for m in re.finditer(r"(-?\d+(?:\.\d+)?)(?:[eE][+-]?\d+)", text):
        nums.append(float(m.group(1) + m.group(0)[len(m.group(1)):]))
    for m in re.finditer(r"(?<![\w.])(-?(?>(?:\d{1,3}(?:,\d{3})+|\d+\.\d+|\d+)))(?![\w%])", text):
        raw = m.group(1).replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            continue
        if v.is_integer() and 1950 < v < 2100:
            continue
        nums.append(v)
    return nums


def split_sections(text):
    """粗分 摘要 与 正文：找到摘要区段（'摘要'/'Abstract' 到下一标题），其余为正文。"""
    m = re.search(r"^#*\s*(摘要|Abstract)\s*$", text, re.MULTILINE)
    if not m:
        return "", text
    start = m.end()
    nxt = re.search(r"^#+\s+\S", text[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(text)
    return text[start:end], text[:start] + text[end:]


def hit_counts(nums):
    from collections import Counter
    return Counter(round(n, 4) for n in nums)


def main():
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="跨文件数字一致性核对（国一冲刺包）")
    ap.add_argument("paper", help="论文 .md/.tex/.docx")
    ap.add_argument("--tol", type=float, default=0.02, help="近似判定容差（相对），默认 0.02")
    args = ap.parse_args()
    if not os.path.exists(args.paper):
        print(f"[err] 论文不存在: {args.paper}", file=sys.stderr)
        return 1

    text = read_text(args.paper)
    if not text.strip():
        print("[err] 论文为空或读取失败", file=sys.stderr)
        return 1
    # 剔除引用键 [1]、[1-3] 与参考文献区，避免把序号/刊期页码当数字
    text = re.sub(r"\[\d+(?:[-,]\d+)*\]", " ", text)
    ref_cut = re.search(r"^#*\s*(参考文献|References|Reference)\s*$", text, re.MULTILINE)
    if ref_cut:
        text = text[:ref_cut.start()]
    abstract, body = split_sections(text)
    abs_nums = extract_numbers(abstract)
    body_nums = extract_numbers(body)
    all_nums = extract_numbers(text)

    print(f"# 跨文件数字一致性核对: {os.path.basename(args.paper)}\n")
    print(f"（摘要数字 {len(abs_nums)} 个 · 正文数字 {len(body_nums)} 个）\n")

    issues = 0

    # ── 1. 摘要孤立数字（摘要有、全文无同值支撑）────────────
    body_set = {round(n, 4) for n in body_nums}
    orphans = sorted({round(n, 4) for n in abs_nums if not _near(round(n, 4), body_set, args.tol)})
    if orphans:
        issues += 1
        print(f"## ⚠ 摘要数字在正文/结论无同值支撑（{len(orphans)} 个）：")
        for v in orphans[:20]:
            print(f"   ! {v}  —— 摘要写了，正文/结论没出现同值，核对是否漏写或抄错")
    else:
        print("## ✓ 摘要数字在正文均有支撑。")

    # ── 2. 近似但不同 数值共存（疑似同一指标两种写法）────────
    print("\n## 近似但不同 的数值共存（疑似不一致）")
    from collections import defaultdict
    by_round = defaultdict(list)
    for v in all_nums:
        by_round[round(v, 2)].append(v)
    suspicious = []
    keys = sorted(by_round)
    for i, k in enumerate(keys):
        # 找 k 的"近邻"：|k2-k|/max(|k|) <= tol 且不是同一值
        for k2 in keys[i + 1:]:
            if k2 <= k:
                continue
            if abs(k2 - k) / max(abs(k), abs(k2), 1e-9) <= args.tol:
                suspicious.append((k, k2))
            elif k2 > k * (1 + args.tol * 4):
                break
    if suspicious:
        issues += 1
        for k, k2 in suspicious[:25]:
            print(f"   ! 同一量级两种取值: {k} vs {k2} —— 确认是不同指标还是同一指标笔误")
    else:
        print("   ✓ 未见容差内矛盾取值。")

    # ── 3. 数字上下文清单（供人工快扫）──────────────────────
    print("\n## 高频数字及上下文（人工快扫一致性）")
    from collections import Counter
    freq = Counter(round(n, 4) for n in all_nums)
    for v, c in freq.most_common(12):
        if c < 2:
            break
        # 找该值的首个出现上下文
        pat = re.escape(str(v)) if v == int(v) else re.escape(f"{v:g}")
        m = re.search(pat, text)
        ctx = text[max(0, m.start() - 12):m.end() + 12].replace("\n", " ") if m else ""
        print(f"   {v:g} ×{c}  …{ctx}…")

    # ── 4. 摘要四要素检测 ────────────────────────────────────
    print("\n## 摘要四要素（问题-方法-结果-结论 + 数值）")
    method = bool(re.search(r"(模型|方法|构建|建立|提出|采用)", abstract))
    result = bool(re.search(r"(结果|误差|率|最优|达|为|精度)", abstract))
    value_cnt = sum(1 for v in abs_nums if abs(v) > 1e-6)
    ok = method and result and value_cnt >= 3
    if not ok:
        issues += 1
    print(f"   {'✓' if method else '✗'} 方法要素（模型/方法/建立）")
    print(f"   {'✓' if result else '✗'} 结果要素（数值/误差/最优）")
    print(f"   {'✓' if value_cnt >= 3 else '✗'} 具体数值 ≥3 个（当前 {value_cnt}）")
    if not abstract.strip():
        print("   ! 未找到摘要区段（需含 '摘要' 或 'Abstract' 标题）")

    print(f"\n[crosscheck] 发现 {issues} 处需核对项。"
          + ("  数字一致性是国一'表述清晰'的硬伤区，逐条改后再交。" if issues else "  ✓ 一致性良好。"))
    return 1 if issues else 0


def _near(v, values, tol):
    for w in values:
        if abs(v - w) / max(abs(w), 1e-9) <= tol:
            return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
