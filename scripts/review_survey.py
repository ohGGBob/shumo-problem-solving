#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赛后复盘四维问题清单生成器 + 复盘草稿模板（零第三方依赖）。

定位:
    数模比赛结束后 48 小时内跑一次，生成一份四维(数据/模型/写作/协作)复盘问题清单，
    并在当前目录生成一个 review_<日期>.md 草稿，逐条自答即可沉淀经验。

用法:
    python review_survey.py                     # 只打印问题清单
    python review_survey.py --out .             # 在当前目录生成 review_<日期>.md
    python review_survey.py --out ./reviews     # 指定输出目录

说明:
    复盘填完后，把「可复用资产」与「可避免教训」主动回流到 skill 的对应 reference 文件，
    形成"用一次强一次"的闭环（详见 references/post-contest-review.md）。
"""
import argparse
import os
import sys
from datetime import datetime

QUESTIONS = {
    "数据复盘": [
        "原始数据规模/质量如何？有哪些缺失、异常、重复？",
        "清洗用了什么流程？哪一步最耗时/最坑？",
        "有没有'以为能用、实际是坑'的字段或数据？",
        "可复用：把清洗流程/函数写进 preprocessing-pipeline.md 或脚本？",
    ],
    "模型复盘": [
        "每题最终用什么模型？效果(误差/指标)如何？",
        "哪个模型是'看似高级、实际没用'？(淘汰，别下次再踩)",
        "哪一步是亮点/创新？评委认了吗？",
        "哪个假设被证明不合理？为什么？",
        "可复用：把'题型→模型→效果'补进 model-recipes.md？把亮点套路补进 innovation-playbook.md？",
    ],
    "写作复盘": [
        "摘要/正文哪里被评委会挑刺？",
        "降重/降AI味哪块没过？具体是哪些句子？",
        "图表哪些被夸/被批(清晰度/信息量)？",
        "可复用：把好的句式/结构补进 bao-paper-writing.md、figures-and-abstract.md？把踩坑补进 writing-deai-dedup.md？",
    ],
    "协作/节奏复盘": [
        "时间分配合理吗？哪个环节超时了？",
        "定题拖到几点？红警线守住了吗？",
        "队友分工顺畅吗？有没有沟通断裂？",
        "可复用：把节奏教训写进 timeline.md？",
    ],
}

REVIEW_TEMPLATE = """# {contest} 赛后复盘（{date}）

> 四维复盘：数据 / 模型 / 写作 / 协作。赛后 48h 内填完，可复用资产与可避免教训主动回流到 skill。

## 一句话总结
本次比赛最大的收获：____；最大的教训：____。

## 1. 数据复盘
- 原始数据规模/质量：____
- 清洗流程与最坑的一步：____
- 踩到的数据坑：____
- → 可复用资产（补进 preprocessing-pipeline.md / scripts）：____

## 2. 模型复盘
- 每题模型与效果：
  - Q1: ____
  - Q2: ____
  - Q3: ____
- 被淘汰的模型（为什么）：____
- 评委认可的亮点：____
- 被证明不合理的假设：____
- → 可复用资产（补进 model-recipes.md / innovation-playbook.md）：____

## 3. 写作复盘
- 摘要/正文被挑刺的点：____
- 降重/降AI没过的句子：____
- 图表被夸/被批：____
- → 可复用资产（补进 bao-paper-writing.md / figures-and-abstract.md / writing-deai-dedup.md）：____

## 4. 协作/节奏复盘
- 时间分配：哪个环节超时？
- 定题与红警线执行：____
- 团队分工与沟通：____
- 答辩被问倒的问题（若有）：____
- → 可复用资产（补进 timeline.md）：____

## 下次必做 / 必避清单
- 下次必做：____
- 下次必避：____
"""


def print_survey():
    print("=" * 60)
    print("数模赛后四维复盘问题清单")
    print("=" * 60)
    for dim, qs in QUESTIONS.items():
        print(f"\n## {dim}")
        for i, q in enumerate(qs, 1):
            print(f"  {i}. {q}")
    print("\n" + "=" * 60)
    print("填完把可复用资产/教训回流到 skill 对应 reference 文件，形成闭环。")
    print("详见 references/post-contest-review.md")


def write_draft(out_dir, name=None):
    os.makedirs(out_dir, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(out_dir, f"review_{date}.md")
    contest = name
    if contest is None:
        try:
            contest = input("本次比赛名称(如 cumcm2026A / mcm2027C，回车可跳过): ").strip() if sys.stdin.isatty() else ""
        except (EOFError, KeyboardInterrupt):
            contest = ""
    content = REVIEW_TEMPLATE.format(contest=contest or "数模比赛", date=date)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[review] 已生成复盘草稿: {path}")
    return path


def main():
    ap = argparse.ArgumentParser(description="生成数模赛后四维复盘问题清单与草稿")
    ap.add_argument("--out", default=None, help="生成复盘草稿的目录；不传则只打印问题清单")
    ap.add_argument("--name", default=None, help="比赛名称（供草稿标题）；非交互环境请显式传入，避免 input() 阻塞")
    args = ap.parse_args()

    print_survey()
    if args.out:
        write_draft(args.out, args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
