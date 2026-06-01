# 408 RAG — 计算机考研知识库问答系统

基于 RAG（检索增强生成）的 408 计算机考研辅导助手。支持 PDF、Markdown、纯文本资料的自动导入、向量化存储和智能问答。

**架构**：后端 FastAPI + 前端 React (Vite)

## 快速开始

### 1. 后端

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key
# 创建 .env 文件，写入：
#   DEEPSEEK_API_KEY=your_deepseek_key
#   DASHSCOPE_API_KEY=your_dashscope_key_for_vision

# 将备考资料放入 data/ 目录
# 目录结构示例：
# data/
#   textbooks/   → 教材
#   outline/     → 考试大纲
#   exams/       → 历年真题
#   notes/       → 笔记
#   minds/       → 思维导图

# 构建向量库
python ingest.py

# 启动 FastAPI 后端
uvicorn server:app --reload --port 8000
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

打开浏览器访问 `http://localhost:5173`

### 3. 命令行（旧接口仍可用）

```bash
# 提问
python qa.py "简述虚拟内存的实现原理"

# 考情分析
python analysis.py

# 练习
python calculation_practice.py cache_hit
python comprehensive_practice.py os_pv_producer_consumer
```

## 特性

### 检索层

| 特性 | 说明 | 开关 |
|------|------|------|
| 混合检索 | 向量检索 (top 20) + BM25 关键词检索 (top 10)，合并去重 | 始终启用 |
| Cross-Encoder 重排序 | 使用 `cross-encoder/ms-marco-MiniLM-L-6-v2` 重排序，取 top 10 | `ENABLE_RERANK` |
| 父文档扩展 | 检索小块后，向上查找所属的完整段落（同一 doc_id 的相邻 chunk） | `ENABLE_PARENT_EXPANSION` |
| 查询重写 | 复杂问题拆分为最多 3 个子问题分别检索后合并 | `ENABLE_QUERY_REWRITE` |
| 核心概念强制召回 | 命中 CORE_CONCEPTS 时追加关键词检索并加权 | 始终启用 |

### 生成层

| 特性 | 说明 |
|------|------|
| 人设"高分学长" | 直击核心风格：直接给出结论与结构化分析 |
| 专题深度总结 | 触发词（比较/异同/区别等）自动启用五段式模板 |
| 链式推理 (CoT) | 「提取知识点 → 分析关联 → 综合回答」三步推理 |
| 分层可信度回答 | 高置信度（基于资料） / 核心概念增强 / 知识库回退 + 免责 |
| 图片问答 | 千问视觉模型识别图片，DeepSeek 修复公式乱码 |
| 记忆力注入 | 薄弱知识点（评分≤2）自动提示 LLM 针对性讲解 |

**专题深度总结触发词：** `比较`、`异同`、`区别`、`联系`、`综合`、`实现原理`、`设计思想`、`演变`、`优缺点`

### 练习模块

| 模块 | 题型数 | 覆盖科目 |
|------|--------|----------|
| 计算专项 | 8 类 | 计组(3) / 操作系统(4) / 计网(1) |
| 大题专项 | 17 类 | 数据结构(3) / 计组(4) / 操作系统(8) / 计网(2) |

### 工程

- **增量导入**：SHA256 缓存，仅处理新增/修改的文件
- **按源更新**：修改文件后仅重建该文件对应的向量块
- **前后端分离**：FastAPI REST API + React 前端
- **跨域支持**：CORS 中间件 + Vite 开发代理
- **Windows 兼容**：自动处理 GBK 编码问题
- **错题本与薄弱点管理**：一键保存错题/标记薄弱点，智能分类统计，同类题生成，Q&A 概念卡片导出

## 项目结构

```
408RAG/
├── server.py              # FastAPI 后端服务（RESTful API）
├── qa.py                  # 问答模块（检索 + LLM 生成）
├── ingest.py              # 资料导入与分块向量化
├── analysis.py            # 考情分析模块
├── calculation_practice.py# 计算题专项练习（8 类题型）
├── comprehensive_practice.py # 大题专项练习（17 类题型）
├── vision.py              # 图片问答（千问视觉模型）
├── memory.py              # 记忆力模块（掌握度追踪）
├── mistake_book.py        # 错题本与薄弱点管理模块
├── config.py              # 配置文件
├── requirements.txt       # Python 依赖
├── frontend/              # React 前端
│   ├── src/
│   │   ├── api/client.js  # API 客户端（所有接口封装）
│   │   ├── components/
│   │   │   ├── MistakeSummary.jsx   # 错题统计摘要
│   │   │   ├── SimilarQuestion.jsx  # 同类题生成
│   │   │   └── ConceptCards.jsx     # Q&A 概念卡片
│   │   ├── pages/
│   │   │   ├── ChatPage.jsx    # 聊天页面
│   │   │   ├── PracticePage.jsx# 练习页面
│   │   │   ├── MistakePage.jsx # 错题本管理页面
│   │   │   └── DataPage.jsx    # 数据管理页面
│   │   ├── App.jsx         # 路由 + 导航栏
│   │   ├── index.css       # 全局样式
│   │   └── main.jsx        # 入口
│   ├── vite.config.js      # 构建配置 + API 代理
│   └── package.json
├── data/                   # 原始备考资料
│   ├── textbooks/          # 教材
│   ├── outline/            # 考试大纲
│   ├── exams/              # 历年真题（23 份）
│   ├── notes/              # 笔记
│   └── minds/              # 思维导图
├── data_output/            # 向量库与缓存
│   ├── chroma_db/          # Chroma 向量数据库（~2900+ 块）
│   └── ingest_cache.json
└── models/                 # 本地 Embedding/Reranker 模型
```

## API 接口一览

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/chat` | POST | 文本问答 |
| `/api/chat/image` | POST | 图片问答（上传图片） |
| `/api/practice/calculation` | GET | 生成计算题 |
| `/api/practice/calculation/list` | GET | 计算题题型列表 |
| `/api/practice/comprehensive` | GET | 生成大题 |
| `/api/practice/comprehensive/list` | GET | 大题题型列表 |
| `/api/ingest` | POST | 上传资料并导入向量库 |
| `/api/analyze` | POST | 考情分析生成报告 |
| `/api/mistake_book` | GET/POST | 错题本管理 |
| `/api/mistake_book` | GET/POST | 错题本管理（旧接口） |
| `/api/mistake/add` | POST | 添加错题或薄弱点 |
| `/api/mistake/list` | GET | 错题列表（支持按类型/科目/知识点筛选） |
| `/api/mistake/{id}` | DELETE | 删除指定条目 |
| `/api/mistake/export` | POST | 导出为 Markdown/PDF |
| `/api/mistake/summary` | GET | 分类统计信息 |
| `/api/mistake/similar` | POST | 基于知识点生成同类题 |
| `/api/mistake/cards` | POST | 生成 Q&A 概念卡片 |
| `/api/mistake/cards/export` | GET | 导出概念卡片（Markdown/Anki CSV） |
| `/api/health` | GET | 健康检查 |

## 配置

所有可调参数在 `config.py` 中，关键参数：

```python
ENABLE_RERANK = True           # Cross-encoder 重排序
ENABLE_QUERY_REWRITE = True    # 查询重写
ENABLE_PARENT_EXPANSION = True # 父文档扩展
VECTOR_TOP_K = 20              # 向量检索数量
BM25_TOP_K = 10                # BM25 检索数量
RERANK_TOP_K = 10              # 重排序后保留数量
CHUNK_SIZE = 256               # 分块大小（字符）
```
