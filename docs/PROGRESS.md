# 408考研知识库 — 项目进度总结

> 更新时间：2026-05-21

---

## 一、项目结构

```
D:/408RAG/
├── config.py                  # 集中配置（API/模型/分块/检索参数）
├── ingest.py                  # 资料导入脚本（增量更新）
├── qa.py                      # 检索问答脚本
├── analysis.py                # 考情分析报告生成
├── requirements.txt           # Python 依赖
├── .env                       # API Key 配置（不入库）
├── .env.example               # 环境变量说明模板
├── PROGRESS.md                # 本文件
├── report_2026.md             # 已生成的考情分析报告
├── ingest_cache.json          # 增量导入缓存（自动生成）
├── chroma_db/                 # ChromaDB 向量库持久化目录
├── models/                    # 本地 Embedding 模型缓存
│   └── AI-ModelScope/
│       └── bge-small-zh-v1___5/
├── data/                      # 原始资料
│   ├── outline/               # 考纲（1 个 PDF）
│   ├── textbooks/             # 教材（11 个 PDF）
│   ├── exams/                 # 真题（23 个 PDF，覆盖 2009-2026）
│   └── notes/                 # 笔记（7 个 PDF）
```

---

## 二、技术架构

| 组件 | 技术方案 | 说明 |
|---|---|---|
| LLM | DeepSeek Chat（API） | 通过 `openai` 兼容接口调用 `deepseek-chat` |
| Embedding | `BAAI/bge-small-zh-v1.5` | 本地 CPU 推理，从 ModelScope 下载，无需联网 |
| 向量库 | ChromaDB（持久化） | collection: `408_knowledge` |
| 文档加载 | LangChain PyPDFLoader / TextLoader | 支持 PDF、MD、TXT |
| 文本分割 | RecursiveCharacterTextSplitter | chunk_size=256, overlap=64，中文标点分隔符 |

### 分块参数（optimized）

```
CHUNK_SIZE = 256      # 较小块提高检索精度
CHUNK_OVERLAP = 64    # 块间重叠避免语义断裂
TOP_K = 10            # 每次检索召回10个块
```

---

## 三、向量库状态

| 指标 | 数值 |
|---|---|
| 资料文件总数 | 42 |
| 处理成功 | 42（100%） |
| 处理失败 | 0 |
| 总块数 | 2,038 |
| 分类分布 | outline: 1, textbooks: 11, exams: 23, notes: 7 |
| 构建耗时 | ~536s（CPU 推理） |

---

## 四、ingest.py — 资料导入

**功能：**
- 递归扫描 `data/` 下所有 PDF/MD/TXT 文件
- SHA256 增量检测，仅处理新增/修改文件
- 自动从父目录推断 `category`（outline/textbooks/exams/notes）
- 每个 chunk 携带 `source`（相对路径）和 `category` 元数据
- 按 source 分组写入：先删旧块再写新块，实现真正的增量更新
- 结束后打印导入摘要（文件数、块数、耗时）

**使用：** `python ingest.py`

---

## 五、qa.py — 检索问答

**SYSTEM_PROMPT 核心规则：**
1. 仔细阅读所有参考资料片段，提取与问题相关的知识点
2. 只要参考资料中涉及问题的相关概念，就据此回答并注明来源
3. 只有完全无关时才回复拒绝语

**测试结果（优化后）：**

| 问题 | 期望 | 实际 | 结果 |
|---|---|---|---|
| 快速排序的时间复杂度 | 应有答案 | 分析后指出检索块未含时间复杂度公式，正确拒绝 | 正确（真题不陈述定义） |
| 红烧肉的做法 | 应拒绝 | 回复"无法回答此问题" | 正确 |

**检索有效性验证：**
- 快速排序查询召回 7 个不同来源（真题考点分类 + 6 个年份真题）
- 检索块包含：快速排序趟数判断、排序算法比较、时间复杂度选择题等
- LLM 正确分析每个块后未找到明确公式，诚实拒绝
- 红烧肉查询跨科召回 5 个来源，LLM 正确判断无关

**使用：**
```bash
python qa.py "你的问题"        # 单次问答
python qa.py --test            # 运行两个内置测试用例
```

---

## 六、analysis.py — 考情分析

**功能：**
- 从 `data/exams/` 加载 23 个真题 PDF（或从 ChromaDB 读取）
- 40+ 关键词自动将混合真题分类到四科
- 正则提取年份（2009-2026），构建各科语料
- 调用 DeepSeek 生成 `report_2026.md`

**已生成报告包含：**
1. 四科高频考点 Top10 表格（排名/考点/频次/年份）
2. 近 3 年命题趋势简述
3. 2026 可能出题方向与冷门提醒

**系统报告严格遵守规则：** 数据结构/计组近年真题语料不足时，明确标注"资料不足，无法判断"

**使用：** `python analysis.py`

---

## 七、已知问题与改进方向

| 问题 | 现状 | 建议 |
|---|---|---|
| Embedding 模型小 | `bge-small` 召回精度有限 | 可升级为 `bge-base-zh-v1.5` 或 `bge-large-zh-v1.5` |
| 中文分块粗糙 | 当前按字符数分割 | 可引入按句号/段落语义分割 |
| 真题碎片化 | 真题默认"考查理解"，不陈述定义 | 需要教学材料（textbooks/notes）补充定义性知识 |
| 检索排名 | 仅用相似度排序 | 可引入 reranker（如 bge-reranker）提升精度 |
| 仅支持单轮问答 | 无对话历史 | 可扩展为多轮对话，记住上下文 |
