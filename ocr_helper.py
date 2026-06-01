"""
OCR 辅助脚本：对 PyPDFLoader 无法提取文本的扫描版 PDF，使用 Tesseract OCR
提取中文文本并保存为同名 .txt 文件，供 ingest.py 自动导入。

使用前安装依赖：
  pip install pytesseract PyMuPDF Pillow

Windows 还需要安装 Tesseract-OCR:
  https://github.com/UB-Mannheim/tesseract/wiki
  (安装时勾选 Chinese Simplified 语言包)

用法：
  python ocr_helper.py                     # 默认：200 DPI + 快速模式 + 单文件
  python ocr_helper.py --fast              # 快速模式：150 DPI + 简化版面分析
  python ocr_helper.py --quality           # 质量优先：300 DPI + 完整版面分析
  python ocr_helper.py --workers 4         # 4 个 PDF 并行处理
  python ocr_helper.py --dir data/minds    # 只处理指定目录
  python ocr_helper.py --dry-run           # 仅预览，不执行
"""

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import config

# Tesseract 快速 / 质量配置
FAST_CONFIG = "--psm 6 --oem 1"       # psm 6=统一文本块, oem 1=LSTM only (快)
QUALITY_CONFIG = "--psm 3 --oem 3"     # psm 3=自动版面, oem 3=混合引擎 (准)

# 图片最大边长（Tesseract/Leptonica 限制）
MAX_DIM = 3600


def can_extract_text(filepath: str) -> bool:
    """用 PyPDFLoader 快速测试 PDF 是否能提取到有效文本"""
    try:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(filepath)
        pages = loader.load()
        total_text = "".join(p.page_content for p in pages).strip()
        return len(total_text) > 100
    except Exception:
        return False


def _ocr_one_page(args: tuple) -> tuple[int, str]:
    """
    单个页面的 OCR（供线程池调用）。
    参数: (page_index, pixmap_samples, width, height, lang, tesseract_config)
    返回: (page_index, text)
    """
    idx, samples, width, height, lang, tesseract_config = args
    import pytesseract
    from PIL import Image

    img = Image.frombytes("RGB", [width, height], samples)
    w, h = img.size
    if max(w, h) > MAX_DIM:
        ratio = MAX_DIM / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    text = pytesseract.image_to_string(img, lang=lang, config=tesseract_config)
    return idx, text


