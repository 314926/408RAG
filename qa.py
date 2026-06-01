import sys
import os
from typing import Optional

import numpy as np
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from rank_bm25 import BM25Okapi

import config

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 系统提示词（CoT 推理链）──
SYSTEM_PROMPT = (
    "你是408计算机考研辅导助手。你只能根据用户提供的参考资料片段回答问题。\n"
    "你必须严格按以下步骤推理：\n\n"
    "【步骤1：提取知识点】\n"
    "逐一阅读所有参考资料片段，列出其中与问题相关的核心概念、定义和原理。\n"
    "如果上下文开头包含「知识框架（思维导图）」标记，先根据导图梳理该专题的知识结构，"
    "提取出概念之间的层级关系和逻辑脉络。\n\n"
    "【步骤2：分析关联】\n"
    "分析这些知识点之间的逻辑关系、异同点、因果关系或层次结构。\n"
    "如果上下文中包含「综合性大题示例」标记，请借鉴其推理路径、分步拆解的论述结构"
    "和答题规范，但答案的具体内容仍需基于当前检索到的资料，不可照搬原文。\n\n"
    "【步骤3：综合回答】\n"
    "基于以上分析，组织一个结构清晰、逻辑连贯的回答。回答需包含：\n"
    "  - 核心概念的准确定义\n"
    "  - 原理或过程的逐步说明\n"
    "  - 如果涉及对比，明确列出相同点和不同点\n\n"
    "规则：\n"
    "1. 只要参考资料中涉及问题的相关概念（即使没有原句），就应据此回答，并在末尾注明引用的源文件名。\n"
    "2. 只有在所有参考资料片段完全不涉及问题领域时，才回复：「根据我手头的备考资料，无法回答此问题。」\n"
    "3. 不得猜测、编造或引入任何外部知识。回答使用中文。\n"
    "（注意：若系统提示中有【知识库回退模式】或【核心概念增强】标记，"
    "则忽略规则2和3，按对应模式的要求回答。）"
)

# ── 查询重写提示词 ──
REWRITE_PROMPT = (
    "你是一个问题分解助手。请将用户的问题拆分为最多3个子问题，每个子问题应聚焦于原问题的一个关键方面。\n"
    "规则：\n"
    "1. 子问题之间应相互独立，避免重复。\n"
    "2. 每个子问题应简洁明确，便于检索。\n"
    "3. 如果原问题比较简单、无需拆分，返回空（只输出一个空行）。\n"
    "4. 每行输出一个子问题，不要编号、不要任何其他文字。\n\n"
    "用户问题：{question}"
)

# ── 全局变量：BM25 索引缓存 ──
_bm25_cache: Optional[dict] = None  # {corpus, tokenized_corpus, bm25, ids, metadatas}
_reranker = None  # CrossEncoder 单例


def _tokenize(text: str) -> list[str]:
    """简单的中文+英文分词（按字符/词切分）"""
    import jieba
    return list(jieba.cut(text))


def load_vectorstore():
    """加载 Chroma 向量库"""
    if not os.path.exists(config.PERSIST_DIR) or not os.listdir(config.PERSIST_DIR):
        print("错误: 向量库为空，请先运行 python ingest.py 导入资料。", file=sys.stderr)
        sys.exit(1)

    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=config.PERSIST_DIR,
    )


