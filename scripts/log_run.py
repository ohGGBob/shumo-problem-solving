#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""极简实验追踪器（72h 内试 10+ 版本时的救命稻草）。

用法:
    # 在 qN.py 里 import 并记录一次运行
    from log_run import log_run
    log_run(question="q1", model="RFMS", params={"w": 0.3, "k": 5},
            metrics={"opt_val": 123.45, "mape": 2.3}, duration_s=12.5,
            git_commit="abc1234", note="基线版本")

    # CLI 查看历史
    python log_run.py list
    python log_run.py show q1
    python log_run.py best q1 --metric mape --minimize

    # 导出模型演进图（CSV → 供 review_survey.py 用）
    python log_run.py export --out out/runs.csv

文件: out/runs.jsonl (逐行 JSON，追加写入，断电不丢)
       out/runs.csv   (导出用，列: timestamp,question,model,git_commit,params_json,metrics_json,duration_s,note)
"""
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_LOG_DIR = "out"
LOG_FILE = "runs.jsonl"
CSV_FILE = "runs.csv"


def get_git_commit() -> str:
    """获取当前 git 短提交哈希，失败返回 'nogit'"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=2
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "nogit"


def get_git_dirty() -> bool:
    """检查工作区是否有未提交变更"""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=2
        )
        return bool(out.stdout.strip())
    except Exception:
        return False


def param_hash(params: Dict[str, Any]) -> str:
    """参数字典的短哈希（用于快速去重/比对）"""
    s = json.dumps(params, sort_keys=True, separators=(",", ":"))
    return hashlib.md5(s.encode()).hexdigest()[:8]


def ensure_log_dir(log_dir: str = DEFAULT_LOG_DIR) -> Path:
    p = Path(log_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def log_run(
    question: str,
    model: str,
    params: Dict[str, Any],
    metrics: Dict[str, float],
    duration_s: float,
    note: str = "",
    git_commit: Optional[str] = None,
    log_dir: str = DEFAULT_LOG_DIR,
) -> Dict[str, Any]:
    """记录一次实验运行，返回记录字典"""
    log_path = ensure_log_dir(log_dir) / LOG_FILE

    if git_commit is None:
        git_commit = get_git_commit()

    record = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "model": model,
        "params": params,
        "param_hash": param_hash(params),
        "metrics": metrics,
        "duration_s": round(duration_s, 2),
        "git_commit": git_commit,
        "git_dirty": get_git_dirty(),
        "note": note,
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 同时追加 CSV（方便 Excel 打开）
    csv_path = ensure_log_dir(log_dir) / CSV_FILE
    csv_exists = csv_path.exists()
    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not csv_exists:
            writer.writerow([
                "timestamp", "question", "model", "git_commit", "git_dirty",
                "param_hash", "params_json", "metrics_json", "duration_s", "note"
            ])
        writer.writerow([
            record["timestamp"], question, model, git_commit, record["git_dirty"],
            record["param_hash"], json.dumps(params, ensure_ascii=False),
            json.dumps(metrics, ensure_ascii=False), duration_s, note
        ])

    print(f"[log_run] {question} | {model} | {param_hash(params)} | "
          f"{', '.join(f'{k}={v}' for k, v in metrics.items())} | {duration_s:.1f}s")
    return record


def load_runs(log_dir: str = DEFAULT_LOG_DIR) -> List[Dict[str, Any]]:
    log_path = Path(log_dir) / LOG_FILE
    if not log_path.exists():
        return []
    runs = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                runs.append(json.loads(line))
    return runs


def filter_runs(runs: List[Dict], question: Optional[str] = None,
                model: Optional[str] = None) -> List[Dict]:
    res = runs
    if question:
        res = [r for r in res if r["question"] == question]
    if model:
        res = [r for r in res if r["model"] == model]
    return res


def print_runs_table(runs: List[Dict]):
    if not runs:
        print("(无记录)")
        return
    # 表头
    print(f"{'时间':<19} {'问':<4} {'模型':<12} {'参数哈希':<8} {'指标':<40} {'耗时':>6} {'提交':<8} {'备注'}")
    print("-" * 120)
    for r in runs:
        metrics_str = ", ".join(f"{k}={v:.4g}" for k, v in r["metrics"].items())
        if len(metrics_str) > 38:
            metrics_str = metrics_str[:35] + "..."
        dirty = "!" if r.get("git_dirty") else ""
        print(f"{r['timestamp']:<19} {r['question']:<4} {r['model']:<12} "
              f"{r['param_hash']:<8} {metrics_str:<40} {r['duration_s']:>5.1f}s "
              f"{r['git_commit']:<8}{dirty} {r.get('note','')}")


def find_best(runs: List[Dict], metric: str, minimize: bool = True) -> Optional[Dict]:
    """按指标找最优运行"""
    valid = [r for r in runs if metric in r["metrics"]]
    if not valid:
        return None
    return min(valid, key=lambda r: r["metrics"][metric]) if minimize else \
           max(valid, key=lambda r: r["metrics"][metric])


def export_csv(runs: List[Dict], out_path: str):
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "question", "model", "git_commit", "git_dirty",
            "param_hash", "params_json", "metrics_json", "duration_s", "note"
        ])
        for r in runs:
            writer.writerow([
                r["timestamp"], r["question"], r["model"], r["git_commit"], r["git_dirty"],
                r["param_hash"], json.dumps(r["params"], ensure_ascii=False),
                json.dumps(r["metrics"], ensure_ascii=False), r["duration_s"], r.get("note", "")
            ])
    print(f"[log_run] 已导出 {len(runs)} 条记录 -> {out_path}")


