import os
import re
import json
import uuid
from datetime import datetime
import streamlit as st

import config
from qa import ask as qa_ask
from memory import MemoryStore
from ingest import (
    compute_sha256, load_cache, save_cache, collect_files,
    load_documents, build_chunks, write_chunks_to_vectorstore,
)
from analysis import (
    load_from_chroma, load_from_files, build_subject_corpora,
    aggregate_stats, generate_report,
)
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from calculation_practice import get_topic_list, generate_problem
from comprehensive_practice import get_topic_list as get_comp_topic_list, generate_problem as generate_comp_problem

# ── Constants ──
CHAT_HISTORY_FILE = os.path.join(config.OUTPUT_DIR, "chat_history.json")
REPORT_PATH = os.path.join(config.OUTPUT_DIR, "report_2026.md")

CATEGORY_MAP = {
    "考纲": "outline",
    "教材": "textbooks",
    "真题": "exams",
    "笔记": "notes",
}

# ── Page config ──
st.set_page_config(
    page_title="408考研专属知识库",
    page_icon="📚",
    layout="wide",
)

# ── Session State ──
defaults = {
    "current_session_id": None,
    "messages": [],
    "report_content": None,
    "show_report": False,
    "last_image_description": None,
    "last_image_msg_index": -1,
    "saved_image_data": [],
    "last_image_multi": False,
    "calc_problem": None,
    "calc_show_answer": False,
    "comp_problem": None,
    "comp_show_answer": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


@st.cache_resource
def _get_memory():
    """跨 rerun 持久的 MemoryStore 单例。"""
    return MemoryStore(config.MEMORY_FILE)


# ══════════════════════════════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════════════════════════════

def _load_sessions():
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def _save_sessions(sessions):
    os.makedirs(os.path.dirname(CHAT_HISTORY_FILE), exist_ok=True)
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


def _persist_current_session():
    """Save current session messages to chat_history.json."""
    if not st.session_state.messages:
        return
    sessions = _load_sessions()
    sid = st.session_state.current_session_id
    entry = {
        "session_id": sid,
        "timestamp": datetime.now().isoformat(),
        "messages": st.session_state.messages,
    }
    for s in sessions:
        if s.get("session_id") == sid:
            s["messages"] = entry["messages"]
            s["timestamp"] = entry["timestamp"]
            break
    else:
        sessions.append(entry)
    _save_sessions(sessions)


def _new_session():
    sid = uuid.uuid4().hex[:8]
    st.session_state.current_session_id = sid
    st.session_state.messages = []


def _vectorstore_exists():
    return (
        os.path.isdir(config.PERSIST_DIR)
        and os.path.exists(os.path.join(config.PERSIST_DIR, "chroma.sqlite3"))
    )


def _do_ingest():
    """Incremental ingest using shared chunking logic from ingest.py.
    Returns (file_count, chunk_count, failed_count).
    """
    cache = load_cache()
    files_to_process = collect_files(config.DATA_DIR, cache)

    if not files_to_process:
        return 0, 0, 0

    embeddings = HuggingFaceEmbeddings(
        model_name=config.EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    raw_docs, failed = load_documents(files_to_process)

    # 使用共享的分类分块逻辑（与 CLI ingest 完全一致）
    all_chunks, _zero_block_files = build_chunks(raw_docs)

    vectorstore = Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=config.PERSIST_DIR,
    )

    # 使用共享的写入逻辑（自动添加 doc_id / chunk_index 元数据）
    write_chunks_to_vectorstore(all_chunks, vectorstore)

    for fp in files_to_process:
        cache[fp] = compute_sha256(fp)
    save_cache(cache)

    return len(files_to_process), len(all_chunks), failed


# ══════════════════════════════════════════════════════════════════════
# Sidebar
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://img.icons8.com/color/96/books.png", width=48)
    st.markdown("## 408考研知识库")

    # ── 资料导入 ──
    st.subheader("📂 资料导入")

    category_label = st.selectbox(
        "资料分类",
        list(CATEGORY_MAP.keys()),
        key="upload_category",
    )
    category_dir = CATEGORY_MAP[category_label]

    uploaded_files = st.file_uploader(
        "选择文件（pdf / md / txt）",
        type=["pdf", "md", "txt"],
        accept_multiple_files=True,
        key="file_uploader",
    )

    if uploaded_files:
        saved_count = 0
        for uf in uploaded_files:
            dest_dir = os.path.join(config.DATA_DIR, category_dir)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, uf.name)
            with open(dest_path, "wb") as f:
                f.write(uf.getbuffer())
            saved_count += 1

        st.success(f"已保存 {saved_count} 个文件到 data/{category_dir}/")

        with st.spinner("正在增量更新知识库..."):
            fc, cc, failed = _do_ingest()
        if fc > 0:
            st.success(f"知识库已更新：{fc} 个文件 → {cc} 个块" + (f"，{failed} 个失败" if failed else ""))
        else:
            st.info("文件已存在且内容未变化，跳过导入")
        st.rerun()

    st.divider()

    # ── 考情分析 ──
    st.subheader("📊 考情分析")

    col_a, col_b = st.columns([3, 2])
    with col_a:
        if st.button("🔍 生成报告", use_container_width=True):
            if not config.API_KEY:
                st.error("请设置 DEEPSEEK_API_KEY 环境变量")
            elif not _vectorstore_exists():
                st.error("向量库为空，请先导入资料")
            else:
                with st.spinner("正在分析历年真题，约需 1-3 分钟..."):
                    try:
                        docs, errors = load_from_chroma()
                        if not docs:
                            exams_dir = os.path.join(config.DATA_DIR, "exams")
                            docs, errors = load_from_files(exams_dir)

                        if not docs:
                            st.error("未找到任何真题文档")
                        else:
                            corpora = build_subject_corpora(docs)
                            stats = aggregate_stats(docs)
                            report = generate_report(docs, corpora, stats)

                            clean = report.strip()
                            if clean.startswith("```"):
                                clean = re.sub(r"^```\w*\n?", "", clean)
                                clean = re.sub(r"\n```$", "", clean)

                            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
                            with open(REPORT_PATH, "w", encoding="utf-8") as f:
                                f.write(clean)

                            st.session_state.report_content = clean
                            st.session_state.show_report = True
                            st.success(f"报告已保存至 data_output/report_2026.md")
                            st.rerun()
                    except Exception as e:
                        st.error(f"生成失败: {e}")

    # Download button always visible if report file exists
    if os.path.exists(REPORT_PATH):
        with col_b:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                existing_report = f.read()
            st.download_button(
                label="📥 下载",
                data=existing_report,
                file_name="report_2026.md",
                mime="text/markdown",
                use_container_width=True,
            )
    elif st.session_state.report_content:
        with col_b:
            st.download_button(
                label="📥 下载",
                data=st.session_state.report_content,
                file_name="report_2026.md",
                mime="text/markdown",
                use_container_width=True,
            )

    st.divider()

    # ── 计算专练 ──
    st.subheader("🧮 计算专练")

    topics = get_topic_list()
    topic_options = {t["name"]: t["id"] for t in topics}
    selected_name = st.selectbox(
        "选择题型",
        list(topic_options.keys()),
        key="calc_topic_select",
    )
    selected_tid = topic_options[selected_name]

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("🎲 生成新题", use_container_width=True):
            st.session_state.calc_problem = generate_problem(selected_tid)
            st.session_state.calc_show_answer = False
            st.rerun()

    with col_c2:
        if st.button("🔄 换一题", key="calc_new_question", use_container_width=True):
            st.session_state.calc_problem = generate_problem(selected_tid)
            st.session_state.calc_show_answer = False
            st.rerun()

    if st.session_state.calc_problem is not None:
        prob = st.session_state.calc_problem
        if st.button("📝 查看答案与步骤", use_container_width=True):
            st.session_state.calc_show_answer = True
            st.rerun()

    st.divider()

    # ── 大题专练 ──
    st.subheader("📝 大题专练")

    comp_topics = get_comp_topic_list()
    # 按科目分组显示
    comp_subjects = sorted(set(t["subject"] for t in comp_topics))
    comp_subject = st.selectbox(
        "选择科目",
        comp_subjects,
        key="comp_subject_select",
    )
    comp_filtered = [t for t in comp_topics if t["subject"] == comp_subject]
    comp_topic_names = {t["name"]: t["id"] for t in comp_filtered}
    comp_selected_name = st.selectbox(
        "选择题型",
        list(comp_topic_names.keys()),
        key="comp_topic_select",
    )
    comp_selected_tid = comp_topic_names[comp_selected_name]

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        if st.button("🎲 生成题目", use_container_width=True):
            st.session_state.comp_problem = generate_comp_problem(comp_selected_tid)
            st.session_state.comp_show_answer = False
            st.rerun()

    with col_d2:
        if st.button("🔄 换一题", key="comp_new_question", use_container_width=True):
            st.session_state.comp_problem = generate_comp_problem(comp_selected_tid)
            st.session_state.comp_show_answer = False
            st.rerun()

    if st.session_state.comp_problem is not None:
        if st.button("📖 查看解答", use_container_width=True):
            st.session_state.comp_show_answer = True
            st.rerun()

    st.divider()

    # ── 历史对话 ──
    st.subheader("💬 历史对话")

    all_sessions = _load_sessions()
    if all_sessions:
        # Show most recent 20 sessions, newest first
        for session in reversed(all_sessions[-20:]):
            sid = session.get("session_id", "")
            messages = session.get("messages", [])
            # First user message as title
            title = "新对话"
            for m in messages:
                if m.get("role") == "user":
                    title = m["content"][:28] + ("..." if len(m["content"]) > 28 else "")
                    break

            ts = session.get("timestamp", "")[:16]
            btn_label = f"📝 {title}"
            if st.button(btn_label, key=f"hist_{sid}", help=f"{ts}", use_container_width=True):
                st.session_state.current_session_id = sid
                st.session_state.messages = messages
                st.rerun()
    else:
        st.caption("暂无历史对话")

    st.divider()

    # ── 导出 ──
    st.subheader("📤 导出")

    if st.button("导出当前对话为 Markdown", use_container_width=True):
        if not st.session_state.messages:
            st.warning("当前对话为空")
        else:
            sid = st.session_state.current_session_id
            lines = [f"# 408考研知识库 · 对话记录\n\n> 会话ID: `{sid}`\n"]
            for m in st.session_state.messages:
                role = "**🧑 你**" if m["role"] == "user" else "**🤖 助手**"
                lines.append(f"\n### {role}\n\n{m['content']}\n")
                if m.get("sources"):
                    lines.append("\n📖 **参考来源：**\n")
                    for s in m["sources"]:
                        lines.append(f"- `{s}`\n")
            export_data = "\n".join(lines)
            st.download_button(
                label="📥 下载 Markdown",
                data=export_data,
                file_name=f"chat_{sid}.md",
                mime="text/markdown",
                use_container_width=True,
            )


