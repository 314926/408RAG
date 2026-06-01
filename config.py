import os

from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── DeepSeek API ──
API_BASE = "https://api.deepseek.com/v1"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# ── 千问视觉模型 ──
VISION_API_KEY = os.getenv("DASHSCOPE_API_KEY")
VISION_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
VISION_MODEL = "qwen3.6-plus"
VISION_MAX_IMAGES = 3              # 多图联合分析最大图片数
VISION_FOLLOWUP_WINDOW = 5         # 追问模式下保留图片上下文的对话轮数

# ── Embedding（本地 BGE 中文模型，从 ModelScope 下载）──
_models_dir = os.path.join(_BASE_DIR, "models", "AI-ModelScope", "bge-small-zh-v1___5")
EMBED_MODEL = _models_dir if os.path.isdir(_models_dir) else "BAAI/bge-small-zh-v1.5"

# ── 分块参数 ──
CHUNK_SIZE = 256
CHUNK_OVERLAP = 64

# ── 分类分块参数 ──
MINDMAP_CHUNK_SIZE = 1500      # 思维导图 .md 文件分块大小
COMPREHENSIVE_CHUNK_SIZE = 2000  # Q&A 大题资料分块大小
MINDS_DIR = "minds"
NOTES_DIR = "notes"

# ── 向量库 ──
OUTPUT_DIR = os.path.join(_BASE_DIR, "data_output")
PERSIST_DIR = os.path.join(OUTPUT_DIR, "chroma_db")
COLLECTION_NAME = "408_knowledge"

# ── 优化开关 ──
ENABLE_RERANK = True           # 混合检索后使用 cross-encoder 重排序
ENABLE_QUERY_REWRITE = True    # 查询重写：将复杂问题拆分为子问题分别检索
ENABLE_PARENT_EXPANSION = True # 父文档扩展：检索小块后向上查找完整段落

# ── 混合检索参数 ──
VECTOR_TOP_K = 20   # 向量检索返回数量
BM25_TOP_K = 10     # BM25 关键词检索返回数量
RERANK_TOP_K = 10   # 重排序后最终保留数量

# ── 重排序模型 ──
_rerank_dir = os.path.join(_BASE_DIR, "models", "cross-encoder__ms-marco-MiniLM-L-6-v2")
RERANK_MODEL = _rerank_dir if os.path.isdir(_rerank_dir) else "cross-encoder/ms-marco-MiniLM-L-6-v2"

# ── 重排序回退模式：如果模型下载失败，自动跳过重排序（不影响检索功能）──
RERANK_FALLBACK = True

# ── 父文档扩展 ──
PARENT_EXPAND_RANGE = 2  # 前后各取 N 个相邻块拼接

# ── 数据目录 ──
DATA_DIR = os.path.join(_BASE_DIR, "data")
MISTAKE_BOOK_DIR = os.path.join(DATA_DIR, "exams", "错题本")  # 错题保存路径
MISTAKE_DATA_FILE = os.path.join(OUTPUT_DIR, "mistake_data.json")  # 错题本结构化数据
EXERCISE_DIR = os.path.join(DATA_DIR, "exercise")  # 选择题练习题库目录

# ── 增量缓存 ──
CACHE_FILE = os.path.join(OUTPUT_DIR, "ingest_cache.json")

# ── 支持的文件扩展名 ──
SUPPORTED_EXT = {".pdf", ".md", ".txt"}

# ── 记忆力模块 ──
MEMORY_ENABLED = True
MEMORY_FILE = os.path.join(OUTPUT_DIR, "memory.json")

# ── 人设配置（直击核心风格）──
PERSONA_ENABLED = True
TEACHER_NAME = "高分学长"
TEACHING_STYLE = "直击核心"

PERSONA_PROMPT = (
    f"【人设：{TEACHER_NAME}（{TEACHING_STYLE}教学）】\n\n"
    f"你是\"{TEACHER_NAME}\"，一位408计算机考研高分学长，擅长用最清晰的结构把复杂问题讲透。\n\n"
    "行为准则：\n"
    "1. 直接给出结论：回答问题时开门见山，先给出核心结论，再展开分析。不反问用户，不进行随堂检测。\n"
    "2. 结构化表达：使用分点、对比表格、步骤说明等方式组织回答，确保逻辑清晰。\n"
    "3. 直击考点：突出408考试中的关键点和常见易错点。\n"
    "4. 简洁专业：语言精炼，以学长身份交流，保持专业和温度。\n"
)

# ── 专题深度总结触发词 ──
SUMMARIZE_TRIGGERS = ["比较", "异同", "区别", "联系", "综合", "实现原理", "设计思想", "演变", "优缺点"]

# ── 检索增强：触发词检测后的权重调整 ──
COMPREHENSIVE_BOOST = 1.5   # type="comprehensive" 文档的相似度放大系数
MINDMAP_EXTRA_K = 2         # 触发后额外检索的 category="mindmap" 片段数

