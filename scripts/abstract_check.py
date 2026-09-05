#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""摘要国一化检查（abstract_check.py）——数字密度 + 四要素覆盖 + 灵敏度 + 套娃词 + 数字对账。

摘要占评分大头（30/100，评委第一印象）。本脚本把"摘要写得好不好"变成可量化的检查：

    python abstract_check.py 摘要.txt
    python abstract_check.py 论文.md --section 摘要          # 从论文提取"摘要"小节
    python abstract_check.py 摘要.txt --results out/results.json   # 数字对账（铁律二）
    python abstract_check.py 摘要.txt --min-words 800 --max-words 1000  # 国赛摘要页字数带

输出: 字数 / 数字密度 / 无数字句 / 四要素覆盖 / 灵敏度结论 / 套娃空话 / 数字对账，
     每项给 PASS/FAIL 与改法。配套手册见 references/abstract-crafting.md。
"""
import argparse
import json
import os
import re
import sys

# ── 数字提取：数字（含单位或纯小数/整数）算关键数字；
#    排除"图表式附第"编号；裸 4 位整数视为年份/编号，不计入 ──
_NUM = re.compile(r"(?<![图表式附第])\d+(?:\.\d+)?\s*(?:[%％‰万亿元吨公里千米kmkg℃°C度人家个倍小时天ms类名位月日级次]|)")
_YEAR = re.compile(r"^\d{4}$")

# 四要素启发式关键词
_KW = {
    "问题": ["针对", "研究了", "本文", "问题", "围绕", "基于", "面向"],
    "方法": ["模型", "构建", "提出", "采用", "算法", "方法", "设计", "建立", "融合", "改进"],
    "结果": ["结果表明", "得到", "误差", "精度", "准确率", "R²", "Mape", "MAPE", "RMSE", "拟合", "优化", "求解"],
    "结论": ["综上", "因此", "表明", "适用于", "推广", "可为", "可应用于", "提供了"],
}
_KW["结果"] = _KW["结果"] + ["可达", "达到", "降低", "提升", "优于"]
_KW["结论"] = _KW["结论"] + ["为决策", "对实际", "提供参考"]

_SENS = ["灵敏度", "稳健", "摄动", "扰动", "±", "波动", "鲁棒"]
_FLUFF = ["首先", "其次", "最后", "众所周知", "显而易见", "不言而喻", "众所周知地", "综上所述，我们"]


def _console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass


def extract_abstract(text, section="摘要"):
    """从论文文本提取摘要段：从「摘要」标题到「关键词」/「一、」/「1.」之前。"""
    m = re.search(rf"{section}", text)
    if not m:
        return text.strip()
    start = m.end()
    cut = re.search(r"(关键词|关键字|目录|\n\s*[一二三四五六七八九十]+[、．.]|\n\s*\d+[、．.])", text[start:])
    end = start + cut.start() if cut else len(text)
    return text[start:end].strip()


def key_numbers(text):
    """提取关键数字列表（(数字+单位, 原token)）；裸 4 位整数视为年份不计，带单位不排除。"""
    out = []
    for tok in _NUM.findall(text):
        num = re.match(r"\d+(?:\.\d+)?", tok).group()
        unit = tok[len(num):].strip()
        if not unit and _YEAR.match(num.strip()):
            continue  # 裸 4 位整数 = 年份/编号
        out.append(tok.strip())
    return out


def sentences(text):
    return [s.strip() for s in re.split(r"[。！？!?；;]", text) if s.strip()]


def check(text, results_path=None, min_words=800, max_words=1000):
    lines = []
    words = len(re.sub(r"\s", "", text))
    nums = key_numbers(text)
    sents = sentences(text)

    lines.append(f"摘要字数：{words}（国赛摘要页通行 800–1000 字）")
    if words < min_words * 0.6:
        lines.append("  [FAIL] 字数过少，信息量不足；按四段式补方法/结果细节")
    elif words > max_words * 1.2:
        lines.append("  [WARN] 字数超带，注意摘要页一页放得下（排版红线）")
    else:
        lines.append("  [PASS] 字数在合理带内")

    lines.append(f"\n关键数字：{len(nums)} 个  |  密度 {len(nums)/max(words/100,1):.1f} 个/百字")
    if len(nums) < 6:
        lines.append("  [FAIL] 数字太少（国一摘要 ≥6 个具体数字，每句尽量 1 个）；去 results.json 找数字补进结果句")
    else:
        lines.append("  [PASS] 数字密度合格")

    no_num = [s for s in sents if not key_numbers(s)]
    lines.append(f"\n句子总数：{len(sents)}，无数字句：{len(no_num)} 句")
    for s in no_num[:5]:
        lines.append(f"  [WARN] 无数字句：{s[:50]}…" if len(s) > 50 else f"  [WARN] 无数字句：{s}")

    lines.append("\n四要素覆盖（问题/方法/结果/结论 + 灵敏度）：")
    text_l = text.lower()
    for k, kws in _KW.items():
        hit = [k for k in kws if k in text_l or k.lower() in text_l]
        lines.append(f"  {'[PASS]' if hit else '[FAIL]'} {k}：{'、'.join(hit[:4]) if hit else '未检出 → 补一句'} ")
    sens = [s for s in _SENS if s in text]
    lines.append(f"  {'[PASS]' if sens else '[FAIL]'} 灵敏度量化结论：{('、'.join(sens)) if sens else '未检出 → 加一句\"±10% 摄动下结论稳健\"'}")

    fluff = [f for f in _FLUFF if f in text]
    lines.append(f"\n套娃/空话词：{len(fluff)} 处" + (f"（{'、'.join(fluff)}）→ 删或换具体表述" if fluff else " → [PASS] 无"))

    if results_path:
        lines.append("\n数字对账（铁律二：摘要数字须能在 results.json 找到）：")
        try:
            with open(results_path, "r", encoding="utf-8-sig") as f:  # utf-8-sig 兼容 BOM
                data = json.load(f)
            vals = {str(v) for v in _flatten(data)}
            miss = [n for n in nums if not any(v == re.match(r"\d+(?:\.\d+)?", n).group() or
                                             _close(v, re.match(r"\d+(?:\.\d+)?", n).group()) for v in vals)]
            if miss:
                lines.append(f"  [FAIL] 以下数字未在 results.json 对账到：{', '.join(miss[:8])} → 补进 results.json 或核对口径")
            else:
                lines.append("  [PASS] 摘要关键数字均可在 results.json 找到")
        except Exception as e:
            lines.append(f"  [WARN] 对账失败（{type(e).__name__}: {str(e)[:80]}），跳过")

    lines.append("\n" + "=" * 46)
    lines.append("结论：摘要已按四要素+数字密度过检 → 全文数字一致性再跑 crosscheck.py；")
    lines.append("      写作细化（四段式模板/修辞清单）见 references/abstract-crafting.md")
    return "\n".join(lines)


def _flatten(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _flatten(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _flatten(v)
    elif isinstance(obj, (int, float)):
        yield obj


def _close(a, b, tol=0.01):
    try:
        return abs(float(a) - float(b)) <= tol * max(1, abs(float(b)))
    except Exception:
        return False


def main():
    _console()
    ap = argparse.ArgumentParser(description="摘要国一化检查（数字密度/四要素/灵敏度/套娃词/数字对账）")
    ap.add_argument("file", help="摘要文本文件，或论文 md（配合 --section）")
    ap.add_argument("--section", default="", help="从论文提取指定小节（如 摘要）")
    ap.add_argument("--results", default="", help="results.json 路径，做摘要数字对账")
    ap.add_argument("--min-words", type=int, default=800)
    ap.add_argument("--max-words", type=int, default=1000)
    args = ap.parse_args()

    try:
        with open(args.file, "r", encoding="utf-8-sig") as f:
            raw = f.read()
    except Exception as e:
        print(f"[err] 读取失败: {e}", file=sys.stderr)
        return 2

    text = extract_abstract(raw, args.section) if args.section else raw.strip()
    if not text:
        print("[err] 摘要为空", file=sys.stderr)
        return 2
    print(check(text, args.results or None, args.min_words, args.max_words))
    return 0


if __name__ == "__main__":
    sys.exit(main())