# ══════════════════════════════════════════════════════════════════════
# Main area
# ══════════════════════════════════════════════════════════════════════

st.title("📚 408考研专属知识库")

# Top bar: session info + new chat button
top_left, top_right = st.columns([6, 1])
with top_left:
    st.caption(f"当前会话 · `{st.session_state.current_session_id or '未开始'}`")
with top_right:
    if st.button("🆕 新对话", use_container_width=True):
        _persist_current_session()
        _new_session()
        st.rerun()

if st.session_state.current_session_id is None:
    _new_session()

# ── Report display (collapsible, above chat) ──
if st.session_state.show_report and st.session_state.report_content:
    with st.expander("📊 考情分析报告 — report_2026.md", expanded=False):
        st.markdown(st.session_state.report_content)
        if st.button("收起报告", key="dismiss_report"):
            st.session_state.show_report = False
            st.rerun()

# ── Calculation practice display ──
if st.session_state.calc_problem is not None:
    prob = st.session_state.calc_problem
    st.divider()
    st.markdown(f"### 🧮 {prob.topic_name}")
    st.caption(f"科目：{prob.subject}　|　知识点：{'、'.join(prob.knowledge_tags)}")
    st.markdown(prob.question)

    if st.session_state.calc_show_answer:
        st.success(f"**答案：{prob.answer}**")
        with st.expander("📐 解题步骤", expanded=True):
            for step in prob.solution_steps:
                st.markdown(step)
        st.caption("💡 提示：可点击侧边栏「换一题」生成同类型新题，或切换题型后点击「生成新题」。")

