"""快速验证：import 所有模块确认路径引用正确。"""
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

errors = []

# 1. 验证 config
try:
    import config
    assert config.API_BASE == "https://api.deepseek.com/v1", "API_BASE"
    assert os.path.isdir(config.OUTPUT_DIR), f"OUTPUT_DIR 不存在: {config.OUTPUT_DIR}"
    assert os.path.isdir(config.PERSIST_DIR), f"PERSIST_DIR 不存在: {config.PERSIST_DIR}"
    assert os.path.isdir(config.DATA_DIR), f"DATA_DIR 不存在: {config.DATA_DIR}"
    assert os.path.isfile(config.CACHE_FILE), f"CACHE_FILE 不存在: {config.CACHE_FILE}"
    print(f"[OK] config — EMBED_MODEL={os.path.basename(config.EMBED_MODEL)}, VECTOR_TOP_K={config.VECTOR_TOP_K}")
except Exception as e:
    errors.append(f"config: {e}")

# 2. 验证 ingest（仅 import，不执行 main）
try:
    from ingest import compute_sha256, collect_files, load_documents
    print("[OK] ingest — 函数导入成功")
except Exception as e:
    errors.append(f"ingest: {e}")

# 3. 验证 qa
try:
    from qa import ask, SYSTEM_PROMPT
    print("[OK] qa — ask() 可导入")
except Exception as e:
    errors.append(f"qa: {e}")

# 4. 验证 analysis
try:
    from analysis import extract_year, build_subject_corpora
    assert extract_year("2024计算机408真题.pdf") == 2024
    print("[OK] analysis — extract_year() 正确")
except Exception as e:
    errors.append(f"analysis: {e}")

# 5. 验证 main
try:
    from main import COMMANDS
    assert set(COMMANDS.keys()) == {"ingest", "ask", "analyze"}
    print("[OK] main — 3个子命令就绪")
except Exception as e:
    errors.append(f"main: {e}")

# 6. 验证关键文件存在
checks = [
    ("docs/README.md", os.path.isfile("docs/README.md")),
    ("docs/PROGRESS.md", os.path.isfile("docs/PROGRESS.md")),
    ("data_output/report_2026.md", os.path.isfile("data_output/report_2026.md")),
    ("data_output/chroma_db/", os.path.isdir("data_output/chroma_db")),
    (".env", os.path.isfile(".env")),
]
for name, ok in checks:
    status = "[OK]" if ok else "[MISS]"
    print(f"{status} 文件检查 — {name}")
    if not ok:
        errors.append(f"缺少文件: {name}")

# ── 总结 ──
print(f"\n{'='*40}")
if errors:
    print(f"FAIL — {len(errors)} 个错误:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("全部通过 — 项目结构正确，所有 import 无报错。")
