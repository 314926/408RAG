"""Run QA tests and write results to file."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
# Try HF mirror first
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from qa import ask

test_questions = [
    "简述虚拟内存的实现原理，并说明其与Cache的异同",
    "分析快速排序在基本有序数组上的性能，并给出优化方法",
    "红烧肉的做法",
]

with open("D:/408RAG/test_results.txt", "w", encoding="utf-8") as f:
    for q in test_questions:
        f.write(f"{'='*60}\n")
        f.write(f"问题: {q}\n")
        f.write(f"{'='*60}\n\n")
        try:
            answer, sources = ask(q)
            f.write(f"回答:\n{answer}\n\n")
            if sources:
                f.write(f"参考来源:\n")
                for s in sources:
                    f.write(f"  - {s}\n")
        except Exception as e:
            f.write(f"ERROR: {e}\n")
            import traceback
            traceback.print_exc(file=f)
        f.write("\n\n")

print("Test results written to test_results.txt")
