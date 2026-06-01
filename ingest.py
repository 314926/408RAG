import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

import config


def compute_sha256(filepath: str) -> str:
    """计算文件的 SHA256 哈希值"""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_cache() -> dict[str, str]:
    """加载增量缓存"""
    if os.path.exists(config.CACHE_FILE):
        with open(config.CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict[str, str]) -> None:
    """保存增量缓存"""
    with open(config.CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def category_from_path(filepath: str) -> str:
    """从文件路径推断分类：outline / textbooks / exams / notes"""
    rel = os.path.relpath(filepath, config.DATA_DIR)
    parts = Path(rel).parts
    return parts[0] if len(parts) > 1 else "unknown"


def doc_id_from_path(filepath: str) -> str:
    """从文件相对路径生成稳定的 doc_id（取 SHA256 前 12 位）"""
    rel = os.path.relpath(filepath, config.DATA_DIR)
    return compute_sha256(filepath)[:12]


def extract_subject(rel_path: str) -> str:
    """从文件路径提取科目名称（用于 mindmap 文件的 subject metadata）"""
    fname = os.path.basename(rel_path)
    fname = os.path.splitext(fname)[0]
    for suffix in ["（含新大纲考点）", "（含新大纲考点)", "(含新大纲考点)", "思维导图", "思维导"]:
        fname = fname.replace(suffix, "")
    return fname.strip()


def detect_qa_format(text: str) -> bool:
    """检测文本是否包含 Q&A 大题格式（支持中英文 Q&A 标记）"""
    q_count = len(re.findall(r"(?:^|\n)\s*Q\s*[:：]", text))
    a_count = len(re.findall(r"(?:^|\n)\s*A\s*[:：]", text))
    if q_count >= 2 and a_count >= 2:
        return True
    for q_pat, a_pat in [
        (r"(?:【题目[：:]?|题目[：:]|问题[：:]|【例\w*[：:]?|题型[：:])", r"(?:【解析】|【答案】|解析[：:]|答案[：:]|解答[：:]|【解】)"),
        (r"\n\s*(?:[一二三四五六七八九十]+[、．.]|\d+[、．.])", r"(?:【解析】|【答案】|答[：:]|解析[：:]|答案[：:])"),
    ]:
        q_matches = len(re.findall(q_pat, text))
        a_matches = len(re.findall(a_pat, text))
        if q_matches >= 2 and a_matches >= 2:
            return True
    return False


def split_qa_pairs(text: str, max_chunk_size: int) -> list[str]:
    """将 Q&A 文本按 Q: 或大题边界拆分，保持每个 Q&A 对完整"""
    separators = [
        r"\n(?=\s*Q\s*[:：])",
        r"\n(?=【题目[：:]?|\d+[、．.])",
        r"\n(?=题目[：:]|问题[：:])",
    ]
    pairs = []
    for sep in separators:
        parts = re.split(sep, text)
        if len(parts) >= 3:
            pairs = parts
            break
    if len(pairs) < 2:
        pairs = [text]

    chunks = []
    for pair in pairs:
        pair = pair.strip()
        if not pair:
            continue
        if len(pair) <= max_chunk_size:
            chunks.append(pair)
        else:
            sub = re.split(r"(\n\s*(?:A\s*[:：]|答案[：:]|解析[：:]|解答[：:]|【解析】|【答案】))", pair, maxsplit=1)
            if len(sub) >= 3:
                q_part = sub[0] + (sub[1] if len(sub) > 1 else "")
                a_part = "".join(sub[2:])
                if len(q_part) > max_chunk_size:
                    chunks.append(q_part[:max_chunk_size])
                else:
                    chunks.append(q_part)
                if len(a_part) > 0:
                    chunks.append("解析/答案: " + a_part[:max_chunk_size])
            else:
                chunks.append(pair[:max_chunk_size])
    return chunks


def collect_files(data_dir: str, cache: dict[str, str]) -> list[str]:
    """扫描所有支持的文件，返回需要处理（新增或修改）的文件列表"""
    files = []
    for root, _, filenames in os.walk(data_dir):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in config.SUPPORTED_EXT:
                continue
            filepath = os.path.join(root, fname)
            current_hash = compute_sha256(filepath)
            if cache.get(filepath) != current_hash:
                files.append(filepath)
    return files


def load_documents(filepaths: list[str]) -> tuple[list, int]:
    """
    加载文件并返回 (文档列表, 失败文件数)
    每个文档的 metadata 包含 source（相对路径）和 category
    """
    docs = []
    failed = 0
    for fp in filepaths:
        ext = os.path.splitext(fp)[1].lower()
        category = category_from_path(fp)
        rel_path = os.path.relpath(fp, config.DATA_DIR)
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(fp)
            else:
                loader = TextLoader(fp, encoding="utf-8")
            loaded = loader.load()
            for doc in loaded:
                doc.metadata["source"] = rel_path
                doc.metadata["category"] = category
            docs.extend(loaded)
            print(f"  [OK] {rel_path} ({len(loaded)} 页/段)")
        except Exception as e:
            print(f"  [FAIL] {rel_path}: {e}", file=sys.stderr)
            failed += 1
    return docs, failed


def build_chunks(raw_docs: list) -> tuple[list, list]:
    """对原始文档按分类策略分块，返回 (all_chunks, zero_block_files)。

    分类策略：
    - minds/ .md 文件 → MarkdownHeaderTextSplitter（保持标题结构）
    - notes/ 文件 → 检测 Q&A 格式，保持 Q&A 完整；否则默认分块
    - 其他文件 → RecursiveCharacterTextSplitter 默认分块
    """
    from collections import defaultdict
    from langchain_core.documents import Document

    default_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""],
    )

    md_headers = [
        ("##", "h2_section"),
        ("###", "h3_section"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=md_headers)
    fine_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.MINDMAP_CHUNK_SIZE,
        chunk_overlap=64,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )

    source_groups: dict[str, list] = defaultdict(list)
    for doc in raw_docs:
        source_groups[doc.metadata["source"]].append(doc)

    all_chunks = []
    zero_block_files = []

    for source, docs in source_groups.items():
        ext = os.path.splitext(source)[1].lower()
        category = docs[0].metadata.get("category", "unknown")
        docs = [d for d in docs if d.page_content and d.page_content.strip()]
        if not docs:
            zero_block_files.append((source, "文本提取为空（可能是扫描版/图片型PDF）"))
            continue
        full_text = "\n\n".join(d.page_content for d in docs)

        if category == config.MINDS_DIR and ext == ".md":
            md_sections = markdown_splitter.split_text(full_text)
            chunks_for_source = []
            for sec in md_sections:
                if len(sec.page_content) <= config.MINDMAP_CHUNK_SIZE:
                    chunks_for_source.append(sec)
                else:
                    sub_chunks = fine_splitter.split_documents([sec])
                    chunks_for_source.extend(sub_chunks)
            subject = extract_subject(source)
            for ch in chunks_for_source:
                ch.metadata["source"] = source
                ch.metadata["category"] = "mindmap"
                ch.metadata["subject"] = subject
            all_chunks.extend(chunks_for_source)
            print(f"  [mindmap/md] {source} → {len(chunks_for_source)} 块 (MarkdownHeaderTextSplitter)")

        elif category == config.NOTES_DIR:
            if detect_qa_format(full_text):
                qa_texts = split_qa_pairs(full_text, config.COMPREHENSIVE_CHUNK_SIZE)
                chunks_for_source = []
                for text in qa_texts:
                    chunks_for_source.append(Document(page_content=text))
                for ch in chunks_for_source:
                    ch.metadata["source"] = source
                    ch.metadata["category"] = category
                    ch.metadata["type"] = "comprehensive"
                all_chunks.extend(chunks_for_source)
                print(f"  [notes/qa] {source} → {len(chunks_for_source)} 块 (Q&A-preserving)")
            else:
                chunks_for_source = default_splitter.split_documents(docs)
                for ch in chunks_for_source:
                    ch.metadata["source"] = source
                    ch.metadata["category"] = category
                all_chunks.extend(chunks_for_source)
                print(f"  [notes/default] {source} → {len(chunks_for_source)} 块")

        else:
            chunks_for_source = default_splitter.split_documents(docs)
            if category == config.MINDS_DIR:
                subject = extract_subject(source)
                for ch in chunks_for_source:
                    ch.metadata["category"] = "mindmap"
                    ch.metadata["subject"] = subject
            all_chunks.extend(chunks_for_source)
            print(f"  [default] {source} → {len(chunks_for_source)} 块")

    for source, _docs in source_groups.items():
        has_chunks = any(
            ch.metadata.get("source") == source for ch in all_chunks
        )
        if not has_chunks:
            if not any(z[0] == source for z in zero_block_files):
                zero_block_files.append((source, "分块后无内容（PDF文本可能为扫描图片）"))

    if zero_block_files:
        print(f"\n⚠ 警告: {len(zero_block_files)} 个文件因无法提取文本而被跳过（旧向量已保留）:")
        for fname, reason in zero_block_files:
            print(f"  ⚠ {fname} — {reason}")

    print(f"\n分块完成: {len(all_chunks)} 个块 (来自 {len(raw_docs)} 个原始片段)")
    return all_chunks, zero_block_files


