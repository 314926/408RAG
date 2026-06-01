"""408 考研知识库 — 统一命令行入口。

用法：
    python main.py ingest          导入资料到向量库
    python main.py ask "问题"      检索并回答问题
    python main.py analyze         生成考情分析报告
"""

import sys

import config

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def cmd_ingest():
    """导入资料：扫描 data/ 下所有文件，分块后写入 ChromaDB"""
    from ingest import main as ingest_main
    ingest_main()


def cmd_ask():
    """检索问答：传入问题，检索向量库后调用 DeepSeek 回答"""
    if len(sys.argv) < 3:
        print("用法: python main.py ask \"你的问题\"")
        sys.exit(1)

    question = sys.argv[2]
    from qa import ask
    answer, sources = ask(question)
    print(answer)
    if sources:
        print(f"\n── 参考来源 ──")
        for s in sources:
            print(f"  - {s}")


def cmd_analyze():
    """考情分析：基于 exams 真题生成 report_2026.md"""
    from analysis import main as analysis_main
    analysis_main()


def usage():
    print(__doc__)


COMMANDS = {
    "ingest": cmd_ingest,
    "ask": cmd_ask,
    "analyze": cmd_analyze,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        usage()
        sys.exit(1)

    if not config.API_KEY:
        print("错误: 请设置 DEEPSEEK_API_KEY 环境变量或在 .env 文件中配置", file=sys.stderr)
        sys.exit(1)

    cmd = COMMANDS[sys.argv[1]]
    cmd()