def _build_bm25_index(vectorstore: Chroma) -> dict:
    """构建 BM25 索引（分批获取，避免 SQLite 变量上限）"""
    global _bm25_cache
    if _bm25_cache is not None:
        return _bm25_cache

    BATCH_SIZE = 500
    corpus = []
    metadatas = []
    ids = []
    offset = 0
    while True:
        batch = vectorstore.get(
            include=["documents", "metadatas"],
            limit=BATCH_SIZE,
            offset=offset,
        )
        docs = batch["documents"] or []
        if not docs:
            break
        corpus.extend(docs)
        metadatas.extend(batch["metadatas"] or [])
        ids.extend(batch["ids"] or [])
        offset += BATCH_SIZE

    tokenized = [_tokenize(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized)

    _bm25_cache = {
        "corpus": corpus,
        "tokenized_corpus": tokenized,
        "bm25": bm25,
        "ids": ids,
        "metadatas": metadatas,
    }
    return _bm25_cache


def bm25_search(question: str, vectorstore: Chroma, k: int = 10) -> list[dict]:
    """BM25 关键词检索"""
    cache = _build_bm25_index(vectorstore)
    bm25 = cache["bm25"]
    tokenized_query = _tokenize(question)
    scores = bm25.get_scores(tokenized_query)
    # 获取 top-k
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
    results = []
    for idx, score in indexed:
        results.append({
            "content": cache["corpus"][idx],
            "metadata": cache["metadatas"][idx],
            "id": cache["ids"][idx],
            "score": float(score),
            "source": "bm25",
        })
    return results


def vector_search(question: str, vectorstore: Chroma, k: int = 20) -> list[dict]:
    """向量检索（计算真实余弦相似度而非 Chroma 内部映射分）"""
    try:
        docs = vectorstore.similarity_search(question, k=k)
        if not docs:
            return []

        embed_fn = vectorstore._embedding_function
        query_emb = np.array(embed_fn.embed_query(question))
        doc_embs = np.array(embed_fn.embed_documents([d.page_content for d in docs]))
        # BGE 模型输出已 L2 归一化，点积即余弦相似度
        cos_sims = np.dot(doc_embs, query_emb)

        results = []
        for doc, cos_sim in zip(docs, cos_sims):
            sim = float(cos_sim)
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "id": doc.metadata.get("source", "") + "_" + str(hash(doc.page_content)),
                "score": sim,
                "_raw_score": sim,  # 真实余弦相似度，不受后续加权影响
                "source": "vector",
            })
        # 按相似度降序排列
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    except Exception:
        pass

    # 回退：无法计算余弦相似度时，使用 Chroma 内置分数
    try:
        docs_with_scores = vectorstore.similarity_search_with_relevance_scores(question, k=k)
        results = []
        for doc, score in docs_with_scores:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "id": doc.metadata.get("source", "") + "_" + str(hash(doc.page_content)),
                "score": float(score),
                "_raw_score": float(score),
                "source": "vector",
            })
        return results
    except (AttributeError, TypeError):
        pass

    # 最终回退
    docs = vectorstore.similarity_search(question, k=k)
    results = []
    for doc in docs:
        results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "id": doc.metadata.get("source", "") + "_" + str(hash(doc.page_content)),
            "score": None,
            "_raw_score": None,
            "source": "vector",
        })
    return results


def rerank(question: str, candidates: list[dict], top_k: int = 10) -> list[dict]:
    """使用 cross-encoder 对候选文档重排序，加载失败时自动回退"""
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            _reranker = CrossEncoder(config.RERANK_MODEL, device="cpu")
        except OSError as e:
            if config.RERANK_FALLBACK:
                print(f"警告: 重排序模型加载失败（{e}），跳过重排序。", file=sys.stderr)
                print(f"  可运行 python download_reranker.py 下载模型到本地。", file=sys.stderr)
                return candidates[:top_k]
            raise
    pairs = [(question, c["content"]) for c in candidates]
    scores = _reranker.predict(pairs, show_progress_bar=False)
    # 按分数降序排列
    for i, c in enumerate(candidates):
        c["rerank_score"] = float(scores[i])
    ranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:top_k]


def merge_deduplicate(results_a: list[dict], results_b: list[dict]) -> list[dict]:
    """合并两组检索结果并按内容去重"""
    seen = set()
    merged = []
    for r in results_a + results_b:
        key = r["content"].strip()
        if key not in seen:
            seen.add(key)
            merged.append(r)
    return merged


