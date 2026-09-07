#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chart_read.py —— 图表识别工具（抽图 + 结构化识别清单，配合视觉模型把图"读进论文"）

数模题面/数据里的图不是装饰：机理示意图、数据曲线、流程图、数据表格往往藏着解题
关键信息。模型虽有视觉模态，但必须先 (a) 把图从 PDF 抽/渲染出来、(b) 按统一口径逐张
识读，否则容易漏图、看图瞎说（漏掉坐标轴单位/图例/拐点/极值）。

本工具负责三件事，识别本身交由「带视觉的模型」完成：
  1. 抽图   from-pdf / page —— 整页高清渲染（矢量图/示意图也能抓到）+ 内嵌位图原分辨率抽取；
  2. 制卡   manifest —— 给每张图生成一张「识别卡」（类型/标题/坐标轴+单位/图例/趋势/关键数值/论文转写句），
            落盘 chart_read.md（人读）+ chart_manifest.json（程序读）；
  3. 单图   read —— 直接打印单张图的识别卡，交由视觉模型逐项回答。

识别结果写回 chart_read.md（或另存 report/figure_reading.md），论文「图解读句」直接
引用，对齐质量三支柱·支柱三的「引出句 → 图表 → 解读句」三件套。

依赖：PyMuPDF（from-pdf/page）+ Pillow（可选，暂未用到）；manifest/read 零依赖，
缺依赖时相应子命令会给出安装提示而非静默降级。Python 3.8+。

用法:
    python chart_read.py from-pdf 题目.pdf --outdir figs/                       # 抽全部图 + 整页渲染
    python chart_read.py from-pdf 题目.pdf --pages 2,3 --scale 3 --outdir figs/  # 指定页，3x 放大
    python chart_read.py page 题目.pdf --page 2 --out p2.png --scale 3           # 单页高清渲染（看矢量图）
    python chart_read.py manifest figs/ --out chart_read.md --json chart_manifest.json
    python chart_read.py manifest 图1.png 图2.png --out chart_read.md            # 直接对图片制卡
    python chart_read.py read 图1.png                                            # 单图识别卡
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")
_PLACEHOLDER = "「待视觉模型填写」"

# 识别卡标准字段与提示 —— 读图口径统一，避免漏掉单位/图例/关键值
_RECOGNITION_CARD = [
    ("图表类型", "折线图 / 柱状图 / 散点图 / 饼图 / 热力图 / 箱线图 / 机理示意图 / 流程图 / 数据表格 / 其他"),
    ("标题/图注", "图中写明的标题、图注、来源、单位说明（有就照抄，没有写「无」）"),
    ("坐标轴", "横轴 X：含义（单位）；纵轴 Y：含义（单位）；双纵轴 / 对数轴 / 起止范围要注明"),
    ("图例/系列", "各系列名称及其线型 / 颜色 / 标记的对应关系"),
    ("数据趋势", "整体趋势（增 / 减 / 周期 / 饱和 / 拐点 / 分叉），分区间描述"),
    ("关键数值", "极值点、拐点、渐近线、阈值、交点、特殊标注的具体数字（务必带单位，看不清写「识别不清」）"),
    ("异常/冲突", "离群点、矛盾处、图与文字不一致的地方；不猜，标「识别不清」"),
    ("论文转写句", "一句话量化结论，可直接用作论文「图解读句」或图注核心句"),
]


def _console():
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass


def _mupdf():
    try:
        import pymupdf as m
    except ImportError:
        import fitz as m  # 旧版兼容
    return m


def _is_img(name):
    return name.lower().endswith(_IMG_EXTS)


def _pages_filter(spec):
    """'2,3-5' -> [2,3,4,5]；None -> None（全部页）。"""
    if not spec:
        return None
    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = (int(x) for x in part.split("-"))
            pages |= set(range(a, b + 1))
        else:
            pages.add(int(part))
    return sorted(pages) if pages else None


def _render_pdf(pdf, outdir, page_filter, scale):
    m = _mupdf()
    os.makedirs(outdir, exist_ok=True)
    doc = m.open(pdf)
    n = doc.page_count
    base = os.path.splitext(os.path.basename(pdf))[0]
    produced = []
    pages = page_filter or range(1, n + 1)
    for i in pages:
        if i < 1 or i > n:
            continue
        page = doc.load_page(i - 1)
        pix = page.get_pixmap(matrix=m.Matrix(scale, scale))
        p = os.path.join(outdir, f"{base}_p{i}.png")
        pix.save(p)
        produced.append(p)
        print(f"  第 {i} 页整页 -> {os.path.basename(p)}（{pix.width}×{pix.height}）")
        for j, img in enumerate(page.get_images(full=True), 1):
            xref = img[0]
            try:
                ipix = m.Pixmap(doc, xref)
                if ipix.n - ipix.alpha > 3:
                    ipix = m.Pixmap(m.csRGB, ipix)
                q = os.path.join(outdir, f"{base}_p{i}_img{j}.png")
                ipix.save(q)
                produced.append(q)
                print(f"    内嵌图 {j} -> {os.path.basename(q)}（{ipix.width}×{ipix.height}）")
            except Exception:
                pass
    doc.close()
    return produced


