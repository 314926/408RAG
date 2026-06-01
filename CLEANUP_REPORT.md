# CLEANUP_REPORT.md — 408RAG 代码清理审计报告

> 审计日期: 2026-05-22 | 涉及文件: 12 个 .py 文件

---

## 一、问题总览

| 级别 | 数量 | 说明 |
|------|------|------|
| 🔴 严重 (Bug) | 1 | 运行时功能异常 |
| 🟡 警告 (Dead Code) | 4 | 未使用导入/参数/变量 |
| 🟢 建议 (改进) | 3 | 代码质量优化 |

---

## 二、🔴 严重问题

### BUG-1: app.py `_do_ingest()` 缺少 doc_id / chunk_index 元数据

- **位置**: `app.py` 第 144-155 行 (`_do_ingest()` 函数)
- **问题**: Streamlit 侧边栏上传文件后，向量块的 metadata 中缺少 `doc_id` 和 `chunk_index` 字段。
- **对比**: `ingest.py` 第 153-158 行在写入前正确设置了这两个字段：

  ```python
  # ingest.py (正确)
  for chunk_idx, chunk in enumerate(source_chunks):
      chunk.metadata["doc_id"] = doc_id_from_path(
          os.path.join(config.DATA_DIR, source)
      )
      chunk.metadata["chunk_index"] = chunk_idx
  ```

  而 `app.py` 的 `_do_ingest()` 直接使用了 `load_documents()` 返回的 metadata（仅有 source、category），没有补充 `doc_id` 和 `chunk_index`。

- **影响范围**: `qa.py` 的 `expand_parent_chunks()` 函数依赖这两个字段来定位相邻块。通过 Streamlit 上传的文档在父文档扩展时会**静默失败**（每个块的 doc_id 为空字符串，chunk_index 为 -1，扩展逻辑被跳过）。检索不会报错，但扩展功能对这部分文档无效。
- **修复建议**: 在 `app.py` 的 `_do_ingest()` 中，参照 `ingest.py` 的写法，为每个 chunk 补充 metadata。同时建议导入 `ingest.doc_id_from_path` 复用逻辑。
- **是否影响现有功能**: ✅ 是，影响 Streamlit 上传路径的父文档扩展

---

## 三、🟡 警告问题

### WARN-1: qa.py `ask()` 的 `k` 参数是死代码

- **位置**: `qa.py` 第 292-299 行
- **问题**: `ask()` 接受 `k` 参数并默认取 `config.TOP_K`，但该值从未传递给任何检索函数。实际检索数量由 `config.VECTOR_TOP_K`、`config.BM25_TOP_K`、`config.RERANK_TOP_K` 分别控制。
- **代码**:
  ```python
  def ask(question: str, k: int = None, memory: ...) -> tuple[str, list[str]]:
      if k is None:
          k = config.TOP_K       # ← 赋值后再无引用
      ...
  ```
- **修复建议**: 移除 `k` 参数，或将其传递给 `retrieve()` / `rerank()` 使其生效。
- **是否影响现有功能**: ❌ 否，仅死代码

### WARN-2: analysis.py 未使用的导入 `Counter`

- **位置**: `analysis.py` 第 5 行
- **问题**: `from collections import defaultdict, Counter` — `Counter` 在整个文件中从未使用。
- **修复建议**: 改为 `from collections import defaultdict`
- **是否影响现有功能**: ❌ 否

### WARN-3: analysis.py 未使用的导入 `Path`

- **位置**: `analysis.py` 第 6 行
- **问题**: `from pathlib import Path` — `Path` 在整个文件中从未使用。（注：`ingest.py` 使用了 `Path`，但 analysis.py 不需要）
- **修复建议**: 删除该行
- **是否影响现有功能**: ❌ 否

### WARN-4: app.py 未使用的导入 `sys`

- **位置**: `app.py` 第 6 行
- **问题**: `import sys` — `sys` 在 `app.py` 中没有任何引用。
- **修复建议**: 删除该行
- **是否影响现有功能**: ❌ 否