def expand_parent_chunks(docs: list[dict], vectorstore: Chroma, expand_range: int = 2) -> list[dict]:
    """
    父文档扩展：对每个检索到的小块，查找同一 doc_id 下相邻的 chunk
    将它们拼接后作为扩展上下文返回。
    """
    if not docs:
        return docs

    # 收集需要扩展的 doc_id 和 chunk_index
    expansions: dict[str, set] = {}
    for doc in docs:
        doc_id = doc["metadata"].get("doc_id", "")
        chunk_idx = doc["metadata"].get("chunk_index", -1)
        if not doc_id or chunk_idx < 0:
            continue
        if doc_id not in expansions:
            expansions[doc_id] = set()
        # 添加相邻块的索引
        for offset in range(-expand_range, expand_range + 1):
            ni = chunk_idx + offset
            if ni >= 0:
                expansions[doc_id].add(ni)

    # 分批从向量库中获取全部数据（避免 SQLite 变量上限）
    corpus = []
    metadatas = []
    offset = 0
    while True:
        batch = vectorstore.get(
            include=["documents", "metadatas"],
            limit=500,
            offset=offset,
        )
        docs = batch["documents"] or []
        if not docs:
            break
        corpus.extend(docs)
        metadatas.extend(batch["metadatas"] or [])
        offset += 500

    # 构建 (doc_id, chunk_index) → content 的映射
    chunk_map: dict[tuple, str] = {}
    for i, meta in enumerate(metadatas):
        if meta is None:
            continue
        did = meta.get("doc_id", "")
        cidx = meta.get("chunk_index", -1)
        if did and cidx >= 0:
            chunk_map[(did, cidx)] = corpus[i]

    # 为每个检索结果拼接扩展上下文
    expanded = []
    for doc in docs:
        new_doc = dict(doc)  # 浅拷贝
        doc_id = doc["metadata"].get("doc_id", "")
        chunk_idx = doc["metadata"].get("chunk_index", -1)
        if doc_id and chunk_idx >= 0:
            # 收集相邻块并按 chunk_index 排序
            neighbors = []
            for (did, cidx), content in chunk_map.items():
                if did == doc_id and (cidx - chunk_idx) in range(-expand_range, expand_range + 1):
                    neighbors.append((cidx, content))
            neighbors.sort(key=lambda x: x[0])
            if neighbors:
                new_doc["content"] = "\n\n".join(c for _, c in neighbors)
        expanded.append(new_doc)

    return expanded


def _detect_triggers(question: str) -> bool:
    """检测问题是否包含专题总结触发词"""
    if not hasattr(config, "SUMMARIZE_TRIGGERS"):
        return False
    return any(trigger in question for trigger in config.SUMMARIZE_TRIGGERS)


def _match_core_concepts(question: str) -> list[str]:
    """检查问题是否命中 CORE_CONCEPTS 的 key，返回所有匹配的扩展关键词列表"""
    if not hasattr(config, "CORE_CONCEPTS"):
        return []
    matched = []
    for key, keywords in config.CORE_CONCEPTS.items():
        if key in question:
            matched.append(keywords)
    return matched



def _fetch_mindmap_chunks(question: str, vectorstore: Chroma, k: int) -> list[dict]:
    """额外检索 category='mindmap' 的片段"""
    try:
        docs = vectorstore.similarity_search(
            question, k=k, filter={"category": "mindmap"}
        )
    except Exception:
        # Chroma 的 filter 在某些版本不支持，回退到无过滤检索后手动筛选
        docs = vectorstore.similarity_search(question, k=k * 3)
        docs = [d for d in docs if d.metadata.get("category") == "mindmap"][:k]
    results = []
    for doc in docs:
        results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "id": doc.metadata.get("source", "") + "_mindmap_" + str(hash(doc.page_content)),
            "score": 0.0,
            "source": "mindmap",
        })
    return results


