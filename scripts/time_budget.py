#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赛程时间预算看板（护住 72h/96h 节奏）。

用法:
    python time_budget.py [--contest {cumcm,mcm}] [--start "2026-09-05 18:00"] [--watch]

功能:
    - 根据赛制加载标准时间轴（timeline.md）
    - 显示当前阶段、剩余时间、硬截止红线
    - --watch 模式下每 30 秒刷新一次终端显示
    - 超过红线自动报警（ANSI 红色 + 响铃）

依赖: 仅标准库（可选 psutil 显示 CPU/内存，无则静默跳过）
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 标准时间轴（与 references/timeline.md 对齐）
TIMELINES = {
    "cumcm": {
        "name": "国赛 CUMCM (72h)",
        "phases": [
            {"name": "读题·定题", "start_h": 0, "end_h": 6, "hard_deadline": 6,
             "deliverable": "每题一句话 + 最迟 6h 定题"},
            {"name": "数据 + 假设", "start_h": 4, "end_h": 18, "hard_deadline": None,
             "deliverable": "clean.csv + 审计表 + 假设清单"},
            {"name": "建模跑通", "start_h": 18, "end_h": 30, "hard_deadline": 30,
             "deliverable": "每问模型可复现跑通（红警线）"},
            {"name": "检验·灵敏度", "start_h": 30, "end_h": 42, "hard_deadline": None,
             "deliverable": "检验表 + 灵敏度图"},
            {"name": "论文撰写", "start_h": 42, "end_h": 68, "hard_deadline": None,
             "deliverable": "可提交 PDF"},
            {"name": "对账收口", "start_h": 70, "end_h": 72, "hard_deadline": 72,
             "deliverable": "数值单一来源逐位对账 + 参考文献核验 + 干净环境复跑抽查"},
        ],
        "total_hours": 72,
        "red_lines": [6, 30, 72],
    },
    "mcm": {
        "name": "美赛 MCM/ICM (96h)",
        "phases": [
            {"name": "读题·定题·数据规划", "start_h": 0, "end_h": 24, "hard_deadline": 24,
             "deliverable": "选题决策卡；数据源清单"},
            {"name": "数据清洗 + 建模跑通（先基线）", "start_h": 12, "end_h": 48, "hard_deadline": 48,
             "deliverable": "每问可复现结果 + 首版图"},
            {"name": "检验·灵敏度 + 打磨可视化", "start_h": 48, "end_h": 72, "hard_deadline": None,
             "deliverable": "检验表 + 主打图"},
            {"name": "论文 + 降AI + 交稿自检", "start_h": 72, "end_h": 96, "hard_deadline": 96,
             "deliverable": "全文 ≤25 页（含 Summary Sheet）"},
        ],
        "total_hours": 96,
        "red_lines": [24, 48, 96],
    },
}

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def parse_start_time(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


def format_td(td: timedelta) -> str:
    total_sec = int(td.total_seconds())
    if total_sec < 0:
        return f"-{format_td(-td)}"
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    if h >= 24:
        d, h = divmod(h, 24)
        return f"{d}d {h:02d}h {m:02d}m"
    return f"{h:02d}h {m:02d}m {s:02d}s"


def get_current_phase(timeline, elapsed_h):
    for ph in timeline["phases"]:
        if ph["start_h"] <= elapsed_h < ph["end_h"]:
            return ph
    # 超过总时长
    if elapsed_h >= timeline["total_hours"]:
        return timeline["phases"][-1]
    return timeline["phases"][0]


def render_dashboard(timeline, start_dt, now_dt, show_sysinfo=False):
    elapsed = now_dt - start_dt
    elapsed_h = elapsed.total_seconds() / 3600
    remaining_h = timeline["total_hours"] - elapsed_h

    phase = get_current_phase(timeline, elapsed_h)
    phase_elapsed = elapsed_h - phase["start_h"]
    phase_total = phase["end_h"] - phase["start_h"]
    phase_remaining = phase["end_h"] - elapsed_h

    # 进度条（用 ASCII 避免编码问题）
    total_pct = min(100, max(0, elapsed_h / timeline["total_hours"] * 100))
    phase_pct = 0
    if phase_total > 0:
        phase_pct = min(100, max(0, phase_elapsed / phase_total * 100))

    bar_width = 40
    total_filled = int(bar_width * total_pct / 100)
    phase_filled = int(bar_width * phase_pct / 100)
    total_bar = "#" * total_filled + "-" * (bar_width - total_filled)
    phase_bar = "#" * phase_filled + "-" * (bar_width - phase_filled)

    # 红线检查
    red_alert = False
    next_red = None
    for rl in timeline["red_lines"]:
        if elapsed_h < rl:
            next_red = rl
            break
    if next_red is not None and (next_red - elapsed_h) < 1.0:  # 1h 内
        red_alert = True

    # ANSI 颜色
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    BELL = "\a"

    lines = []
    lines.append(f"{BOLD}{CYAN}================================================================{RESET}")
    lines.append(f"{BOLD}{CYAN}  {timeline['name']}  时间预算看板{RESET}")
    lines.append(f"{BOLD}{CYAN}================================================================{RESET}")
    lines.append(f"  开赛时间: {start_dt.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"  当前时间: {now_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"")
    lines.append(f"  {BOLD}总进度:{RESET} [{total_bar}] {total_pct:5.1f}%  "
                 f"已用 {format_td(elapsed)} / 共 {timeline['total_hours']}h  "
                 f"剩余 {format_td(timedelta(hours=remaining_h))}")
    lines.append(f"")
    lines.append(f"  {BOLD}当前阶段:{RESET} {phase['name']}")
    lines.append(f"  {BOLD}阶段进度:{RESET} [{phase_bar}] {phase_pct:5.1f}%  "
                 f"阶段剩余 {format_td(timedelta(hours=phase_remaining))}")
    lines.append(f"  {BOLD}交付物:{RESET} {phase['deliverable']}")
    lines.append(f"")

    # 红线
    lines.append(f"  {BOLD}硬截止红线:{RESET}")
    for rl in timeline["red_lines"]:
        rl_dt = start_dt + timedelta(hours=rl)
        rl_remain = rl - elapsed_h
        if rl_remain <= 0:
            status = f"{RED}已超 {format_td(timedelta(hours=-rl_remain))}{RESET}"
        elif rl_remain <= 1:
            status = f"{RED}{BOLD}!! 仅剩 {format_td(timedelta(hours=rl_remain))}{RESET}"
        elif rl_remain <= 3:
            status = f"{YELLOW}!! 剩余 {format_td(timedelta(hours=rl_remain))}{RESET}"
        else:
            status = f"{GREEN}剩余 {format_td(timedelta(hours=rl_remain))}{RESET}"
        lines.append(f"    - {rl}h ({rl_dt.strftime('%m-%d %H:%M')}) -- {status}")

    lines.append(f"")

    # 系统信息
    if show_sysinfo and HAS_PSUTIL:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        lines.append(f"  {BOLD}系统:{RESET} CPU {cpu:.1f}%  内存 {mem.percent:.1f}% "
                     f"({mem.available/1024/1024/1024:.1f}GB 可用)")
    elif show_sysinfo:
        lines.append(f"  {BOLD}系统:{RESET} psutil 未安装，装上可看 CPU/内存 (pip install psutil)")

    lines.append(f"{BOLD}{CYAN}================================================================{RESET}")

    output = "\n".join(lines)
    if red_alert:
        output = f"{RED}{BOLD}!! 红线临近/已超！立即砍复杂度保可交付！ !!{RESET}\n{BELL}" + output
    return output


def main():
    ap = argparse.ArgumentParser(description="赛程时间预算看板")
    ap.add_argument("--contest", choices=["cumcm", "mcm"], default="cumcm",
                    help="赛制类型")
    ap.add_argument("--start", default=None,
                    help="开赛时间 (YYYY-MM-DD HH:MM)，默认现在")
    ap.add_argument("--watch", action="store_true",
                    help="持续监视模式（每 30 秒刷新）")
    ap.add_argument("--sysinfo", action="store_true",
                    help="显示 CPU/内存（需 psutil）")
    ap.add_argument("--once", action="store_true",
                    help="只打印一次并退出（用于脚本调用）")
    args = ap.parse_args()

    timeline = TIMELINES[args.contest]
    start_dt = parse_start_time(args.start) if args.start else datetime.now()

    if args.once or not args.watch:
        print(render_dashboard(timeline, start_dt, datetime.now(), args.sysinfo))
        return 0

    # 监视模式
    try:
        while True:
            # 清屏（跨平台）
            os.system('cls' if os.name == 'nt' else 'clear')
            print(render_dashboard(timeline, start_dt, datetime.now(), args.sysinfo))
            print("  按 Ctrl+C 退出监视")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[time_budget] 监视已停止")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())