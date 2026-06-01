"""
408 考研知识库 — FastAPI 后端服务

将现有 Python 业务逻辑（qa / ingest / analysis / vision / calculation_practice /
comprehensive_practice / memory）统一包装成 RESTful API，供 React 前端调用。

启动方式:
    uvicorn server:app --reload --port 8000
"""

import asyncio
import base64
import concurrent.futures
from concurrent.futures import TimeoutError as _ThreadTimeout
import io
import json
import logging
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config

# ── 日志配置 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("server")

# ── FastAPI 应用 ──
app = FastAPI(
    title="408 考研知识库 API",
    version="1.0.0",
    description="为 408 计算机考研知识库提供 RESTful 接口，支持问答、练习、资料导入、考情分析等功能。",
)

# ── CORS 中间件（允许 React 开发服务器跨域访问） ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API 路由前缀 ──
api_router = APIRouter(prefix="/api")


# ═══════════════════════════════════════════════════════════════════════════
# 启动校验
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
def startup_validation():
    """启动时校验必需配置，避免运行时崩溃。"""
    missing = []
    if not config.API_KEY:
        missing.append("DEEPSEEK_API_KEY")
    if not config.VISION_API_KEY:
        logger.warning("DASHSCOPE_API_KEY 未设置，图片问答功能不可用。")

    vectorstore_exists = (
        os.path.exists(config.PERSIST_DIR)
        and os.path.isdir(config.PERSIST_DIR)
        and any(f.startswith("chroma") for f in os.listdir(config.PERSIST_DIR))
    )
    if not vectorstore_exists:
        logger.warning(
            "向量库目录 (%s) 为空或不存在。请先通过 /ingest 接口导入资料。",
            config.PERSIST_DIR,
        )

    if missing:
        logger.warning("缺少以下环境变量: %s", ", ".join(missing))

    logger.info("✅ 服务启动完成，已加载配置: EMBED_MODEL=%s", config.EMBED_MODEL)
    logger.info("   向量库目录: %s", config.PERSIST_DIR)
    logger.info("   资料目录:   %s", config.DATA_DIR)


# ═══════════════════════════════════════════════════════════════════════════
# Pydantic 请求/响应模型
# ═══════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    retry_count: int = 0


class ChatImageRequest(BaseModel):
    question: Optional[str] = ""
    image_base64: str           # 单张图片 base64（含 data URI 前缀或裸 base64）
    session_id: Optional[str] = None


class MistakeEntry(BaseModel):
    question: str
    answer: str
    topic: Optional[str] = None
    source: Optional[str] = None
    knowledge_point: Optional[str] = None


class MistakeAddRequest(BaseModel):
    question: str
    answer: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    type: str = "错题"           # "错题" 或 "薄弱点"
    source: Optional[str] = None
    user_answer: Optional[str] = None
    image_base64: Optional[str] = None


class MistakeExportRequest(BaseModel):
    format: str = "markdown"     # "markdown" 或 "pdf"
    item_ids: Optional[list[str]] = None  # None = 全部


class SimilarQuestionRequest(BaseModel):
    topic: str


class FollowUpRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    previous_question: str = ""
    previous_answer: str = ""


class SimilarQuestionExportRequest(BaseModel):
    topic: str
    format: str = "markdown"


class ChatSessionInfo(BaseModel):
    session_id: str
    timestamp: str
    message_count: int = 0
    preview: str = ""


class ChatHistoryDeleteRequest(BaseModel):
    session_ids: list[str]


class CardsRequest(BaseModel):
    concepts: list[str]


class CardExportRequest(BaseModel):
    format: str = "markdown"     # "markdown" 或 "anki"


class AnalysisResponse(BaseModel):
    report: str
    stats: dict = {}


class IngestResponse(BaseModel):
    files_processed: int = 0
    chunks_added: int = 0
    errors: list[str] = []


class PracticeRequest(BaseModel):
    type: str          # 题型 id
    subject: Optional[str] = None
    topic: Optional[str] = None


class PracticeResponse(BaseModel):
    question: str
    solution_steps: list[str] = []
    answer: str
    type_name: str = ""
    subject: str = ""


class HealthResponse(BaseModel):
    status: str = "ok"
    api_key_configured: bool = False
    vision_key_configured: bool = False
    vectorstore_ready: bool = False
    data_dir_ready: bool = False
    total_exams: int = 0


# ═══════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════