def write_chunks_to_vectorstore(all_chunks: list, vectorstore: Chroma) -> None:
    """将分块按 source 分组写入向量库（先删旧块再写新块，增量更新）。
    自动为每个块补充 doc_id 和 chunk_index 元数据，确保父文档扩展正常工作。
    """
    from collections import defaultdict

    if not all_chunks:
        return

    groups: dict[str, list] = defaultdict(list)
    for i, doc in enumerate(all_chunks):
        groups[doc.metadata["source"]].append((i, doc))

    for source, items in groups.items():
        vectorstore._collection.delete(where={"source": source})

        indices, source_chunks = zip(*items)
        for chunk_idx, chunk in enumerate(source_chunks):
            chunk.metadata["doc_id"] = doc_id_from_path(
                os.path.join(config.DATA_DIR, source)
            )
            chunk.metadata["chunk_index"] = chunk_idx

        texts = [doc.page_content for doc in source_chunks]
        metadatas = [doc.metadata for doc in source_chunks]
        ids = [f"{source}_{idx}" for idx in indices]
        vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        print(f"  已写入: {source} ({len(texts)} 块)")


def main():
    start_time = time.time()

    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    cache = load_cache()
    files_to_process = collect_files(config.DATA_DIR, cache)

    if not files_to_process:
        print("没有新文件或修改的文件，无需更新。")
        return

    print(f"发现 {len(files_to_process)} 个待处理文件：")
    for fp in files_to_process:
        print(f"  - {os.path.relpath(fp, config.DATA_DIR)}")

    raw_docs, failed_count = load_documents(files_to_process)

    all_chunks, zero_block_files = build_chunks(raw_docs)

    vectorstore = Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=config.PERSIST_DIR,
    )

    write_chunks_to_vectorstore(all_chunks, vectorstore)

    for fp in files_to_process:
        cache[fp] = compute_sha256(fp)
    save_cache(cache)

    elapsed = time.time() - start_time
    print(f"\n── 导入摘要 ──")
    print(f"  文件数: {len(files_to_process)} (成功: {len(files_to_process) - failed_count}, 失败: {failed_count})")
    print(f"  块数:   {len(all_chunks)}")
    print(f"  耗时:   {elapsed:.1f}s")


if __name__ == "__main__":
    main()
