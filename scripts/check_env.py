#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赛前环境体检（国一冲刺包 #1）。开赛前 10 分钟跑一遍，把环境/复现风险清零。

国一论文最常见的"没拿到"，不是模型不行，而是交稿前环境翻车：
库没装、版本不锁、图里中文变豆腐块、磁盘满了导出失败。本脚本一次性体检。

用法:
    python check_env.py [--strict]

检查项:
    1. Python 版本（>=3.8）
    2. 关键科学库 import + 版本（numpy/scipy/pandas/sklearn/matplotlib/statsmodels）
    3. matplotlib 中文字体探测（找不到则图中中文会变 □，需改用英文标签）
    4. Pillow 有无（figcheck.py 的 DPI 硬检需要；缺失会自动降级跳过）
    5. 磁盘剩余空间（数据/图/报告落盘需要）
    6. 当前目录可写（结果导出）
    7. 随机种子可固定（numpy.random.default_rng(seed) 可复现）

退出码: 0=全过  1=有警告（不影响主流程）  2=有阻断项（缺库/版本过低/Python 太旧）
--strict 时警告也计为失败（交稿前推荐）。
零第三方依赖；导入科学库失败时如实标记，不假装成功。
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys

# 关键科学库：缺失/过旧会直接阻断建模求解，标红
CORE_LIBS = [
    ("numpy", "1.22"),
    ("scipy", "1.8"),
    ("pandas", "1.4"),
    ("sklearn", "1.1"),
    ("matplotlib", "3.5"),
    ("statsmodels", "0.13"),
]

# 绘图/校验增强库：缺失可降级（脚本设计已兼容），标黄即可
OPTIONAL_LIBS = ["PIL", "openpyxl", "sympy", "torch", "keras", "tensorflow", "pydot"]


def _console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass


def parse_version(v):
    """'1.26.4' -> (1,26,4) 比较用；解析失败返回 None。"""
    try:
        return tuple(int(x) for x in v.split(".")[:3])
    except Exception:
        return None


def cmp_min(v, minv):
    a, b = parse_version(v), parse_version(minv)
    if a is None or b is None:
        return None  # 无法判断，不武断
    return a >= b


def check_python():
    v = sys.version_info
    ok = v >= (3, 8)
    print(f"[{'OK ' if ok else 'FAIL'}] Python {v.major}.{v.minor}.{v.micro} (需 >=3.8)")
    return 2 if not ok else 0


def check_core_libs():
    """返回 (阻断数, 警告数)。"""
    block = warn = 0
    for name, minv in CORE_LIBS:
        try:
            mod = __import__(name)
            ver = getattr(mod, "__version__", "?")
            if ver == "?":
                print(f"[WARN] {name} 已安装，但读不到版本号（无法核验锁版本）")
                warn += 1
                continue
            if cmp_min(ver, minv) is False:
                print(f"[FAIL] {name} {ver} 过旧（需>={minv}），pip install -U {name}")
                block += 1
            else:
                print(f"[OK  ] {name} {ver}")
        except ImportError:
            print(f"[FAIL] {name} 未安装（pip install {name}）")
            block += 1
    return block, warn


def check_optional_libs():
    warn = 0
    for name in OPTIONAL_LIBS:
        try:
            __import__(name)
            print(f"[INFO] {name} 可用")
        except ImportError:
            print(f"[INFO] {name} 未装（可选；对应功能将自动降级）")
            warn += 1
    return warn


def check_cjk_font():
    """matplotlib 中文字体探测；失败时提示图用英文标签。"""
    try:
        from matplotlib import font_manager
        installed = {f.name for f in font_manager.fontManager.ttflist}
        cands = ["SimHei", "Microsoft YaHei", "Microsoft JhengHei",
                 "Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC",
                 "WenQuanYi Zen Hei", "WenQuanYi Micro Hei",
                 "PingFang SC", "Hiragino Sans GB", "Arial Unicode MS"]
        hit = next((c for c in cands if c in installed), None)
        if hit:
            print(f"[OK  ] 中文字体命中: {hit}")
            return 0
        print("[WARN] 未找到中文字体——图中中文会变 □；要么装字体，要么按 figure-polish.md 改英文标签")
        return 1
    except ImportError:
        print("[WARN] matplotlib 未装，跳过中文字体探测")
        return 1


def check_disk(min_free_gb=2.0):
    try:
        p = os.getcwd()
        free = shutil.disk_usage(p).free / (1024 ** 3)
        ok = free >= min_free_gb
        print(f"[{'OK ' if ok else 'WARN'}] 磁盘剩余 {free:.1f} GB（需>={min_free_gb}GB，{p}）")
        return 0 if ok else 1
    except OSError as e:
        print(f"[WARN] 无法读取磁盘空间: {e}")
        return 1


def check_writable():
    probe = os.path.join(os.getcwd(), ".env_check_probe")
    try:
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        print(f"[OK  ] 当前目录可写: {os.getcwd()}")
        return 0
    except OSError as e:
        print(f"[FAIL] 当前目录不可写（结果无法导出）: {e}")
        return 2


def check_seed():
    try:
        import numpy as np
        rng = np.random.default_rng(0)
        a = rng.random(3)
        rng2 = np.random.default_rng(0)
        b = rng2.random(3)
        ok = bool((a == b).all())
        print(f"[{'OK ' if ok else 'FAIL'}] 随机种子可复现（default_rng(0) 两次一致）")
        return 0 if ok else 2
    except ImportError:
        print("[WARN] numpy 未装，跳过 seed 抽查")
        return 1


def main():
    ap = argparse.ArgumentParser(description="赛前环境体检（国一冲刺包）")
    ap.add_argument("--strict", action="store_true",
                    help="警告也计为失败（交稿前推荐：python check_env.py --strict）")
    args = ap.parse_args()

    _console()
    print(f"# 赛前环境体检  @ {platform.system()} {platform.release()}\n")
    block = warn = 0
    block += check_python()
    b, w = check_core_libs(); block += b; warn += w
    warn += check_optional_libs()
    warn += check_cjk_font()
    warn += check_disk()
    block += check_writable()
    warn += check_seed()

    print(f"\n[check_env] 阻断 {block} 项，警告 {warn} 项。")
    if block:
        print("[check_env] 存在阻断项——先修复再开赛（缺库/过旧/不可写）。")
        return 2
    if warn and args.strict:
        print("[check_env] --strict 下警告视为失败，逐项消掉再交稿。")
        return 2
    if warn:
        print("[check_env] 有警告但不阻断（可按需处理）。")
        return 1
    print("[check_env] ✓ 环境就绪，放心开赛。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
