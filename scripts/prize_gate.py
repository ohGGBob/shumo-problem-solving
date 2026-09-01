#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""国一冲刺计分板（国一冲刺包 #3）。交稿前一条命令，把全部校验串成一张表：
哪些过了、哪些红、还差什么。按 SKILL「交稿前自检收口」六道关组织，跑完直接看到
"这稿能不能冲国一"的客观状态，避免手忙脚乱漏项。

用法:
    python prize_gate.py <项目目录> [--paper report/main.md] [--json out/results.json] [--source 题干.txt] [--strict]

    <项目目录> 需是 init_project.py 生成的标准骨架：
        <项目>/report/main.md   <项目>/out/results.json   <项目>/data src out report

检查项（每项 = 一个 PASS/FAIL 行）:
    1. 环境体检（check_env.py）
    2. 数值对账（check_results.py）：论文数字 vs results.json
    3. 量纲/量级（sanity_check.py）：需 --json 提供规则（未给规则则只报"未配规则"）
    4. 文献核验（verify_refs.py）：孤儿/悬空 + 字段完整性
    5. 图表规范（figcheck.py）：DPI/命名/引用
    6. 降AI味/降重（dedup_scan.py）：词库密度 + 结构 + 题干比对
    7. 跨文件一致性（crosscheck.py）：摘要/正文数字是否各写各的

退出码: 0=全部通过  1=有红项（不建议交）
仅标准库；所有子校验失败也不阻断计分板输出（逐项显示 FAIL）。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys


def _console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass


def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _run(label, args, show_tail=3):
    """跑一个子校验，返回 (name, pass:bool|None)。None=跳过/无法判定。"""
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
    except Exception as e:  # noqa
        print(f"  [ERR ] {label}: 无法执行 ({e})")
        return label, False
    tail = [ln for ln in out.splitlines() if ln.strip()][-show_tail:]
    tail_txt = " | ".join(t.strip() for t in tail)
    # 以退出码为主，若子脚本意外 0 但输出明显失败则兜底
    ok = r.returncode == 0
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if tail_txt:
        print(f"         {tail_txt[:160]}")
    return label, ok


def main():
    _console()
    ap = argparse.ArgumentParser(description="国一冲刺计分板（聚合全部校验）")
    ap.add_argument("project", help="标准骨架项目目录（init_project.py 生成）")
    ap.add_argument("--paper", default=None, help="论文相对/绝对路径；默认 report/main.md")
    ap.add_argument("--json", default=None, help="results.json；默认 out/results.json")
    ap.add_argument("--source", default=None, help="题干文本（降重/抄题比对）")
    ap.add_argument("--strict", action="store_true", help="sanity_check 未配规则时计为红项")
    args = ap.parse_args()

    root = os.path.abspath(args.project)
    if not os.path.isdir(root):
        print(f"[err] 项目目录不存在: {root}", file=sys.stderr)
        return 2
    paper = os.path.abspath(args.paper) if args.paper else os.path.join(root, "report", "main.md")
    jpath = os.path.abspath(args.json) if args.json else os.path.join(root, "out", "results.json")
    src = os.path.abspath(args.source) if args.source else None
    sd = _script_dir()

    print(f"# 国一冲刺计分板  @ {root}\n")
    print(f"论文: {paper}")
    print(f"结果: {jpath}")
    print(f"题干: {src or '(未提供，跳过抄题比对)'}\n")

    rows = []

    # 1. 环境体检
    env_args = [sys.executable, os.path.join(sd, "check_env.py")]
    if args.strict:
        env_args.append("--strict")
    rows.append(_run("环境体检 check_env", env_args))

    # 2. 数值对账
    if os.path.exists(paper) and os.path.exists(jpath):
        rows.append(_run("数值对账 check_results", [sys.executable, os.path.join(sd, "check_results.py"), paper, "--json", jpath]))
    else:
        print(f"  [SKIP] 数值对账：缺论文({os.path.exists(paper)})或 results.json({os.path.exists(jpath)})")
        rows.append(("数值对账", None))

    # 3. 量纲/量级：规则需用户在 --json 后补；此处提示
    if os.path.exists(jpath):
        # 无规则时 sanity_check 空跑没有意义，给提示而非盲跑
        print("  [INFO] 量纲/量级 sanity_check：需按题目手动配规则，例：")
        print("         python sanity_check.py out/results.json --nonneg q1_optimal --bounds 'weight_*:0,1,sum=1'")
        if args.strict:
            rows.append(("量纲/量级", False))
        else:
            rows.append(("量纲/量级", None))
    else:
        print("  [SKIP] 量纲/量级：缺 results.json")
        rows.append(("量纲/量级", None))

    # 4. 文献核验
    if os.path.exists(paper):
        rows.append(_run("文献核验 verify_refs", [sys.executable, os.path.join(sd, "verify_refs.py"), paper]))
    else:
        rows.append(("文献核验", None))

    # 5. 图表规范
    report_dir = os.path.dirname(paper)
    if os.path.isdir(report_dir):
        rows.append(_run("图表规范 figcheck", [sys.executable, os.path.join(sd, "figcheck.py"), report_dir, "--paper", paper]))
    else:
        rows.append(("图表规范", None))

    # 6. 降AI味/降重
    if os.path.exists(paper):
        a = [sys.executable, os.path.join(sd, "dedup_scan.py"), paper]
        if src and os.path.exists(src):
            a.append(src)
        rows.append(_run("降AI味/降重 dedup_scan", a))
    else:
        rows.append(("降AI味/降重", None))

    # 7. 跨文件一致性
    if os.path.exists(paper):
        rows.append(_run("跨文件一致性 crosscheck", [sys.executable, os.path.join(sd, "crosscheck.py"), paper]))
    else:
        rows.append(("跨文件一致性", None))

    # ── 汇总 ──
    fails = [n for n, ok in rows if ok is False]
    skips = [n for n, ok in rows if ok is None]
    print(f"\n[prize_gate] 通过 {sum(1 for _, ok in rows if ok is True)} / 共 {len(rows)} 项"
          + (f" · 红 {len(fails)}: {', '.join(fails)}" if fails else "")
          + (f" · 跳过 {len(skips)}: {', '.join(skips)}" if skips else ""))
    if fails:
        print("[prize_gate] 存在红项——逐条消掉再交，别带病提交。")
        return 1
    if skips:
        print("[prize_gate] 有跳过项——补全输入（题干/规则/文件）后再确认。")
        return 1
    print("[prize_gate] ✓ 六道收口全绿，可以提交。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
