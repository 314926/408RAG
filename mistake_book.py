"""
408 考研知识库 — 错题本与薄弱点追踪模块

数据模型、JSON 持久化、分类统计、导出（Markdown/PDF）、
同类题生成、Q&A 概念卡片生成。

依赖:
    - config.py（数据目录、LLM 配置）
    - qa.py（可选，用于大模型辅助分类和同类题生成）
    - markdown / weasyprint（可选，用于 PDF 导出）
"""

import csv
import io
import json
import logging
import os
import random
import re
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  数据模型
# ═══════════════════════════════════════════════════════════════════════════

class MistakeItem(BaseModel):
    """错题/薄弱点数据模型"""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    question: str                    # 题目文本
    answer: str                      # 正确答案
    user_answer: str = ""            # 用户答案或备注
    source: str = ""                 # 来源：qa（问答）/ practice（练习，附带题型）
    subject: str = ""                # 科目：DS/CO/OS/CN
    topic: str = ""                  # 知识点标签
    type: str = "错题"               # 错题 / 薄弱点
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    image_base64: str = ""           # 可选，题目包含图片时的 Base64


# ═══════════════════════════════════════════════════════════════════════════
#  存储路径
# ═══════════════════════════════════════════════════════════════════════════

MISTAKE_DATA_FILE = os.path.join(
    config.OUTPUT_DIR, "mistake_data.json"
)

# 兼容旧版错题本目录（用于读取但不写入）
MISTAKE_BOOK_DIR_OLD = config.MISTAKE_BOOK_DIR


# ═══════════════════════════════════════════════════════════════════════════
#  数据读写
# ═══════════════════════════════════════════════════════════════════════════

