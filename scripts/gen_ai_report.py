#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 使用报告生成器（2026 国赛合规辅助材料）。

依据《全国大学生数学建模竞赛人工智能工具使用规定（2026年试行）》（2026-08-03 发布，9/1 起试行）：
  - 所有参赛队（无论用没用 AI）都必须在论文「参考文献之前」设置「AI工具使用声明」；
  - 使用 AI 的参赛队还须在支撑材料中提交「AI工具使用详情.pdf」，
    内容四要素：①工具名称/版本或型号 ②具体使用目的和环节 ③主要提示方式与使用过程说明（可附典型交互示例）
    ④对 AI 输出的采纳、人工修改和核验的主要情况（语言润色除外）；
  - 详情文件必须匿名（不出现学校/队号/队员姓名/教师/联系方式/账号/签名）；
  - 故意隐瞒、虚假声明、把未经人工核实的 AI 输出当核心成果 → 取消评奖资格。

本脚本只做「如实记录与格式化」，不编造使用情况。数据来源：决策日志 decision_log.py 的 --ai 字段。

用法:
    python gen_ai_report.py <项目目录> [--tools "豆包;ChatGPT 4o"] [--used/--unused] [--pdf pandoc|none]

输出:
    <项目>/report/ai_declaration.txt   —— 论文内嵌声明（直接粘贴到参考文献之前）
    <项目>/log/ai_usage_report.md     —— AI 工具使用详情（满足官方 4 点 + 匿名）
    （--pdf pandoc 且系统有 pandoc 时，额外转出 <项目>/out/AI工具使用详情.pdf）
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys


def _console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass


def _log_path(project):
    return os.path.join(project, "log", "decisions.md")


def _entry_count(p):
    if not os.path.exists(p):
        return 0
    return len(re.findall(r"### D-\d+", open(p, encoding="utf-8-sig").read()))


def _collect_ai_usage(project):
    """从决策日志收集 AI 参与记录，返回 [(环节, 决策, AI描述), ...]。"""
    p = _log_path(project)
    if not os.path.exists(p):
        return []
    out = []
    for b in re.split(r"(?m)^### D-\d+ ", open(p, encoding="utf-8-sig").read()):
        if not b.startswith("·"):
            continue
        phase = re.search(r"· \d{4}-\d{2}-\d{2} \d{2}:\d{2} · (.+?)\n", b)
        dec = re.search(r"- 决策：(.+)", b)
        ai = re.search(r"- AI参与：(.+)", b)
        if ai:
            out.append((phase.group(1) if phase else "未分类",
                        dec.group(1) if dec else "",
                        ai.group(1)))
    return out