# ── Comprehensive practice display ──
if st.session_state.comp_problem is not None:
    prob = st.session_state.comp_problem
    st.divider()
    st.markdown(f"### 📝 {prob.topic_name}")
    st.caption(f"科目：{prob.subject}")
    st.markdown(prob.question)

    if st.session_state.comp_show_answer:
        st.success(f"**答案：{prob.answer}**")
        with st.expander("📐 解题步骤与伪代码", expanded=True):
            for i, step in enumerate(prob.solution_steps, 1):
                st.markdown(step)
                if i < len(prob.solution_steps):
                    st.divider()
        st.caption("💡 提示：可点击侧边栏「换一题」生成同类型变式，或切换科目/题型。")

# ── Chat messages ──
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📖 参考来源"):
                for s in msg["sources"]:
                    st.caption(f"- `{s}`")

        # ── 反馈按钮（仅未评分的助手消息）──
        if (
            config.MEMORY_ENABLED
            and msg["role"] == "assistant"
            and not msg.get("rated", True)  # 旧消息无 rated 字段默认视为已评分
        ):
            topic = msg.get("topic", "")
            col_a, col_b, _spacer = st.columns([1, 1, 6])
            with col_a:
                if st.button("✅ 答对了", key=f"correct_{i}"):
                    _get_memory().update(topic, True)
                    st.session_state.messages[i]["rated"] = True
                    st.rerun()
            with col_b:
                if st.button("❌ 还需加强", key=f"wrong_{i}"):
                    _get_memory().update(topic, False)
                    st.session_state.messages[i]["rated"] = True
                    st.rerun()

        # ── 错题一键入库（仅图片回答 + 未保存）──
        if (
            msg["role"] == "assistant"
            and msg.get("from_image")
            and not msg.get("saved_to_book", False)
            and st.session_state.get("saved_image_data")
        ):
            if st.button("📥 保存到错题本", key=f"save_book_{i}"):
                os.makedirs(config.MISTAKE_BOOK_DIR, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                saved_count = 0
                for img_data in st.session_state.saved_image_data:
                    img_bytes = img_data["bytes"]
                    img_name = img_data["name"]
                    # 保存原始图片
                    img_dest = os.path.join(config.MISTAKE_BOOK_DIR, f"{ts}_{img_name}")
                    with open(img_dest, "wb") as f:
                        f.write(img_bytes)
                    saved_count += 1
                # 保存识别文字为 .md（供 RAG 检索）
                desc = msg.get("image_description", "")
                if desc:
                    md_dest = os.path.join(config.MISTAKE_BOOK_DIR, f"{ts}_题目描述.md")
                    with open(md_dest, "w", encoding="utf-8") as f:
                        f.write(f"# 错题记录\n\n> 保存时间: {ts}\n\n{desc}")
                # 增量导入
                fc, cc, failed = _do_ingest()
                st.session_state.messages[i]["saved_to_book"] = True
                st.success(f"✅ 已保存 {saved_count} 张图片并加入知识库"
                           f"（{cc} 个新块）" if cc else "✅ 已保存（内容未变化）")
                st.rerun()

# ── Image upload (多图联合分析 + 追问上下文) ──
uploaded_images = st.file_uploader(
    "📷 上传408题目图片（可选，最多3张）",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key="image_uploader",
    label_visibility="collapsed",
)

# 限制最多 VISION_MAX_IMAGES 张
if uploaded_images and len(uploaded_images) > config.VISION_MAX_IMAGES:
    st.warning(f"最多只能上传 {config.VISION_MAX_IMAGES} 张图片，仅前 {config.VISION_MAX_IMAGES} 张生效")
    uploaded_images = uploaded_images[:config.VISION_MAX_IMAGES]

if uploaded_images:
    # 多图缩略图展示
    n = len(uploaded_images)
    cols = st.columns(n)
    for i, img in enumerate(uploaded_images):
        with cols[i]:
            st.image(img, width=200 if n == 1 else 140)
            st.caption(img.name)

    col_clear, col_ctx = st.columns([1, 2])
    with col_clear:
        if st.button("❌ 清除图片", key="clear_images"):
            st.session_state.image_uploader = None
            st.rerun()

# 追问上下文状态 + 清除按钮
if st.session_state.last_image_description is not None:
    remaining = config.VISION_FOLLOWUP_WINDOW - (
        len(st.session_state.messages) - st.session_state.last_image_msg_index
    )
    remaining = max(0, remaining)
    col_ctx_status, col_ctx_btn = st.columns([3, 1])
    with col_ctx_status:
        st.caption(f"📷 图片上下文已缓存 · 剩余 {remaining} 轮追问")
    with col_ctx_btn:
        if st.button("🗑 清除上下文", key="clear_context"):
            st.session_state.last_image_description = None
            st.session_state.last_image_msg_index = -1
            st.session_state.saved_image_data = []
            st.session_state.last_image_multi = False
            st.rerun()

# ── Chat input ──
if prompt := st.chat_input("输入你的408考研问题…"):
    if not config.API_KEY:
        st.error("请先设置 DEEPSEEK_API_KEY 环境变量")
        st.stop()

    if not _vectorstore_exists():
        st.error("向量库为空，请先在侧边栏导入备考资料")
        st.stop()

    # ── 视觉理解预处理（优化1/2/5）──
    image_description = None
    from_image = False
    is_multi = False
    saved_image_data = []

    if uploaded_images:
        # ── 新上传图片：调用视觉模型 ──
        from_image = True
        is_multi = len(uploaded_images) > 1

        if not config.VISION_API_KEY:
            st.error("请先设置 DASHSCOPE_API_KEY 环境变量以使用图片问答功能")
            st.stop()

        spinner_text = "正在联合分析多张图片..." if is_multi else "正在理解图片内容…"
        with st.spinner(spinner_text):
            import tempfile
            from vision import understand_image, polish_text

            tmp_paths = []
            try:
                for img in uploaded_images:
                    suffix = "." + img.name.rsplit(".", 1)[-1] if "." in img.name else ".jpg"
                    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
                    tmp.write(img.getbuffer())
                    tmp.flush()
                    tmp.close()  # Windows 上必须关闭句柄，否则后续读取会报 PermissionError
                    tmp_paths.append(tmp.name)
                # 优化5: 多图联合分析
                raw_desc = understand_image(tmp_paths[0] if len(tmp_paths) == 1 else tmp_paths)
                # 优化2: 公式修复
                image_description = polish_text(raw_desc)
            finally:
                for p in tmp_paths:
                    os.unlink(p)

        # 保存图片字节供错题本使用
        saved_image_data = [{"bytes": img.getvalue(), "name": img.name} for img in uploaded_images]
        st.session_state.saved_image_data = saved_image_data
        st.session_state.last_image_multi = is_multi

        # 优化3: 存储描述供追问模式
        st.session_state.last_image_description = image_description
        st.session_state.last_image_msg_index = len(st.session_state.messages) + 2

    elif (
        st.session_state.last_image_description is not None
        and len(st.session_state.messages) - st.session_state.last_image_msg_index
        <= config.VISION_FOLLOWUP_WINDOW
    ):
        # ── 优化3: 追问模式 ──
        image_description = st.session_state.last_image_description
        from_image = True
        is_multi = st.session_state.last_image_multi
        saved_image_data = st.session_state.get("saved_image_data", [])

    # ── 构建最终问题 ──
    if image_description and uploaded_images:
        # 首次图片问答：显示标注
        full_prompt = f"[上传图片描述]\n{image_description}\n\n[用户问题]\n{prompt}"
        if is_multi:
            display_prompt = f"📷 *（根据{len(uploaded_images)}张上传图片联合分析）*\n\n{prompt}"
        else:
            display_prompt = f"📷 *（根据上传图片理解）*\n\n{prompt}"
    elif image_description:
        # 追问模式：隐藏上下文前缀，仅将描述注入检索
        full_prompt = f"[当前讨论的图片内容]\n{image_description}\n\n[用户问题]\n{prompt}"
        display_prompt = prompt
    else:
        # 纯文字问答
        full_prompt = prompt
        display_prompt = prompt

    # Show user message
    st.session_state.messages.append({"role": "user", "content": display_prompt})
    with st.chat_message("user"):
        st.markdown(display_prompt)

    # Generate answer
    with st.chat_message("assistant"):
        memory_obj = _get_memory() if config.MEMORY_ENABLED else None
        with st.spinner("正在检索资料…"):
            try:
                answer, sources = qa_ask(full_prompt, memory=memory_obj)
            except SystemExit:
                answer = "向量库加载失败，请先导入资料。"
                sources = []

        if image_description and uploaded_images:
            prefix = (
                f"（根据{len(uploaded_images)}张上传图片联合分析）\n\n"
                if is_multi
                else "（根据上传图片理解）\n\n"
            )
            answer = prefix + answer

        st.markdown(answer)
        if sources:
            with st.expander("📖 参考来源"):
                for s in sources:
                    st.caption(f"- `{s}`")

    # 优化4: 标记图片消息，错题本按钮在消息循环中渲染
    msg_entry = {
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "topic": prompt,
        "rated": False,
    }
    if from_image:
        msg_entry["from_image"] = True
        msg_entry["image_description"] = image_description
        msg_entry["saved_to_book"] = False
    st.session_state.messages.append(msg_entry)

    _persist_current_session()
    st.rerun()
