#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""紧急全流程编排器（紧急模式）——时间极紧时，把 skill 的 7 步流程变成
一条命令管到底的作战系统：不跳步、进度透明、红警自动降级、一键收口。

设计哲学：本脚本不替你建模求解（那是人与 AI 协作的活），它做三件事——
  1. checkpoint 护城河：7 个阶段必须各有产物才能推进，杜绝"慌到跳步/漏项"；
  2. 红警护城河：按 deadline 自动判断"时间 vs 进度"，给"砍什么保什么"的具体建议；
  3. 一键收口：finish 自动跑 prize_gate（全链路校验）+ gen_ai_report（AI 声明/详情）+ 生成提交清单。

用法:
    python emergency_run.py <项目目录> init --source 题干.txt [--deadline "2026-09-13 20:00"]
    python emergency_run.py <项目目录> status
    python emergency_run.py <项目目录> advance --phase 建模求解 --note "..."
    python emergency_run.py <项目目录> guard --deadline "2026-09-13 20:00"
    python emergency_run.py <项目目录> finish [--source 题干.txt]

阶段与必产物:
    read   读题拆解   → report/problem_restatement.md
    model  选型定位   → log/decisions.md（选型决策）
    assume 模型假设   → report/assumptions.md
    solve  建模求解   → out/results.json（关键结果落盘）
    check  模型检验   → report/validation.md
    paper  论文成文   → report/main.md
    close  交稿收口   → report/ai_declaration.txt + 支撑材料清单
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys


def _console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass


PHASES = [
    ("read", "读题拆解", ["report/problem_restatement.md"], "topic-selection.md / cumcm-years.md"),
    ("model", "选型定位", ["log/decisions.md"], "model-recipes.md / innovation-playbook.md"),
    ("assume", "模型假设", ["report/assumptions.md"], "assumptions-justification.md / logic-rigor.md"),
    ("solve", "建模求解", ["out/results.json"], "code-templates.md / advanced-methods-templates.md"),
    ("check", "模型检验", ["report/validation.md"], "validation-checklist.md / sanity_check.py"),
    ("paper", "论文成文", ["report/main.md"], "paper-skeleton.md / bao-paper-writing.md / paper-quality-gate.md"),
    ("close", "交稿收口", ["report/ai_declaration.txt"], "prize_gate.py / gen_ai_report.py / rules-and-deadlines.md"),
]


def _sd():
    return os.path.dirname(os.path.abspath(__file__))


def _state_path(project):
    return os.path.join(project, "log", "emergency.json")


def _load(project):
    p = _state_path(project)
    if not os.path.exists(p):
        return {"deadline": "", "phases": {}, "updated": ""}
    return json.load(open(p, encoding="utf-8-sig"))


