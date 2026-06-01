# 项目日志

## 2026-06-02 — 错题本与薄弱点追踪 + 智能复习功能

### 新增功能

**错题本与薄弱点管理**（后端 `mistake_book.py` + 前端 `MistakePage.jsx`）

- 新建 `mistake_book.py` 模块：Pydantic 数据模型、JSON 文件 CRUD、Markdown/PDF 导出、分类统计、同类题生成、Q&A 概念卡片生成
- 存储方式：`data_output/mistake_data.json`，结构化存储错题/薄弱点条目
- 新增 8 个 RESTful API（`/api/mistake/*`）：添加、列表（筛选）、删除、导出、统计、同类题、卡片生成、卡片导出
- 导出功能：Markdown 按科目题型分组，薄弱点 ⚠️ 高亮标记，错题 ❌ 标记；PDF 通过 markdown→HTML→weasyprint（优雅降级）
- 分类统计：按知识点标签聚合，生成高频薄弱点列表
- 同类题生成：优先从 `/data/exercise` 练习题库检索匹配题目，回退到 LLM 生成
- 概念卡片：LLM 生成问答对，支持 Markdown 表格 / Anki CSV 格式导出

**前端错题本管理页面**

- 新建 `MistakePage.jsx`：四选项卡布局（题目列表 / 统计摘要 / 同类题 / 概念卡片）
- 列表视图：按类型/科目/知识点筛选，全选批量导出 Markdown/PDF
- 统计摘要：概览卡片 + 知识点表格（高频热点标记 🔥）
- 同类题生成：输入知识点，生成同类题，可折叠查看答案
- 概念卡片：输入概念列表，生成 Q&A 卡片，一键导出 Anki/Markdown
- 快速选择按钮：预设常用知识点/概念组合

**聊天页面改动**（`ChatPage.jsx`）

- 每条 AI 回答下方增加两个按钮：「❌ 加入错题本」「⚠️ 标记薄弱点」
- 点击弹出表单：自动填入当前问题/答案，支持编辑科目、知识点标签
- 科目自动识别：基于文本关键词匹配 DS/CO/OS/CN

**练习页面改动**（`PracticePage.jsx`）

- 题目展示区下方增加「❌ 加入错题本」「⚠️ 标记薄弱点」按钮
- 自动预填题目、答案、科目、题型信息

**导航与路由**

- 导航栏新增「📖 错题本」入口，路由指向 `/mistakes`

**练习题库集成**

- `mistake_book.py` 中实现 `_load_exercise_questions()` 函数，解析 `/data/exercise` 目录下的选择题 PDF 文本
- `generate_similar_question()` 优先从题库检索匹配知识点，回退 LLM 生成

### 新增/修改文件一览

| 文件 | 变更 |
|------|------|
| `mistake_book.py` | ✨ 新建（891行） |
| `server.py` | 🔧 新增 8 个 API接口 |
| `config.py` | 🔧 添加 MISTAKE_DATA_FILE / EXERCISE_DIR |
| `frontend/src/api/client.js` | 🔧 新增 8 个 API 函数 |
| `frontend/src/pages/MistakePage.jsx` | ✨ 新建 |
| `frontend/src/pages/MistakePage.css` | ✨ 新建 |
| `frontend/src/components/MistakeSummary.jsx` | ✨ 新建 |
| `frontend/src/components/SimilarQuestion.jsx` | ✨ 新建 |
| `frontend/src/components/ConceptCards.jsx` | ✨ 新建 |
| `frontend/src/pages/ChatPage.jsx` | 🔧 新增错题/薄弱点按钮+表单弹窗 |
| `frontend/src/pages/PracticePage.jsx` | 🔧 新增错题/薄弱点按钮+表单弹窗 |
| `frontend/src/App.jsx` | 🔧 新增路由和导航 |
| `frontend/src/index.css` | 🔧 新增模态框/弹窗全局样式 |
| `frontend/src/pages/PracticePage.css` | 🔧 新增错题按钮样式 |
| `README.md` | 📝 更新项目结构和API表格 |

### 验证

- [x] 后端语法检查通过（`mistake_book.py`、`server.py`）
- [x] 后端语法检查通过（`config.py`）

# 项目日志

## 2026-06-01 — 代码清理（P0-2 / P0-6）

### 修改内容

**优化：移除 qa.py 中未使用的 `_compute_avg_relevance` 死代码函数**
- 该函数在第 323-333 行定义，全项目无任何调用
- 安全移除，不影响任何业务逻辑

**优化：清理 analysis.py 中未使用的 `defaultdict` 导入**
- `from collections import defaultdict` 已导入但实际未使用
- 函数内使用普通 dict 字面量 `{s: [] for s in ...}`，移除后无影响

**优化：删除根目录下 26 个临时文件**
- `_*.py` x4: `_check_metric.py`、`_diagnose.py`、`_patch_config.py`、`_test_questions.py`
- `_*.txt` x21: 测试输出 / 调试记录 / 环境检查等临时文本
- `_*.log` x1: `_test2.log`
- 创建 `.gitignore` 添加 `_*.py`、`_*.txt`、`_*.log` 规则，防止未来再次提交

### 验证结果