def _save_uploaded_file(upload: UploadFile, target_dir: str) -> str:
    """保存上传文件到目标目录，返回保存路径。"""
    os.makedirs(target_dir, exist_ok=True)
    # 防止路径穿越
    safe_name = os.path.basename(upload.filename or "upload")
    dest = os.path.join(target_dir, safe_name)
    content = upload.file.read()
    with open(dest, "wb") as f:
        f.write(content)
    logger.info("已保存上传文件: %s (%d 字节)", dest, len(content))
    return dest


def timeout_exec(func, timeout_sec: int = 120, *args, **kwargs):
    """
    在独立线程中执行函数，设置超时保护。
    如果超时未返回，抛出 _ThreadTimeout。
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_sec)
        except _ThreadTimeout:
            raise _ThreadTimeout(f"操作超时（{timeout_sec}s），请检查网络或 LLM 服务状态")


def _save_base64_image(b64_data: str, filename: str = "upload.png") -> str:
    """将 base64 图片数据保存为临时文件，返回文件路径。"""
    # 去掉可能的 data URI 前缀
    if "," in b64_data:
        b64_data = b64_data.split(",", 1)[1]
    image_bytes = base64.b64decode(b64_data)
    tmp_dir = tempfile.mkdtemp(prefix="vision_")
    tmp_path = os.path.join(tmp_dir, filename)
    with open(tmp_path, "wb") as f:
        f.write(image_bytes)
    return tmp_path


# ═══════════════════════════════════════════════════════════════════════════
#  问答接口
# ═══════════════════════════════════════════════════════════════════════════

@api_router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    问答接口：接收问题，检索知识库，调用 LLM 回答。

    请求体:
        {"question": "...", "session_id": "..."}
    返回:
        {"answer": "...", "sources": [...], "retry_count": 0}
    """
    start = time.time()
    logger.info("[chat] 收到问题: %s (session=%s)", req.question[:80], req.session_id)

    try:
        from qa import ask
        from memory import MemoryStore

        # 加载记忆力模块（用于注入薄弱知识点提示）
        memory = None
        if config.MEMORY_ENABLED:
            memory = MemoryStore(config.MEMORY_FILE)

        # 使用超时保护（问答最长等待 180 秒）
        result = timeout_exec(
            lambda: ask(req.question, memory=memory),
            timeout_sec=180,
        )
        answer, sources = result

        elapsed = time.time() - start
        logger.info("[chat] 回答完成, 耗时 %.2fs, 来源: %s", elapsed, sources)

        return ChatResponse(
            answer=answer,
            sources=sources,
            retry_count=0,
        )

    except _ThreadTimeout as e:
        logger.error("[chat] 超时: %s", e)
        raise HTTPException(status_code=504, detail="问答处理超时，请检查网络或 LLM 服务状态")
    except Exception as e:
        logger.error("[chat] 请求失败: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")