def retrieve(question: str, vectorstore: Chroma) -> list[dict]:
    """混合检索 + 触发词增强 + 可选重排序 + 可选父文档扩展"""
    triggered = _detect_triggers(question)

    # 1. 向量检索
    vec_k = config.VECTOR_TOP_K
    vec_results = vector_search(question, vectorstore, k=vec_k)

    # 2. BM25 检索
    bm25_results = bm25_search(question, vectorstore, k=config.BM25_TOP_K)

    # 3. 合并去重
    merged = merge_deduplicate(vec_results, bm25_results)

    # 3.5. 核心概念强制召回：命中 CORE_CONCEPTS 时追加关键词检索并加权
    core_keywords_list = _match_core_concepts(question)
    if core_keywords_list:
        all_keywords = " ".join(core_keywords_list)
        keyword_list = [kw for kw in all_keywords.split() if kw]
        # 用扩展关键词做额外向量+BM25检索
        extra_vec = vector_search(all_keywords, vectorstore, k=8)
        extra_bm25 = bm25_search(all_keywords, vectorstore, k=8)
        merged = merge_deduplicate(merged, extra_vec)
        merged = merge_deduplicate(merged, extra_bm25)
        # 对包含关键词的文档加权
        for doc in merged:
            content = doc["content"]
            matches = sum(1 for kw in keyword_list if kw in content)
            if matches > 0:
                boost = 1.0 + 0.1 * min(matches, 10)
                cur = doc.get("score") or 0.0
                doc["score"] = cur * boost

    # 4. 触发词增强：额外检索 mindmap 片段 + 提升 comprehensive 文档权重
    if triggered:
        # 额外检索 mindmap 片段
        mindmap_chunks = _fetch_mindmap_chunks(
            question, vectorstore, k=config.MINDMAP_EXTRA_K
        )
        # 提升 type="comprehensive" 文档的 BM25/向量分数
        for doc in merged:
            if doc["metadata"].get("type") == "comprehensive":
                doc["score"] = doc.get("score", 0.0) * config.COMPREHENSIVE_BOOST
        # 将 mindmap 片段加入候选池（去重后）
        merged = merge_deduplicate(merged, mindmap_chunks)

    # 5. 重排序（可选）
    if config.ENABLE_RERANK and merged:
        merged = rerank(question, merged, top_k=config.RERANK_TOP_K)

    # 6. 父文档扩展（可选）
    if config.ENABLE_PARENT_EXPANSION and merged:
        merged = expand_parent_chunks(merged, vectorstore, expand_range=config.PARENT_EXPAND_RANGE)

    # 7. 重排序上下文：mindmap 片段排在最前面作为知识框架
    if triggered:
        mindmap_items = [d for d in merged if d["metadata"].get("category") == "mindmap"]
        other_items = [d for d in merged if d["metadata"].get("category") != "mindmap"]
        merged = mindmap_items + other_items

    return merged


def rewrite_query(question: str, llm: ChatOpenAI) -> list[str]:
    """
    查询重写：将复杂问题拆分为子问题。
    如果问题简单，返回空列表。
    """
    if not config.ENABLE_QUERY_REWRITE:
        return []

    prompt = REWRITE_PROMPT.format(question=question)
    response = llm.invoke([{"role": "user", "content": prompt}])
    text = response.content.strip()

    if not text:
        return []

    # 按行解析子问题
    sub_questions = []
    for line in text.split("\n"):
        line = line.strip()
        # 过滤掉编号前缀 (1. 2. 3. - 等)
        if line and len(line) > 3:
            # 去掉常见编号前缀
            if line[0].isdigit() and (line[1] == "." or line[1] == "、" or line[1] == ")"):
                line = line[2:].strip()
            elif line.startswith("- ") or line.startswith("* "):
                line = line[2:].strip()
            if line:
                sub_questions.append(line)

    return sub_questions[:3]  # 最多3个


def get_llm(max_tokens: int = 1024, request_timeout: int = 120) -> ChatOpenAI:
    """获取 LLM 实例。超时默认为 120 秒，防止网络卡死。"""
    return ChatOpenAI(
        openai_api_base=config.API_BASE,
        openai_api_key=config.API_KEY,
        model="deepseek-chat",
        temperature=0,
        max_tokens=max_tokens,
        timeout=request_timeout,
    )