DEEP_SUMMARY_TEMPLATE = """
请按以下结构回答：
【核心结论】（一句话概括）
【知识背景】（涉及的知识点及它们在408中的位置）
【分点对比/深度分析】（如果是比较类，用表格或列表；如果是原理类，分步骤说明）
【关键易错点】（408考试中常见的坑）
【一句话记忆口诀】（可选）
"""

# ── 核心概念强制召回机制 ──
# 当用户问题命中以下 key（子串匹配），自动追加检索 value 中指定的关键词，
# 并对包含这些关键词的文档加权，确保基础概念不被漏检。
# 提示：请根据你的教材侧重点补充 key 和关键词。
CORE_CONCEPTS = {
    # ══ 计算机组成原理 ══
    "指令译码": "指令周期 译码 微操作 控制单元 CU 操作码 寻址方式",
    "指令周期": "取指 间址 执行 中断 指令周期 CPU工作周期 微操作序列",
    "微程序": "微程序 微指令 微操作 控制存储器 CM 微地址 顺序控制",
    "Cache": "Cache 缓存 命中率 写策略 写回法 写直达法 映射方式 替换算法 LRU",
    "虚拟内存": "虚拟内存 请求分页 缺页中断 页表 TLB 快表 地址变换 页面置换",
    "中断": "中断 中断隐指令 中断向量 中断响应 关中断 保护现场 中断服务程序",
    "DMA": "DMA 直接存储器访问 周期挪用 中断 数据传送 总线控制权",
    "流水线": "流水线 冒险 数据相关 控制相关 结构相关 流水段 流水线性能",
    "总线": "总线 系统总线 数据总线 地址总线 控制总线 总线仲裁 总线标准",
    "浮点数": "浮点数 IEEE754 规格化 阶码 尾数 对阶 舍入 溢出判断",
    "补码": "补码 原码 反码 移码 模运算 加减运算 溢出 符号扩展",
    "存储器": "存储器 层次结构 SRAM DRAM ROM 刷新 存储容量 扩展",
    # ══ 操作系统 ══
    "进程": "进程 PCB 进程状态 五状态模型 进程调度 上下文切换 进程控制",
    "线程": "线程 TCB 用户级线程 内核级线程 多线程模型 线程切换",
    "死锁": "死锁 互斥 请求保持 不可剥夺 环路等待 银行家算法 死锁检测",
    "调度": "调度 先来先服务 短作业优先 时间片轮转 优先级 多级反馈队列 响应比",
    "信号量": "信号量 PV操作 同步 互斥 临界区 生产者消费者 读者写者",
    "页面置换": "页面置换 OPT LRU FIFO CLOCK 改进型CLOCK 缺页率 抖动",
    "文件系统": "文件系统 FCB 索引节点 inode 目录结构 文件分配 空闲空间管理",
    "磁盘": "磁盘 寻道时间 旋转延迟 磁盘调度 SSTF SCAN CSCAN 磁盘结构",
    # ══ 数据结构 ══
    "排序": "排序 快速排序 归并排序 堆排序 插入排序 时间复杂度 稳定性 比较次数",
    "树": "树 二叉树 二叉搜索树 平衡二叉树 AVL 哈夫曼树 遍历 线索二叉树",
    "图": "图 邻接矩阵 邻接表 DFS BFS 最小生成树 最短路径 拓扑排序 关键路径",
    "查找": "查找 顺序查找 折半查找 散列表 哈希 B树 B+树 平均查找长度 冲突",
    "链表": "链表 单链表 双链表 循环链表 头插法 尾插法 逆置 合并",
    "栈和队列": "栈 队列 顺序栈 链栈 循环队列 表达式求值 括号匹配 双端队列",
    "堆": "堆 完全二叉树 大根堆 小根堆 堆排序 优先队列 堆调整 建堆",
    "串": "串 KMP next数组 模式匹配 串的存储 朴素匹配",
    # ══ 计算机网络 ══
    "TCP": "TCP 三次握手 四次挥手 拥塞控制 流量控制 可靠传输 滑动窗口 序号确认",
    "IP": "IP IP地址 子网划分 CIDR 路由协议 NAT ARP ICMP 分组转发",
    "HTTP": "HTTP 请求报文 响应报文 状态码 无状态 Cookie HTTPS 持久连接",
    "DNS": "DNS 域名解析 递归查询 迭代查询 本地域名服务器 根域名服务器",
    "以太网": "以太网 CSMA/CD MAC帧 交换机 冲突域 广播域 生成树 ARQ",
    "传输层": "传输层 UDP TCP 端口 套接字 复用分用 可靠传输 流量控制",
}

# 核心概念检索相似度阈值（低于此值且命中核心概念时触发知识库回退，不直接拒绝回答）
CORE_CONCEPT_SIM_THRESHOLD = 0.5
