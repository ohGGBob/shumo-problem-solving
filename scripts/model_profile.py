#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模型画像工具（DeepSeek V4 Pro / V4 Flash 适配）。

本 skill 默认由 V4-Pro / V4-Flash 双引擎驱动。本工具按模型输出推荐执行配置：
token 预算、加载策略、任务分工、价格提示、升级/降级信号——帮执行者"想交给 Pro、做交给 Flash"。

用法:
    python model_profile.py              # 双模型对比总览
    python model_profile.py v4-pro       # V4-Pro 推荐配置
    python model_profile.py v4-flash     # V4-Flash 推荐配置
    python model_profile.py --json       # JSON 输出（供程序消费）

规格与价格为公开可核实信息，价格以官方定价页为准。
"""
from __future__ import annotations

import argparse
import json
import sys

PROFILES = {
    "v4-pro": {
        "name": "DeepSeek-V4-Pro",
        "params": "1.6T / 49B 激活 (MoE)",
        "context": "1M tokens / 输出 384K",
        "position": "高端推理 + Agentic Coding，复杂长链论证",
        "latency": "~800ms+ / 并发 ~500",
        "price": "输入 ¥3/M（缓存 ¥0.025）/ 输出 ¥6/M",
        "role": "主力干'想'——选型、创新设计、假设自洽、论文论证、复杂求解",
        "token_budget": "省着用：只喂当前环节关键 references（按 SKILL 路由表），长文档分页/摘要，别整库全读",
        "prompt": "开放式多方案推导；让 DeepThink 长链验证；给反例与取舍；输出论证链",
        "upgrade_signal": "（本档为最高推理档，无升级目标）",
        "downgrade_signal": "在跑机械校验/格式整理/批量改写 → 降级 v4-flash 省钱提速",
        "use_in_skill": "模型选型 / 创新点 / 假设自洽 / 论文成文 / 紧急模式推理环节（默认）",
    },
    "v4-flash": {
        "name": "DeepSeek-V4-Flash",
        "params": "284B / 13B 激活 (MoE)",
        "context": "1M tokens / 输出 384K",
        "position": "高并发、低成本、轻量任务，长文档全量消化",
        "latency": "~200-300ms / 并发 ~2500",
        "price": "输入 ¥1/M（缓存 ¥0.02）/ 输出 ¥2/M",
        "role": "主力干'做'——数据清洗、脚本批量、校验脚本、降重改写、AI 报告、格式化",
        "token_budget": "放开用：可全量读长文档/论文/日志，批量预处理；缓存命中价低，高频小任务最划算",
        "prompt": "明确模板化指令 + 结构化输出（JSON/表格/固定字段）；短指令链逐步确认",
        "upgrade_signal": "多次试错无进展 / 推理敷衍 / 关键取舍说不清 → 该环节升级 v4-pro",
        "downgrade_signal": "（本档为执行档，机械任务由它消化）",
        "use_in_skill": "读题拆解 / 真题定位 / 求解落盘 / 全部校验脚本 / 降 AI 味改写 / AI 报告 / 紧急模式执行环节（默认）",
    },
}

LITE_FIELDS = ["name", "position", "role", "token_budget", "use_in_skill"]


def main():
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="模型画像工具（V4 Pro / Flash 适配）")
    ap.add_argument("model", nargs="?", default=None, help="v4-pro / v4-flash；缺省输出双模型对比")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    if args.model and args.model not in PROFILES:
        print(f"[err] 未知模型 {args.model}，可选: {', '.join(PROFILES)}", file=sys.stderr)
        return 2

    if args.model:
        p = PROFILES[args.model]
        if args.json:
            print(json.dumps(p, ensure_ascii=False, indent=2))
            return 0
        print(f"# {p['name']} 推荐配置\n")
        for k, label in [("params", "规格"), ("context", "上下文/输出"), ("position", "定位"),
                         ("latency", "延迟/并发"), ("price", "参考价"), ("role", "分工"),
                         ("token_budget", "上下文预算"), ("prompt", "提示词策略"),
                         ("upgrade_signal", "升级信号"), ("downgrade_signal", "降级信号"),
                         ("use_in_skill", "在 skill 中的环节")]:
            print(f"- {label}：{p[k]}")
        return 0

    # 双模型对比
    if args.json:
        print(json.dumps(PROFILES, ensure_ascii=False, indent=2))
        return 0
    print("# DeepSeek V4 双引擎对比\n")
    rows = [
        ("规格", "params"), ("上下文/输出", "context"), ("定位", "position"),
        ("延迟/并发", "latency"), ("参考价", "price"), ("分工", "role"),
        ("上下文预算", "token_budget"),
    ]
    print(f"{'维度':<10} | {'V4-Pro':<34} | V4-Flash")
    print("-" * 100)
    for label, key in rows:
        a = PROFILES["v4-pro"][key]
        b = PROFILES["v4-flash"][key]
        print(f"{label:<8} | {a[:32]:<34} | {b}")
    print("\n一句话：Pro 想（选型/创新/论文论证），Flash 做（批量/校验/改写/报告）。")
    print("更多细节：references/model-adaptation.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
