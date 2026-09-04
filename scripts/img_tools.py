#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
img_tools.py —— 图片查看与提取工具（配合模型视觉模态，读题/读图/看细节）

用途：模型虽有视觉模态，但 PDF 里的图得先提取出来才能看；图太小、字太小
得先放大/裁剪局部再给模型看。本工具统一处理：信息查看 / 放大 / 裁剪 / 从
PDF 提取全部图片 / 批量处理。

依赖：Pillow（info/zoom/crop/batch）+ PyMuPDF（from-pdf/list）。
赛前配好：python -m pip install pillow pymupdf

用法:
    python img_tools.py info 图.png                      # 基本信息（尺寸/格式/模式/DPI/体积）
    python img_tools.py zoom 图.png --out zoom.png --scale 3     # 放大 3 倍（看小字/细节）
    python img_tools.py crop 图.png --out crop.png --box 100,100,600,600   # 裁剪局部（左上x,左上y,右下x,右下y）
    python img_tools.py from-pdf 题目.pdf --outdir imgs/  # 从 PDF 逐页提取全部图片（保留原始分辨率）
    python img_tools.py list 题目.pdf                    # 列出 PDF 中的图片（不提取）
    python img_tools.py batch 图目录/ --out 输出目录/ --scale 2   # 批量放大目录下全部图片

说明:
    - from-pdf 逐页抽取嵌入图片并按页+序号命名（p1_1.png），供模型视觉逐张读取
    - zoom/crop 输出后模型直接读新图，小字细节更容易看清
    - 扫描件 PDF（无文字层）用 from-pdf 提不出文字、但能提出页面图：此时可整页渲染
      `page 2` 子命令把指定页渲染成 PNG 供视觉/OCR 读取
