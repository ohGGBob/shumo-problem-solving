#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_audit.py —— Agent Skill 通用体检器（零第三方依赖）

用途：升级/改造任意 skill 后，一键回归验证，防止"改出新问题"。
默认审计 shumo-solver 数模 skill，也可传入任意 skill 根目录。

用法:
    python skill_audit.py                      # 审计默认 skill（自动定位：脚本在 <preset>/tools/ 下时取 <preset>/skills/shumo-problem-solving，否则用内置默认路径）
    python skill_audit.py <skill根目录>        # 审计指定 skill

检查项:
    A. 脚本可运行性      每个 scripts/*.py 跑 --help，抓语法/依赖错误
    B. 路由覆盖度        references/ 是否被 SKILL.md 路由表点名（孤儿文件=永远不会被加载）
    C. README 覆盖度     scripts 是否都在 README 里提及
    D. 数量口径一致性    "N 个脚本 / N 个文档" 各处声明与实际是否相符
    E. 交叉引用死链      SKILL.md+README+references 内部互引的文件是否真实存在
    F. 门禁/规则一致性   自定义：检测 skill 内部是否出现自相矛盾的指令
    G. preset 根一致性   preset.yml / agent.cordis.yml 里的脚本计数声明是否与实际相符
                         （v1.8.1 新增：堵住"skill 内部全对齐、preset 根漂移"的盲区）

退出码: 0=全过  1=有警告  2=有阻断项
"""
import re
import os
import sys
import glob
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
# 布局一：脚本在 <skill>/tools/ 下 → skill 根即上级目录
_CAND = os.path.normpath(os.path.join(_HERE, ".."))
# 布局二：脚本在 <preset>/tools/ 下 → skill 根在 ../skills/shumo-problem-solving
_CAND2 = os.path.normpath(os.path.join(_HERE, "..", "skills", "shumo-problem-solving"))
if os.path.exists(os.path.join(_CAND, "SKILL.md")):
    DEFAULT_SKILL = _CAND
elif os.path.exists(os.path.join(_CAND2, "SKILL.md")):
    DEFAULT_SKILL = _CAND2
else:
    DEFAULT_SKILL = r"C:/Users/li618/.dsh/.agent-presets/shumo-solver/skills/shumo-problem-solving"

# 运行时生成物 / 占位符 / 外部路径 —— 不算死链
ALLOW_EXACT = {
    "export_results.py", "explore.py", "demo_2023c.py", "figures/style.py",
    "results.json", "requirements.txt", "data.csv", "series.csv",
    "heatmap.png", "facets.png", "init_project.py", "LICENSE",
    # 数据清洗流水线的输出产物（由 preprocess.py 生成，非仓库内文件）
    "missing_report.csv", "outlier_scan.csv",
}
ALLOW_RE = [
    re.compile(r"review_\d{4}-\d{2}-\d{2}\.md$"), re.compile(r"\bpaper/"),
    re.compile(r"\breport/"), re.compile(r"\bsrc/"), re.compile(r"^review_"),
    re.compile(r"cases-<年>"), re.compile(r"out/results\.json$"),
    re.compile(r"log/"), re.compile(r"^experiment_<"),
    re.compile(r"AI工具使用详情\.pdf$"),
]

# 计数声明正则（D/G 共用）
COUNT_PATS = [re.compile(r"(\d+)\s*个(?:本地)?(?:工程化)?(?:校验)?脚本"),
              re.compile(r"(\d+)\s*个专题文档"),
              re.compile(r"(\d+)\s*个\s*references")]


def audit(base):
    SKILL = os.path.join(base, "SKILL.md")
    refs_dir = os.path.join(base, "references")
    scripts_dir = os.path.join(base, "scripts")
    readme = os.path.join(base, "README.md")
    if not os.path.exists(SKILL):
        print(f"[阻断] 找不到 SKILL.md: {SKILL}")
        return 2

    block, warn = 0, 0
    scripts = sorted(glob.glob(os.path.join(scripts_dir, "*.py")))
    refs = sorted(glob.glob(os.path.join(refs_dir, "*.md")))
    s_names = {os.path.basename(p) for p in scripts}
    r_names = {os.path.basename(p) for p in refs}
    skill_txt = open(SKILL, encoding="utf-8").read()

    # ---- A. 脚本可运行性 ----
    print(f"=== A. 脚本 --help 体检（共 {len(scripts)} 个）===")
    bad = []
    for s in scripts:
        n = os.path.basename(s)
        try:
            r = subprocess.run([sys.executable, s, "--help"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=40)
            if r.returncode != 0:
                bad.append((n, f"exit={r.returncode}"))
        except Exception as e:
            bad.append((n, str(e)[:60]))
    print(f"通过 {len(scripts)-len(bad)}/{len(scripts)}")
    for n, e in bad:
        print(f"   FAIL: {n}  {e}")
    block += len(bad)

    # ---- B. 路由覆盖度 ----
    print(f"\n=== B. 路由覆盖度 ===")
    orphans = []
    for name in sorted(r_names):
        if name in skill_txt:
            continue
        if re.match(r"cases-(\d{4})\.md$", name) and re.search(r"cases-<年>\.md", skill_txt):
            continue
        orphans.append(name)
    print(f"references {len(r_names)} 个，孤儿 {len(orphans)} 个")
    for o in orphans:
        print(f"   孤儿(永不被加载): {o}")
    miss_s = [s for s in sorted(s_names) if s not in skill_txt]
    print(f"scripts {len(s_names)} 个，未被 SKILL.md 提及 {len(miss_s)} 个")
    for m in miss_s:
        print(f"   未提及: {m}")
    block += len(miss_s)
    warn += len(orphans)

    # ---- C. README 覆盖度 ----
    print(f"\n=== C. README 覆盖度 ===")
    if os.path.exists(readme):
        rd = open(readme, encoding="utf-8").read()
        miss_r = [s for s in sorted(s_names) if s not in rd]
        print(f"scripts 未被 README 提及 {len(miss_r)} 个")
        for m in miss_r:
            print(f"   未提及: {m}")
        warn += len(miss_r)
    else:
        print("（无 README.md，跳过）")

    # ---- D. 数量口径一致性 ----
    print(f"\n=== D. 数量口径（实际 refs={len(r_names)} scripts={len(s_names)}）===")
    targets = [("SKILL.md", SKILL), ("README.md", readme),
               ("UPGRADE_PLAN.md", os.path.join(base, "UPGRADE_PLAN.md"))]
    targets += [(os.path.basename(p), p) for p in refs]
    for label, path in targets:
        if not os.path.exists(path):
            continue
        hits = set()
        for p in COUNT_PATS:
            hits |= set(p.findall(open(path, encoding="utf-8").read()))
        if not hits:
            continue
        ok = all(int(h) in (len(r_names), len(s_names)) for h in hits)
        print(f"  [{'OK  ' if ok else '不符'}] {label}: 声明 {sorted(hits)}")
        if not ok:
            warn += 1

    # ---- E. 死链 ----
    print(f"\n=== E. 交叉引用死链 ===")
    docs = [SKILL] + ([readme] if os.path.exists(readme) else []) + refs
    tok_re = re.compile(r"`([^`\n]+)`")
    dead = {}
    for f in docs:
        for mo in tok_re.finditer(open(f, encoding="utf-8").read()):
            tok = mo.group(1).strip()
            if not re.search(r"[\w\-/<>]+\.(md|py|yml|csv|json|txt|png|pdf)$", tok):
                continue
            if tok in ALLOW_EXACT or any(r.search(tok) for r in ALLOW_RE):
                continue
            if any(c in tok for c in " ()|→+"):
                continue
            if not any(os.path.exists(os.path.join(d, tok)) for d in [base, refs_dir, scripts_dir]):
                dead.setdefault(tok, set()).add(os.path.basename(f))
    print(f"扫 {len(docs)} 个文档，疑似死链 {len(dead)} 个")
    for d, w in sorted(dead.items()):
        print(f"   {d}  <- {sorted(w)}")
    warn += len(dead)

    # ---- F. 门禁/规则一致性（自定义） ----
    print(f"\n=== F. 门禁/规则一致性 ===")
    em = os.path.join(refs_dir, "emergency-mode.md")
    if os.path.exists(em):
        emt = open(em, encoding="utf-8").read()
        conflict = re.search(r"触发口令[^\n]*全自动", emt)
        print(f"  紧急模式触发口令含「全自动」: {'是（冲突！）' if conflict else '否（已解绑）'}")
        if conflict:
            block += 1
        guard = "门禁不可因措辞而绕过" in skill_txt
        strict = "也绝不例外" in skill_txt
        print(f"  SKILL.md 门禁不可绕过声明: {'有' if guard else '无'}")
        print(f"  SKILL.md 门禁『绝不例外』原文保留: {'是' if strict else '否'}")
        if not guard:
            warn += 1
    else:
        print("  （无 emergency-mode.md，跳过专项检查）")

    # ---- G. preset 根一致性 ----
    print(f"\n=== G. preset 根一致性 ===")
    preset_root = os.path.normpath(os.path.join(base, "..", ".."))
    root_files = [("preset.yml", os.path.join(preset_root, "preset.yml")),
                  ("agent.cordis.yml", os.path.join(preset_root, "agent.cordis.yml"))]
    found_any = False
    for label, path in root_files:
        if not os.path.exists(path):
            continue
        found_any = True
        hits = set()
        for p in COUNT_PATS:
            hits |= set(p.findall(open(path, encoding="utf-8").read()))
        if not hits:
            print(f"  [{label}] 无脚本计数声明（跳过）")
            continue
        bad_hits = sorted(h for h in hits if int(h) not in (len(r_names), len(s_names)))
        if bad_hits:
            print(f"  [不符] {label}: 声明 {sorted(hits)}，实际 scripts={len(s_names)} refs={len(r_names)}")
            warn += 1
        else:
            print(f"  [OK  ] {label}: 声明 {sorted(hits)}")
    if not found_any:
        print("  （preset 根无 preset.yml / agent.cordis.yml，跳过）")

    print(f"\n===== 汇总：阻断 {block} 项，警告 {warn} 项 =====")
    return 2 if block else (1 if warn else 0)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SKILL
    print(f"# Skill 体检 @ {target}\n")
    sys.exit(audit(target))
