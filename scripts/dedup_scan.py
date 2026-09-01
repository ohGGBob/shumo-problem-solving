#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""降 AI 味 / 降重自查：套娃词、零信息句、疑似抄题面。

用法:
    python dedup_scan.py <论文.md|论文.tex|论文.docx>

检查项（对应 writing-deai-dedup.md / paper-quality-gate.md 关卡五）:
    1. AI 味套娃词：首先/其次/最后/综上所述/值得注意的是/众所周知/显而易见/
       具有重要意义/重要作用/本文提出了/在...背景下/随着...发展。
    2. 套娃结构：连续出现"首先...其次...最后"（叙事模板痕迹）。
    3. 零信息句：含"重要意义/重大贡献/广泛应用/奠定基础"等但句中无数字。
    4. 疑似抄题面：题干高频原词在论文"问题重述"段大段复现（弱启发式）。
    5. 空话密度：整段不含任何阿拉伯数字（建模/结果段落应为异常）。

输出命中位置与行号，供逐句改写。
"""
import argparse
import os
import re
import sys

AI_PHRASES = [
    "首先", "其次", "最后", "综上所述", "值得注意的是", "众所周知", "显而易见",
    "具有重要意义", "重要作用", "本文提出了", "在.*背景下", "随着.*发展",
    "不言而喻", "毋庸置疑", "在很大程度上",
]
EMPTY_WORDS = ["重要意义", "重大贡献", "广泛应用", "奠定基础", "提供有力支撑", "具有重要的", "参考价值"]
COPY_HINT_WORDS = ["题目给出", "题目所述", "根据题意", "题面", "本题中"]


def read_text(path):
    if path.lower().endswith(".docx"):
        try:
            import zipfile
            with zipfile.ZipFile(path) as z:
                return re.sub(r"<[^>]+>", " ", z.read("word/document.xml").decode("utf-8", "ignore"))
        except Exception as e:  # noqa
            print(f"[warn] docx 读取失败: {e}", file=sys.stderr)
            return ""
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser(description="降AI味与降重自查")
    ap.add_argument("paper")
    args = ap.parse_args()
    if not os.path.exists(args.paper):
        print(f"[err] 论文不存在: {args.paper}", file=sys.stderr)
        return 1

    text = read_text(args.paper)
    lines = text.splitlines()
    total_hits = 0

    print(f"# 降 AI 味 / 降重自查: {os.path.basename(args.paper)}\n")

    # 1. 套娃词
    print("## 1. AI 味套娃词")
    found_phrases = {}
    for i, ln in enumerate(lines, 1):
        for ph in AI_PHRASES:
            if re.search(ph, ln):
                found_phrases.setdefault(ph, []).append(i)
    if not found_phrases:
        print("   ✓ 未命中常见套娃词。")
    else:
        for ph, locs in found_phrases.items():
            total_hits += len(locs)
            print(f"   ! 「{ph}」 出现 {len(locs)} 次，行: {locs[:10]}{'...' if len(locs)>10 else ''}")

    # 2. 套娃结构（同句/邻句 首先+其次+最后）
    print("\n## 2. 套娃结构（首先/其次/最后 同段）")
    struct_hits = 0
    for i, ln in enumerate(lines, 1):
        if ("首先" in ln and "其次" in ln) or ("其次" in ln and "最后" in ln) or ("首先" in ln and "最后" in ln):
            struct_hits += 1
            total_hits += 1
            print(f"   ! 行 {i}: 含连续套娃连接词，建议改成因果/并列逻辑句")
    if struct_hits == 0:
        print("   ✓ 未检出套娃连接结构。")

    # 3. 零信息句
    print("\n## 3. 零信息句（含空话词但无数字）")
    empty_hits = 0
    for i, ln in enumerate(lines, 1):
        if any(w in ln for w in EMPTY_WORDS):
            if not re.search(r"\d", ln):
                empty_hits += 1
                total_hits += 1
                print(f"   ! 行 {i}: 含空话词但无数字，改写为带量化结论的句子")
    if empty_hits == 0:
        print("   ✓ 未检出零信息空话句。")

    # 4. 疑似抄题面（弱）
    print("\n## 4. 疑似抄题面（弱启发式）")
    copy_hits = [i for i, ln in enumerate(lines, 1) if any(w in ln for w in COPY_HINT_WORDS) and len(ln) > 120]
    if not copy_hits:
        print("   ✓ 未发现明显的整段复述题面。")
    else:
        for i in copy_hits[:10]:
            total_hits += 1
            print(f"   ! 行 {i}: 同时出现解题指代词且句过长，确认是转述而非抄题")

    # 5. 空话密度（建模/结果段无数字）
    print("\n## 5. 长段无数字（建模/结果段落应为异常）")
    nodigit = [i for i, ln in enumerate(lines, 1) if len(ln) > 40 and not re.search(r"\d", ln)
               and ("模型" in ln or "结果" in ln or "本文" in ln or "我们" in ln)]
    if not nodigit:
        print("   ✓ 未发现超 40 字且不含数字的关键段落。")
    else:
        for i in nodigit[:10]:
            total_hits += 1
            print(f"   ! 行 {i}: 关键段落超 40 字但无数字，补具体数值")

    print(f"\n[dedup_scan] 共 {total_hits} 处命中。逐句改写后再过一次，目标趋近 0。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