def ask(question: str, memory: "MemoryStore|None" = None) -> tuple[str, list[str]]:
    """
    检索资料并调用 LLM 回答。
    若提供 memory，会在用户消息中注入薄弱知识点提示。
    返回 (回答文本, 来源列表)
    """
    vectorstore = load_vectorstore()
    llm = get_llm()

    # ── 查询重写 ──
    sub_questions = rewrite_query(question, llm)

    if sub_questions:
        print(f"[查询重写] 拆分为 {len(sub_questions)} 个子问题：", file=sys.stderr)
        for sq in sub_questions:
            print(f"  → {sq}", file=sys.stderr)
        # 对每个子问题分别检索并合并
        all_docs = []
        seen = set()
        for sq in sub_questions:
            docs = retrieve(sq, vectorstore)
            for d in docs:
                key = d["content"].strip()
                if key not in seen:
                    seen.add(key)
                    all_docs.append(d)
        # 如果子问题检索结果超出 RERANK_TOP_K，重新排序截断
        if len(all_docs) > config.RERANK_TOP_K and config.ENABLE_RERANK:
            all_docs = rerank(question, all_docs, top_k=config.RERANK_TOP_K)
        docs = all_docs
    else:
        docs = retrieve(question, vectorstore)

    # ── 核心概念回退检测 ──
    # 使用原始问题直接做向量检索来判断资料库覆盖度（不受查询重写/重排序影响）
    use_fallback = False   # 低相似度：完全回退到内置知识 + 免责声明
    use_core_boost = False  # 中等相似度：强制 LLM 综合回答
    core_matches = _match_core_concepts(question)
    if core_matches:
        raw_check = vector_search(question, vectorstore, k=5)
        raw_scores = [d["_raw_score"] for d in raw_check if d.get("_raw_score") is not None]
        if raw_scores:
            avg_raw = sum(raw_scores) / len(raw_scores)
            if avg_raw < config.CORE_CONCEPT_SIM_THRESHOLD:
                use_fallback = True
                print(f"[核心概念回退] 原始余弦相似度 {avg_raw:.3f} < "
                      f"阈值 {config.CORE_CONCEPT_SIM_THRESHOLD}，触发知识库回退", file=sys.stderr)
            else:
                use_core_boost = True
                print(f"[核心概念增强] 原始余弦相似度 {avg_raw:.3f}，注入强制回答指令", file=sys.stderr)
        else:
            use_fallback = True
            print("[核心概念回退] 无法获取向量相似度分数，默认启用回退保护", file=sys.stderr)

    # 构建上下文（mindmap 标记为「知识框架」，comprehensive 标记为「大题示例」）
    context_parts = []
    sources = []
    seen_sources = set()
    for i, doc in enumerate(docs):
        src = doc["metadata"].get("source", "未知来源")
        cat = doc["metadata"].get("category", "")
        dtype = doc["metadata"].get("type", "")
        # 根据元数据生成标签
        if cat == "mindmap":
            tag = f"知识框架（思维导图）来源: {src}"
        elif dtype == "comprehensive":
            tag = f"综合性大题示例 来源: {src}"
        else:
            tag = f"片段{i+1} 来源: {src}"
        context_parts.append(f"[{tag}]\n{doc['content']}")
        if src not in seen_sources:
            sources.append(src)
            seen_sources.add(src)

    context = "\n\n".join(context_parts)

    # ── 构建系统提示词（人设优先于资料约束）──
    system_content = SYSTEM_PROMPT
    if config.PERSONA_ENABLED:
        system_content = config.PERSONA_PROMPT + "\n" + SYSTEM_PROMPT

    # ── 专题深度总结触发检测 ──
    if hasattr(config, "SUMMARIZE_TRIGGERS") and hasattr(config, "DEEP_SUMMARY_TEMPLATE"):
        if any(trigger in question for trigger in config.SUMMARIZE_TRIGGERS):
            system_content += "\n" + config.DEEP_SUMMARY_TEMPLATE

    # ── 核心概念知识库回退 ──
    if use_fallback:
        system_content += (
            "\n\n【知识库回退模式】\n"
            "当前检索到的资料片段与问题相关度过低，但问题明确属于408计算机基础核心概念。\n"
            "请使用你内置的408计算机基础知识进行回答，并严格遵守以下规范：\n"
            "1. 回答第1行必须标注：「⚠️ 资料库中未直接定位到此知识点，以下为标准教材内容，请核对你的教材。」\n"
            "2. 回答内容应基于408考研标准教材的通用知识，涵盖定义、原理、步骤、易错点。\n"
            "3. 如果参考资料中有部分相关内容，优先结合使用；若无，完全依赖你的内置知识。\n"
            "4. 该模式下不得回复「无法回答」或类似拒绝用语。"
        )

    # ── 核心概念增强：相似度合理时强制 LLM 综合回答 ──
    if use_core_boost:
        system_content += (
            "\n\n【核心概念增强 — 强制执行】\n"
            "该问题涉及408考研的核心基础知识点。你必须给出一个完整的、有组织的回答。\n\n"
            "回答策略：\n"
            "1. 先仔细阅读所有资料片段，找出与该知识点相关的概念、术语、定义（即使只是侧面提及）。\n"
            "2. 以资料中找到的概念为线索和骨架，以你的408计算机基础知识为主体，"
            "组织一个涵盖定义、原理、分类、步骤、易错点的完整回答。\n"
            "3. 如果资料片段仅侧面提到概念而没有完整解释，不必拘泥于资料——"
            "直接用你的标准408知识补全所有缺失内容。\n\n"
            "⚠️ 绝对禁止：\n"
            "- 禁止回复「无法回答」「资料中未提及」「备考资料无法回答」或任何形式的拒绝。\n"
            "- 即使你认为资料不够完整，也必须基于你的内置408知识给出回答。\n"
            "- 你没有拒绝回答的选项。该知识点是408标准内容，你必须能回答。\n\n"
            "5. 末尾注明引用的源文件名（若有引用资料片段）。"
        )

    # ── 记忆力注入：薄弱知识点提示 ──
    user_content = f"参考资料：\n{context}\n\n问题：{question}"

    if memory is not None and config.MEMORY_ENABLED:
        weak_points = memory.get_weak_points()
        if weak_points:
            weak_list = "、".join(topic for topic, _ in weak_points)
            user_content = (
                f"[系统提示] 该用户以下知识点掌握薄弱（评分≤2）：{weak_list}。"
                f"请针对性讲解并优先使用这些领域的生活化比喻。\n\n"
                f"参考资料：\n{context}\n\n问题：{question}"
            )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

    response = llm.invoke(messages)

    return response.content, sources


