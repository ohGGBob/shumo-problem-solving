#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决策日志（紧急模式 & AI 使用报告 的公共数据源）。

「强制确认门禁」每次拍板都值得沉淀：谁/选了啥/为什么/取舍/风险/AI 参与度。
本脚本把决策追加到 <项目>/log/decisions.md，并可按需导出两类素材：
  - 论文「设计意图」段（评委最吃的"为什么这么设计"，直接取材于取舍与理由）；
  - AI 工具使用详情（gen_ai_report.py 依赖本日志的 --ai 字段汇总）。

用法:
    python decision_log.py <项目目录> add --phase 模型选型 --decision "问题1用X模型" \
        --why "..." --tradeoff "精度 vs 速度" --risk "..." [--ai "AI提供3种候选思路，本队独立推导验证"]
    python decision_log.py <项目目录> list
    python decision_log.py <项目目录> export --for design     # 论文「设计意图」素材
    python decision_log.py <项目目录> export --for aireport   # AI 使用详情素材

零第三方依赖；纯文本追加式，可多人多轮并发写同一文件。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys


def _console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass


def _log_path(project):
    return os.path.join(project, "log", "decisions.md")


def _ensure(project):
    logdir = os.path.join(project, "log")
    os.makedirs(logdir, exist_ok=True)
    p = _log_path(project)
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write("# 决策日志\n\n> 每次拍板自动追加。论文「设计意图」与 AI 使用详情都从这里取材。\n\n")
    return p


def _next_id(path):
    max_n = 0
    if os.path.exists(path):
        for m in re.finditer(r"### D-(\d+)\b", open(path, encoding="utf-8-sig").read()):
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def add(project, args):
    p = _ensure(project)
    if not args.decision:
        print("[err] --decision 必填", file=sys.stderr)
        return 1
    n = _next_id(p)
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"### D-{n:03d} · {now} · {args.phase or '未分类'}",
        f"- 决策：{args.decision}",
    ]
    if args.why:
        lines.append(f"- 理由：{args.why}")
    if args.tradeoff:
        lines.append(f"- 取舍：{args.tradeoff}")
    if args.risk:
        lines.append(f"- 风险：{args.risk}")
    if args.ai:
        lines.append(f"- AI参与：{args.ai}")
    lines.append(f"- 状态：{args.status}")
    lines.append("")
    with open(p, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[decision_log] 已追加 D-{n:03d} → {p}")
    return 0


def _entries(path):
    txt = open(path, encoding="utf-8-sig").read()
    blocks = re.split(r"(?m)^### D-\d+ ", txt)
    out = []
    for b in blocks:
        if b.startswith("·"):
            out.append("### " + b)
    return out


def list_entries(project):
    p = _ensure(project)
    if not os.path.exists(p) or _next_id(p) == 1 and _entry_count(p) == 0:
        print("[decision_log] 暂无决策记录。")
        return 0
    body = open(p, encoding="utf-8-sig").read()
    print(body if body.strip() else "[decision_log] 暂无决策记录。")
    return 0


def _entry_count(p):
    txt = open(p, encoding="utf-8-sig").read()
    return len(re.findall(r"### D-\d+", txt))


def export_design(project):
    p = _ensure(project)
    if _entry_count(p) == 0:
        print("[decision_log] 无决策记录，无法导出设计意图素材。", file=sys.stderr)
        return 1
    entries = []
    for b in re.split(r"(?m)^### D-\d+ ", open(p, encoding="utf-8-sig").read()):
        if not b.startswith("·"):
            continue
        phase = re.search(r"· (.*?) ·", b)
        dec = re.search(r"- 决策：(.+)", b)
        why = re.search(r"- 理由：(.+)", b)
        to = re.search(r"- 取舍：(.+)", b)
        if dec:
            head = dec.group(1)
            if why and to:
                head += f"（理由：{why.group(1)}；取舍：{to.group(1)}）"
            entries.append(f"- {head}")
    print("# 论文「设计意图」素材（从决策日志提取，可直接改写进论文）\n")
    print("> 用法：把下面每条展开成「我们为什么这么设计」的论证段，配表图三件套。\n")
    print("\n".join(entries))
    return 0


def export_aireport(project):
    p = _ensure(project)
    if _entry_count(p) == 0:
        print("[decision_log] 无决策记录。", file=sys.stderr)
        return 1
    used = []
    for b in re.split(r"(?m)^### D-\d+ ", open(p, encoding="utf-8-sig").read()):
        if not b.startswith("·"):
            continue
        phase = re.search(r"· \d{4}-\d{2}-\d{2} \d{2}:\d{2} · (.+?)\n", b)
        ai = re.search(r"- AI参与：(.+)", b)
        dec = re.search(r"- 决策：(.+)", b)
        if ai:
            used.append((phase.group(1) if phase else "未分类", dec.group(1) if dec else "", ai.group(1)))
    if not used:
        print("[decision_log] 日志中无 AI 参与记录——请确认本队是否使用了 AI 工具（合规须如实）。", file=sys.stderr)
        return 1
    print("# AI 使用详情素材（按环节汇总，供 gen_ai_report.py / 人工整理）\n")
    for phase, dec, ai in used:
        print(f"- 【{phase}】{dec}\n  AI：{ai}")
    return 0


def main():
    _console()
    ap = argparse.ArgumentParser(description="决策日志：记录/查看/导出")
    ap.add_argument("project", help="项目目录（<项目>/log/decisions.md）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="追加一条决策")
    a.add_argument("--phase", default="", help="环节（读题/选型/假设/求解/检验/论文…）")
    a.add_argument("--decision", required=True, help="决策内容")
    a.add_argument("--why", default="", help="理由")
    a.add_argument("--tradeoff", default="", help="取舍")
    a.add_argument("--risk", default="", help="风险")
    a.add_argument("--ai", default="", help="AI 参与情况（无 AI 则不填）")
    a.add_argument("--status", default="已拍板", help="状态，默认'已拍板'")
    a.set_defaults(func=add)

    sub.add_parser("list", help="查看全部决策").set_defaults(func=lambda p, a: list_entries(p))
    e = sub.add_parser("export", help="导出素材")
    e.add_argument("--for", dest="purpose", required=True, choices=["design", "aireport"],
                   help="design=论文设计意图素材；aireport=AI 使用详情素材")
    e.set_defaults(func=lambda p, a: export_design(p) if a.purpose == "design" else export_aireport(p))

    args = ap.parse_args()
    return args.func(args.project, args)


if __name__ == "__main__":
    raise SystemExit(main())