- [x] `qa.py` 语法检查通过
- [x] `analysis.py` 语法检查通过
- [x] `app.py` 语法检查通过
- [x] 临时文件已全部删除，根目录整洁
- [x] `.gitignore` 已创建并生效

## 2026-05-22 — RAG 知识库优化 + OCR 支持

### 目标

充分利用 data/minds/（思维导图）和 data/notes/（大题资料）的专题资料，提升 408 考研知识库回答的结构性和深度。

### 修改文件

#### `config.py` — 新增分类分块与检索增强配置

- `MINDMAP_CHUNK_SIZE = 1500`（思维导图 .md 分块大小）
- `COMPREHENSIVE_CHUNK_SIZE = 2000`（大题资料 Q&A 对分块大小）
- `MINDS_DIR = "minds"` / `NOTES_DIR = "notes"`
- `COMPREHENSIVE_BOOST = 1.5`（触发总结模式时 comprehensive 文档的权重倍数）
- `MINDMAP_EXTRA_K = 2`（触发后额外检索的思维导图片段数）

#### `ingest.py` — 分类分块与元数据标记

- **MarkdownHeaderTextSplitter**：minds/ 目录下 .md 文件按 `##`/`###` 标题拆分，chunk_size=1500，超长段二次细拆分
- **Q&A 格式检测**：`detect_qa_format()` 支持英文 `Q:/A:` 和中文字 `【题目】/【解析】`、`题目：/答案：` 等模式
- **Q&A 保持完整**：`split_qa_pairs()` 按题目边界拆分，保持每个 Q&A 对完整，超长时在 A: 处截断
- **元数据标记**：
  - minds/ 文件 → `category=mindmap` + `subject`（从文件名提取科目名）
  - notes/ Q&A 文件 → `type=comprehensive`
- **空页过滤**：自动跳过 PDF 文本提取为空的页面，输出 `⚠ 警告` 日志
- **零块保护**：文件分块为 0 时保留旧向量不删除（增量更新安全）

#### `qa.py` — 检索增强 + 上下文排序 + SQLite 兼容

- **触发词检测**：`_detect_triggers()` 检查问题是否包含 config.SUMMARIZE_TRIGGERS 关键词
- **思维导图额外检索**：`_fetch_mindmap_chunks()` 带 filter 回退的 mindmap 专用检索
- **权重增强**：comprehensive 文档分数 ×1.5，额外注入 mindmap 片段
- **上下文排序**：触发后 mindmap 片段排最前（知识框架），然后是普通资料和大题示例
- **上下文标签**：mindmap → `[知识框架（思维导图）]`，comprehensive → `[综合性大题示例]`
- **SYSTEM_PROMPT 更新**：引导 LLM 根据思维导图梳理知识结构，借鉴大题推理路径
- **SQLite 兼容**：`_build_bm25_index` 和 `expand_parent_chunks` 改为分批获取（500 条/批），解决 2400+ 块触发的 "too many SQL variables" 错误

#### `ocr_helper.py` — 新增 OCR 辅助脚本

- 扫描版/图片型 PDF 文本提取（PyMuPDF 渲染 + Tesseract OCR）
- 自动检测可提取文本的 PDF 并跳过（`can_extract_text`）
- 自动缩放超大图片防止 Leptonica 溢出（MAX_DIM=3600）
- 三种模式：默认 200 DPI / `--fast` 150 DPI / `--quality` 300 DPI
- Tesseract 配置：快速模式 `--psm 6 --oem 1`，质量模式 `--psm 3 --oem 3`
- 支持 `--workers N` 多 PDF 并行（ProcessPoolExecutor）
- 支持 `--page-workers N` 单文件多页并行（ThreadPoolExecutor）
- 增量处理：已有 .txt 的文件自动跳过；`--dry-run` 预览模式
- 输出 .txt 与源 PDF 同目录，ingest.py 可自动导入

### 已知问题

- **minds/ 无 .md 文件**：MarkdownHeaderTextSplitter 路径未触发，当前仅 PDF/OCR 文本。思维导图建议导出为 .md 格式以充分利用标题级分块
- **notes/ Q&A 检测未命中**：OCR 后的 .txt 文件为纯文本流，无结构化 Q:/A: 标记，走默认分块。如需 Q&A 保留，需手动整理格式

### 最终数据

| 类别 | 文件数 | 分块数 |
|------|--------|--------|
| minds/（思维导图） | 4 PDF + 2 OCR .txt | ~200 |
| notes/（大题资料） | 14 PDF + N OCR .txt | ~550 |
| exams/（真题） | 23 PDF | ~1,900 |
| textbooks/（教材） | 10 PDF + N OCR .txt | ~250 |
| outline/（大纲） | 1 PDF | 0（图片型） |
| **合计** | **~60+** | **~2,900+** |

### 验证结果

- [x] OCR 全部扫描版 PDF 完成，.txt 已导入
- [x] 跨科问题「虚拟内存从硬件支持到软件管理的完整流程」测试通过
  - 检索触发查询重写（3 个子问题：MMU/TLB 硬件 → OS 地址映射/缺页 → 软硬协同）
  - 回答展示三层结构：硬件地址转换 → OS 缺页处理 → Cache 对比表格
  - mindmap 和 notes 来源均被引用，知识框架标记生效
- [ ] 后续优化方向：将思维导图导出 .md 格式以启用 MarkdownHeaderTextSplitter
