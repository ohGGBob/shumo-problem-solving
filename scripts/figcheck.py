#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图表规范检查：DPI、命名、引用。

用法:
    python figcheck.py <report_dir> [--dpi 300] [--paper 论文.md|论文.tex]

检查项:
    1. 图片文件 DPI >= --dpi（需 Pillow；无 Pillow 时跳过 DPI 检查并提示）。
    2. 图片命名是否含图序(fig1 / figure_2)或语义名，禁止 IMG_/截图/微信等。
    3. 论文中每个 \\includegraphics{/![...](...)} 引用都有对应文件。
    4. 注：标题/单位/图注的"自足性"需人工核对，本脚本不检查（见 `bao-paper-writing.md` 图表三件套）。

输出问题清单，供交稿前清理。
"""
import argparse
import os
import re
import sys

IMG_EXT = (".png", ".jpg", ".jpeg", ".svg", ".pdf", ".tif", ".tiff")


def list_images(d):
    res = []
    for root, _, files in os.walk(d):
        for fn in files:
            if fn.lower().endswith(IMG_EXT):
                res.append(os.path.join(root, fn))
    return res


def dpi_of(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            dp = im.info.get("dpi")
            if dp:
                return round(max(dp))
    except ImportError:
        return None
    except Exception:  # noqa
        return None
    return None


def main():
    ap = argparse.ArgumentParser(description="图表规范检查")
    ap.add_argument("report_dir", help="论文/report 目录")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--paper", default=None, help="可选：论文文件，用于核对图引用")
    args = ap.parse_args()

    if not os.path.isdir(args.report_dir):
        print(f"[err] 目录不存在: {args.report_dir}", file=sys.stderr)
        return 1

    imgs = list_images(args.report_dir)
    if not imgs:
        print(f"[figcheck] 未发现图片文件。", file=sys.stderr)
        return 0

    have_pil = True
    try:
        import PIL  # noqa
    except ImportError:
        have_pil = False

    print(f"发现图片 {len(imgs)} 张，DPI 阈值 {args.dpi}\n")
    issues = 0
    for p in sorted(imgs):
        name = os.path.basename(p)
        flags = []
        if have_pil:
            d = dpi_of(p)
            if d is not None and d < args.dpi:
                flags.append(f"DPI={d}<{args.dpi}")
        else:
            flags.append("DPI未检(无Pillow)")
        if re.search(r"(IMG_|微信|截图|screenshot|capture|未命名|image)", name, re.I):
            flags.append("命名不规范(含 IMG_/截图/微信 等)")
        if flags:
            issues += 1
            print(f"  ! {name}: {'; '.join(flags)}")
        else:
            print(f"  ok {name}")

    # 论文引用核对
    if args.paper and os.path.exists(args.paper):
        with open(args.paper, encoding="utf-8", errors="ignore") as f:
            txt = f.read()
        refs = set()
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", txt):
            refs.add(os.path.basename(m.group(1)))
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", txt):
            refs.add(os.path.basename(m.group(1)))
        for r in sorted(refs):
            if not any(r == os.path.basename(p) for p in imgs):
                issues += 1
                print(f"  ! 论文引用了图片但文件缺失: {r}")

    print(f"\n[figcheck] 完成，发现 {issues} 处需清理项。" if issues else "\n[figcheck] ✓ 全部通过。")
    if not have_pil:
        print("提示: 安装 Pillow 可做 DPI 硬检查: pip install Pillow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
