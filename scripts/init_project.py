#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成数模解题标准目录骨架 + 锁版本 requirements + export_results.py 模板。

用法:
    python init_project.py <题名缩写> [--dir <路径>]

示例:
    python init_project.py cumcm2026A
    python init_project.py mcm2027C --dir ./work

生成结构:
    <题名>/
      data/           原始数据
      src/            q1.py q2.py ... + export_results.py
      out/            results.json(空模板) + 图表(png/svg,>=300dpi)
      report/         main.tex / main.docx + figures/ + data_inventory.md(数据清单模板)
      requirements.txt  锁版本(==)
      README.md
"""
import argparse
import json
import os
import sys

EXPORT_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把全部关键数字落成 out/results.json（数值单一来源，论文只引用它）。

用法: 各 qN.py 算完把结果 import 进来，或在本文件里直接 import 各模块后汇总。
原则: 论文/摘要/图注里的每个数字都必须能在这个文件里找到出处。
"""
import json
import os

# 把所有要写进论文的数字放进这个字典（含单位/置信，不要手抄，用代码算出来填）
RESULTS = {
    # "q1_optimal_value": 123.45,
    # "q1_error_pct": 2.3,
}


def dump(path="out/results.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2)
    print(f"[export_results] 已写出 {len(RESULTS)} 个关键数字 -> {path}")


if __name__ == "__main__":
    # TODO: 在此 import 各 qN 模块，把它们的计算结果填进 RESULTS
    dump()
'''

README_TEMPLATE = """# {name}

生成时间: {ts}

## 目录约定
- `data/` 原始数据（不要直接改，清洗产物放 `out/clean.csv`）
- `src/` 每个子问题的求解脚本 `q1.py q2.py ...`，统一由 `export_results.py` 导出数字
- `out/` 结果表格、图（png/svg，>=300dpi）、`results.json`
- `report/` 论文 `main.tex`/`main.docx`、图表 `figures/`

## 铁律
1. 论文每个数字必须来自 `out/results.json`（数值单一来源）。
2. 固定随机种子，交付前 canonical 脚本复跑逐位核对。
3. 改一个数字必 grep 全目录旧值。
4. 数据完整性：先建 `report/data_inventory.md`（读全所有数据再判断，铁律四），
   数字必有出处——数据文件 → data_inventory → 代码 → results.json → 论文，环环可回溯。
"""

DATA_INVENTORY_TEMPLATE = """# 数据清单（data_inventory）

> 铁律四 · 不读完不算懂，读全再判断：拿到全部数据附件后，先把每张表登记到这里，
> 与 `data/` 目录逐项对照、确认无遗漏，再进建模。生成命令：
>
> ```bash
> python scripts/data_profiler.py data/ --inventory --out report/data_inventory.md
> ```
>
> 清单上没登记的附件/表 = 还没读，禁止进入建模；每个数字必须能在清单里找到出处。

## 附件清单（`data/` 下每个文件都要登记，缺一即没读完）

| # | 文件 | 表/sheet | 行 | 列 | 关键列 / 用途 |
|---|---|---|---|---|---|
| 1 | （示例）supplier.xlsx | Sheet1 | 402 | 8 | 供应商ID、周均供货、价格 |

## 逐表要点（分布/缺失/常量列/关联键，跑 data_profiler 后摘录）

- （示例）supplier.xlsx：价格列 5% 缺失待补；供应商ID 全唯一勿当特征。
"""

REQUIREMENTS = """# 占位版本（并非常年最优）：交付前在本项目 venv 里 `pip freeze` 后精修为真实锁定版，见 references/reproducibility.md 铁律二。
# 锁版本，精确到 == ，干净环境 pip install -r 可复跑
numpy==1.26.4
scipy==1.13.1
pandas==2.2.2
scikit-learn==1.5.1
matplotlib==3.9.2
statsmodels==0.14.2
"""


def main():
    ap = argparse.ArgumentParser(description="生成数模解题标准目录骨架")
    ap.add_argument("name", help="题名缩写，如 cumcm2026A")
    ap.add_argument("--dir", default=".", help="父目录，默认当前目录")
    args = ap.parse_args()

    root = os.path.join(args.dir, args.name)
    if os.path.exists(root):
        print(f"[init] 目标已存在，中止: {root}", file=sys.stderr)
        return 1

    dirs = ["data", "src", "out", os.path.join("report", "figures")]
    for d in dirs:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    with open(os.path.join(root, "src", "export_results.py"), "w", encoding="utf-8") as f:
        f.write(EXPORT_TEMPLATE)
    with open(os.path.join(root, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(REQUIREMENTS)
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as f:
        from datetime import datetime
        f.write(README_TEMPLATE.format(name=args.name, ts=datetime.now().isoformat(timespec="seconds")))

    with open(os.path.join(root, "report", "data_inventory.md"), "w", encoding="utf-8") as f:
        f.write(DATA_INVENTORY_TEMPLATE)

    # 占位文件，避免空目录在某些工具里被忽略
    for rel in ["data/.gitkeep", "out/.gitkeep", "report/figures/.gitkeep"]:
        open(os.path.join(root, rel), "w", encoding="utf-8").close()

    print(f"[init] 已生成项目骨架: {root}")
    print("        data/ src/ out/ report/(figures+data_inventory.md) + requirements.txt + README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
