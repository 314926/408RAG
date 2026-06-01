# 408 考研知识库

基于个人备考资料的 RAG 知识库系统，所有回答严格来源于你提供的资料（教材、真题、笔记、考纲），不引入任何外部知识。

## 环境要求

- Python 3.10+
- 有效的 DeepSeek API Key（[获取地址](https://platform.deepseek.com/api_keys)）

## 安装

```bash
pip install -r requirements.txt
```

## 配置 API Key

在项目根目录创建 `.env` 文件：

```
DEEPSEEK_API_KEY=sk-你的key
```

或直接设置环境变量：

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-你的key"

# Linux / Mac
export DEEPSEEK_API_KEY="sk-你的key"
```

## 使用步骤

### 1. 放入资料

将你的备考资料按分类放入 `data/` 对应子目录：

```
data/
├── outline/      # 考纲 PDF
├── textbooks/    # 教材 PDF
├── exams/        # 真题 PDF
└── notes/        # 笔记 PDF / MD / TXT
```

### 2. 导入资料到向量库

```bash
python main.py ingest
```

首次运行会处理所有文件并构建向量索引，后续只会处理新增或修改的文件（增量更新）。

### 3. 提问

```bash
python main.py ask "快速排序的时间复杂度是多少？"
```

回答严格基于你的资料，末尾注明引用来源。如果资料中无相关信息，会明确告诉你"无法回答"。

### 4. 生成考情分析

```bash
python main.py analyze
```

基于历年真题自动生成 `report_2026.md`，包含四科高频考点 Top10、近 3 年趋势、2026 出题方向与冷门提醒。

## 项目结构

```
408RAG/
├── main.py                    # 统一入口
├── ingest.py                  # 资料导入（PDF→分块→向量库）
├── qa.py                      # 检索问答
├── analysis.py                # 考情分析报告生成
├── config.py                  # 集中配置（模型/分块/检索参数）
├── requirements.txt           # Python 依赖
├── .env                       # API Key（不入版本控制）
├── .env.example               # 环境变量说明模板
├── chroma_db/                 # ChromaDB 向量库（自动生成）
├── ingest_cache.json          # 增量导入缓存（自动生成）
├── models/                    # 本地 Embedding 模型
├── data/                      # 备考资料
│   ├── outline/               # 考纲
│   ├── textbooks/             # 教材
│   ├── exams/                 # 真题
│   └── notes/                 # 笔记
└── report_2026.md             # 考情分析报告（analyze 后生成）
```

## 技术栈

| 组件 | 技术 |
|---|---|
| LLM | DeepSeek Chat（API） |
| Embedding | BGE-small-zh-v1.5（本地 CPU） |
| 向量库 | ChromaDB |
| 文档加载 | LangChain PyPDFLoader / TextLoader |
| 文本分割 | RecursiveCharacterTextSplitter（256 字符/块，64 字符重叠） |
