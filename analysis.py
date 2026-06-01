import os
import re
import sys
import time
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

import config

# ── 408 四科及其关键词（用于将混合真题分类到具体科目） ──
SUBJECT_KEYWORDS = {
    "数据结构": [
        "数据结构", "线性表", "栈", "队列", "树", "二叉树", "图", "排序",
        "查找", "散列", "哈希", "BFS", "DFS", "链表", "堆", "算法", "遍历",
        "森林", "最小生成树", "最短路径", "拓扑排序", "关键路径",
    ],
    "计算机组成原理": [
        "计算机组成", "CPU", "存储器", "指令", "总线", "I/O", "Cache",
        "流水线", "补码", "浮点", "寻址", "微程序", "控制器", "ALU",
        "寄存器", "主存", "辅存", "虚拟存储", "中断", "DMA",
    ],
    "操作系统": [
        "操作系统", "进程", "线程", "死锁", "内存管理", "虚拟内存",
        "文件系统", "调度", "PV操作", "页面", "段表", "页表", "磁盘",
        "设备管理", "并发", "同步", "互斥", "信号量", "管程", "SPOOLing",
    ],
    "计算机网络": [
        "计算机网络", "TCP", "UDP", "IP", "HTTP", "DNS", "FTP", "SMTP",
        "路由", "链路层", "传输层", "网络层", "应用层", "以太网", "交换机",
        "路由器", "子网", "拥塞控制", "流量控制", "ARP", "NAT", "ICMP", "IPv4", "IPv6",
    ],
}

SYSTEM_PROMPT = (
    "你是408计算机考研考情分析师。你只能根据用户提供的历年真题资料进行分析。\n"
    "规则：\n"
    "1. 所有分析严格基于提供的真题内容，不引入任何外部知识或猜测。\n"
    "2. 若资料不足以支撑某个判断，明确标注「资料不足，无法判断」。\n"
    "3. 输出使用中文Markdown格式，表格对齐，层次分明。"
)


def extract_year(filename: str) -> int | None:
    """从文件名提取4位年份（如 2024计算机408真题 → 2024）"""
    m = re.search(r"(20\d{2})", filename)
    return int(m.group(1)) if m else None


def extract_subject_from_filename(filename: str) -> str | None:
    """从文件名提取科目名（如 竟成408真题考点分类 - 数据结构.pdf）"""
    subjects = ["数据结构", "计算机组成原理", "操作系统", "计算机网络"]
    for s in subjects:
        if s in filename:
            return s
    return None


def classify_chunk_by_keywords(text: str) -> str | None:
    """根据关键词将一段文本分类到四科之一，返回科目名或 None"""
    scores = {subj: 0 for subj in SUBJECT_KEYWORDS}
    for subj, keywords in SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text.lower():
                scores[subj] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None


def load_from_chroma() -> tuple[list[dict], list[str]]:
    """从 ChromaDB 加载所有 exams 分类的文档，返回 (文档列表, 错误信息列表)"""
    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=config.PERSIST_DIR,
    )
    # 获取 collection 中所有 metadata 含 source 的文档
    collection = vectorstore._collection
    results = collection.get(where={"category": "exams"})
    docs = []
    if results["ids"]:
        for i, doc_id in enumerate(results["ids"]):
            docs.append({
                "id": doc_id,
                "content": results["documents"][i],
                "metadata": results["metadatas"][i] if results["metadatas"] else {},
            })
    return docs, []


def load_from_files(exams_dir: str) -> tuple[list[dict], list[str]]:
    """直接从 data/exams/ PDF 文件加载，返回 (文档列表, 错误列表)"""
    docs: list[dict] = []
    errors: list[str] = []

    for fname in sorted(os.listdir(exams_dir)):
        if not fname.lower().endswith(".pdf"):
            continue
        fp = os.path.join(exams_dir, fname)
        try:
            loader = PyPDFLoader(fp)
            pages = loader.load()
            full_text = "\n".join(p.page_content for p in pages)
            docs.append({
                "source": fname,
                "content": full_text,
                "year": extract_year(fname),
                "subject": extract_subject_from_filename(fname),
            })
            print(f"  [OK] {fname} ({len(pages)} 页)")
        except Exception as e:
            errors.append(f"{fname}: {e}")
            print(f"  [FAIL] {fname}: {e}", file=sys.stderr)

    return docs, errors


def build_subject_corpora(docs: list[dict]) -> dict[str, str]:
    """
    将混合真题文档按科目拆分，构建四个科目的完整文本语料。
    策略：
    - 文件名已标注科目的（考点分类系列），直接归入对应科目
    - 未标注的（年度真题），按关键词将每页归类
    """
    corpora: dict[str, list[str]] = {s: [] for s in SUBJECT_KEYWORDS}

    for doc in docs:
        pre_classified = doc.get("subject")
        if pre_classified and pre_classified in corpora:
            corpora[pre_classified].append(doc["content"])
            continue

        # 年度真题：按段落拆分后分类
        paragraphs = doc["content"].split("\n\n")
        for para in paragraphs:
            if len(para.strip()) < 20:
                continue
            subj = classify_chunk_by_keywords(para)
            if subj:
                corpora[subj].append(para)

    return {s: "\n\n".join(chunks) for s, chunks in corpora.items()}


