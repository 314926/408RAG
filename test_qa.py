"""测试 qa.py 的回答风格"""
import sys
import os

# 确保输出不被缓冲
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["PYTHONUNBUFFERED"] = "1"

from qa import ask

test_questions = [
    "简述虚拟内存的实现原理，并说明其与Cache的异同",
    "数组和链表有哪些区别",
]

log_lines = []
for q in test_questions:
    log_lines.append(f"\n{'='*60}")
    log_lines.append(f"问题: {q}")
    log_lines.append(f"{'='*60}")

    # 检查触发词
    import config
    triggers_hit = [t for t in config.SUMMARIZE_TRIGGERS if t in q]
    log_lines.append(f"命中触发词: {triggers_hit}")

    try:
        answer, sources = ask(q)
        log_lines.append(f"\n回答:\n{answer}")
        log_lines.append(f"\n来源: {', '.join(sources) if sources else '无'}")
    except Exception as e:
        log_lines.append(f"\n错误: {e}")

# 写入日志文件
log_text = "\n".join(log_lines)
with open("test_output.log", "w", encoding="utf-8") as f:
    f.write(log_text)

# 同时输出到控制台
print(log_text)
