#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""参考文献核验清单 + 孤儿条目检测。

用法:
    python verify_refs.py <论文.md|论文.tex|论文.docx> [--out refs_checklist.md]

功能:
    1. 抽出参考文献表条目（支持 GB/T 7714 [n] 编号条目 / 方括号引用）。
    2. 抽出正文引用键（[1] [2-4] 等）。
    3. 检测"孤儿条目"（文献表有、正文无引用）与"悬空引用"（正文引用、表内无）。
    4. 输出"待联网核验清单"：标注每条已有字段，提示需核实 DOI/作者/年份/卷期/页码。
    5. 编造风险预警：条目明显缺字段、或作者/年份像占位符。

说明: 本脚本只做本地结构化检查，不联网。联网核实动作由人/AI 按清单逐条完成
      （见 SKILL.md「铁律一·参考文献」）。
"""
import argparse
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


def split_ref_section(text):
    """粗略切出参考文献区段（在 '参考文献'/'References'/'REFERENCES' 标题之后）。"""
    idx = -1
    for kw in ["参考文献", "References", "REFERENCES", "引用文献"]:
        m = re.search(rf"^#*\s*{kw}\s*$", text, re.MULTILINE)
        if m:
            idx = m.end()
            break
    if idx < 0:
        return "", text
    return text[idx:], text[:idx]


def parse_entries(ref_section):
    """解析编号条目 [1] ... [2] ... 或逐行条目。"""
    entries = []
    # 编号条目：[1] 作者. 题名[文献类型]. 出处, 年.
    for m in re.finditer(r"\[(\d+)\][^\n]*(?:\n(?!\s*\[\d+\])[^\n]*)*", ref_section):
        entries.append((int(m.group(1)), m.group(0).strip()))
    if not entries:
        # 退化为非空行
        for i, line in enumerate(re.split(r"\n+", ref_section), 1):
            line = line.strip()
            if len(line) > 8:
                entries.append((i, line))
    return entries


def body_cites(body):
    cites = set()
    for m in re.finditer(r"\[(\d+(?:[-,]\d+)*)\]", body):
        for part in m.group(1).split(","):
            if "-" in part:
                a, b = part.split("-")
                try:
                    cites.update(range(int(a), int(b) + 1))
                except ValueError:
                    pass
            else:
                try:
                    cites.add(int(part))
                except ValueError:
                    pass
    return cites


def field_completeness(entry_text):
    has_author = bool(re.search(r"[\u4e00-\u9fa5a-zA-Z]{2,}", entry_text.split(".", 1)[0]))
    has_year = bool(re.search(r"(19|20)\d{2}", entry_text))
    has_doi = "doi" in entry_text.lower() or re.search(r"10\.\d{4,9}/[^\s]+", entry_text)
    has_pages = bool(re.search(r"\d+\s*[-–]\s*\d+", entry_text)) or "pp" in entry_text.lower()
    return {
        "author": has_author,
        "year": has_year,
        "doi": has_doi,
        "pages": has_pages,
    }


def main():
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="参考文献核验清单与孤儿条目检测")
    ap.add_argument("paper")
    ap.add_argument("--out", default=None, help="输出核验清单 md，默认打印到终端")
    args = ap.parse_args()

    if not os.path.exists(args.paper):
        print(f"[err] 论文不存在: {args.paper}", file=sys.stderr)
        return 1

    text = read_text(args.paper)
    ref_section, body = split_ref_section(text)
    entries = parse_entries(ref_section)
    cites = body_cites(body)
    entry_ids = {i for i, _ in entries}

    lines = []
    lines.append("# 参考文献核验清单\n")
    lines.append(f"- 文献表条目数: {len(entries)}")
    lines.append(f"- 正文引用键: {sorted(cites)}\n")

    orphans = entry_ids - cites
    dangling = cites - entry_ids
    if orphans:
        lines.append(f"## ⚠ 孤儿条目（文献表有、正文未引用）: {sorted(orphans)}")
    if dangling:
        lines.append(f"## ⚠ 悬空引用（正文引用、文献表无对应）: {sorted(dangling)}")
    if not orphans and not dangling:
        lines.append("## ✓ 引用键与文献表一一对应，无孤儿/悬空。\n")

    lines.append("## 逐条待联网核验")
    for eid, etext in entries:
        fc = field_completeness(etext)
        missing = [k for k, v in fc.items() if not v]
        tag = "✓" if not missing else "缺:" + ",".join(missing)
        lines.append(f"\n### [{eid}] 字段完整性: {tag}")
        lines.append(f"> {etext[:200]}")
        if missing:
            lines.append(f"- 联网核实重点: 补全 {', '.join(missing)}，并逐字段比对原文（作者/年份/刊名/卷期/页码/DOI）")
        else:
            lines.append("- 联网核实: 逐字段比对原文，确认与数据库一致（尤其 DOI 与卷期页码）")

    lines.append("\n## 红线提醒")
    lines.append("- 凡不能联网核实的文献，删除或标注 [待核实]，严禁编造。")
    lines.append("- 引用键与文献表必须一一对应，无孤儿、无悬空。")

    out = "\n".join(lines)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[verify_refs] 清单已写出: {args.out}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