def aggregate_stats(docs: list[dict]) -> dict:
    """汇总基础统计信息"""
    years = sorted(d for d in (doc.get("year") for doc in docs) if d)
    return {
        "total_files": len(docs),
        "year_range": f"{years[0]}-{years[-1]}" if years else "未知",
        "years_covered": years,
        "recent_3_years": [y for y in years if y >= max(years) - 2] if years else [],
    }


def generate_report(docs: list[dict], corpora: dict[str, str], stats: dict) -> str:
    """
    调用 DeepSeek Chat 生成考情分析报告。
    拼接统计信息 + 各科目语料摘要，让模型严格基于资料分析。
    """
    # 构建各科目语料的截取摘要（防止上下文溢出，每科取15000字）
    subject_summaries = {}
    for subj, text in corpora.items():
        subject_summaries[subj] = text[:15000] if text else "（该科目暂无真题资料）"

    prompt = f"""请基于以下历年408真题资料，生成一份考情分析报告。

## 基础统计
- 历年真题文件数：{stats['total_files']}
- 年份范围：{stats['year_range']}
- 近3年：{stats['recent_3_years']}

## 各科目真题语料摘要

### 数据结构
{subject_summaries.get('数据结构', '无')[:5000]}

### 计算机组成原理
{subject_summaries.get('计算机组成原理', '无')[:5000]}

### 操作系统
{subject_summaries.get('操作系统', '无')[:5000]}

### 计算机网络
{subject_summaries.get('计算机网络', '无')[:5000]}

## 报告要求
请生成一份Markdown格式的分析报告，文件名为 report_2026.md，内容包含：

1. **四科高频考点 Top10 表格**（每科一个表格，列为：排名 | 考点 | 出现频次 | 涉及年份）
2. **近3年命题趋势简述**（每科一段，严格基于上述语料）
3. **2026可能出题方向与冷门提醒**（列出可能的重点方向，以及近年未考但考纲包含的冷门考点）

严格基于提供的资料内容，无法判断的地方标注「资料不足」。"""

    print("\n正在调用 DeepSeek 生成分析报告...(可能需要1-3分钟)")
    llm = ChatOpenAI(
        openai_api_base=config.API_BASE,
        openai_api_key=config.API_KEY,
        model="deepseek-chat",
        temperature=0,
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    response = llm.invoke(messages)
    return response.content


def main():
    start = time.time()

    if not config.API_KEY:
        print("错误: 请设置环境变量 DEEPSEEK_API_KEY", file=sys.stderr)
        sys.exit(1)

    exams_dir = os.path.join(config.DATA_DIR, "exams")

    # 1. 加载真题文档（优先 ChromaDB，回退到文件系统）
    docs: list[dict] = []
    errors: list[str] = []
    source_mode = ""

    print("正在加载真题资料...")
    vectorstore_exists = (
        os.path.exists(config.PERSIST_DIR)
        and os.path.isdir(config.PERSIST_DIR)
        and any(f.startswith("chroma") for f in os.listdir(config.PERSIST_DIR))
    )

    if vectorstore_exists:
        print("  模式: ChromaDB 向量库")
        try:
            docs, errors = load_from_chroma()
            source_mode = "ChromaDB"
        except Exception as e:
            print(f"  ChromaDB 读取失败: {e}，回退到文件加载。", file=sys.stderr)

    if not docs:
        print("  模式: 直接加载 PDF 文件")
        docs, errors = load_from_files(exams_dir)
        source_mode = "文件系统"

    if not docs:
        print("错误: 没有加载到任何真题文档。", file=sys.stderr)
        sys.exit(1)

    print(f"\n加载完成: {len(docs)} 个文档 (来源: {source_mode})")
    if errors:
        print(f"  失败: {len(errors)} 个")
        for e in errors:
            print(f"    - {e}")

    # 2. 构建各科目语料
    print("\n正在按科目分类语料...")
    corpora = build_subject_corpora(docs)
    for subj, text in corpora.items():
        print(f"  {subj}: {len(text)} 字符")

    # 3. 基础统计
    stats = aggregate_stats(docs)
    print(f"\n基础统计: {stats['year_range']}, 共 {stats['total_files']} 个文件")

    # 4. 调用 DeepSeek 生成报告
    report = generate_report(docs, corpora, stats)

    # 5. 保存报告
    report_path = os.path.join(config.OUTPUT_DIR, "report_2026.md")
    # 确保报告内容以标题开头，去除可能的 markdown 代码块包裹
    clean_report = report.strip()
    if clean_report.startswith("```"):
        clean_report = re.sub(r"^```\w*\n?", "", clean_report)
        clean_report = re.sub(r"\n```$", "", clean_report)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(clean_report)

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"报告已保存至: {report_path}")
    print(f"总耗时: {elapsed:.1f}s")

    # 打印报告预览（前50行）
    lines = clean_report.split("\n")
    print(f"\n── 报告预览（前50行）──")
    for line in lines[:50]:
        print(line)


if __name__ == "__main__":
    main()