def ocr_pdf(
    filepath: str,
    output_path: str,
    dpi: int = 200,
    lang: str = "chi_sim",
    tesseract_config: str = FAST_CONFIG,
    workers: int = 1,
) -> int:
    """
    OCR 单个 PDF 文件。workers > 1 时使用线程池并行处理页面。
    返回提取到的总字符数。
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(f"  错误: 缺少 PyMuPDF，请运行 pip install PyMuPDF", file=sys.stderr)
        return 0

    try:
        doc = fitz.open(filepath)
    except Exception as e:
        print(f"  错误: 无法打开 PDF - {e}", file=sys.stderr)
        return 0

    total = len(doc)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    # 渲染所有页面为原始像素数据（避免 PIL Image 序列化开销）
    page_data = []
    for i in range(total):
        try:
            pix = doc[i].get_pixmap(matrix=mat)
            page_data.append((i, pix.samples, pix.width, pix.height, lang, tesseract_config))
        except Exception as e:
            print(f"  错误 (第{i+1}页): 渲染失败 - {e}", file=sys.stderr)

    doc.close()

    if workers > 1 and len(page_data) > 1:
        # 线程池并行 OCR（Tesseract 会释放 GIL）
        from concurrent.futures import ThreadPoolExecutor
        results: dict[int, str] = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_ocr_one_page, args): args[0] for args in page_data}
            for future in as_completed(futures):
                idx, text = future.result()
                results[idx] = text
                if len(results) % 10 == 0:
                    print(f"  进度: {len(results)}/{total} 页")
        all_text = [results[i] for i in range(total) if results.get(i, "").strip()]
    else:
        # 单线程顺序处理
        import pytesseract
        from PIL import Image
        all_text = []
        for i, samples, width, height, lang_cfg, cfg in page_data:
            try:
                img = Image.frombytes("RGB", [width, height], samples)
                w, h = img.size
                if max(w, h) > MAX_DIM:
                    ratio = MAX_DIM / max(w, h)
                    img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
                text = pytesseract.image_to_string(img, lang=lang_cfg, config=cfg)
                if text.strip():
                    all_text.append(text)
            except Exception as e:
                print(f"  错误 (第{i+1}页): {e}", file=sys.stderr)
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{total} 页")

    combined = "\n".join(all_text)
    if combined.strip():
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(combined)
    return len(combined)


def _ocr_pdf_worker(args_tuple: tuple) -> tuple[str, int]:
    """进程池工作函数：OCR 单个文件"""
    pdf_path, txt_path, dpi, lang, tesseract_config, page_workers = args_tuple
    fname = os.path.basename(pdf_path)
    char_count = ocr_pdf(pdf_path, txt_path, dpi=dpi, lang=lang,
                         tesseract_config=tesseract_config, workers=page_workers)
    return fname, char_count


def collect_pdfs(root_dir: str, force: bool) -> list[tuple[str, str]]:
    """扫描需要 OCR 的 PDF 文件"""
    jobs = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if not fname.lower().endswith(".pdf"):
                continue
            pdf_path = os.path.join(dirpath, fname)
            txt_path = os.path.splitext(pdf_path)[0] + ".txt"
            if not force and os.path.exists(txt_path):
                continue
            if not force and can_extract_text(pdf_path):
                continue
            jobs.append((pdf_path, txt_path))
    return jobs


def main():
    parser = argparse.ArgumentParser(description="OCR 扫描版 PDF → 文本文件")
    parser.add_argument("--dir", default=None, help="指定要扫描的目录（默认: data/）")
    parser.add_argument("--force", action="store_true",
                        help="强制 OCR 所有 PDF（忽略已有 .txt 或可提取文本）")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅列出需要 OCR 的文件，不执行")
    parser.add_argument("--dpi", type=int, default=200,
                        help="OCR 分辨率，越高越清晰越慢 (默认: 200)")
    parser.add_argument("--lang", default="chi_sim",
                        help="Tesseract 语言包 (默认: chi_sim)")
    parser.add_argument("--fast", action="store_true",
                        help="极速模式: 150 DPI + 简化版面分析")
    parser.add_argument("--quality", action="store_true",
                        help="质量优先: 300 DPI + 完整版面分析")
    parser.add_argument("--workers", type=int, default=1,
                        help="并行处理 N 个 PDF 文件 (默认: 1)")
    parser.add_argument("--page-workers", type=int, default=1,
                        help="单文件内并行处理 N 页 (默认: 1，大文件可设 2-4)")
    args = parser.parse_args()

    root = args.dir or config.DATA_DIR
    if not os.path.isdir(root):
        print(f"错误: 目录不存在 - {root}", file=sys.stderr)
        sys.exit(1)

    # 确定 DPI 和 Tesseract 配置
    dpi = args.dpi
    tesseract_config = FAST_CONFIG
    if args.fast:
        dpi = 150
        tesseract_config = FAST_CONFIG
    elif args.quality:
        dpi = 300
        tesseract_config = QUALITY_CONFIG

    jobs = collect_pdfs(root, args.force)

    if not jobs:
        print("没有需要 OCR 的 PDF 文件。")
        return

    print(f"发现 {len(jobs)} 个待 OCR 文件 (DPI={dpi}, workers={args.workers})")
    for pdf_path, _ in jobs:
        print(f"  - {os.path.relpath(pdf_path, config.DATA_DIR)}")

    if args.dry_run:
        print("\n(仅预览，未执行 OCR)")
        return

    start_time = time.time()

    if args.workers > 1 and len(jobs) > 1:
        # 多进程并行处理多个 PDF
        task_args = [(p, t, dpi, args.lang, tesseract_config, args.page_workers)
                     for p, t in jobs]
        success = 0
        failed = 0
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(_ocr_pdf_worker, ta): ta[0] for ta in task_args}
            for future in as_completed(futures):
                fname, char_count = future.result()
                if char_count > 0:
                    print(f"  ✓ {fname} ({char_count:,} 字符)")
                    success += 1
                else:
                    print(f"  ✗ {fname} (无文本)", file=sys.stderr)
                    failed += 1
    else:
        # 单进程顺序处理
        success = 0
        failed = 0
        for pdf_path, txt_path in jobs:
            rel = os.path.relpath(pdf_path, config.DATA_DIR)
            print(f"\n处理: {rel}")
            char_count = ocr_pdf(pdf_path, txt_path, dpi=dpi, lang=args.lang,
                                 tesseract_config=tesseract_config,
                                 workers=args.page_workers)
            if char_count > 0:
                print(f"  完成: {char_count:,} 字符")
                success += 1
            else:
                print(f"  失败: 未提取到文本", file=sys.stderr)
                failed += 1

    elapsed = time.time() - start_time
    print(f"\n── OCR 摘要 ──")
    print(f"  成功: {success}  失败: {failed}  耗时: {elapsed:.1f}s")
    if success > 0:
        print(f"  下一步: python ingest.py")


if __name__ == "__main__":
    main()
