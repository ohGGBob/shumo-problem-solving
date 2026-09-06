#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""降 AI 味 / 降重自查 v2：分层词库(中/英) + 密度统计 + 结构检测 + 题干 n-gram 比对。

用法:
    python dedup_scan.py <论文.md|.tex|.docx> [题干.txt] [--drop-repeat N] [--strip-header TEXT] [--dup-span N]

警告(踩坑): 用 PyMuPDF 等把 PDF 抽成文本再喂本脚本时，逐页重复的页眉/页脚会被当成正文，
    导致两类误报——"段首 X 字开局 N 段"(页面标题每页都出现)与"与题干 8 字片重合"。
    对策: 优先用 .tex/.md 源码分析；若只能用 PDF 文本，请加 --drop-repeat 或 --strip-header 剔掉版式行。

检查项（对应 writing-deai-dedup.md / deai-rewrite-bank.md / paper-quality-gate.md 关卡五）:
    1. 中文 AI 味词库（套娃连接 / 空话套话 / 政论腔 / 模糊词）
    2. 英文 AI 味词库（美赛 Summary 高频模板词）
    3. 密度统计：每千字命中率 + 命中数排名（告诉你哪类最刺眼）
    4. 结构检测：段首词重复 / 被动堆砌(被…被…被) / 等长排比
    5. 题干 n-gram 比对：传第二个参数(题干文本)，标出疑似直接抄题面的句子
    6. 查重式连续字符重复（对齐知网/维普连续匹配）：传题干时，扫与题干最大连续同文片段(默认 ≥7 字)，
       按「受保护(含数字/字母/公式) vs 待改写(纯中文)」分类，给出需改写重点——交稿前自检降重

