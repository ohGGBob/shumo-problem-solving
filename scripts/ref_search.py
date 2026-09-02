#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ref_search.py —— 参考文献真实检索与核验（OpenAlex API，零第三方依赖，需联网）

铁律一「先验证、后引用」的自动化武器：
  - 搜索：按关键词搜真实文献，直出 GB/T 7714 著录草稿（国赛）——杜绝"凭记忆编一条"
  - 核验：给 DOI/标题，确认是否真实存在；核不过 = 不得引用

用法:
    python ref_search.py <搜索词>                    # 搜索，默认 8 条
    python ref_search.py <搜索词> --limit 5          # 控制条数
    python ref_search.py --json <搜索词>             # 机读 JSON 输出
    python ref_search.py --verify "10.1016/j.apm.2019.05.044"   # 按 DOI 核验
    python ref_search.py --verify "multivariable grey prediction model"  # 按标题核验

说明:
    - OpenAlex 对英文期刊覆盖好；**中文文献（知网系）覆盖有限**，中文文献仍须在
      知网/期刊官网人工核验后再引用（本工具搜不到 ≠ 中文文献不存在）。
    - 自动核验只保证"这篇文献存在"；著录字段（卷期页码）仍要对照原文逐字确认。
    - 需要联网；离线时按 SKILL.md「脚本不可运行时手工清单」第 ③ 条人工核。
"""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.openalex.org/works"
MAILTO = "shumo-skill@example.com"  # OpenAlex 礼貌池，提高限速配额


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": f"shumo-skill/1.9 (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _authors(w, max_n=3):
    out = []
    for a in (w.get("authorships") or [])[:max_n]:
        n = (a.get("author") or {}).get("display_name") or ""
        if n:
            out.append(n)
    more = len(w.get("authorships") or []) - len(out)
    return out, (more if more > 0 else 0)


def _journal(w):
    src = (w.get("primary_location") or {}).get("source") or {}
    return src.get("display_name") or ""


def _biblio(w):
    b = w.get("biblio") or {}
    vol = b.get("volume") or ""
    iss = b.get("issue") or ""
    fp, lp = b.get("first_page") or "", b.get("last_page") or ""
    pages = f"{fp}-{lp}" if fp and lp and str(fp) != str(lp) else (str(fp) if fp else "")
    return vol, iss, pages


def gbt7714(w):
    """GB/T 7714 著录草稿（英文文献口径；卷期页缺失处留空待人工补）。"""
    auths, more = _authors(w, max_n=3)
    names = ", ".join(auths) + (", et al" if more else "")
    if not names:
        names = "Anon"
    title = w.get("display_name") or ""
    j = _journal(w)
    year = w.get("publication_year") or ""
    vol, iss, pages = _biblio(w)
    volpart = f"{vol}" + (f"({iss})" if iss else "")
    tail = ", ".join(p for p in [volpart, pages] if p)
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    return f"{names}. {title}[J]. {j}, {year}" + (f", {tail}" if tail else "") + (f". DOI: {doi}." if doi else ".")


def _fmt_hit(w, idx):
    auths, more = _authors(w, max_n=3)
    cited = w.get("cited_by_count") or 0
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    lines = [
        f"[{idx}] {(w.get('display_name') or '')[:90]}",
        f"    作者: {', '.join(auths)}" + (f" 等{more}人" if more else ""),
        f"    期刊: {_journal(w)}  年份: {w.get('publication_year')}",
        f"    DOI: {doi or '(无)'}  被引: {cited}",
        f"    GB/T 7714 草稿: {gbt7714(w)}",
    ]
    return "\n".join(lines)


def search(query, limit=8, as_json=False):
    q = urllib.parse.quote(query)
    url = f"{API}?search={q}&per-page={min(limit, 25)}&mailto={MAILTO}"
    try:
        data = _get(url)
    except Exception as e:
        print(f"[网络失败] {type(e).__name__}: {str(e)[:120]}")
        print("→ 离线/受限时：按铁律一人工联网核验（知网 / PubMed / doi.org / 期刊官网），禁止凭记忆著录。")
        return 2
    results = data.get("results") or []
    if as_json:
        slim = [{"title": w.get("display_name"), "year": w.get("publication_year"),
                 "journal": _journal(w), "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                 "authors": [(a.get("author") or {}).get("display_name") or "" for a in (w.get("authorships") or [])],
                 "gbt7714": gbt7714(w)} for w in results]
        print(json.dumps(slim, ensure_ascii=False, indent=2))
        return 0
    print(f"搜索「{query}」→ {len(results)} 条真实结果（OpenAlex，英文覆盖为主）\n")
    for i, w in enumerate(results, 1):
        print(_fmt_hit(w, i))
    print("\n⚠️ 铁律一：以上为【真实存在】的候选，著录字段仍须对照原文核对后才能写入论文；")
    print("   中文文献 OpenAlex 覆盖有限，搜不到 ≠ 不存在，请到知网/官网人工核验。")
    return 0


def verify(key, as_json=False):
    key = key.strip()
    if key.lower().startswith("10.") or "doi.org" in key.lower():
        doi = key.replace("https://doi.org/", "")
        url = f"{API}/works/https://doi.org/{urllib.parse.quote(doi)}?mailto={MAILTO}"
    else:
        url = f"{API}?search={urllib.parse.quote(key)}&per-page=1&mailto={MAILTO}"
    try:
        w = _get(url)
        if "results" in w:
            w = (w.get("results") or [None])[0]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[不存在] OpenAlex 无此 DOI（404）→ 按铁律一：核实失败即视为不存在，禁止引用。")
            return 1
        print(f"[网络失败] HTTP {e.code}: {str(e.reason)[:100]}")
        print("→ 核验失败按「核实失败即视为不存在」处理：不得写入论文，或换网络后重试。")
        return 2
    except Exception as e:
        print(f"[网络失败] {type(e).__name__}: {str(e)[:120]}")
        print("→ 核验失败按「核实失败即视为不存在」处理：不得写入论文，或换网络后重试。")
        return 2
    if not w or not w.get("id"):
        print(f"[不存在] 未检索到「{key}」→ 按铁律一：核实失败即视为不存在，禁止引用。")
        return 1
    if as_json:
        print(json.dumps({"title": w.get("display_name"), "year": w.get("publication_year"),
                          "journal": _journal(w), "gbt7714": gbt7714(w),
                          "doi": (w.get("doi") or "").replace("https://doi.org/", "")},
                         ensure_ascii=False, indent=2))
    else:
        print(f"[存在 ✓] 核验通过，可用（著录仍须对照原文）:\n")
        print(_fmt_hit(w, 1))
    return 0


def main():
    ap = argparse.ArgumentParser(description="参考文献真实检索与核验（OpenAlex；铁律一自动化）")
    ap.add_argument("query", nargs="*", help="搜索词，或 --verify 后接 DOI/标题")
    ap.add_argument("--limit", type=int, default=8, help="搜索返回条数（默认 8）")
    ap.add_argument("--verify", action="store_true", help="核验模式：确认 DOI/标题真实存在")
    ap.add_argument("--json", action="store_true", help="JSON 机读输出")
    args = ap.parse_args()
    q = " ".join(args.query).strip()
    if not q:
        ap.print_help()
        return 2
    if args.verify:
        return verify(q, as_json=args.json)
    return search(q, limit=args.limit, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