@api_router.post("/chat/image", response_model=ChatResponse)
def chat_image_endpoint(
    file: UploadFile = File(None),
    question: str = Form(""),
    image_base64: str = Form(""),
):
    """
    图片问答接口：上传图片或提供 base64 → 视觉模型提取文字 → 调用 qa.ask()。

    支持两种方式:
    1. multipart/form-data: file=图片文件 + question=可选问题
    2. JSON: {"image_base64": "...", "question": "..."}

    返回: {"answer": "...", "sources": [...], "retry_count": 0}
    """
    import vision

    start = time.time()
    logger.info("[chat/image] 收到图片问答请求")

    try:
        # 保存图片
        image_path = None
        if file:
            # 文件上传方式
            tmp_dir = tempfile.mkdtemp(prefix="vision_")
            image_path = os.path.join(tmp_dir, file.filename or "image.png")
            content = file.file.read()
            with open(image_path, "wb") as f:
                f.write(content)
            logger.info("[chat/image] 保存上传文件: %s (%d bytes)", image_path, len(content))
        else:
            raise HTTPException(status_code=400, detail="请通过 file 字段上传图片")

        # 调用视觉模型提取文字
        vision_text = vision.understand_image(image_path)
        polished = vision.polish_text(vision_text)

        logger.info("[chat/image] 视觉模型识别完成")

        # 将提取的文字作为问题补充
        enhanced_question = question.strip() if question.strip() else f"请分析以下图片内容：\n\n{polished}"

        # 调用 qa.ask()
        from qa import ask
        from memory import MemoryStore

        memory = None
        if config.MEMORY_ENABLED:
            memory = MemoryStore(config.MEMORY_FILE)

        answer, sources = ask(enhanced_question, memory=memory)

        elapsed = time.time() - start
        logger.info("[chat/image] 图片问答完成, 耗时 %.2fs", elapsed)

        return ChatResponse(
            answer=answer,
            sources=sources,
            retry_count=0,
        )

    except Exception as e:
        logger.error("[chat/image] 处理失败: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"图片问答失败: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
#  聊天历史 & 追问接口
# ═══════════════════════════════════════════════════════════════════════════

CHAT_HISTORY_FILE = os.path.join(config.OUTPUT_DIR, "chat_history.json")


def _load_chat_history() -> list[dict]:
    """从 JSON 文件加载聊天历史。"""
    if not os.path.exists(CHAT_HISTORY_FILE):
        return []
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("读取聊天历史失败: %s", e)
        return []


def _save_chat_history(sessions: list[dict]):
    """保存聊天历史到 JSON 文件。"""
    os.makedirs(os.path.dirname(CHAT_HISTORY_FILE), exist_ok=True)
    sessions = sessions[-50:]
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


@api_router.post("/chat/save")
def chat_save(req: ChatRequest):
    """保存一条问答对到聊天历史。"""
    sessions = _load_chat_history()
    session = None
    for s in sessions:
        if s.get("session_id") == req.session_id:
            session = s
            break
    if not session:
        session = {
            "session_id": req.session_id or "",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "messages": [],
        }
        sessions.append(session)
    from qa import ask
    from memory import MemoryStore
    memory = None
    if config.MEMORY_ENABLED:
        memory = MemoryStore(config.MEMORY_FILE)
    answer, sources = ask(req.question, memory=memory)
    session["messages"].append({"role": "user", "content": req.question})
    session["messages"].append({"role": "assistant", "content": answer, "sources": sources})
    session["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save_chat_history(sessions)
    return {"session_id": req.session_id, "answer": answer, "sources": sources}


@api_router.get("/chat/history")
def chat_history_list():
    """获取所有聊天会话列表。"""
    sessions = _load_chat_history()
    result = []
    for s in sessions:
        msgs = s.get("messages", [])
        preview = ""
        for m in reversed(msgs):
            if m.get("role") == "user":
                preview = m.get("content", "")[:60]
                break
        result.append({
            "session_id": s.get("session_id", ""),
            "timestamp": s.get("timestamp", ""),
            "message_count": len(msgs),
            "preview": preview,
        })
    result.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"sessions": result, "count": len(result)}


@api_router.get("/chat/history/{session_id}")
def chat_history_detail(session_id: str):
    """获取指定会话的详细消息。"""
    sessions = _load_chat_history()
    for s in sessions:
        if s.get("session_id") == session_id:
            return {"session": s}
    raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")


@api_router.delete("/chat/history/{session_id}")
def chat_history_delete(session_id: str):
    """删除指定聊天会话。"""
    sessions = _load_chat_history()
    new_sessions = [s for s in sessions if s.get("session_id") != session_id]
    if len(new_sessions) == len(sessions):
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
    _save_chat_history(new_sessions)
    return {"status": "deleted", "session_id": session_id}


@api_router.post("/chat/export")
def chat_export(req: ChatSessionInfo):
    """导出指定会话为 Markdown。"""
    sessions = _load_chat_history()
    session = None
    for s in sessions:
        if s.get("session_id") == req.session_id:
            session = s
            break
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 {req.session_id} 不存在")
    lines = ["# 💬 408 考研知识库 - 对话记录\n"]
    lines.append(f"> 会话 ID：{session.get('session_id', '')}\n")
    lines.append(f"> 导出时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"> 消息数：{len(session.get('messages', []))}\n")
    lines.append("---\n")
    for msg in session.get("messages", []):
        role = msg.get("role", "")
        content = msg.get("content", "")
        sources = msg.get("sources", [])
        if role == "user":
            lines.append(f"### 🧑‍🎓 提问\n\n{content}\n")
        else:
            lines.append(f"### 🤖 回答\n\n{content}\n")
            if sources:
                lines.append(f"**参考来源**：{', '.join(sources)}\n")
        lines.append("---\n")
    return Response(
        content="\n".join(lines).encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=chat_{session.get('session_id', 'export')}.md"},
    )


@api_router.post("/chat/follow-up", response_model=ChatResponse)
def chat_follow_up(req: FollowUpRequest):
    """
    追问接口：基于之前的上下文继续对话或生成同类题。
    请求体含 question, session_id, previous_question, previous_answer。
    """
    start = time.time()
    # 用户要求出同类题
    if "同类题" in req.question or req.question.strip() == "":
        logger.info("[follow-up] 用户请求生成同类题")
        try:
            import mistake_book as mb
            topic = req.previous_question[:30]
            if req.previous_question:
                for key in config.CORE_CONCEPTS:
                    if key in req.previous_question:
                        topic = key
                        break
            result = timeout_exec(
                lambda: mb.generate_similar_question(topic),
                timeout_sec=120,
            )
            answer = (
                f"### 🎯 同类题\n\n**知识点**：{topic}\n\n"
                f"{result['question']}\n\n---\n"
                f"**答案**：\n{result['answer']}\n\n"
                f"*来源：{result.get('source', 'AI生成')}*"
            )
            return ChatResponse(answer=answer, sources=[result.get("source", "同类题生成")])
        except _ThreadTimeout:
            answer = f"### 🎯 同类题\n\n⏳ 生成超时，请稍后重试。"
            return ChatResponse(answer=answer, sources=["超时"])
        except Exception as e:
            logger.error("[follow-up] 同类题生成失败: %s", e)
    # 普通追问
        logger.info("[follow-up] 用户请求生成同类题")
        try:
            import mistake_book as mb
            topic = req.previous_question[:30]
            if req.previous_question:
                for key in config.CORE_CONCEPTS:
                    if key in req.previous_question:
                        topic = key
                        break
            result = mb.generate_similar_question(topic)
            answer = (
                f"### 🎯 同类题\n\n**知识点**：{topic}\n\n"
                f"{result['question']}\n\n---\n"
                f"**答案**：\n{result['answer']}\n\n"
                f"*来源：{result.get('source', 'AI生成')}*"
            )
            return ChatResponse(answer=answer, sources=[result.get("source", "同类题生成")])
        except Exception as e:
            logger.error("[follow-up] 同类题生成失败: %s", e)
    # 普通追问
    try:
        from qa import get_llm
        context_prompt = (
            f"以下是之前的对话内容：\n\n"
            f"**用户问题**：{req.previous_question}\n\n"
            f"**你的回答**：{req.previous_answer}\n\n"
            f"---\n\n"
            f"用户继续追问：{req.question}\n\n"
            f"请基于之前的上下文回答用户的追问。"
        )
        llm = get_llm(max_tokens=2048)
        response = llm.invoke([{"role": "user", "content": context_prompt}])
        answer = response.content.strip()
        elapsed = time.time() - start
        logger.info("[follow-up] 追问完成, 耗时 %.2fs", elapsed)
        return ChatResponse(answer=answer, sources=["追问上下文"])
    except Exception as e:
        logger.error("[follow-up] 追问失败: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"追问处理失败: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
#  练习接口
# ═══════════════════════════════════════════════════════════════════════════

@api_router.get("/practice/calculation", response_model=PracticeResponse)
def calculation_practice(type: str = Query("", description="题型 id，如 cache_hit、pipeline")):
    """
    计算题专项练习：按题型生成一道随机计算题。

    查询参数:
        type: 题型 id（可通过 /practice/calculation/list 获取所有题型）
    返回:
        {"question": "...", "solution_steps": [...], "answer": "...", "type_name": "...", "subject": "..."}
    """
    import calculation_practice as cp

    if not type:
        raise HTTPException(status_code=400, detail="请指定 type 参数（题型 id）")

    problem = cp.generate_problem(type)
    if problem is None:
        topics = [t["id"] for t in cp.get_topic_list()]
        raise HTTPException(
            status_code=404,
            detail=f"未知题型: '{type}'。可用题型: {', '.join(topics)}",
        )

    return PracticeResponse(
        question=problem.question,
        solution_steps=problem.solution_steps,
        answer=problem.answer,
        type_name=problem.topic_name,
        subject=problem.subject,
    )


@api_router.get("/practice/calculation/list")
def calculation_practice_list():
    """返回计算题所有可用题型列表。"""
    import calculation_practice as cp
    return {"topics": cp.get_topic_list()}


@api_router.get("/practice/comprehensive", response_model=PracticeResponse)
def comprehensive_practice(
    type: str = Query("", description="大题题型 id，如 os_pv_producer_consumer"),
):
    """
    大题专项练习：按题型生成一道随机大题。

    查询参数:
        type: 题型 id（可通过 /practice/comprehensive/list 获取所有题型）
    返回:
        {"question": "...", "solution_steps": [...], "answer": "...", "type_name": "...", "subject": "..."}
    """
    import comprehensive_practice as comp

    if not type:
        raise HTTPException(status_code=400, detail="请指定 type 参数（题型 id）")

    problem = comp.generate_problem(type)
    if problem is None:
        topics = [t["id"] for t in comp.get_topic_list()]
        raise HTTPException(
            status_code=404,
            detail=f"未知题型: '{type}'。可用题型: {', '.join(topics)}",
        )

    return PracticeResponse(
        question=problem.question,
        solution_steps=problem.solution_steps,
        answer=problem.answer,
        type_name=problem.topic_name,
        subject=problem.subject,
    )


@api_router.get("/practice/comprehensive/list")
def comprehensive_practice_list():
    """返回大题所有可用题型列表。"""
    import comprehensive_practice as comp
    return {"topics": comp.get_topic_list()}


# ═══════════════════════════════════════════════════════════════════════════
#  资料导入接口
# ═══════════════════════════════════════════════════════════════════════════

@api_router.post("/ingest", response_model=IngestResponse)
async def ingest_files(
    files: list[UploadFile] = File(..., description="上传文件（PDF/MD/TXT，支持多选）"),
    category: str = Form("uploaded", description="分类标记（如 textbooks/exams/notes/minds）"),
):
    """
    资料导入接口：上传文件并增量导入向量库。

    上传方式:
        multipart/form-data
        - files: 文件列表（支持 PDF/MD/TXT）
        - category: 分类（默认为 uploaded）
    返回:
        {"files_processed": N, "chunks_added": N, "errors": [...]}
    """
    import ingest

    start = time.time()
    logger.info("[ingest] 收到 %d 个文件上传请求", len(files))

    processed = 0
    total_chunks = 0
    errors = []

    # 1. 保存上传文件到 data/ 下对应分类目录
    target_dir = os.path.join(config.DATA_DIR, category)
    os.makedirs(target_dir, exist_ok=True)

    saved_files = []
    for f in files:
        if not f.filename:
            continue
        try:
            path = _save_uploaded_file(f, target_dir)
            saved_files.append(path)
            processed += 1
        except Exception as e:
            errors.append(f"{f.filename}: {e}")

    if not saved_files:
        raise HTTPException(status_code=400, detail="没有可处理的有效文件")

    # 2. 加载向量库
    embeddings = ingest.HuggingFaceEmbeddings(
        model_name=config.EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = ingest.Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=config.PERSIST_DIR,
    )

    # 3. 处理文件（复用 ingest.py 的分块逻辑）
    cache = ingest.load_cache()

    raw_docs, failed_count = ingest.load_documents(saved_files)
    all_chunks, zero_block_files = ingest.build_chunks(raw_docs)
    ingest.write_chunks_to_vectorstore(all_chunks, vectorstore)

    # 4. 更新缓存
    for fp in saved_files:
        cache[fp] = ingest.compute_sha256(fp)
    ingest.save_cache(cache)

    total_chunks = len(all_chunks)

    elapsed = time.time() - start
    logger.info("[ingest] 完成: %d 文件, %d 块, 耗时 %.1fs", processed, total_chunks, elapsed)

    return IngestResponse(
        files_processed=processed,
        chunks_added=total_chunks,
        errors=errors,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  考情分析接口
# ═══════════════════════════════════════════════════════════════════════════

@api_router.post("/analyze", response_model=AnalysisResponse)
def analyze_exams():
    """
    考情分析接口：分析历年真题，生成考情报告。

    返回:
        {"report": "Markdown 格式报告", "stats": {...}}
    """
    import analysis

    start = time.time()
    logger.info("[analyze] 开始考情分析")

    try:
        if not config.API_KEY:
            raise HTTPException(status_code=500, detail="未配置 DEEPSEEK_API_KEY")

        exams_dir = os.path.join(config.DATA_DIR, "exams")
        if not os.path.isdir(exams_dir):
            raise HTTPException(status_code=500, detail=f"真题目录不存在: {exams_dir}")

        # 加载真题
        docs, errors = analysis.load_from_files(exams_dir)
        if not docs:
            raise HTTPException(status_code=500, detail="未加载到任何真题文档")

        # 构建各科目语料
        corpora = analysis.build_subject_corpora(docs)

        # 基础统计
        stats = analysis.aggregate_stats(docs)
        stats["files_loaded"] = len(docs)

        # 生成报告
        report = analysis.generate_report(docs, corpora, stats)

        # 保存报告
        report_path = os.path.join(config.OUTPUT_DIR, "report_2026.md")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        elapsed = time.time() - start
        logger.info("[analyze] 分析完成, 耗时 %.1fs, 保存至 %s", elapsed, report_path)

        return AnalysisResponse(
            report=report,
            stats=stats,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[analyze] 失败: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"考情分析失败: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
#  错题本与薄弱点接口
# ═══════════════════════════════════════════════════════════════════════════

@api_router.post("/mistake/add")
def mistake_add(req: MistakeAddRequest):
    """
    添加错题或薄弱点。

    请求体:
        {
            "question": "...", "answer": "...", "subject": "OS",
            "topic": "进程同步", "type": "错题",
            "source": "问答", "user_answer": "...",
            "image_base64": "data:image/png;base64,..."
        }
    返回:
        {"id": "uuid", "status": "added"}
    """
    import mistake_book as mb
    from memory import MemoryStore

    try:
        item_id = mb.add_item(mb.MistakeItem(
            question=req.question,
            answer=req.answer,
            user_answer=req.user_answer or "",
            source=req.source or "问答",
            subject=req.subject or "未分类",
            topic=req.topic or "",
            type=req.type,  # "错题" 或 "薄弱点"
            image_base64=req.image_base64 or "",
        ))

        # 同时更新记忆力模块
        if config.MEMORY_ENABLED:
            memory = MemoryStore(config.MEMORY_FILE)
            memory.update(req.topic or req.question[:30], correct=(req.type != "错题"))

        logger.info("[mistake/add] 已添加 %s: %s (id=%s)", req.type, req.question[:40], item_id)
        return {"id": item_id, "status": "added"}

    except Exception as e:
        logger.error("[mistake/add] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")


@api_router.get("/mistake/list")
def mistake_list(
    type: str = Query("", description="筛选类型：错题/薄弱点/空=全部"),
    subject: str = Query("", description="筛选科目：DS/CO/OS/CN/空=全部"),
    topic: str = Query("", description="筛选知识点标签/空=全部"),
):
    """
    错题本列表，支持按类型/科目/知识点筛选。

    返回:
        {"items": [...], "count": N}
    """
    import mistake_book as mb

    try:
        items = mb.get_all_items(filter_type=type or None)
        # 二级筛选：科目
        if subject:
            items = [i for i in items if i.subject == subject]
        # 三级筛选：知识点
        if topic:
            items = [i for i in items if topic in i.topic]
        # 按创建时间降序
        items.sort(key=lambda x: x.created_at, reverse=True)
        return {
            "items": [i.dict() for i in items],
            "count": len(items),
        }
    except Exception as e:
        logger.error("[mistake/list] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@api_router.delete("/mistake/{item_id}")
def mistake_delete(item_id: str):
    """
    删除指定错题/薄弱点。

    返回:
        {"status": "deleted", "id": "..."}
    """
    import mistake_book as mb

    try:
        mb.delete_item(item_id)
        logger.info("[mistake/delete] 已删除: %s", item_id)
        return {"status": "deleted", "id": item_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("[mistake/delete] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@api_router.post("/mistake/export")
def mistake_export(req: MistakeExportRequest):
    """
    导出错题/薄弱点。

    请求体:
        {"format": "markdown", "item_ids": ["id1", "id2"]}  # item_ids 可选
    返回:
        Markdown 文本直接返回；PDF 通过 StreamingResponse 返回二进制文件。
    """
    import mistake_book as mb

    try:
        # 获取待导出条目
        all_items = mb.get_all_items()
        if req.item_ids:
            items = [i for i in all_items if i.id in req.item_ids]
        else:
            items = all_items

        if not items:
            raise HTTPException(status_code=400, detail="没有可导出的项目")

        result = mb.export_items(items, format=req.format)

        if req.format == "markdown":
            # 编码为 UTF-8 字节以支持中文；filename 使用 ASCII 文件名避免 header 编码问题
            result_bytes = result.encode("utf-8")
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                content=result,
                media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition": "attachment; filename=408_mistakes.md"},
            )
        elif req.format == "pdf":
            from fastapi.responses import StreamingResponse
            import io
            pdf_bytes = result if isinstance(result, bytes) else result.encode("utf-8")
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": "attachment; filename=408_mistakes.pdf"},
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {req.format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[mistake/export] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@api_router.get("/mistake/summary")
def mistake_summary():
    """
    错题本分类统计。

    返回:
        {
            "summary": {"进程同步": {"count": 3, "type": "薄弱点", "subjects": ["OS"]}, ...},
            "total": 5,
            "weak_count": 2,
            "mistake_count": 3
        }
    """
    import mistake_book as mb

    try:
        summary = mb.summarize_mistakes()
        items = mb.get_all_items()
        total = len(items)
        weak_count = sum(1 for i in items if i.type == "薄弱点")
        mistake_count = sum(1 for i in items if i.type == "错题")
        return {
            "summary": summary,
            "total": total,
            "weak_count": weak_count,
            "mistake_count": mistake_count,
        }
    except Exception as e:
        logger.error("[mistake/summary] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")


@api_router.post("/mistake/similar")
def mistake_similar(req: SimilarQuestionRequest):
    """
    基于知识点生成同类题。

    请求体:
        {"topic": "进程同步"}
    返回:
        {
            "question": "...", "answer": "...",
            "source": "exercise_db|llm_generated",
            "topic": "进程同步"
        }
    """
    import mistake_book as mb

    try:
        # 带 120 秒超时保护
        result = timeout_exec(
            lambda: mb.generate_similar_question(req.topic),
            timeout_sec=120,
        )
        return result
    except _ThreadTimeout:
        raise HTTPException(status_code=504, detail="生成同类题超时，请稍后重试")
    except Exception as e:
        logger.error("[mistake/similar] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"生成同类题失败: {str(e)}")


@api_router.post("/mistake/similar/export")
def mistake_similar_export(req: SimilarQuestionExportRequest):
    """导出同类题为 Markdown。"""
    import mistake_book as mb
    try:
        result = mb.generate_similar_question(req.topic)
        md_content = mb.export_similar_question_md(result)
        return Response(
            content=md_content.encode("utf-8"),
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=similar_{req.topic}.md"},
        )
    except Exception as e:
        logger.error("[mistake/similar/export] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"导出同类题失败: {str(e)}")


@api_router.post("/mistake/cards")
def mistake_cards(req: CardsRequest):
    """
    生成 Q&A 概念卡片。

    请求体:
        {"concepts": ["LRU替换", "TCP三次握手"]}
    返回:
        {"cards": [{"question": "...", "answer": "...", "concept": "..."}], "count": N}
    """
    import mistake_book as mb

    try:
        cards = timeout_exec(
            lambda: mb.generate_qa_cards(req.concepts),
            timeout_sec=120,
        )
        return {"cards": cards, "count": len(cards)}
    except _ThreadTimeout:
        raise HTTPException(status_code=504, detail="生成概念卡片超时，请稍后重试")
    except Exception as e:
        logger.error("[mistake/cards] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"生成卡片失败: {str(e)}")


@api_router.get("/mistake/cards/export")
def mistake_cards_export(
    format: str = Query("markdown", description="导出格式: markdown 或 anki"),
):
    """
    导出已生成的 Q&A 卡片（需要先调用 POST /mistake/cards 生成）。

    查询参数:
        format: markdown | anki
    返回:
        Markdown / CSV 文本文件下载。
    """
    import mistake_book as mb

    try:
        # 从内存获取最近一次生成的卡片（简化方案：重新生成示例卡片）
        from mistake_book import generate_qa_cards
        # 从 summary 提取热点概念
        summary = mb.summarize_mistakes()
        top_concepts = sorted(summary.keys(), key=lambda k: summary[k]["count"], reverse=True)[:10]
        if not top_concepts:
            top_concepts = ["Cache替换算法", "TCP拥塞控制", "页面置换", "PV操作", "死锁"]
        cards = mb.generate_qa_cards(top_concepts)
        output = mb.export_cards(cards, format=format)

        media_type = "text/csv" if format == "anki" else "text/markdown"
        ext = "csv" if format == "anki" else "md"
        return Response(
            content=output,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename=408_cards.{ext}"},
        )
    except Exception as e:
        logger.error("[mistake/cards/export] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"导出卡片失败: {str(e)}")


# ── 向后兼容：保留旧的 /mistake_book 端点 ──
# ═══════════════════════════════════════════════════════════════════════════
#  练习题库接口（/data/exercise 选择题库）
# ═══════════════════════════════════════════════════════════════════════════

@api_router.get("/exercise/list")
def exercise_list(
    subject: str = Query("", description="筛选科目：DS/CO/OS/CN/空=全部"),
    keyword: str = Query("", description="关键词搜索"),
    limit: int = Query(50, description="最多返回条数"),
):
    """
    获取练习题库中的选择题列表。

    查询参数:
        subject: 科目筛选
        keyword: 关键词搜索
        limit: 最大返回数（默认 50）
    返回:
        {"items": [...], "count": N, "subjects": [...]}
    """
    import mistake_book as mb

    try:
        questions = mb._load_exercise_questions()
        subjects = sorted(set(q.get("subject", "") for q in questions if q.get("subject")))

        # 筛选
        if subject:
            questions = [q for q in questions if q.get("subject") == subject]
        if keyword:
            questions = [q for q in questions if keyword in q.get("question", "")]

        questions = questions[:limit]

        return {
            "items": questions,
            "count": len(questions),
            "subjects": subjects,
        }
    except Exception as e:
        logger.error("[exercise/list] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取题库失败: {str(e)}")


@api_router.get("/exercise/search")
def exercise_search(
    q: str = Query("", description="搜索关键词"),
    limit: int = Query(20, description="最多返回条数"),
):
    """
    搜索练习题库中的选择题。

    查询参数:
        q: 搜索关键词
        limit: 最大返回数
    返回:
        {"items": [...], "count": N, "keyword": "..."}
    """
    import mistake_book as mb

    try:
        questions = mb._load_exercise_questions()
        if not q:
            return {"items": [], "count": 0, "keyword": q}

        # 模糊匹配：题目文本和知识点
        matched = []
        for q_item in questions:
            text = q_item.get("question", "") + " " + q_item.get("topic", "")
            if q in text:
                matched.append(q_item)

        matched = matched[:limit]
        return {
            "items": matched,
            "count": len(matched),
            "keyword": q,
        }
    except Exception as e:
        logger.error("[exercise/search] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"搜索题库失败: {str(e)}")


@api_router.post("/mistake_book")
def add_mistake_legacy(entry: MistakeEntry):
    """旧的错题本添加接口（向后兼容）。"""
    from memory import MemoryStore
    try:
        memory = MemoryStore(config.MEMORY_FILE)
        topic = entry.knowledge_point or entry.topic or entry.question[:30]
        memory.update(topic, correct=False)

        # 调用新接口添加
        import mistake_book as mb
        item_id = mb.add_item(mb.MistakeItem(
            question=entry.question,
            answer=entry.answer,
            user_answer="",
            source=entry.source or "问答",
            subject="未分类",
            topic=entry.topic or "",
            type="错题",
            image_base64="",
        ))
        logger.info("[mistake_book/legacy] 已保存错题: %s", item_id)
        return {"status": "saved", "id": item_id}
    except Exception as e:
        logger.error("[mistake_book/legacy] 失败: %s", e)
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@api_router.get("/mistake_book")
def list_mistakes_legacy():
    """旧的错题本列表接口（向后兼容）。"""
    import mistake_book as mb
    items = mb.get_all_items()
    result = []
    for it in items:
        result.append({
            "id": it.id,
            "question": it.question,
            "answer": it.answer,
            "topic": it.topic,
            "source": it.source,
            "knowledge_point": it.topic,
            "timestamp": it.created_at,
        })
    return {"mistakes": result, "count": len(result)}


# ═══════════════════════════════════════════════════════════════════════════
#  健康检查
# ═══════════════════════════════════════════════════════════════════════════

@api_router.get("/health", response_model=HealthResponse)
def health_check():
    """健康检查接口，返回系统状态。"""
    vectorstore_ready = (
        os.path.exists(config.PERSIST_DIR)
        and os.path.isdir(config.PERSIST_DIR)
        and any(f.startswith("chroma") for f in os.listdir(config.PERSIST_DIR))
    )

    data_dir_ready = os.path.isdir(config.DATA_DIR)

    exams_dir = os.path.join(config.DATA_DIR, "exams")
    total_exams = 0
    if os.path.isdir(exams_dir):
        total_exams = len([f for f in os.listdir(exams_dir) if f.lower().endswith(".pdf")])

    return HealthResponse(
        status="ok",
        api_key_configured=bool(config.API_KEY),
        vision_key_configured=bool(config.VISION_API_KEY),
        vectorstore_ready=vectorstore_ready,
        data_dir_ready=data_dir_ready,
        total_exams=total_exams,
    )


# ── 挂载 API 路由 ──
app.include_router(api_router)


# ═══════════════════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