def main():
    ap = argparse.ArgumentParser(description="极简实验追踪器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # list
    p_list = sub.add_parser("list", help="列出所有运行记录")
    p_list.add_argument("--question", "-q", help="按问题筛选")
    p_list.add_argument("--model", "-m", help="按模型筛选")
    p_list.add_argument("--dir", "-d", default=DEFAULT_LOG_DIR, help="日志目录")

    # show
    p_show = sub.add_parser("show", help="显示某问题的所有运行")
    p_show.add_argument("question", help="问题名，如 q1")
    p_show.add_argument("--dir", "-d", default=DEFAULT_LOG_DIR)

    # best
    p_best = sub.add_parser("best", help="按指标找最优运行")
    p_best.add_argument("question", help="问题名")
    p_best.add_argument("--metric", required=True, help="指标名，如 mape、opt_val")
    p_best.add_argument("--minimize", action="store_true", default=True,
                        help="越小越好（默认）")
    p_best.add_argument("--maximize", action="store_true", help="越大越好")
    p_best.add_argument("--dir", "-d", default=DEFAULT_LOG_DIR)

    # export
    p_export = sub.add_parser("export", help="导出 CSV")
    p_export.add_argument("--out", "-o", default=None, help="输出路径，默认 out/runs.csv")
    p_export.add_argument("--dir", "-d", default=DEFAULT_LOG_DIR)

    # log（CLI 直接记录一条，少用）
    p_log = sub.add_parser("log", help="手动记录一条（调试用）")
    p_log.add_argument("--question", "-q", required=True)
    p_log.add_argument("--model", "-m", required=True)
    p_log.add_argument("--params", default="{}", help="JSON 字符串")
    p_log.add_argument("--metrics", required=True, help="JSON 字符串")
    p_log.add_argument("--duration", type=float, default=0)
    p_log.add_argument("--note", default="")
    p_log.add_argument("--dir", "-d", default=DEFAULT_LOG_DIR)

    args = ap.parse_args()

    runs = load_runs(args.dir)

    if args.cmd == "list":
        filtered = filter_runs(runs, args.question, args.model)
        print_runs_table(filtered)

    elif args.cmd == "show":
        filtered = filter_runs(runs, args.question)
        print_runs_table(filtered)

    elif args.cmd == "best":
        filtered = filter_runs(runs, args.question)
        minimize = not args.maximize
        best = find_best(filtered, args.metric, minimize)
        if best:
            print(f"[BEST] {best['question']} | {best['model']} | "
                  f"{args.metric}={best['metrics'][args.metric]:.4g} | "
                  f"params={best['param_hash']} | commit={best['git_commit']}")
            print(f"       完整指标: {best['metrics']}")
            print(f"       参数: {best['params']}")
            print(f"       备注: {best.get('note','')}")
        else:
            print(f"[best] 无匹配记录或指标 {args.metric} 不存在")

    elif args.cmd == "export":
        out = args.out or os.path.join(args.dir, CSV_FILE)
        export_csv(runs, out)

    elif args.cmd == "log":
        log_run(
            question=args.question,
            model=args.model,
            params=json.loads(args.params),
            metrics=json.loads(args.metrics),
            duration_s=args.duration,
            note=args.note,
            log_dir=args.dir,
        )


if __name__ == "__main__":
    raise SystemExit(main())