def gen_declaration(project, used, summary):
    """官方模板二选一。"""
    if used:
        s = f"本参赛队在竞赛过程中使用了AI工具，主要用于{summary}，详细使用情况见支撑材料。"
    else:
        s = "本参赛队在竞赛过程中未使用任何AI工具。"
    out = os.path.join(project, "report", "ai_declaration.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("AI工具使用声明（放在论文参考文献之前）\n\n")
        f.write(s + "\n")
    return out, s


def gen_detail(project, tools, usage):
    """生成 AI 工具使用详情（官方 4 点 + 匿名）。usage=[(环节,决策,AI描述),...]"""
    lines = []
    lines.append("# AI工具使用详情")
    lines.append("")
    lines.append("> 本文件匿名编写：不含学校、参赛队编号、队员姓名、指导教师、联系方式、账号与签名。")
    lines.append("> 依据《全国大学生数学建模竞赛人工智能工具使用规定（2026年试行）》第 4 条编制。")
    lines.append("")
    lines.append("## 一、所用AI工具名称、版本或型号")
    if tools:
        for t in tools.split(";"):
            t = t.strip()
            if t:
                lines.append(f"- {t}")
    else:
        lines.append("- （请逐项填写：工具名 + 版本/型号，如 豆包（桌面端 · 版本号 x.x））")
    lines.append("")
    lines.append("## 二、具体使用目的和环节")
    lines.append("")
    if usage:
        lines.append("| 环节 | 决策/任务 | AI 参与情况 |")
        lines.append("|---|---|---|")
        for phase, dec, ai in usage:
            lines.append(f"| {phase} | {dec} | {ai} |")
    else:
        lines.append("（从决策日志未提取到 AI 参与记录——请人工补全，或确认本队确实未使用 AI）")
    lines.append("")
    lines.append("## 三、主要提示方式与使用过程说明（可附典型交互示例）")
    lines.append("")
    lines.append("> 每条示例写清：目的 / 提示方式（可附提示词摘录）/ AI 输出要点 / 本队后续处理。")
    lines.append("> 例：")
    lines.append("> - 目的：求解线性规划；提示：'请给出该问题的 Python 求解代码'；AI 输出：提供 scipy.optimize.linprog 方案；本队：替换为论文实际数据后运行验证。")
    lines.append("")
    lines.append("## 四、对AI输出的采纳、人工修改和核验的主要情况（语言润色除外）")
    lines.append("")
    lines.append("> 逐项写：采纳了什么 / 修改了什么 / 如何核验（如：对 AI 给出的公式逐行推导验证；对 AI 结果用真实数据重算比对；对 AI 结论用第二来源交叉确认）。")
    lines.append("> 禁止只写'已核验'三个字，要写核验动作。")
    lines.append("")

    os.makedirs(os.path.join(project, "log"), exist_ok=True)
    out = os.path.join(project, "log", "ai_usage_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out


def try_pdf(project, md_path):
    pdf_out = os.path.join(project, "out", "AI工具使用详情.pdf")
    os.makedirs(os.path.dirname(pdf_out), exist_ok=True)
    pandoc = shutil.which("pandoc")
    if not pandoc:
        return None, "未安装 pandoc，未自动转 PDF——请用 Word/浏览器打开 ai_usage_report.md 另存为 PDF，文件名必须为「AI工具使用详情.pdf」"
    r = subprocess.run([pandoc, md_path, "-o", pdf_out, "--pdf-engine=wkhtmltopdf" if shutil.which("wkhtmltopdf") else "pdflatex"],
                       capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(pdf_out):
        return pdf_out, None
    return None, "pandoc 转 PDF 失败：" + (r.stderr or "")[:200]


def main():
    _console()
    ap = argparse.ArgumentParser(description="AI 使用报告生成器（2026 国赛合规）")
    ap.add_argument("project", help="项目目录")
    ap.add_argument("--tools", default="", help="分号分隔的工具清单，如 '豆包;ChatGPT 4o'")
    ap.add_argument("--used", action="store_true", help="声明本队使用了 AI（默认从决策日志推断）")
    ap.add_argument("--unused", action="store_true", help="声明本队未使用 AI（生成'未使用'声明）")
    ap.add_argument("--summary", default="语言润色、代码调试、建模思路讨论等", help="声明中的简要用途")
    ap.add_argument("--pdf", choices=["auto", "none"], default="auto", help="是否尝试转 PDF（默认 auto）")
    args = ap.parse_args()
    if not os.path.isdir(args.project):
        print(f"[err] 项目目录不存在: {args.project}", file=sys.stderr)
        return 2

    usage = _collect_ai_usage(args.project)
    used = args.used or (not args.unused and bool(usage))

    decl_path, decl_txt = gen_declaration(args.project, used, args.summary)
    print(f"[gen_ai_report] 声明 → {decl_path}")
    print(f"    {decl_txt}\n")

    if used:
        detail = gen_detail(args.project, args.tools, usage)
        print(f"[gen_ai_report] 使用详情 → {detail}")
        if args.pdf != "none":
            pdf_path, err = try_pdf(args.project, detail)
            if pdf_path:
                print(f"[gen_ai_report] PDF → {pdf_path}")
            else:
                print(f"[gen_ai_report] {err}")
        n_ai = len(usage)
        if n_ai == 0:
            print("[gen_ai_report] 提示：决策日志中没有 AI 参与记录，但声明为'使用了 AI'——请在详情文件人工补全使用情况（合规须如实）。")
        else:
            print(f"[gen_ai_report] 已从决策日志汇总 {n_ai} 条 AI 参与记录。")
    else:
        print("[gen_ai_report] 声明为'未使用 AI'，无需生成使用详情。若实际使用过 AI，请用 --used 并如实填写。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