---

## 四、🟢 改进建议

### IMP-1: config.py `TOP_K` 配置项形同虚设

- **位置**: `config.py` 第 27 行
- **问题**: `TOP_K = 10` 只在 `qa.py` 的 `ask()` 中被读取一次，但从未实际使用。检索量由 `VECTOR_TOP_K`(20)、`BM25_TOP_K`(10)、`RERANK_TOP_K`(10) 分别控制。`TOP_K` 的存在容易让维护者误以为它是统一的检索数量上限。
- **建议**: 
  - 如果确实不需要统一控制，删除 `TOP_K` 并同步清理 `qa.py` 的 `k` 参数（见 WARN-1）。
  - 如果需要统一控制，将其传入 `retrieve()` 覆盖各阶段参数。

### IMP-2: ingest.py 与 app.py 的导入逻辑高度重复

- **位置**: `ingest.py` 第 98-177 行 `main()` vs `app.py` 第 116-161 行 `_do_ingest()`
- **问题**: 两处有 ~60 行几乎相同的代码（初始化 embeddings、splitter、vectorstore、分组写入、缓存更新），差异仅在于 `app.py` 多了一个空列表检查。这增加了维护成本 — BUG-1 正是由此产生。
- **建议**: 将 ingest 核心逻辑提取为 `ingest.py` 中的 `run_ingest(files_to_process)` 公共函数，`main()` 和 `_do_ingest()` 都调用它。

### IMP-3: test_qa.py / run_qa_test.py 功能重叠

- **位置**: `test_qa.py`（刚创建）和 `run_qa_test.py` 都是测试 qa.py 的脚本
- **问题**: 两个文件做了类似的事情（调用 ask() 并输出结果），`test_qa.py` 额外检查了触发词命中情况。
- **建议**: 合并为一个测试脚本，或删除旧的 `run_qa_test.py`。

---

## 五、无问题确认清单

以下文件经过审查，未发现代码问题：

| 文件 | 审查结论 |
|------|----------|
| `config.py` | ✅ 所有变量均被引用，无冗余 |
| `memory.py` | ✅ 代码简洁清晰，无问题 |
| `main.py` | ✅ 仅有的 `config` import 用于 API_KEY 校验 |
| `ingest.py` | ✅ 逻辑正确；`from collections import defaultdict` 在 main() 内局部导入，属合理用法 |
| `download_reranker.py` | ✅ 工具脚本，无问题 |
| `check_meta.py` | ✅ 工具脚本，无问题 |
| `quick_check.py` | ✅ 检查脚本，引用的 `docs/README.md`、`docs/PROGRESS.md` 建议确认是否存在 |

---

## 六、修复优先级建议

```
1. [立即] BUG-1: 修复 app.py _do_ingest() 缺少元数据   ← 影响功能正确性
2. [本PR] WARN-1~4: 清理死代码和未使用导入             ← 零风险，顺手清理
3. [后续] IMP-1~3: 重构优化                           ← 需测试，可单独 PR
```

---

## 七、修改安全确认

以下修改**不会**影响现有检索逻辑和 Streamlit 前端：

| 修改项 | 影响检索？ | 影响前端？ | 理由 |
|--------|-----------|-----------|------|
| BUG-1 修复: 补充 doc_id/chunk_index | ❌ 不影响核心检索 | ❌ 不影响前端 | 仅补充元数据，扩展功能受益 |
| 删除 analysis.py 的 Counter/Path import | ❌ 不影响 | ❌ 不影响 | 纯未使用导入 |
| 删除 app.py 的 sys import | ❌ 不影响 | ❌ 不影响 | 纯未使用导入 |
| 删除 qa.py ask() 的 k 参数 | ❌ 不影响 | ❌ 不影响 | 参数从未生效 |
| 删除 config.TOP_K | ❌ 不影响 | ❌ 不影响 | 从未实际控制检索 |
