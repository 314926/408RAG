import base64
import mimetypes
import sys

from openai import OpenAI

import config

VISION_SYSTEM_PROMPT = (
    "你是一位专业的408计算机考研题目分析助手。"
    "请详细描述图片中的内容，严格按以下格式输出：\n\n"
    "1. 题目文字：完整摘录题干、选项、问题要求等文字内容\n"
    "2. 图表信息：描述示意图、流程图、状态转换图、数据结构图等视觉元素\n"
    "   - 树/图结构用「节点→边」方式描述，保留层次关系，如：\n"
    "     · 根节点A → 左子节点B → 左子节点D\n"
    "     · 根节点A → 右子节点C\n"
    "3. 公式符号：所有数学公式必须用LaTeX格式输出（如 $O(n^2)$、$\\frac{a}{b}$、$\\sum_{i=1}^{n}$）\n"
    "4. 代码块：所有代码用```包裹并注明语言（如```c、```python）\n"
    "5. 表格：用Markdown表格格式输出\n"
    "6. 题目类型：判断这是选择题、简答题、综合应用题还是其他类型\n\n"
    "请用清晰的中文输出，确保不遗漏任何关键信息。"
)

MULTI_IMAGE_PROMPT = (
    "你是一位专业的408计算机考研题目分析助手。"
    "请对比分析以下多张图片，如果包含题目和答案/解析，请：\n"
    "1. 先完整摘录题目内容（题干、选项、问题要求）\n"
    "2. 再摘录答案/解析内容，指出答案的得分要点和关键步骤\n"
    "3. 如果是多道题，逐一分析每道题\n\n"
    "格式要求：\n"
    "- 数学公式用LaTeX格式（如 $O(n^2)$、$\\frac{a}{b}$）\n"
    "- 代码用```包裹并注明语言\n"
    "- 表格用Markdown表格\n"
    "- 树/图结构用「节点→边」方式描述，保留层次关系\n\n"
    "请用清晰的中文输出。"
)

POLISH_PROMPT = (
    "你是一个408计算机考研公式修复助手。请修复以下文本中的公式和术语错误：\n"
    "1. 将OCR乱码的公式还原为正确的LaTeX格式（如 0(n2) → $O(n^2)$、log2n → $\\log_2 n$、"
    "n2 → $n^2$、2^n → $2^n$）\n"
    "2. 补全408常见术语的缩写或错别字（如 LRU、FIFO、TLB、PCB、DMA、CISC/RISC、"
    "cache、页表、缺页、快表、Cache行、组相联、全相联、直接映射等）\n"
    "3. 保持原文结构和内容不变，只修复公式和术语\n"
    "4. 直接输出修复后的文本，不要加任何说明\n\n"
    "待修复文本：\n{raw_text}"
)


def _get_mime_type(image_path: str) -> str:
    """根据文件扩展名推断 MIME 类型。"""
    mime, _ = mimetypes.guess_type(image_path)
    return mime or "image/jpeg"


def image_to_base64(image_path: str) -> str:
    """读取图片文件并转为 base64 字符串（含 data URI 前缀）。"""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    mime = _get_mime_type(image_path)
    return f"data:{mime};base64,{data}"


def understand_image(image_paths: str | list[str]) -> str:
    """使用千问视觉模型理解图片内容，返回文字描述。

    Args:
        image_paths: 单个图片路径或路径列表。多图时进行联合对比分析。
    """
    if not config.VISION_API_KEY:
        raise RuntimeError(
            "未设置 DASHSCOPE_API_KEY 环境变量，无法使用视觉模型。"
            "请在 .env 文件中添加 DASHSCOPE_API_KEY=your_key"
        )

    if isinstance(image_paths, str):
        image_paths = [image_paths]

    client = OpenAI(
        api_key=config.VISION_API_KEY,
        base_url=config.VISION_BASE_URL,
    )

    # 构建图片内容列表
    image_contents = []
    for path in image_paths:
        image_b64 = image_to_base64(path)
        image_contents.append({
            "type": "image_url",
            "image_url": {"url": image_b64},
        })

    # 根据图片数量选择提示词和 token 预算
    is_multi = len(image_paths) > 1
    system_prompt = MULTI_IMAGE_PROMPT if is_multi else VISION_SYSTEM_PROMPT
    user_text = (
        f"请对比分析以下{len(image_paths)}张图片"
        if is_multi
        else "请详细描述图片中的408题目内容"
    )

    user_content = image_contents + [
        {"type": "text", "text": user_text},
    ]

    response = client.chat.completions.create(
        model=config.VISION_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        max_tokens=2048 if is_multi else 1024,
    )

    return response.choices[0].message.content


def polish_text(raw_text: str) -> str:
    """使用 DeepSeek V4 修复 OCR 识别结果中的公式乱码和术语错误。"""
    if not config.API_KEY:
        return raw_text

    client = OpenAI(
        api_key=config.API_KEY,
        base_url=config.API_BASE,
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": POLISH_PROMPT.format(raw_text=raw_text)},
        ],
        temperature=0,
        max_tokens=2048,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python vision.py <图片路径> [图片路径2 ...]", file=sys.stderr)
        sys.exit(1)

    paths = sys.argv[1:]
    description = understand_image(paths)
    print("── 原始识别结果 ──")
    print(description)
    print("\n── 修复后结果 ──")
    print(polish_text(description))