命中 = 提醒而非禁用；同一类词**堆叠**才扣分，逐条改写见 deai-rewrite-bank.md。
仅用标准库（Python 3.8+），无第三方依赖。
"""
import argparse
import os
import re
import sys
from collections import Counter
from difflib import SequenceMatcher

# ── 中文 AI 味词库（分层）──────────────────────────────────────────
CN_CATS = [
    ("套娃连接/叙事模板", [
        "首先", "其次", "再次", "最后", "综上所述", "总而言之", "总之",
        "值得注意的是", "众所周知", "显而易见", "不言而喻", "毋庸置疑",
        "与此同时", "更进一步", "此外", "换句话说", "换言之",
        "在此基础上", "有鉴于此",
    ]),
    ("空话/套话", [
        "具有重要意义", "重要作用", "重大贡献", "广泛应用", "奠定基础",
        "提供有力支撑", "参考价值", "重要的理论意义", "实践价值",
        "不可或缺", "至关重要", "举足轻重", "日益重要", "越来越重要",
        "发挥着重要", "扮演着重要", "不可忽视", "必不可少",
    ]),
    ("政论腔/模板句式", [
        "随着.*发展", "在.*背景下", "本文提出了", "本文建立了", "本文通过",
        "本文首先", "采用.*方法", "进行.*分析", "做出.*贡献", "取得.*成果",
        "实现.*目标", "科学合理", "切实可行", "行之有效", "有效地",
        "显著提高", "有效提升", "大幅提升", "整体而言", "总体来看",
        "从某种意义",
    ]),
    ("模糊程度词", [
        "大约", "大概", "较为", "一定程度上", "初步", "大致", "若干", "诸多",
    ]),
]

# ── 英文 AI 味词库（美赛；含词干前缀以覆盖过去式/-ing）──────────────
EN_AI = [
    "delve", "furthermore", "moreover", "in summary", "in conclusion",
    "it is worth noting", "worth noting", "in today's world",
    "in recent years", "in the realm of", "shed light on", "pave the way",
    "a wide range of", "diverse array", "state-of-the-art", "cutting-edge",
    "plays a crucial role", "plays a pivotal role", "crucial", "pivotal",
    "paramount", "underscor", "significantly", "comprehensive", "holistic",
    "multifaceted", "intricate", "seamless", "unveil", "unlock",
    "showcas", "leverag", "utiliz", "facilitat", "robust", "revolutioniz",
]


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


def cjk_count(text):
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def en_word_count(text):
    return len(re.findall(r"[A-Za-z]+", text))


def paragraphs(lines):
    """把文本粗分成段落，返回 [(起始行号, 段落文本)]。"""
    paras, buf, start = [], [], 1
    for i, ln in enumerate(lines, 1):
        if not ln.strip() or re.match(r"^\s*#", ln):
            if buf:
                paras.append((start, " ".join(buf)))
                buf = []
            start = i + 1
        else:
            buf.append(ln)
    if buf:
        paras.append((start, " ".join(buf)))
    return paras


def shingles(s, n=8):
    s = re.sub(r"\s+", "", s)
    if len(s) < n:
        return set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def max_contiguous_spans(text, source, min_len):
    """(查重式) 找出 text 中同时出现在 source 里的最大连续同文字符片段，长度 >= min_len。

    返回 [(start, length, span)]，按 length 降序；记录后按该片段长度跳进步进，保证片段互不重叠。
    对齐「知网/维普式连续字符重复」自检：种子取 source 的 min_len 子串集合，命中后贪心向右扩展成最大连续片段。
    仅用字符串 in 判定，无第三方库；对数模论文规模足够，无需复杂后缀结构。
    """
    src = re.sub(r"\s+", "", source)
    t = re.sub(r"\s+", "", text)
    if min_len < 2 or len(src) < min_len:
        return []
    src_set = {src[j:j + min_len] for j in range(len(src) - min_len + 1)}
    spans = []
    i, n = 0, len(t)
    while i <= n - min_len:
        seed = t[i:i + min_len]
        if seed not in src_set:
            i += 1
            continue
        best = min_len
        while i + best < n and t[i:i + best + 1] in src:
            best += 1
        spans.append((i, best, t[i:i + best]))
        i += best
    spans.sort(key=lambda x: (-x[1], x[0]))
    return spans


def classify_span(span):
    """保护 vs 待改写：含数字/拉丁字母/百分号/单位/公式符号的片段多为专名、公式、数字或单位，
    检测系统通常识别为受保护内容，不建议动；纯中文连续片段才判为「待改写」。"""
    return "protected" if re.search(r"[0-9０-９A-Za-z%￥]", span) else "review"


def main():
    # 兼容 Windows 管道/GBK 控制台：统一输出 UTF-8，且遇到 ✓ 等特殊字符不崩溃。
    # 踩坑：只 reconfigure(errors=...) 不改编码时，父进程用 subprocess 捕获(非 tty)会按 cp936
    # 编码写出中文而乱码，甚至抛 UnicodeDecodeError；必须一并把 encoding 设成 utf-8。
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="降AI味与降重自查 v2")
    ap.add_argument("paper")
    ap.add_argument("source", nargs="?", default=None, help="题干/原题文本，用于查疑似抄题")
    ap.add_argument("--strip-header", action="append", default=None, metavar="TEXT",
                    help="删除等于 TEXT 的行(可多次)，用于去掉 PDF 逐页重复的页眉/页脚再分析")
    ap.add_argument("--drop-repeat", type=int, default=None, metavar="N",
                    help="删除出现 >= N 次的重复行(通常为逐页页眉/页脚)，降低'段首高频重复/题干重合'误报")
    ap.add_argument("--dup-span", type=int, default=7, metavar="N",
                    help="查重式连续字符重复自检阈值：与题干/来源匹配的最大连续同文字符数(默认 7)。传 0 关闭本项。")
    args = ap.parse_args()
    if not os.path.exists(args.paper):
        print(f"[err] 论文不存在: {args.paper}", file=sys.stderr)
        return 1

    text = read_text(args.paper)
    if not text.strip():
        print("[err] 论文内容为空或读取失败", file=sys.stderr)
        return 1
    lines = text.splitlines()
    orig_lines = len(lines)
    header_set = {h.strip() for h in (args.strip_header or []) if h.strip()}
    if args.drop_repeat and args.drop_repeat >= 2:
        cnt = Counter(ln.strip() for ln in lines if ln.strip())
        header_set |= {ln for ln, c in cnt.items() if c >= args.drop_repeat}
    if header_set:
        lines = [ln for ln in lines if ln.strip() not in header_set]
        print(f"[note] 已剔除 {orig_lines - len(lines)} 行页眉/页脚/重复版式行，"
              f"降低'段首高频重复/题干重合'的版式误报。\n")
    text = "\n".join(lines)
    total_hits = 0
    n_cjk = cjk_count(text)
    n_en = en_word_count(text)

    print(f"# 降 AI 味 / 降重自查 v2: {os.path.basename(args.paper)}\n")
    print(f"（中文字符 {n_cjk}，英文词 {n_en}）\n")

    # ── 1+2. 词库命中（中文分层 + 英文），带密度 ──────────────────
    print("## 1. 词库命中（中文分层 / 英文）")
    cn_counter = Counter()
    for cat, pats in CN_CATS:
        detail = {}
        for i, ln in enumerate(lines, 1):
            for p in pats:
                if re.search(p, ln):
                    detail.setdefault(p, []).append(i)
        cat_hits = 0
        for p, locs in detail.items():
            cn_counter[p] += len(locs)
            cat_hits += len(locs)
        total_hits += cat_hits
        rate = cat_hits / (n_cjk / 1000) if n_cjk else 0
        print(f"   [{cat}] {cat_hits} 次 · {rate:.1f} 次/千字")
        for p, locs in sorted(detail.items(), key=lambda kv: -len(kv[1]))[:6]:
            print(f"      「{p}」 {len(locs)} 次")

    en_counter = Counter()
    en_detail = {}
    for i, ln in enumerate(lines, 1):
        for p in EN_AI:
            if re.search(r"\b" + re.escape(p), ln, re.IGNORECASE):
                en_detail.setdefault(p, []).append(i)
    for p, locs in en_detail.items():
        en_counter[p] += len(locs)
    en_hits = sum(en_counter.values())
    total_hits += en_hits
    erate = en_hits / (n_en / 1000) if n_en else 0
    print(f"   [英文 AI 味词] {en_hits} 次 · {erate:.1f} 次/千词")
    for p, c in en_counter.most_common(8):
        print(f"      「{p}」 {c} 次")

    # ── 命中数排名（跨类）──────────────────────────────────────────
    print("\n## 2. 命中数排名（Top 8，先改这些）")
    merged = Counter(cn_counter)
    merged.update(en_counter)
    if merged:
        for p, c in merged.most_common(8):
            print(f"   {c:>2} 次  {p}")
    else:
        print("   ✓ 未命中任何词库条目。")

    # ── 3. 结构检测 ────────────────────────────────────────────────
    print("\n## 3. 结构检测")

    # 段首词重复
    opener = Counter()
    for _, t in paragraphs(lines):
        t2 = re.sub(r"^\s*[#>\-*\d\.、）\)\|\s]+", "", t).strip()
        if len(t2) < 2 or not re.search(r"[\u4e00-\u9fffA-Za-z]", t2):
            continue
        opener[t2[:2]] += 1
    dup_openers = {w: c for w, c in opener.items() if c >= 3}
    if dup_openers:
        for w, c in sorted(dup_openers.items(), key=lambda kv: -kv[1]):
            total_hits += 1
            print(f"   ! 段首 2 字「{w}」开局 {c} 段——段首模板化，换措辞或加具体主语")
    else:
        print("   ✓ 段首未见高频重复开局。")

    # 被动堆砌
    passive = [i for i, ln in enumerate(lines, 1) if ln.count("被") >= 3]
    if passive:
        for i in passive[:5]:
            total_hits += 1
            print(f"   ! 行 {i}：出现 ≥3 个「被」，改主动语态")
    else:
        print("   ✓ 未见被动堆砌（单行 ≥3 被）。")

    # 等长排比（一句内 3+ 个等长分句）
    flagged_para = 0
    for i, ln in enumerate(lines, 1):
        if len(re.findall(r"[，,、;；]", ln)) < 2:
            continue
        clauses = [c for c in re.split(r"[，,、;；]", ln) if len(c.strip()) >= 6]
        if len(clauses) >= 3:
            lens = [len(c) for c in clauses]
            if max(lens) - min(lens) <= 2:
                flagged_para += 1
                total_hits += 1
                if flagged_para <= 5:
                    print(f"   ! 行 {i}：出现 ≥3 个长度近似的排比分句，打破节奏")
    if flagged_para == 0:
        print("   ✓ 未见等长排比。")

    # ── 4. 题干 n-gram 比对（疑似抄题）─────────────────────────────
    print("\n## 4. 题干 n-gram 比对（疑似抄题面）")
    if not args.source:
        print("   (未提供题干文件；用法：python dedup_scan.py 论文.md 题干.txt 以启用本项)")
    elif not os.path.exists(args.source):
        print(f"   [warn] 题干文件不存在: {args.source}")
    else:
        src = read_text(args.source)
        if not src.strip():
            print("   [warn] 题干为空")
        else:
            src_shingles = shingles(src, 8)
            src_norm = re.sub(r"\s+", "", src)
            flagged = 0
            for i, ln in enumerate(lines, 1):
                norm = re.sub(r"\s+", "", ln)
                if len(norm) < 15:
                    continue
                win = shingles(norm, 8)
                if not win:
                    continue
                frac = sum(1 for w in win if w in src_shingles) / len(win)
                if frac >= 0.5:
                    lcs = SequenceMatcher(None, norm, src_norm).find_longest_match(
                        0, len(norm), 0, len(src_norm)).size
                    flagged += 1
                    total_hits += 1
                    if flagged <= 8:
                        print(f"   ! 行 {i}：与题干 8 字片重合率 {frac:.0%}，最长连续同文 {lcs} 字——确认是转述而非照抄")
            if flagged == 0:
                print("   ✓ 未发现与题干高重合的整句。")

    # ── 5. 查重式连续字符重复（对齐知网/维普连续匹配；--dup-span 控制阈值）──
    print("\n## 5. 连续字符重复（查重式 · 对齐知网/维普连续匹配）")
    if not args.source or args.dup_span <= 0:
        print("   (未提供题干文件或 --dup-span=0；传题干文件即启用本项)")
    elif not os.path.exists(args.source):
        print(f"   [warn] 题干文件不存在: {args.source}")
    else:
        src = read_text(args.source)
        if not src.strip():
            print("   [warn] 题干为空")
        else:
            spans = max_contiguous_spans(text, src, args.dup_span)
            cjk = cjk_count(text)
            review = [s for s in spans if classify_span(s[2]) == "review"]
            prot = [s for s in spans if classify_span(s[2]) == "protected"]
            rev_chars = sum(s[1] for s in review)
            print(f"   与题干最大连续同文片段(≥{args.dup_span} 字)：共 {len(spans)} 段，"
                  f"其中受保护(含数字/字母/公式) {len(prot)} 段，待改写(纯中文) {len(review)} 段")
            if cjk:
                print(f"   待改写连续重复字数 {rev_chars}，占全文中文 {rev_chars / cjk:.1%}")
            for (start, length, span) in review[:10]:
                total_hits += 1
                print(f"   ! [{length} 字] 「{span}」")
            if not review:
                print(f"   ✓ 未发现 ≥{args.dup_span} 字的纯中文连续同文片段。")
            print("   (受保护片段=专名/公式/数字/单位，检测系统常识别为受保护内容；纯中文连续片段才是改写重点。)")

    print(f"\n[dedup_scan] 共 {total_hits} 处命中/提醒。"
          f"命中=提醒而非禁用，同词堆叠才扣分；逐条改写见 writing-deai-dedup.md / deai-rewrite-bank.md。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())