def _list_images(inputs, outdir):
    files = []
    inputs = inputs or ["."]
    for x in inputs:
        if os.path.isdir(x):
            files += [os.path.join(x, f) for f in sorted(os.listdir(x)) if _is_img(f)]
        elif os.path.isfile(x):
            if _is_img(x):
                files.append(os.path.normpath(x))
            elif x.lower().endswith(".pdf"):
                files += _render_pdf(x, outdir, None, 2)
            else:
                print(f"[warn] 非图片/PDF，跳过: {x}", file=sys.stderr)
        else:
            print(f"[err] 不存在: {x}", file=sys.stderr)
    return files


def _card_text(path):
    size = os.path.getsize(path) if os.path.exists(path) else 0
    lines = [f"## 图：{os.path.basename(path)}（{size // 1024} KB）", f"> 图片来源：{path}"]
    for field, hint in _RECOGNITION_CARD:
        lines.append(f"- **{field}**: {_PLACEHOLDER}（提示：{hint}）")
    lines.append("")
    return "\n".join(lines)


def _manifest(files, out, json_out):
    blocks = [
        f"# 图表识别清单（{len(files)} 张图）",
        "",
        "> 逐张回答识别卡，把「待视觉模型填写」替换为结论；识别不清的字段写「识别不清」，禁止看图瞎猜。",
        "> 识别结果另存 `report/figure_reading.md`，论文图解读句直接引用（支柱三三件套）。",
        "",
    ]
    for f in files:
        blocks.append(_card_text(f))
    body = "\n".join(blocks)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(body)
        print(f"[manifest] 已生成 {out}（{len(files)} 张图）")
    else:
        print(body)
    if json_out:
        payload = [{"file": os.path.basename(f), "path": f,
                    "card": {field: {"value": None, "hint": hint} for field, hint in _RECOGNITION_CARD}}
                   for f in files]
        with open(json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"[manifest] JSON 清单已生成 {json_out}")


def main():
    _console()
    ap = argparse.ArgumentParser(description="图表识别工具（抽图 + 结构化识别清单，配合视觉模型）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("from-pdf", help="抽取 PDF 全部图表（整页渲染 + 内嵌位图）")
    p.add_argument("pdf")
    p.add_argument("--outdir", default="figs")
    p.add_argument("--pages", help="页码范围，如 1,3-5（缺省全部）")
    p.add_argument("--scale", type=int, default=2, help="整页渲染缩放倍数（默认 2）")

    p = sub.add_parser("page", help="把 PDF 某页高清渲染成 PNG")
    p.add_argument("pdf")
    p.add_argument("--page", type=int, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--scale", type=int, default=3)

    p = sub.add_parser("manifest", help="生成图表识别清单（图片目录/文件/PDF）")
    p.add_argument("inputs", nargs="*", help="图片目录 / 图片文件 / PDF（可多个）")
    p.add_argument("--outdir", default="figs", help="PDF 渲染输出目录（配合 PDF 输入）")
    p.add_argument("--out", help="markdown 清单输出路径（缺省打印 stdout）")
    p.add_argument("--json", dest="json_out", help="JSON 清单输出路径")

    p = sub.add_parser("read", help="打印单张图的识别卡")
    p.add_argument("img")

    args = ap.parse_args()

    try:
        if args.cmd == "from-pdf":
            if not os.path.exists(args.pdf):
                print(f"[err] 找不到 PDF: {args.pdf}", file=sys.stderr)
                return 2
            files = _render_pdf(args.pdf, args.outdir, _pages_filter(args.pages), args.scale)
            if not files:
                print("[warn] 未产出图片（PDF 可能渲染失败）", file=sys.stderr)
            print(f"[from-pdf] 共产出 {len(files)} 张 -> {args.outdir}")
            return 0

        if args.cmd == "page":
            m = _mupdf()
            doc = m.open(args.pdf)
            if args.page < 1 or args.page > doc.page_count:
                print(f"[err] 页码越界: {args.page}（共 {doc.page_count} 页）", file=sys.stderr)
                return 2
            pix = doc.load_page(args.page - 1).get_pixmap(matrix=m.Matrix(args.scale, args.scale))
            pix.save(args.out)
            print(f"[page] 第 {args.page} 页 -> {args.out}（{pix.width}×{pix.height}）")
            doc.close()
            return 0

        if args.cmd == "read":
            if not os.path.exists(args.img):
                print(f"[err] 找不到图片: {args.img}", file=sys.stderr)
                return 2
            print(_card_text(args.img))
            return 0

        if args.cmd == "manifest":
            files = _list_images(args.inputs, args.outdir)
            if not files:
                print("[err] 没有可识别的图片（目录无图 / 图片路径错误 / PDF 无图）", file=sys.stderr)
                return 2
            _manifest(files, args.out, args.json_out)
            return 0
    except ImportError as e:
        print(f"[err] 缺依赖: {e}。装齐后重试：python -m pip install pymupdf pillow", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"[err] {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())