#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf_extract.py —— PDF 全文提取（供 AI 读取并理解 PDF 全部信息，防遗漏）

多后端降级（按优先级自动选第一个可用的）：
  1. PyMuPDF (fitz)   —— 提取质量最高，保留页面结构/文本顺序，推荐（pip install PyMuPDF）
  2. pypdf            —— 纯 Python 轻量兜底（pip install pypdf）
  3. 系统 pdftotext   —— 若本机装了 poppler（Linux/WSL 常见）
  都没有 → 打印安装指引并退出 2（不静默降级交付）。

保证"不要有遗漏"：
  - 逐页提取并带页标记（==== 第 i / N 页 ====），页眉页脚不丢；
  - 输出元数据（标题/作者/创建时间/页数）；
  - 完整性报告：总页数、每页字符数、空页列表（空页=扫描件/纯图片，需 OCR 或视觉读取，另行处理）；
  - 表格尽力提取（fitz 后端支持时），并标注提取到的表格位置。

用法:
    python pdf_extract.py 题目.pdf                  # 全文输出到 stdout
    python pdf_extract.py 题目.pdf --out 题目.txt    # 写文件（AI 直接读这个）
    python pdf_extract.py 题目.pdf --page 2          # 只提取第 2 页
    python pdf_extract.py 题目.pdf --range 1-3       # 提取 1-3 页
    python pdf_extract.py 题目.pdf --no-tables       # 跳过表格提取

⚠️ 边界：本工具提取的是 PDF 的【文字层】。扫描件 / 纯图片 PDF 没有文字层，
   会报"空页"——此时用视觉/OCR 方案读取（或先对扫描件做 OCR 生成文字层）。
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

_BACKENDS = []  # [(name, extractor), ...]


def _find_backend():
    """按优先级探测可用后端，返回 (名称, 提取函数) 或 None。"""
    try:
        try:
            import pymupdf as fitz  # PyMuPDF 新版命名（避免 fitz deprecation warning）
        except ImportError:
            import fitz  # 旧版兼容

        def _fitz(pdf, page_filter):
            doc = fitz.open(pdf)
            meta = {k: (v or "") for k, v in doc.metadata.items()}
            n = doc.page_count
            pages = []
            for i in range(n):
                if page_filter and i + 1 not in page_filter:
                    continue
                page = doc.load_page(i)
                text = page.get_text("text") or ""
                tables = []
                try:
                    for tb in page.find_tables().tables:
                        rows = [" | ".join(c.replace("\n", " ").strip() if c else "" for c in row)
                                for row in tb.extract()]
                        tables.append("\n".join(rows))
                except Exception:
                    tables = []
                pages.append((i + 1, text, tables))
            doc.close()
            return meta, n, pages
        return ("PyMuPDF(fitz)", _fitz)
    except ImportError:
        pass

    try:
        from pypdf import PdfReader

        def _pypdf(pdf, page_filter):
            doc = PdfReader(pdf)
            meta = dict(doc.metadata or {})
            meta = {k: (str(v) if v is not None else "") for k, v in meta.items()}
            n = len(doc.pages)
            pages = []
            for i in range(n):
                if page_filter and i + 1 not in page_filter:
                    continue
                text = doc.pages[i].extract_text() or ""
                pages.append((i + 1, text, []))
            return meta, n, pages
        return ("pypdf", _pypdf)
    except ImportError:
        pass

    if shutil.which("pdftotext"):
        def _pdftotext(pdf, page_filter):
            meta = {}
            out = subprocess.run(["pdftotext", "-q", pdf, "-"], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace")
            n = out.stdout.count("\f") + (1 if out.stdout.strip() else 0)
            pages = [(1, out.stdout.replace("\f", "\n\n"), [])]
            return meta, n, pages
        return ("pdftotext", _pdftotext)

    return None


def main():
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="PDF 全文提取（供 AI 读取，防遗漏）")
    ap.add_argument("pdf", help="PDF 文件路径")
    ap.add_argument("--out", help="输出到文件（缺省打印 stdout）")
    ap.add_argument("--page", type=int, help="只提取单页（页码从 1 起）")
    ap.add_argument("--range", help="提取页码范围，如 1-3")
    ap.add_argument("--no-tables", action="store_true", help="跳过表格提取")
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        print(f"[err] 找不到 PDF: {args.pdf}", file=sys.stderr)
        return 2

    backend = _find_backend()
    if backend is None:
        print("[err] 本机无任何 PDF 提取后端。安装其一后重试：", file=sys.stderr)
        print("    pip install PyMuPDF     # 推荐，提取质量最好", file=sys.stderr)
        print("    pip install pypdf       # 纯 Python 轻量", file=sys.stderr)
        print("    或安装 poppler（提供 pdftotext）", file=sys.stderr)
        return 2
    name, extractor = backend

    page_filter = None
    if args.page:
        page_filter = {args.page}
    elif args.range:
        try:
            a, b = (int(x) for x in args.range.split("-"))
            page_filter = set(range(a, b + 1))
        except Exception:
            print(f"[err] 非法 --range 格式: {args.range}（应为 1-3）", file=sys.stderr)
            return 2

    try:
        meta, n, pages = extractor(args.pdf, page_filter)
    except Exception as e:
        print(f"[err] 提取失败: {type(e).__name__}: {str(e)[:150]}", file=sys.stderr)
        return 2

    lines = []
    lines.append(f"# PDF 全文提取 · {os.path.basename(args.pdf)}")
    lines.append(f"- 后端: {name} | 总页数: {n} | 提取页: {len(pages)}")
    if meta:
        for k in ("title", "author", "creationDate", "modDate"):
            if meta.get(k):
                lines.append(f"- {k}: {meta[k]}")
    lines.append("")
    empty = []
    for idx, text, tables in pages:
        lines.append(f"==== 第 {idx} / {n} 页（{len(text)} 字符）====")
        lines.append(text if text.strip() else "[本页无文字层 —— 扫描件/纯图片，需 OCR 或视觉读取]")
        if not text.strip():
            empty.append(idx)
        if tables and not args.no_tables:
            for j, t in enumerate(tables, 1):
                lines.append(f"--- 第 {idx} 页 表格 {j} ---")
                lines.append(t)
        lines.append("")
    body = "\n".join(lines)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(body)
        print(f"[pdf_extract] 已写出 {args.out}（{name}，{len(pages)} 页，{len(body)} 字符）")
        if empty:
            print(f"  ⚠️ 空页（无文字层）: 第 {', '.join(str(e) for e in empty)} 页 —— 需 OCR/视觉读取，勿遗漏", file=sys.stderr)
        return 0

    print(body)
    if empty:
        print(f"[警告] 空页（无文字层）: 第 {', '.join(str(e) for e in empty)} 页 —— 需 OCR/视觉读取，勿遗漏", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