"""
from __future__ import annotations

import argparse
import os
import sys


def _console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(errors="replace")
        except Exception:
            pass


def _info(path):
    from PIL import Image
    im = Image.open(path)
    dpi = im.info.get("dpi", (None, None))
    size_mb = os.path.getsize(path) / 1048576
    print(f"[图片] {os.path.basename(path)}")
    print(f"  尺寸: {im.width} × {im.height} px")
    print(f"  格式: {im.format} | 模式: {im.mode}")
    print(f"  DPI : {dpi[0] if dpi[0] else '未知'}")
    print(f"  体积: {size_mb:.2f} MB")
    return 0


def _zoom(path, out, scale):
    from PIL import Image
    im = Image.open(path)
    im2 = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    im2.save(out)
    print(f"[zoom] {os.path.basename(path)} ×{scale} -> {out}（{im2.width}×{im2.height}）")
    return 0


def _crop(path, out, box):
    from PIL import Image
    im = Image.open(path)
    x0, y0, x1, y1 = box
    im2 = im.crop((x0, y0, x1, y1))
    im2.save(out)
    print(f"[crop] {os.path.basename(path)} 裁剪 {box} -> {out}（{im2.width}×{im2.height}）")
    return 0


def _pdf_list(pdf):
    import pymupdf
    doc = pymupdf.open(pdf)
    total = 0
    for i, page in enumerate(doc, 1):
        imgs = page.get_images(full=True)
        if imgs:
            print(f"  第 {i} 页: {len(imgs)} 张图片")
            for img in imgs:
                xref = img[0]
                try:
                    pix = pymupdf.Pixmap(doc, xref)
                    print(f"    · xref {xref}: {pix.width}×{pix.height}")
                    if pix.n - pix.alpha > 3:
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                except Exception:
                    print(f"    · xref {xref}: (解析失败)")
            total += len(imgs)
    print(f"[list] PDF 共 {doc.page_count} 页，含 {total} 张图片")
    doc.close()
    return 0


def _pdf_extract(pdf, outdir):
    import pymupdf
    os.makedirs(outdir, exist_ok=True)
    doc = pymupdf.open(pdf)
    n = 0
    for i, page in enumerate(doc, 1):
        for img in page.get_images(full=True):
            xref = img[0]
            pix = pymupdf.Pixmap(doc, xref)
            if pix.n - pix.alpha > 3:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            name = f"p{i}_{xref}.png"
            path = os.path.join(outdir, name)
            pix.save(path)
            print(f"  第 {i} 页 → {name}（{pix.width}×{pix.height}）")
            n += 1
    doc.close()
    print(f"[from-pdf] 共提取 {n} 张图片 -> {outdir}")
    return 0


def _pdf_page(pdf, page_no, out):
    """把指定页渲染成 PNG（扫描件整页，供视觉/OCR 读取）。"""
    import pymupdf
    doc = pymupdf.open(pdf)
    if page_no < 1 or page_no > doc.page_count:
        print(f"[err] 页码越界：{page_no}（共 {doc.page_count} 页）", file=sys.stderr)
        return 2
    page = doc.load_page(page_no - 1)
    mat = pymupdf.Matrix(2, 2)  # 2x 缩放提升清晰度
    pix = page.get_pixmap(matrix=mat)
    pix.save(out)
    print(f"[page] 第 {page_no} 页渲染 -> {out}（{pix.width}×{pix.height}）")
    doc.close()
    return 0


def _batch(directory, outdir, scale):
    from PIL import Image
    os.makedirs(outdir, exist_ok=True)
    exts = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
    files = [f for f in sorted(os.listdir(directory)) if f.lower().endswith(exts)]
    if not files:
        print(f"[err] 目录 {directory} 下没有图片", file=sys.stderr)
        return 2
    for f in files:
        im = Image.open(os.path.join(directory, f))
        im2 = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
        out = os.path.join(outdir, f)
        im2.save(out)
        print(f"  {f} ×{scale} -> {out}")
    print(f"[batch] 处理 {len(files)} 张 -> {outdir}")
    return 0


def main():
    _console()
    ap = argparse.ArgumentParser(description="图片查看与提取（Pillow + PyMuPDF）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("info", help="查看图片信息")
    p.add_argument("img")
    p = sub.add_parser("zoom", help="放大图片")
    p.add_argument("img")
    p.add_argument("--out", required=True)
    p.add_argument("--scale", type=int, default=2)
    p = sub.add_parser("crop", help="裁剪局部")
    p.add_argument("img")
    p.add_argument("--out", required=True)
    p.add_argument("--box", required=True, help="x0,y0,x1,y1")
    p = sub.add_parser("list", help="列出 PDF 内图片")
    p.add_argument("pdf")
    p = sub.add_parser("from-pdf", help="从 PDF 提取全部图片")
    p.add_argument("pdf")
    p.add_argument("--outdir", required=True)
    p = sub.add_parser("page", help="把 PDF 某页渲染成 PNG（扫描件用）")
    p.add_argument("pdf")
    p.add_argument("page_no", type=int)
    p.add_argument("--out", required=True)
    p = sub.add_parser("batch", help="批量放大目录下图片")
    p.add_argument("directory")
    p.add_argument("--out", required=True)
    p.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()

    try:
        if args.cmd == "info":
            return _info(args.img)
        if args.cmd == "zoom":
            return _zoom(args.img, args.out, args.scale)
        if args.cmd == "crop":
            try:
                box = tuple(int(x) for x in args.box.split(","))
            except Exception:
                print(f"[err] --box 格式应为 x0,y0,x1,y1: {args.box}", file=sys.stderr)
                return 2
            if len(box) != 4:
                print("[err] --box 需 4 个数字", file=sys.stderr)
                return 2
            return _crop(args.img, args.out, box)
        if args.cmd == "list":
            return _pdf_list(args.pdf)
        if args.cmd == "from-pdf":
            return _pdf_extract(args.pdf, args.outdir)
        if args.cmd == "page":
            return _pdf_page(args.pdf, args.page_no, args.out)
        if args.cmd == "batch":
            return _batch(args.directory, args.out, args.scale)
    except ImportError as e:
        print(f"[err] 缺依赖: {e}。赛前配好: python -m pip install pillow pymupdf", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[err] {type(e).__name__}: {str(e)[:150]}", file=sys.stderr)
        return 2
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