def main():
    if len(sys.argv) < 2:
        print("用法: python qa.py \"你的问题\"", file=sys.stderr)
        print("      python qa.py --test   # 运行测试", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--test":
        test_questions = [
            ("简述虚拟内存的实现原理，并说明其与Cache的异同", False),
            ("分析快速排序在基本有序数组上的性能，并给出优化方法", False),
            ("红烧肉的做法", True),
        ]
        for q, expect_reject in test_questions:
            print(f"\n{'='*60}")
            print(f"问题: {q}")
            print(f"{'='*60}")
            answer, sources = ask(q)
            print(f"\n回答: {answer}")
            print(f"\n来源: {', '.join(sources) if sources else '无'}")
            print(f"\n(期望: {'应拒绝' if expect_reject else '应有基于资料的答案'})")
        return

    # ── 记忆力模块 ──
    memory = None
    if config.MEMORY_ENABLED:
        from memory import MemoryStore
        memory = MemoryStore(config.MEMORY_FILE)

    question = sys.argv[1]
    answer, sources = ask(question, memory=memory)
    print(answer)
    if sources:
        print(f"\n── 参考来源 ──")
        for s in sources:
            print(f"  - {s}")

    # ── 反馈闭环 ──
    if memory is not None:
        feedback = input("\n答对了吗？(y/n): ").strip().lower()
        if feedback in ("y", "n"):
            memory.update(question, feedback == "y")
        else:
            print("未识别反馈，已跳过记录。")


if __name__ == "__main__":
    main()
