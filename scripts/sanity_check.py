#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量纲 / 量级 / 边界 自动校验（sanity check，服务逻辑严谨性支柱）。

两种用法：
1) 库用法（推荐，在 qN.py 里 import）：
       from sanity_check import check_number, check_bounds, summary
       check_number("time_to_empty_h", sol.t_events[0][0]/3600, low=0, high=24,
                    expect="续航应在 0–24h 量级")
       check_bounds("weight", w, low=0, high=1, close_sum=1.0)   # 权重非负且和为1
       check_bounds("prob", p, low=0, high=1)                    # 概率在[0,1]
       check_distinct("y_pred", y_pred, 2)                       # 预测至少有2种取值（防退化）
       summary()          # 结束时打印是否全部通过
2) CLI 用法（对 results.json 批量校验）：
       python sanity_check.py results.json \
           --rule "q1_optimal=0,1000" \
           --rule "q1_error_pct=0,20" \
           --nonneg q1_optimal \
           --bounds "weight_*:0,1,sum=1" \
           --distinct "y_pred_*:2"
   --rule  key=min,max     ：数值须在 [min,max]
   --nonneg key            ：须非负
   --bounds  glob:min,max[,sum=S] ：匹配 key 须在[low,high]，可选校验加和≈S
   --distinct glob:min     ：匹配 key 的数组取值多样性≥min（专抓"输出退化/集中"：
                             所有预测同一类、所有解相同 = 模型空转信号，对标社区
                             risk-probe 的 output degeneracy / concentration 检查）
   key 支持 * 通配（如 weight_*）。