def _load_data() -> list[dict]:
    """从 JSON 文件加载所有错题数据"""
    if not os.path.exists(MISTAKE_DATA_FILE):
        return []
    try:
        with open(MISTAKE_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("读取错题数据文件失败: %s", e)
        return []


def _save_data(items: list[dict]):
    """保存错题数据到 JSON 文件"""
    os.makedirs(os.path.dirname(MISTAKE_DATA_FILE), exist_ok=True)
    with open(MISTAKE_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#  增删改查
# ═══════════════════════════════════════════════════════════════════════════

def add_item(item: MistakeItem) -> str:
    """
    添加一条错题或薄弱点记录。
    返回该条记录的 id。
    """
    items = _load_data()
    item_dict = item.model_dump()
    items.append(item_dict)
    _save_data(items)
    logger.info("[mistake_book] 已添加: %s (type=%s, topic=%s)", item.id, item.type, item.topic)
    return item.id


def get_all_items(filter_type: Optional[str] = None,
                  filter_subject: Optional[str] = None,
                  filter_topic: Optional[str] = None) -> list[MistakeItem]:
    """
    获取所有错题记录，支持按类型/科目/知识点筛选。
    返回 MistakeItem 列表。
    """
    items = _load_data()
    result = []
    for d in items:
        if filter_type and d.get("type") != filter_type:
            continue
        if filter_subject and d.get("subject") != filter_subject:
            continue
        if filter_topic:
            topic = d.get("topic", "")
            if filter_topic not in topic:
                continue
        result.append(MistakeItem(**d))
    return result


def delete_item(item_id: str) -> bool:
    """删除指定 id 的错题记录。"""
    items = _load_data()
    new_items = [d for d in items if d.get("id") != item_id]
    if len(new_items) == len(items):
        return False  # 未找到
    _save_data(new_items)
    logger.info("[mistake_book] 已删除: %s", item_id)
    return True


def update_item(item_id: str, updates: dict) -> bool:
    """更新指定 id 的错题记录字段。"""
    items = _load_data()
    for d in items:
        if d.get("id") == item_id:
            allowed_fields = {"question", "answer", "user_answer", "source",
                              "subject", "topic", "type", "image_base64"}
            for key, value in updates.items():
                if key in allowed_fields:
                    d[key] = value
            _save_data(items)
            logger.info("[mistake_book] 已更新: %s", item_id)
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
#  导出功能
# ═══════════════════════════════════════════════════════════════════════════

def export_items(items: List[MistakeItem], format: str = "markdown") -> str:
    """
    导出错题/薄弱点列表。

    参数:
        items: 待导出的 MistakeItem 列表
        format: "markdown" 或 "pdf"
    返回:
        - markdown: 导出的 Markdown 字符串
        - pdf: PDF 文件路径（生成临时文件）
    """
    if format == "markdown":
        return _export_markdown(items)
    elif format == "pdf":
        return _export_pdf(items)
    else:
        raise ValueError(f"不支持的导出格式: {format}")


def _export_markdown(items: List[MistakeItem]) -> str:
    """
    导出为 Markdown 字符串。

    格式：
    1. 按科目分组（DS/CO/OS/CN + 未分类）
    2. 每个科目内按题型分组
    3. 错题用 ❌ 标记，薄弱点用 ⚠️ **薄弱点** 高亮
    """
    lines = []
    lines.append("# 📚 408 错题本与薄弱点汇总\n")
    lines.append(f"> 导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"> 总条目：{len(items)}\n")
    lines.append("---\n")

    # 按科目分组
    subjects_order = ["DS", "CO", "OS", "CN", ""]
    grouped = {s: [] for s in subjects_order}
    for item in items:
        s = item.subject.strip()
        if s in grouped:
            grouped[s].append(item)
        else:
            grouped[""].append(item)

    for subject in subjects_order:
        group = grouped[subject]
        if not group:
            continue

        subject_name = {
            "DS": "数据结构",
            "CO": "计算机组成原理",
            "OS": "操作系统",
            "CN": "计算机网络",
            "": "未分类",
        }.get(subject, subject)

        lines.append(f"## 📖 {subject_name}\n")
        lines.append(f"_共 {len(group)} 条_\n")

        # 按知识点分组
        topic_groups: dict[str, list] = {}
        for item in group:
            t = item.topic or "其他"
            if t not in topic_groups:
                topic_groups[t] = []
            topic_groups[t].append(item)

        for topic, topic_items in topic_groups.items():
            lines.append(f"### {topic}\n")

            for idx, item in enumerate(topic_items, 1):
                # 类型标记
                if item.type == "薄弱点":
                    type_tag = "⚠️ **薄弱点**"
                else:
                    type_tag = "❌ 错题"

                lines.append(f"#### {idx}. {type_tag}\n")
                lines.append(f"**题目：**\n\n{item.question}\n")
                if item.user_answer:
                    lines.append(f"**你的答案：** {item.user_answer}\n")
                lines.append(f"**正确答案：**\n\n{item.answer}\n")
                if item.source:
                    lines.append(f"_来源：{item.source}_\n")
                lines.append("---\n")

        lines.append("\n")

    return "\n".join(lines)


def _export_pdf(items: List[MistakeItem]) -> str:
    """
    导出为 PDF 文件。

    流程：Markdown → HTML → PDF（使用 weasyprint 或 pdfkit）。
    如果依赖缺失，打印安装指引并回退为 Markdown 导出。
    """
    # 1. 先生成 Markdown
    md_content = _export_markdown(items)

    # 2. 尝试将 Markdown 转为 HTML
    try:
        import markdown as md_lib
        html_body = md_lib.markdown(
            md_content,
            extensions=["extra", "codehilite", "tables", "fenced_code"]
        )
    except ImportError:
        logger.warning(
            "markdown 库未安装，无法生成 HTML。"
            "请运行: pip install markdown"
        )
        # 回退：返回 Markdown 文件路径
        fallback_path = os.path.join(config.OUTPUT_DIR, "mistake_export.md")
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("回退为 Markdown 导出: %s", fallback_path)
        return fallback_path

    # 3. HTML 包装
    html_full = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: "Noto Sans SC", "Source Han Sans SC", "Microsoft YaHei", sans-serif;
        font-size: 12pt;
        line-height: 1.8;
        padding: 40px;
        max-width: 800px;
        margin: 0 auto;
        color: #333;
    }}
    h1 {{ color: #1a1a2e; border-bottom: 2px solid #646cff; padding-bottom: 8px; }}
    h2 {{ color: #2d3748; margin-top: 32px; border-left: 4px solid #646cff; padding-left: 12px; }}
    h3 {{ color: #4a5568; margin-top: 24px; }}
    h4 {{ color: #5a67d8; }}
    .mistake-weak {{ background: #fff3cd; padding: 2px 6px; border-radius: 4px; }}
    .mistake-error {{ background: #f8d7da; padding: 2px 6px; border-radius: 4px; }}
    blockquote {{ border-left: 4px solid #cbd5e0; margin: 16px 0; padding: 8px 16px; background: #f7fafc; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }}
    th {{ background: #edf2f7; }}
    @media print {{
        body {{ padding: 20px; }}
        h2 {{ page-break-before: always; }}
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    # 4. 尝试用 weasyprint 生成 PDF
    try:
        import weasyprint
        pdf_path = os.path.join(config.OUTPUT_DIR, "mistake_export.pdf")
        weasyprint.HTML(string=html_full).write_pdf(pdf_path)
        logger.info("PDF 导出成功: %s", pdf_path)
        return pdf_path
    except ImportError:
        logger.warning(
            "weasyprint 未安装，无法生成 PDF。\n"
            "请运行: pip install weasyprint\n"
            "如有必要，安装 GTK3 运行时: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer\n"
            "回退为 HTML 导出。"
        )
        html_path = os.path.join(config.OUTPUT_DIR, "mistake_export.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_full)
        logger.info("回退为 HTML 导出: %s", html_path)
        return html_path
    except Exception as e:
        logger.error("PDF 生成失败: %s", e)
        # 回退为 Markdown
        fallback_path = os.path.join(config.OUTPUT_DIR, "mistake_export.md")
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("回退为 Markdown 导出: %s", fallback_path)
        return fallback_path


# ═══════════════════════════════════════════════════════════════════════════
#  总结与分类
# ═══════════════════════════════════════════════════════════════════════════

def summarize_mistakes() -> dict:
    """
    从所有错题/薄弱点中提取知识点标签，返回分类统计数据。

    返回格式:
        {
            "summary": {
                "total": N,
                "by_type": {"错题": N, "薄弱点": N},
                "by_subject": {"DS": N, ...},
            },
            "topics": {
                "进程同步": {"count": 3, "type": "薄弱点", "subject": "OS"},
                "Cache映射": {"count": 2, "type": "错题", "subject": "CO"},
                ...
            }
        }
    """
    items = _load_data()
    if not items:
        return {
            "summary": {"total": 0, "by_type": {}, "by_subject": {}},
            "topics": {}
        }

    # ── 基础统计 ──
    total = len(items)
    by_type: dict[str, int] = {}
    by_subject: dict[str, int] = {}
    topics: dict[str, dict] = {}

    for d in items:
        t = d.get("type", "错题")
        by_type[t] = by_type.get(t, 0) + 1

        s = d.get("subject", "未分类")
        by_subject[s] = by_subject.get(s, 0) + 1

        topic_name = d.get("topic", "其他").strip()
        if not topic_name:
            topic_name = "其他"
        if topic_name not in topics:
            topics[topic_name] = {"count": 0, "type": t, "subject": s}
        topics[topic_name]["count"] += 1
        # 如果同一知识点既有错题又有薄弱点，type 优先显示"薄弱点"
        if t == "薄弱点":
            topics[topic_name]["type"] = "薄弱点"

    return {
        "summary": {
            "total": total,
            "by_type": by_type,
            "by_subject": by_subject,
        },
        "topics": topics,
    }


def _extract_topics_from_text(text: str) -> list[str]:
    """
    从文本中提取可能的知识点标签（基于 CORE_CONCEPTS 字典）。
    用于自动补全分类。
    """
    matches = set()
    for key in config.CORE_CONCEPTS.keys():
        if key in text:
            matches.add(key)
    return list(matches)


def _classify_subject(topic: str, question: str = "") -> str:
    """
    根据知识点和题目内容推测科目。
    返回 DS / CO / OS / CN 之一。
    """
    combined = topic + " " + question

    # 关键词匹配 → 科目
    ds_keywords = ["排序", "树", "图", "查找", "链表", "栈", "队列", "堆", "串", "KMP",
                   "二叉树", "二叉搜索树", "AVL", "哈希", "B树"]
    co_keywords = ["Cache", "流水线", "浮点数", "补码", "指令", "总线", "中断", "DMA",
                   "存储器", "微程序", "CPU", "内存", "IO", "输入输出"]
    os_keywords = ["进程", "线程", "死锁", "调度", "信号量", "页面置换", "文件系统", "磁盘",
                   "虚拟内存", "分页", "分段"]
    cn_keywords = ["TCP", "IP", "HTTP", "DNS", "以太网", "传输层", "网络层", "路由",
                   "拥塞控制", "三次握手"]

    for kw in ds_keywords:
        if kw in combined:
            return "DS"
    for kw in co_keywords:
        if kw in combined:
            return "CO"
    for kw in os_keywords:
        if kw in combined:
            return "OS"
    for kw in cn_keywords:
        if kw in combined:
            return "CN"

    return ""


# ═══════════════════════════════════════════════════════════════════════════
#  同类题生成
# ═══════════════════════════════════════════════════════════════════════════

# ── 模块级缓存：练习题库，避免重复加载 ──
_exercise_cache: list[dict] | None = None


def _load_exercise_questions(force_reload: bool = False) -> list[dict]:
    """
    从 /data/exercise 目录加载选择题（递归扫描所有 .txt 文件）。

    使用模块级缓存避免重复加载（第一次加载后即缓存）。
    会递归扫描 exercise/ 下所有子目录（含 exam/ 真题分类目录）。

    返回 [{question, answer, subject, topic, source_file, is_exam}, ...] 列表。
    其中 is_exam=True 表示来自 exam/ 真题分类目录，应作为最高优先级参考。
    """
    global _exercise_cache
    if _exercise_cache is not None and not force_reload:
        return _exercise_cache

    # 找 exercise 子目录
    exercise_root = None
    for sub in ["exercise", "exercises"]:
        candidate = os.path.join(config.DATA_DIR, sub)
        if os.path.isdir(candidate):
            exercise_root = candidate
            break
    else:
        candidate = os.path.join(config.DATA_DIR, "exercise")
        if os.path.isdir(candidate):
            exercise_root = candidate
        else:
            logger.warning("练习题库目录不存在: %s", candidate)
            _exercise_cache = []
            return []

    questions = []
    seen_texts = set()

    # 递归扫描所有 .txt 文件（含子目录）
    for root, dirs, files in os.walk(exercise_root):
        for fname in sorted(files):
            if not fname.endswith(".txt"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                extracted = _parse_exercise_text(content, fname)
                # 判断是否来自 exam/ 子目录（真题分类）
                rel_path = os.path.relpath(fpath, exercise_root)
                is_exam = rel_path.startswith("exam" + os.sep)
                for q in extracted:
                    text_key = q["question"][:100]
                    if text_key not in seen_texts:
                        seen_texts.add(text_key)
                        q["source_file"] = rel_path
                        q["is_exam"] = is_exam
                        questions.append(q)
            except Exception as e:
                logger.warning("读取练习文件失败 %s: %s", fname, e)

    # 统计
    txt_count = sum(1 for _, _, files in os.walk(exercise_root) for f in files if f.endswith('.txt'))
    exam_count = sum(1 for q in questions if q.get("is_exam"))
    logger.info("[exercise] 加载了 %d 道练习题（从 %d 个 .txt 文件，含 %d 道真题分类）",
                len(questions), txt_count, exam_count)

    _exercise_cache = questions
    return questions


def _parse_exercise_text(text: str, filename: str) -> list[dict]:
    """
    解析练习文本，提取选择题。
    支持格式：
    - "1. 题目内容？ A. 选项1 B. 选项2 C. 选项3 D. 选项4"
    - "答案：A" 或 "【答案】A"
    """
    questions = []
    subject_map = {
        "数据结构": "DS",
        "计算机组成原理": "CO",
        "操作系统": "OS",
        "计算机网络": "CN",
    }

    # 从文件名推测科目
    file_subject = ""
    for name, code in subject_map.items():
        if name in filename:
            file_subject = code
            break

    # 按行解析
    lines = text.split("\n")
    current_q = {"question": "", "answer": "", "options": [], "subject": file_subject, "topic": ""}

    # 题目编号正则
    q_num_pattern = re.compile(r'^(\d+)[.、．]\s*(.*)')
    answer_pattern = re.compile(r'[【\[]\s*答案\s*[】\]]\s*([A-Da-d])')
    option_pattern = re.compile(r'^([A-Da-d])[.、．]\s*(.*)')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 答案行
        answer_match = answer_pattern.search(line)
        if answer_match:
            if current_q["question"]:
                current_q["answer"] = answer_match.group(1).upper()
                # 拼接 question + options 作为完整题目
                if current_q["options"]:
                    opts_str = "\n".join(f"{k}) {v}" for k, v in current_q["options"])
                    current_q["question"] = current_q["question"] + "\n" + opts_str
                if current_q["question"] and current_q["answer"]:
                    questions.append(current_q)
            current_q = {"question": "", "answer": "", "options": [], "subject": file_subject, "topic": ""}
            continue

        # 题目编号行
        q_match = q_num_pattern.match(line)
        if q_match:
            # 如果上一条还没保存且内容不为空，先保存
            if current_q["question"] and current_q.get("answer"):
                if current_q["options"]:
                    opts_str = "\n".join(f"{k}) {v}" for k, v in current_q["options"])
                    current_q["question"] = current_q["question"] + "\n" + opts_str
                questions.append(current_q)
            current_q = {"question": q_match.group(2), "answer": "", "options": [], "subject": file_subject, "topic": ""}
            continue

        # 选项行
        opt_match = option_pattern.match(line)
        if opt_match:
            current_q["options"].append((opt_match.group(1).upper(), opt_match.group(2)))
            continue

        # 其他行 → 追加到当前题目描述
        if current_q["question"]:
            current_q["question"] += " " + line

    # 保存最后一题
    if current_q["question"] and current_q.get("answer"):
        if current_q["options"]:
            opts_str = "\n".join(f"{k}) {v}" for k, v in current_q["options"])
            current_q["question"] = current_q["question"] + "\n" + opts_str
        questions.append(current_q)

    return questions


def generate_similar_question(topic: str) -> dict:
    """
    基于给定的知识点生成一道同类题。

    策略：
    1. 从 /data/exercise 题库中检索相关题目作为参考素材 → 提取知识点和题型结构
       ⚠️ 不允许原样照抄题库题目，须实质性修改题面、参数、选项
    2. 从向量库检索相关上下文作为背景知识
    3. 将以上素材作为参考输入 LLM，生成一道全新的同类题

    返回:
        {"question": "...", "answer": "...", "source": "llm (参考: exercise 题库)", "topic": "..."}
    """
    exercise_references = []
    exam_references = []
    knowledge_context = ""

    # 1. 从题库检索参考素材（匹配知识点），将真题分类（exam/）与普通题分开
    exercise_questions = _load_exercise_questions()
    if exercise_questions:
        exam_matched = []
        exercise_matched = []
        for q in exercise_questions:
            q_text = q.get("question", "") + " " + q.get("topic", "")
            if topic in q_text:
                if q.get("is_exam"):
                    exam_matched.append(q)
                else:
                    exercise_matched.append(q)
        # 真题优先：最多取 3 道真题 + 2 道普通题
        import random as _random
        exam_samples = _random.sample(exam_matched, min(len(exam_matched), 3)) if exam_matched else []
        exer_samples = _random.sample(exercise_matched, min(len(exercise_matched), 2)) if exercise_matched else []
        for s in exam_samples:
            exam_references.append({
                "source": s.get("source_file", "题库"),
                "subject": s.get("subject", ""),
                "question": s.get("question", ""),
                "answer": s.get("answer", ""),
            })
        for s in exer_samples:
            exercise_references.append({
                "source": s.get("source_file", "题库"),
                "subject": s.get("subject", ""),
                "question": s.get("question", ""),
                "answer": s.get("answer", ""),
            })
        logger.info("[similar] 从题库找到 %d 道真题参考 + %d 道普通题参考（知识点: %s）",
                     len(exam_samples), len(exer_samples), topic)

    # 2. 从向量库检索相关背景知识
    try:
        from qa import retrieve, load_vectorstore
        vectorstore = load_vectorstore()
        docs = retrieve(topic, vectorstore)
        if docs:
            knowledge_context = "\n".join(d["content"][:300] for d in docs[:3])
            logger.info("[similar] 从知识库检索到背景知识")
    except Exception as e:
        logger.warning("[similar] 知识库检索失败: %s", e)

    # 3. 构建出题 prompt（LLM 生成全新题目）
    try:
        from qa import get_llm
        llm = get_llm(max_tokens=1024, request_timeout=60)

        # ── prompt 头部：出题任务 ──
        prompt = (
            f"你是一个408计算机考研出题助手。请基于知识点「{topic}」**新编**一道选择题。\n\n"
            f"## 任务要求\n"
            f"1. 题目必须紧扣知识点「{topic}」，难度贴近408真题\n"
            f"2. 包含4个选项（A/B/C/D），选项要有区分度，迷惑项设计合理\n"
            f"3. 给出正确答案 + 简要解析（说明为什么对、迷惑项为什么错）\n"
            f"4. 格式：\n"
            f"   题目：...\n"
            f"   A) ...\n"
            f"   B) ...\n"
            f"   C) ...\n"
            f"   D) ...\n"
            f"   答案：X\n"
            f"   解析：...\n"
        )

        # ── 真题分类参考（最高优先级）──
        if exam_references:
            prompt += (
                f"\n## 🏆 历年真题参考（最高优先级！真题是最重要的出题参考依据）\n"
                f"以下是从历年408真题分类中检索到的相关真题。真题最能反映考研的出题风格、难度和考察角度。\n"
                f"请**仔细研究**这些真题的题型结构、考察方式和难度，然后出同类的新题：\n"
                f"- 真题的考点方向是最重要的参考\n"
                f"- 真题的难度层次（基础/综合/计算）保持相似\n"
                f"- 但**不要照抄**真题原题，必须变换场景、数字、选项\n\n"
            )
            for i, ref in enumerate(exam_references, 1):
                prompt += f"--- 真题参考 {i}（来源：{ref['source']}）---\n"
                prompt += f"题目：{ref['question'][:400]}\n"
                prompt += f"答案：{ref['answer']}\n\n"

        # ── 普通题库参考（辅助参考）──
        if exercise_references:
            prompt += (
                f"\n## 模拟题参考（辅助参考）\n"
                f"以下是从练习题库中找到的模拟题，仅用于补充参考：\n"
                f"- 同样**不要照抄**\n"
                f"- 真题参考优先于模拟题参考\n\n"
            )
            for i, ref in enumerate(exercise_references, 1):
                prompt += f"--- 参考题 {i}（来源：{ref['source']}）---\n"
                prompt += f"题目：{ref['question'][:400]}\n"
                prompt += f"答案：{ref['answer']}\n\n"

        # ── 知识库背景 ──
        if knowledge_context:
            prompt += f"\n## 补充背景知识（供参考理解知识点）\n{knowledge_context}\n"

        # ── 禁止照抄的强调 ──
        prompt += (
            "\n## ⚠️ 严格禁止\n"
            "- ❌ 禁止原样复制或仅微调参考题目的题干\n"
            "- ❌ 禁止原样套用参考题目的选项结构（如 A=xxx B=yyy 一一对应）\n"
            "- ❌ 禁止不经修改直接输出题库中的题目\n"
            "- ✅ 必须产出一道**全新**的题目，仅在知识点范围上与参考题一致\n"
        )

        response = llm.invoke([{"role": "user", "content": prompt}])
        content = response.content.strip()

        # 标记来源：注明参考了题库（优先显示真题来源）
        if exam_references:
            exam_sources = set(r['source'] for r in exam_references)
            source_label = f"llm (参考: 真题分类 {', '.join(exam_sources)}"
            if exercise_references:
                exer_sources = set(r['source'] for r in exercise_references)
                source_label += f" + {', '.join(exer_sources)}"
            source_label += ")"
        elif exercise_references:
            source_label = f"llm (参考: {', '.join(set(r['source'] for r in exercise_references))})"
        else:
            source_label = "llm"

        logger.info("[similar] 大模型生成成功: %s", topic)
        return {
            "question": content,
            "answer": "(见题目内答案)",
            "source": source_label,
        }
    except Exception as e:
        logger.error("[similar] 大模型生成失败: %s", e)
        return {
            "question": f"未能生成关于「{topic}」的同类题，请稍后重试。",
            "answer": "",
            "source": "error",
        }


# ═══════════════════════════════════════════════════════════════════════════
#  Q&A 概念卡片生成
# ═══════════════════════════════════════════════════════════════════════════

def generate_qa_cards(concepts: list[str]) -> list[dict]:
    """
    对给定概念列表生成 Q&A 卡片。

    参数:
        concepts: 概念字符串列表，如 ["LRU替换", "TCP三次握手"]
    返回:
        [{"question": "什么是LRU替换？", "answer": "LRU...", "concept": "LRU替换"}, ...]
    """
    if not concepts:
        return []

    cards = []

    # 优先从练习题库中检索相关题目-答案对
    exercise_questions = _load_exercise_questions()

    for concept in concepts:
        concept = concept.strip()
        if not concept:
            continue

        # 从题库查找匹配的题作为参考素材（不直接照抄）
        matched_refs = []
        for eq in exercise_questions:
            q_text = eq.get("question", "") + " " + eq.get("topic", "")
            if concept in q_text:
                matched_refs.append(eq)
                if len(matched_refs) >= 2:
                    break

        # 调用大模型生成卡片（题库匹配到的话作为参考输入）
        try:
            from qa import get_llm
            llm = get_llm(max_tokens=512, request_timeout=60)

            prompt = (
                f"你是一个408计算机考研学习助手。请以简洁的问答对形式解释概念「{concept}」。\n\n"
                f"格式要求（严格按此格式输出）：\n"
                f"问：……\n"
                f"答：……\n\n"
                f"要求：答案控制在100字以内，核心准确，适合做Anki卡片。"
            )

            if matched_refs:
                prompt += (
                    f"\n\n以下是从题库中找到的相关题目，仅作为参考素材了解该概念的考察角度，"
                    f"请**不要照抄**，而是用自己的语言重新组织问答：\n"
                )
                for mq in matched_refs:
                    prompt += f"参考：{mq['question'][:200]}\n答案：{mq['answer']}\n\n"

            response = llm.invoke([{"role": "user", "content": prompt}])
            content = response.content.strip()

            # 解析问/答
            q_match = re.search(r'问[：:]\s*(.*?)(?=\n答[：:])', content, re.DOTALL)
            a_match = re.search(r'答[：:]\s*(.*)', content, re.DOTALL)

            if q_match and a_match:
                cards.append({
                    "question": q_match.group(1).strip(),
                    "answer": a_match.group(1).strip(),
                    "concept": concept,
                })
            else:
                # 解析失败，用整段作为答案
                cards.append({
                    "question": f"什么是{concept}？",
                    "answer": content,
                    "concept": concept,
                })
        except Exception as e:
            logger.warning("[cards] 生成卡片失败 '%s': %s", concept, e)
            cards.append({
                "question": f"什么是{concept}？",
                "answer": f"（生成失败：{e}）",
                "concept": concept,
            })

    logger.info("[cards] 生成了 %d 张卡片（共 %d 个概念）", len(cards), len(concepts))
    return cards


def export_cards(cards: list[dict], format: str = "markdown") -> str:
    """
    导出 Q&A 卡片为 Markdown 或 Anki CSV。

    参数:
        cards: generate_qa_cards 返回的卡片列表
        format: "markdown" 或 "anki"
    返回:
        字符串内容（如果是 anki，返回 CSV 格式内容）
    """
    if format == "markdown":
        return _export_cards_markdown(cards)
    elif format == "anki":
        return _export_cards_anki(cards)
    else:
        raise ValueError(f"不支持的导出格式: {format}")


def _export_cards_markdown(cards: list[dict]) -> str:
    """导出为 Markdown 表格"""
    lines = []
    lines.append("# 🃏 408 核心概念 Q&A 卡片\n")
    lines.append(f"> 导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"> 总卡片数：{len(cards)}\n")
    lines.append("---\n")

    # 按概念分组
    current_concept = ""
    for card in cards:
        if card["concept"] != current_concept:
            current_concept = card["concept"]
            lines.append(f"\n## 📌 {current_concept}\n")

        lines.append(f"**Q：** {card['question']}\n")
        lines.append(f"**A：** {card['answer']}\n")
        lines.append("---\n")

    return "\n".join(lines)


def export_similar_question_md(result: dict) -> str:
    """
    将同类题结果导出为 Markdown 字符串。

    参数:
        result: generate_similar_question 返回的字典
    返回:
        Markdown 格式字符串
    """
    lines = []
    lines.append("# 🎯 同类题\n")
    lines.append(f"> 知识点：{result.get('topic', '')}\n")
    lines.append(f"> 来源：{result.get('source', '未知')}\n")
    lines.append(f"> 导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("---\n")
    lines.append("## 📝 题目\n")
    lines.append(f"{result.get('question', '')}\n")
    lines.append("---\n")
    lines.append("## ✅ 答案\n")
    lines.append(f"{result.get('answer', '')}\n")
    return "\n".join(lines)


def _export_cards_anki(cards: list[dict]) -> str:
    """
    导出为 Anki 可导入的 CSV 格式。
    字段顺序: Front, Back, Tags
    """
    output = io.StringIO()
    writer = csv.writer(output)

    for card in cards:
        tags = card.get("concept", "408")
        writer.writerow([
            card["question"],
            card["answer"],
            f"408_{tags}",
        ])

    return output.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
#  旧版兼容：读取原来 data/exams/错题本/ 目录中的 JSON 文件
# ═══════════════════════════════════════════════════════════════════════════

def import_old_mistakes():
    """
    将旧版错题本目录（data/exams/错题本/）中的 JSON 文件导入到新版存储。
    幂等：已导入的条目不会重复添加（基于 question 去重）。
    """
    if not os.path.isdir(MISTAKE_BOOK_DIR_OLD):
        return 0

    existing = _load_data()
    existing_questions = {d.get("question", "")[:100] for d in existing}

    count = 0
    for fname in sorted(os.listdir(MISTAKE_BOOK_DIR_OLD)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(MISTAKE_BOOK_DIR_OLD, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                entry = json.load(f)

            question = entry.get("question", "")
            if question[:100] in existing_questions:
                continue

            item = MistakeItem(
                question=question,
                answer=entry.get("answer", ""),
                user_answer=entry.get("user_answer", ""),
                source=entry.get("source", "旧版错题本"),
                subject=_classify_subject(
                    entry.get("knowledge_point", "") or entry.get("topic", ""),
                    question,
                ),
                topic=entry.get("knowledge_point", "") or entry.get("topic", ""),
                type="错题",
            )
            existing.append(item.model_dump())
            existing_questions.add(question[:100])
            count += 1
        except Exception as e:
            logger.warning("导入旧版错题失败 %s: %s", fname, e)

    if count > 0:
        _save_data(existing)
        logger.info("[migrate] 导入了 %d 条旧版错题", count)

    return count