def _save(project, st):
    os.makedirs(os.path.join(project, "log"), exist_ok=True)
    st["updated"] = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(_state_path(project), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def _parse_dt(s):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return _dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def cmd_init(project, args):
    # 复用 init_project.py 生成标准骨架（它负责创建目录；已存在会中止）
    name = os.path.basename(project.rstrip("/\\"))
    parent = os.path.dirname(os.path.abspath(project))
    r = subprocess.run([sys.executable, os.path.join(_sd(), "init_project.py"), name, "--dir", parent],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1"})
    _skel = (r.stdout or r.stderr or "").strip()
    print(f"[emergency_run] 骨架步骤: {_skel}" if _skel else "[emergency_run] 骨架已生成")
    if not os.path.isdir(project):
        print(f"[err] 骨架生成失败: {project}", file=sys.stderr)
        return 2
    # 题干放入 data/
    if args.source and os.path.exists(args.source):
        os.makedirs(os.path.join(project, "data"), exist_ok=True)
        dst = os.path.join(project, "data", "题目.txt")
        shutil.copyfile(args.source, dst)
        print(f"[emergency_run] 题干已复制 → {dst}")
    st = _load(project)
    if args.deadline:
        st["deadline"] = args.deadline
    for key, _, _, _ in PHASES:
        st["phases"].setdefault(key, {"done": False, "note": ""})
    _save(project, st)
    print(f"[emergency_run] 紧急作战看板已初始化 → {_state_path(project)}")
    return 0


def cmd_status(project, args):
    st = _load(project)
    print(f"# 紧急作战看板  @ {project}")
    print(f"截止: {st.get('deadline') or '未设置（用 guard --deadline 设置）'}\n")
    done = 0
    for key, label, artifacts, res in PHASES:
        p = st["phases"].get(key, {})
        ok = bool(p.get("done"))
        if ok:
            done += 1
        mark = "✓" if ok else "·"
        note = (" — " + p.get("note", "")) if p.get("note") else ""
        missing = [a for a in artifacts if not os.path.exists(os.path.join(project, a))]
        miss_txt = f"  [缺产物: {', '.join(missing)}]" if missing else ""
        print(f"  [{mark}] {label}{note}{miss_txt}")
        if not ok:
            print(f"       参考: {res}")
    print(f"\n[emergency_run] 进度 {done}/{len(PHASES)}")
    if done < len(PHASES):
        nxt = next((l for k, l, _, _ in PHASES if not st["phases"].get(k, {}).get("done")), None)
        print(f"[emergency_run] 下一步: {nxt}")
    return 0


def cmd_advance(project, args):
    st = _load(project)
    key = args.phase
    names = {k: l for k, l, _, _ in PHASES}
    if key not in names:
        print(f"[err] 未知阶段 {key}，可选: {', '.join(names)}", file=sys.stderr)
        return 2
    artifacts = dict((k, a) for k, _, a, _ in PHASES)[key]
    missing = [a for a in artifacts if not os.path.exists(os.path.join(project, a))]
    if missing and not args.force:
        print(f"[emergency_run] 阶段「{names[key]}」缺必产物: {', '.join(missing)}", file=sys.stderr)
        print("    紧急模式也不跳步——先产出该产物，或用 --force 显式声明跳过（需写明理由）。", file=sys.stderr)
        return 1
    st["phases"][key] = {"done": True, "note": args.note or ""}
    _save(project, st)
    print(f"[emergency_run] ✓ {names[key]} 完成" + (f"（{args.note}）" if args.note else ""))
    return 0


def cmd_guard(project, args):
    st = _load(project)
    dl = args.deadline or st.get("deadline", "")
    if not dl:
        print("[emergency_run] 未设置截止时间——用 --deadline 'YYYY-MM-DD HH:MM' 设置。", file=sys.stderr)
        return 1
    d = _parse_dt(dl)
    if not d:
        print(f"[err] 无法解析截止时间: {dl}", file=sys.stderr)
        return 2
    remain_h = (d - _dt.datetime.now()).total_seconds() / 3600.0
    done = sum(1 for k, _, _, _ in PHASES if st["phases"].get(k, {}).get("done"))
    print(f"# 红警检查  ·  剩余 {remain_h:.1f} 小时  ·  进度 {done}/{len(PHASES)}")

    if remain_h <= 0:
        print("[RED] 已过截止时间——立即按最小可交付原则提交已完成的全部内容！")
        return 1
    paper_done = st["phases"].get("paper", {}).get("done")
    solve_done = st["phases"].get("solve", {}).get("done")
    if remain_h < 6 and not paper_done:
        print("[RED] 剩余 <6h 且论文未成文 → 砍次要问题到一页，先保：摘要四要素 + 三件套 + 核心结论数字 + 参考文献真文献。")
        return 1
    if remain_h < 24 and not solve_done:
        print("[RED] 剩余 <24h 且主问未求解 → 立即简化模型：放弃炫技算法，改用已验证模板；先跑通主问拿结果落盘。")
        return 1
    if remain_h < 24 and solve_done and not paper_done:
        print("[AMBER] 求解已过、论文未成文 → 进入写作冲刺：按 paper-skeleton.md 逐节填，每节配数字。")
        return 1
    print("[GREEN] 节奏正常——按当前进度推进，每问过 sanity_check。")
    return 0


def cmd_finish(project, args):
    st = _load(project)
    done = sum(1 for k, _, _, _ in PHASES if st["phases"].get(k, {}).get("done"))
    if done < len(PHASES):
        todo = [l for k, l, _, _ in PHASES if not st["phases"].get(k, {}).get("done")]
        print(f"[emergency_run] 尚有阶段未完成: {', '.join(todo)}", file=sys.stderr)
        print("    紧急模式也先推进完（或用 advance --force 声明跳过并写明理由），再收口。", file=sys.stderr)
        return 1
    print("# 交稿收口\n")
    # 1. 全链路校验
    print("== 1/3 全链路校验（prize_gate）==")
    r = subprocess.run([sys.executable, os.path.join(_sd(), "prize_gate.py"), project] +
                       (["--source", args.source] if args.source else []),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1"})
    print((r.stdout or r.stderr or "")[-1500:])
    # 2. AI 使用报告
    print("\n== 2/3 AI 使用报告 ==")
    r = subprocess.run([sys.executable, os.path.join(_sd(), "gen_ai_report.py"), project, "--pdf", "auto"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1"})
    print((r.stdout or r.stderr or "")[-1200:])
    # 3. 提交清单
    print("\n== 3/3 提交清单（按 2026 国赛通知核对）==")
    print("""- [ ] 参赛论文：PDF 或 Word，不含承诺书/编号页，源程序作为附录放正文之后
- [ ] 支撑材料：代码+数据+资料 用 WinRAR 压缩为 ZIP/RAR，独立于论文
- [ ] 支撑材料内含「AI工具使用详情.pdf」（文件名严格一致，匿名）
- [ ] 论文参考文献之前含「AI工具使用声明」（gen_ai_report 已生成）
- [ ] 任何文件/文件名/文档属性不含学校、队号、队员姓名、教师、联系方式
- [ ] 9/13 20:00 前：客户端生成并提交论文+支撑材料 MD5 码（打开保存会改变 MD5，需重提）
- [ ] 9/13 20:30–9/14 14:00：上传与 MD5 对应的电子文档
- [ ] 纸质版按赛区要求打印并附承诺书/编号页提交""")
    print("\n[emergency_run] 收口完成——按清单逐项确认后提交。")
    return 0


def main():
    _console()
    ap = argparse.ArgumentParser(description="紧急全流程编排器（紧急模式）")
    ap.add_argument("project", help="项目目录")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="初始化骨架+看板")
    i.add_argument("--source", default="", help="题干文件路径")
    i.add_argument("--deadline", default="", help="截止时间 'YYYY-MM-DD HH:MM'")
    i.set_defaults(func=cmd_init)
    sub.add_parser("status", help="看板").set_defaults(func=lambda p, a: cmd_status(p, a))
    ad = sub.add_parser("advance", help="推进阶段")
    ad.add_argument("--phase", required=True)
    ad.add_argument("--note", default="")
    ad.add_argument("--force", action="store_true")
    ad.set_defaults(func=cmd_advance)
    g = sub.add_parser("guard", help="红警检查")
    g.add_argument("--deadline", default="")
    g.set_defaults(func=lambda p, a: cmd_guard(p, a))
    f = sub.add_parser("finish", help="一键收口")
    f.add_argument("--source", default="")
    f.set_defaults(func=cmd_finish)
    args = ap.parse_args()
    return args.func(args.project, args)


if __name__ == "__main__":
    raise SystemExit(main())