原则：本脚本只报"明显不合理"，不代替人工判断；所有命中项都是"该解释/该修"的信号。
"""
import argparse
import json
import os
import re
import sys

_F = []  # 累积失败项
_P = []  # 累积通过项


def check(name, ok, msg, expect=""):
    """记录一次校验结果。"""
    if ok:
        _P.append(name)
        return True
    _F.append((name, msg, expect))
    return False


def check_number(name, value, low=None, high=None, expect="", eps=1e-9):
    """数值须在 [low, high]（可省略任一界），并解释预期。"""
    if value is None or (isinstance(value, float) and value != value):  # NaN
        return check(name, False, f"值为 NaN/None", expect)
    if low is not None and value < low - eps:
        return check(name, False, f"{value} < 下界 {low}", expect)
    if high is not None and value > high + eps:
        return check(name, False, f"{value} > 上界 {high}", expect)
    return check(name, True, f"{value} 在预期范围", expect)


def check_bounds(name, values, low=0, high=1, close_sum=None, eps=1e-3, expect=""):
    """批量数值须在 [low,high]，可选校验加和≈close_sum。"""
    arr = list(values)
    if not arr:
        return check(name, False, "空数组", expect)
    bad = [v for v in arr if not (low - eps <= v <= high + eps)]
    ok = not bad
    msg = f"越界值={bad[:5]}" if bad else f"全部在[{low},{high}]"
    check(name, ok, msg, expect)
    if close_sum is not None:
        s = sum(arr)
        check(f"{name}.sum", abs(s - close_sum) < eps, f"加和={s} 应≈{close_sum}",
              f"{name} 各分量应和为 {close_sum}")
    return ok


def check_distinct(name, values, min_unique, expect=""):
    """数组取值多样性须≥min_unique（防输出退化：全同值=模型空转/塌缩信号）。"""
    arr = list(values)
    if not arr:
        return check(name, False, "空数组", expect)
    uniq = len(set(arr))
    return check(name, uniq >= min_unique,
                 f"唯一值数={uniq}（要求≥{min_unique}）" if uniq < min_unique
                 else f"唯一值数={uniq}，多样性正常",
                 expect or "输出不应全部相同（退化/集中 = 模型未起作用，须解释或修模型）")


def _match_rule(key, pattern):
    """key 与 'weight_*' 这类带 * 的模式匹配。"""
    if pattern == key:
        return True
    if "*" in pattern:
        rx = re.escape(pattern).replace(r"\*", ".*")
        return re.fullmatch(rx, key) is not None
    return False


def _flatten(data, prefix=""):
    """展平嵌套字典为 [(扁平键, 值)]，供各类规则共用。"""
    items = []
    for k, v in data.items():
        name = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            items.extend(_flatten(v, name))
        else:
            items.append((name, v))
    return items


def validate_results(data, rules):
    """对 results.json 字典批量应用规则。rules: [(key, low, high, sum)] 其中 sum 可 None。"""
    walk = _flatten  # 兼容旧命名
    for key, low, high, close_sum in rules:
        matched = [(n, v) for n, v in walk(data) if _match_rule(n, key)]
        if not matched:
            check(key, False, "无匹配键", "检查键名/通配符")
            continue
        for n, v in matched:
            if isinstance(v, (int, float)):
                check_number(n, v, low, high, expect=f"规则 {key}: [{low},{high}]")
            elif isinstance(v, list):
                check_bounds(n, v, low, high, close_sum, expect=f"规则 {key}")
            else:
                check(n, False, f"类型 {type(v).__name__} 非数值", "只校验数值/数值数组")


def validate_distinct(data, rules):
    """对 results.json 应用多样性规则。rules: [(glob_key, min_unique)]。"""
    for key, min_unique in rules:
        matched = [(n, v) for n, v in _flatten(data) if _match_rule(n, key)]
        if not matched:
            check(f"distinct:{key}", False, "无匹配键", "检查键名/通配符")
            continue
        for n, v in matched:
            if isinstance(v, list):
                check_distinct(n, v, min_unique, expect=f"规则 distinct {key}: ≥{min_unique} 种取值")
            else:
                check(f"distinct:{n}", False, f"类型 {type(v).__name__} 非数组",
                      "--distinct 只校验数组（单值请用 --rule）")


def main():
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="量纲/量级/边界 sanity check")
    ap.add_argument("results_json", nargs="?", help="results.json（可选；省略则仅库用法）")
    ap.add_argument("--rule", action="append", default=[], help="key=min,max")
    ap.add_argument("--nonneg", action="append", default=[], help="须非负的 key")
    ap.add_argument("--bounds", action="append", default=[], help="glob:min,max[,sum=S]")
    ap.add_argument("--distinct", action="append", default=[],
                    help="glob:min（匹配 key 的数组取值多样性≥min，防输出退化）")
    args = ap.parse_args()

    rules = []
    for r in args.rule:
        key, _, rng = r.partition("=")
        lo, _, hi = rng.partition(",")          # "0,100" -> lo=0, hi=100
        rules.append((key.strip(), float(lo), float(hi), None))
    for k in args.nonneg:
        rules.append((k.strip(), 0, None, None))
    for b in args.bounds:
        key, _, rest = b.partition(":")
        parts = rest.split(",")
        lo, hi = float(parts[0]), float(parts[1])
        close_sum = float(parts[2].split("=")[1]) if len(parts) > 2 else None
        rules.append((key.strip(), lo, hi, close_sum))

    distinct_rules = []
    for d in args.distinct:
        key, _, rest = d.partition(":")
        distinct_rules.append((key.strip(), int(rest)))

    if args.results_json and os.path.exists(args.results_json):
        with open(args.results_json, encoding="utf-8-sig") as f:
            data = json.load(f)
        validate_results(data, rules)
        validate_distinct(data, distinct_rules)
    elif args.results_json:
        print(f"[err] 找不到 results.json: {args.results_json}", file=sys.stderr)
        return 1

    return _report()


def _report():
    print(f"\n[sanity] 通过 {len(_P)} 项，失败 {len(_F)} 项。")
    for name, msg, exp in _F:
        print(f"  ✗ {name}: {msg}" + (f"  (预期: {exp})" if exp else ""))
    for n in _P:
        print(f"  ✓ {n}")
    if _F:
        print("[sanity] 存在未通过项——请修复或显式解释后加入白名单。")
        return 1
    print("[sanity] ✓ 全部通过。")
    return 0


def summary():
    """库用法：在脚本结尾调用，打印校验结果。"""
    return _report()


if __name__ == "__main__":
    raise SystemExit(main())
