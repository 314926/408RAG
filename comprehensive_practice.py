"""
408 大题专项练习模块

采用"模板 + 参数替换"方式生成高频大题题型，覆盖数据结构算法设计、
计算机组成原理、操作系统、计算机网络四科核心大题考点。

每道大题包含：题目骨架（含可替换参数）+ 标准解题步骤/伪代码 + 标准答案。
所有算法模板以 C 语言风格伪代码给出，便于考试复习。
"""

import random
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompProblem:
    """一道大题"""
    topic_id: str
    topic_name: str
    subject: str
    question: str
    params: dict
    solution_steps: list[str]     # 分步解题过程
    answer: str                   # 标准答案
    knowledge_tags: list[str] = field(default_factory=list)
    has_pseudocode: bool = False  # 解题步骤中是否包含伪代码


# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════

def _rand_int(low: int, high: int, step: int = 1) -> int:
    return random.randrange(low, high + 1, step)


def _rand_choice(items: list) -> any:
    return random.choice(items)


# ═══════════════════════════════════════════════════════════════════════════
# 数据结构 — 算法设计题
# ═══════════════════════════════════════════════════════════════════════════

# ── 1. 单链表逆转 ──

def _gen_ds_list_reverse() -> CompProblem:
    n = _rand_int(6, 15)  # 链表长度
    head_type = _rand_choice(["带头结点", "不带头结点"])
    head_note = "（头结点中不存储数据）" if head_type == "带头结点" else ""

    params = {"n": n, "head_type": head_type}

    question = (
        f"设 **{head_type}的单链表**{head_note}，结点结构为 `data | next`，\n"
        f"链表中有 **{n} 个**数据结点。\n\n"
        f"请设计一个算法将链表原地逆转（即不使用额外的链表结点空间），要求：\n"
        f"(1) 写出算法思想\n"
        f"(2) 用 C 语言写出算法（或伪代码）\n"
        f"(3) 分析算法的时间复杂度和空间复杂度"
    )

    steps = [
        "**【算法思想】**\n\n"
        "采用 **头插法** 实现单链表的原地逆转：\n"
        f"1. 如果{'头结点为空或' if head_type == '带头结点' else ''}链表为空或只有一个结点，无需操作\n"
        "2. 使用三个指针 `p`（当前结点）、`q`（后继结点）、`r`（临时指针）进行遍历\n"
        "3. 从第一个数据结点开始，依次将每个结点的 next 指向前驱结点（即逆转指向方向）\n"
        "4. 最后将头指针指向原链表的最后一个结点",
        "**【伪代码】**\n\n"
        "```c\n"
        "// 单链表结点定义\n"
        "typedef struct LNode {\n"
        "    int data;\n"
        "    struct LNode *next;\n"
        "} LNode, *LinkList;\n\n"
        "// 原地逆转单链表\n"
        "void Reverse(LinkList L) {\n"
        f"    // 空表或单结点，直接返回\n"
        f"    if ({'L->next == NULL || L->next->next == NULL' if head_type == '带头结点' else 'L == NULL || L->next == NULL'})\n"
        "        return;\n\n"
        f"    LNode *p = {'L->next' if head_type == '带头结点' else 'L'};  // p 指向第一个数据结点\n"
        f"    LNode *q = NULL;\n\n"
        f"    {'L->next = NULL;  // 将头结点的 next 置空' if head_type == '带头结点' else 'L = NULL;  // 断开原头指针'}\n\n"
        "    while (p != NULL) {\n"
        "        q = p->next;          // q 暂存 p 的后继\n"
        "        p->next = L;          // 逆转指针方向\n"
        f"        {'L = p;' if head_type == '带头结点' else 'L = p;'}                // 移动头指针\n"
        "        p = q;                // p 前进到下一个结点\n"
        "    }\n"
        "}\n"
        "```",
        "**【复杂度分析】**\n\n"
        f"- **时间复杂度**：遍历链表一次，处理每个结点只需 O(1) 操作，共处理 {n} 个结点\n"
        "  所以 T(n) = **O(n)**\n\n"
        f"- **空间复杂度**：只使用了有限的几个指针变量（`p`、`q`{'、`r`' if n > 10 else ''}），"
        "不随问题规模变化\n"
        "  所以 S(n) = **O(1)**",
        "**【算法要点】**\n"
        "1. 核心思想是**头插法**：依次摘下原链表结点，插入到新链表头部\n"
        "2. 必须用 `q`（或 `r`）暂存后继结点，否则断链后无法继续遍历\n"
        f"3. {'带头结点法将头结点的 next 初始置空，' if head_type == '带头结点' else '不带头结点时用 L 本身充当结果链表头，'}简化了边界处理\n"
        "4. 408 考试中链表操作是高频算法题，务必掌握此基本操作",
    ]

    answer = (
        "算法：头插法原地逆转，T(n)=O(n)，S(n)=O(1)。\n"
        "核心代码：三个指针 p/q（当前/后继），依次将 p->next 指向前驱，最后更新头指针。"
    )

    return CompProblem(
        topic_id="ds_list_reverse",
        topic_name="单链表逆转",
        subject="数据结构",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["链表", "单链表", "逆转", "头插法", "算法设计"],
        has_pseudocode=True,
    )


# ── 2. 二叉树非递归中序遍历 ──

def _gen_ds_tree_inorder() -> CompProblem:
    n = _rand_int(7, 15)  # 节点数
    tree_type = _rand_choice(["二叉链表", "三叉链表"])

    params = {"n": n, "tree_type": tree_type}

    question = (
        f"给定一棵具有 **{n} 个结点**的二叉树，采用 **{tree_type}** 存储结构。\n\n"
        f"请写出**非递归中序遍历**算法，要求：\n"
        f"(1) 写出算法思想\n"
        f"(2) 用类 C 语言写出算法代码\n"
        f"(3) 分析算法的时间复杂度和空间复杂度"
    )

    steps = [
        "**【算法思想】**\n\n"
        "非递归中序遍历借助 **栈** 来模拟递归过程：\n"
        "1. 从根结点出发，沿左子树一路入栈，直到最左下的结点\n"
        "2. 弹出栈顶结点并访问\n"
        "3. 将指针移动到该结点的右子树，重复步骤 1-2\n"
        "4. 当栈为空且当前指针为 NULL 时，遍历结束\n\n"
        "中序遍历的访问顺序为：**左子树 → 根结点 → 右子树**",
        "**【伪代码】**\n\n"
        "```c\n"
        "// 二叉树结点定义\n"
        "typedef struct BiTNode {\n"
        "    int data;\n"
        "    struct BiTNode *lchild, *rchild;\n"
        "} BiTNode, *BiTree;\n\n"
        "// 非递归中序遍历\n"
        "void InOrder(BiTree T) {\n"
        "    InitStack(S);          // 初始化栈\n"
        "    BiTNode *p = T;        // p 为遍历指针\n\n"
        "    while (p != NULL || !StackEmpty(S)) {\n"
        "        if (p != NULL) {\n"
        "            // 一路向左：将当前结点入栈\n"
        "            Push(S, p);\n"
        "            p = p->lchild;\n"
        "        } else {\n"
        "            // 左子树为空：弹出栈顶并访问，然后转向右子树\n"
        "            Pop(S, p);\n"
        "            visit(p);           // 访问结点\n"
        "            p = p->rchild;      // 转向右子树\n"
        "        }\n"
        "    }\n"
        "}\n"
        "```",
        "**【执行示例】**（以 5 个结点的满二叉树为例）\n"
        "```\n"
        "        A\n"
        "       / \\\n"
        "      B   C\n"
        "     / \\\n"
        "    D   E\n"
        "中序遍历结果：D → B → E → A → C\n"
        "栈的变化（简略）：\n"
        "  初始: p=A, stack=[]\n"
        "  ① 入栈 A,B,D → D 无左子 → 弹出 D(访问)→ p=D->rchild(NULL)\n"
        "  ② 弹出 B(访问)→ p=B->rchild(E)\n"
        "  ③ 入栈 E → E 无左子 → 弹出 E(访问)→ p=NULL\n"
        "  ④ 弹出 A(访问)→ p=A->rchild(C)\n"
        "  ⑤ 入栈 C → C 无左子 → 弹出 C(访问)→ p=NULL, stack=∅ → 结束\n"
        "```",
        "**【复杂度分析】**\n\n"
        f"- **时间复杂度**：每个结点入栈一次、出栈一次，共 {n} 个结点\n"
        "  每次操作 O(1)，所以 T(n) = **O(n)**\n\n"
        "- **空间复杂度**：栈的最大深度等于二叉树的高度\n"
        "  最坏情况（单支树）为 O(n)，平均为 O(log₂n)\n"
        "  所以 S(n) = **O(n)**（最坏）",
        "**【408 考点提示】**\n"
        "1. 三种非递归遍历中，**中序**和**前序**较简单，**后序**较复杂（需标记右子树是否已访问）\n"
        "2. 核心思路：用栈保存待返回的结点，替代系统栈\n"
        "3. 常见的应用场景：表达式求值（中缀表达式）、二叉搜索树顺序输出",
    ]

    answer = (
        "非递归中序遍历使用栈模拟递归：沿左子树入栈 → 弹出访问 → 转向右子树。\n"
        "T(n)=O(n)，S(n)=O(h)（h为树高，最坏O(n)）。"
    )

    return CompProblem(
        topic_id="ds_tree_inorder",
        topic_name="二叉树非递归中序遍历",
        subject="数据结构",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["二叉树", "遍历", "中序遍历", "栈", "非递归"],
        has_pseudocode=True,
    )


# ── 3. 拓扑排序 ──

def _gen_ds_topological_sort() -> CompProblem:
    n = _rand_int(5, 8)  # 顶点数
    e = _rand_int(n, n * (n - 1) // 3)  # 边数约为 1/3 完全图

    # 构造一个有向无环图描述
    params = {"n": n, "e": e}

    question = (
        f"给定一个 **{n} 个顶点 {e} 条边**的有向无环图（DAG），\n"
        f"采用 **邻接表** 作为存储结构。\n\n"
        f"请写出 **拓扑排序算法**（Kahn 算法），要求：\n"
        f"(1) 写出算法思想\n"
        f"(2) 用类 C 语言写出算法代码\n"
        f"(3) 分析算法的时间复杂度和空间复杂度"
    )

    steps = [
        "**【算法思想】**（Kahn 算法）\n\n"
        "1. 计算图中所有顶点的**入度**（存入 indegree[] 数组）\n"
        "2. 将所有**入度为 0** 的顶点入栈（或队列、链表）\n"
        "3. 当栈不为空时：\n"
        "   - 弹出栈顶顶点 u，将其输出（加入拓扑序列）\n"
        "   - 遍历 u 的所有邻接点 v，令 indegree[v]--\n"
        "   - 若 indegree[v] 变为 0，将 v 入栈\n"
        "4. 若输出顶点数 < 图中总顶点数，说明图中存在环，无法完成拓扑排序",
        "**【伪代码】**\n\n"
        "```c\n"
        "#define MAX_VERTEX_NUM 100\n\n"
        "// 邻接表结点定义\n"
        "typedef struct ArcNode {\n"
        "    int adjvex;                 // 邻接点下标\n"
        "    struct ArcNode *next;\n"
        "} ArcNode;\n\n"
        "typedef struct VNode {\n"
        "    int data;\n"
        "    ArcNode *first;\n"
        "} VNode, AdjList[MAX_VERTEX_NUM];\n\n"
        "typedef struct {\n"
        "    AdjList vertices;\n"
        "    int vexnum, arcnum;\n"
        "} Graph;\n\n"
        "// 拓扑排序\n"
        "bool TopologicalSort(Graph G) {\n"
        "    int indegree[G.vexnum];\n"
        "    // 计算各顶点入度（省略初始化代码）\n"
        "    CalcIndegree(G, indegree);\n\n"
        "    Stack S;\n"
        "    InitStack(S);\n\n"
        "    // 所有入度为 0 的顶点入栈\n"
        "    for (int i = 0; i < G.vexnum; i++)\n"
        "        if (indegree[i] == 0)\n"
        "            Push(S, i);\n\n"
        "    int count = 0;  // 已输出顶点数\n"
        "    while (!StackEmpty(S)) {\n"
        "        Pop(S, i);\n"
        "        print(i);           // 输出顶点\n"
        "        count++;\n\n"
        "        // 遍历 i 的所有邻接点\n"
        "        for (ArcNode *p = G.vertices[i].first; p != NULL; p = p->next) {\n"
        "            int v = p->adjvex;\n"
        "            if (--indegree[v] == 0)\n"
        "                Push(S, v);\n"
        "        }\n"
        "    }\n\n"
        "    // 检查是否所有顶点都输出了\n"
        "    return count == G.vexnum;\n"
        "}\n"
        "```",
        "**【复杂度分析】**\n\n"
        "- **时间复杂度**：\n"
        "  - 计算入度：O(n + e)，需遍历所有边\n"
        "  - 每个顶点入栈/出栈一次：O(n)\n"
        "  - 每条边被访问一次（遍历邻接表）：O(e)\n"
        f"  所以总 T(n) = **O(n + e)** = O({n} + {e}) = **O({n + e})**\n\n"
        "- **空间复杂度**：\n"
        "  需要 indegree 数组 O(n)、栈 O(n)\n"
        "  所以 S(n) = **O(n)**",
        "**【408 考点提示】**\n"
        "1. 拓扑排序可以检测有向图中是否存在**环**（返回 false）\n"
        "2. **Kahn 算法**是基于入度的，还有基于 DFS 的逆后序方法\n"
        "3. 拓扑排序的结果**不唯一**——入度为 0 的顶点入栈顺序影响输出顺序\n"
        "4. 应用场景：工程调度（AOV 网）、依赖关系排序、编译器的模块编译顺序",
    ]

    answer = (
        "Kahn算法：入度为0顶点入栈 → 弹出并输出 → 减少邻接点入度 → 入度变为0者入栈。\n"
        "T(n)=O(n+e)，S(n)=O(n)。适合DAG的拓扑排序与环检测。"
    )

    return CompProblem(
        topic_id="ds_topological_sort",
        topic_name="拓扑排序（Kahn算法）",
        subject="数据结构",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["图", "拓扑排序", "DAG", "Kahn", "AOV", "环检测"],
        has_pseudocode=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 计算机组成原理
# ═══════════════════════════════════════════════════════════════════════════

# ── 4. 指令格式与寻址方式 ──

def _gen_co_instruction_format() -> CompProblem:
    # 指令格式参数
    opcode_bits = _rand_int(4, 6)
    addr_mode_bits = 2  # 固定2位寻址方式
    reg_bits = _rand_int(3, 4)  # 3-4位寄存器编号
    offset_bits = _rand_int(6, 10)

    # 各寄存器内容
    reg_values = {}
    reg_names = []
    for i in range(2 ** reg_bits):
        reg_name = f"R{i}"
        reg_names.append(reg_name)
        reg_values[reg_name] = _rand_int(100, 500)

    # 内存内容（关键地址）
    mem_loc = _rand_int(1000, 2000)
    mem_val = _rand_int(1, 9999)

    # 寻址方式编码
    mode_code = _rand_int(0, 3)
    mode_names = ["立即寻址", "直接寻址", "寄存器间接寻址", "变址寻址"]
    mode_name = mode_names[mode_code]

    # 指令编码
    form_addr = _rand_int(1, 127)  # 形式地址（7位有符号）
    opcode = _rand_int(0, (1 << opcode_bits) - 1)
    reg_idx = _rand_int(0, (1 << reg_bits) - 1)
    reg_sel = f"R{reg_idx}"

    # 结果计算
    effective_addr = None
    result_desc = ""
    if mode_code == 0:  # 立即寻址
        effective_addr = None
        operand = form_addr  # 形式地址本身就是操作数
        result_desc = f"操作数 = 形式地址 = {form_addr}"
    elif mode_code == 1:  # 直接寻址
        effective_addr = form_addr
        result_desc = f"EA = {form_addr}，操作数 = M[{form_addr}] = 内存内容待查"
    elif mode_code == 2:  # 寄存器间接寻址
        effective_addr = reg_values[reg_sel]
        result_desc = f"EA = ({reg_sel}) = {reg_values[reg_sel]}"
    elif mode_code == 3:  # 变址寻址：EA = (R) + 形式地址
        effective_addr = reg_values[reg_sel] + form_addr
        result_desc = f"EA = ({reg_sel}) + 形式地址 = {reg_values[reg_sel]} + {form_addr} = {effective_addr}"

    # 将寄存器值列表整理成可读格式
    reg_display = []
    for i in range(min(8, 2 ** reg_bits)):
        reg_display.append(f"R{i} = {reg_values[f'R{i}']}")

    params = {
        "opcode_bits": opcode_bits, "addr_mode_bits": addr_mode_bits,
        "reg_bits": reg_bits, "offset_bits": offset_bits,
        "opcode": opcode, "reg_sel": reg_sel,
        "form_addr": form_addr, "mode_name": mode_name,
        "mode_code": mode_code, "reg_values": reg_values,
        "effective_addr": effective_addr,
    }

    question = (
        f"某计算机指令格式如下：\n\n"
        f"| 操作码 ({opcode_bits}位) | 寻址方式 (2位) | 寄存器 ({reg_bits}位) | 形式地址 ({offset_bits}位) |\n"
        f"|{'---|' * 4}\n\n"
        f"已知各寄存器内容为：{'，'.join(reg_display[:8])}（其余类似）。\n\n"
        f"一条指令编码为：**操作码 = 0x{opcode:X}**（占 {opcode_bits} 位），"
        f"**寻址方式 = {mode_code:02b}**（{mode_name}），"
        f"**寄存器 = {reg_sel}**，**形式地址 = {form_addr}**。\n\n"
        f"请计算该指令的 **有效地址 EA** 及 **操作数**。"
    )

    steps = [
        f"**第 1 步：分析指令格式**\n"
        f"指令总长度 = {opcode_bits} + {addr_mode_bits} + {reg_bits} + {offset_bits} = "
        f"{opcode_bits + addr_mode_bits + reg_bits + offset_bits} 位\n"
        f"寻址方式字段二进制为 `{mode_code:02b}`，对应 **{mode_name}**",
        f"**第 2 步：确定寻址方式含义**\n"
        f"各寻址方式定义：\n"
        f"- `00` = 立即寻址：操作数 = 形式地址（立即数）\n"
        f"- `01` = 直接寻址：EA = 形式地址\n"
        f"- `10` = 寄存器间接寻址：EA = (寄存器)\n"
        f"- `11` = 变址寻址：EA = (变址寄存器) + 形式地址\n\n"
        f"当前寻址方式：**{mode_name}**",
        f"**第 3 步：计算有效地址**\n" +
        {
            0: f"立即寻址：无需计算有效地址，操作数 = 形式地址 = **{form_addr}**",
            1: f"直接寻址：EA = 形式地址 = **{form_addr}**\n\n操作数 = M[{form_addr}]（需根据内存内容确定）",
            2: f"寄存器间接寻址：EA = ({reg_sel}) = {reg_values[reg_sel]} = **{effective_addr}**\n\n操作数 = M[{effective_addr}]（需根据内存内容确定）",
            3: f"变址寻址：EA = ({reg_sel}) + 形式地址 = {reg_values[reg_sel]} + {form_addr} = **{effective_addr}**\n\n操作数 = M[{effective_addr}]（需根据内存内容确定）",
        }[mode_code],
        f"**第 4 步：结论**\n"
        f"有效地址 EA = **{effective_addr if effective_addr is not None else '无需（立即数）'}**\n"
        f"寻址方式：{mode_name}",
        "**【408 考点提示】**\n"
        "1. 指令格式的字段划分是408**计组**的必考知识点\n"
        "2. 重点掌握 7 种寻址方式：立即、直接、间接、寄存器、寄存器间接、变址、相对\n"
        "3. 注意区别 EA（有效地址）和操作数本身——对立即寻址，形式地址就是操作数\n"
        "4. 变址寻址的 EA = 变址寄存器 + 形式地址，常用于数组访问",
    ]

    answer = (
        f"EA = {effective_addr if effective_addr is not None else '无需（立即数）'}，"
        f"寻址方式 = {mode_name}。"
    )

    return CompProblem(
        topic_id="co_instruction_format",
        topic_name="指令格式与寻址方式",
        subject="计算机组成原理",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["指令格式", "寻址方式", "有效地址", "指令系统"],
    )


# ── 5. 数据通路分析 ──

def _gen_co_datapath() -> CompProblem:
    instr = _rand_choice(["ADD R0, R1", "LOAD R2, (R1)", "STORE R2, (R1)", "SUB R3, R4"])
    bus_type = _rand_choice(["单总线结构", "三总线结构"])

    # 解析指令
    instr_name = instr.split()[0]
    instr_desc = {
        "ADD": "加法指令",
        "LOAD": "取数指令",
        "STORE": "存数指令",
        "SUB": "减法指令",
    }[instr_name]

    params = {"instr": instr, "instr_name": instr_name, "instr_desc": instr_desc, "bus_type": bus_type}

    question = (
        f"某计算机采用 **{bus_type}**，CPU 内部包含 ALU、通用寄存器组（R0∼R7）、\n"
        f"IR（指令寄存器）、PC（程序计数器）、MAR（地址寄存器）、MDR（数据寄存器）等部件。\n\n"
        f"执行指令 **{instr}**（{instr_desc}），请：\n"
        f"(1) 写出该指令的**执行流程**（分阶段描述）\n"
        f"(2) 标出每个阶段的**控制信号**和**数据通路**\n"
        f"(3) 说明需要几个时钟周期"
    )

    # 不同指令的流程不同
    if instr_name == "ADD":
        steps = [
            "**【第 1 阶段：取指令】**\n\n"
            "1. `PC → MAR`：将 PC 内容送地址寄存器\n"
            "2. `M(MAR) → MDR`：从内存读取指令到数据寄存器\n"
            "3. `MDR → IR`：将指令送指令寄存器\n"
            "4. `(PC) + 1 → PC`：PC 自增，指向下一条指令\n\n"
            "**控制信号**：`PCout, MARin, Read, MDRout, IRin, PC+1`\n"
            "**占用 4 个时钟周期**\n\n"
            "（此阶段对所有指令都是相同的，微操作序列一致）",
            "**【第 2 阶段：译码 + 取操作数】**\n\n"
            "1. `IR → 控制单元`：指令译码，识别出是 ADD 指令\n"
            "2. `R1 → ALU_A`：将源操作数 R1 的内容送到 ALU 的 A 输入端\n\n"
            "**控制信号**：`指令译码, R1out, ALU_Ain`\n"
            "**占用 2 个时钟周期**",
            "**【第 3 阶段：执行】**\n\n"
            "1. ALU 执行加法运算：`(R0) + (R1) → ALU_Output`\n"
            f"2. 结果送回到 R0：`ALU_Output → R0`\n\n"
            "**控制信号**：`ALU_ADD, ALUout, R0in`\n"
            "**占用 2 个时钟周期**\n\n"
            "数据通路：\n"
            "```\n"
            "   R1 ──→ ALU_A   \\\n"
            "                      ALU(+)\n"
            "   R0 ──→ ALU_B   /      │\n"
            "                           ↓\n"
            "                           R0\n"
            "```",
            "**【总结】**\n\n"
            "| 阶段 | 时钟周期数 | 主要控制信号 |\n"
            "|------|-----------|-------------|\n"
            "| 取指令(F) | 4 | PCout, MARin, Read, MDRout, IRin, PC+1 |\n"
            "| 译码+取数(D) | 2 | 译码, R1out, ALU_Ain |\n"
            "| 执行(E) | 2 | ALU_ADD, ALUout, R0in |\n\n"
            f"**总时钟周期数：4 + 2 + 2 = 8 个周期**",
        ]
    elif instr_name == "LOAD":
        steps = [
            "**【第 1 阶段：取指令】**\n\n"
            "1. `PC → MAR`\n"
            "2. `M(MAR) → MDR`\n"
            "3. `MDR → IR`\n"
            "4. `(PC) + 1 → PC`\n\n"
            "**控制信号**：`PCout, MARin, Read, MDRout, IRin, PC+1`",
            "**【第 2 阶段：计算源地址】**\n\n"
            "LOAD R2, (R1) 表示以 R1 的内容为内存地址取数\n"
            "1. `R1 → MAR`：将寄存器 R1 的内容送地址寄存器\n\n"
            "**控制信号**：`R1out, MARin`",
            "**【第 3 阶段：取操作数】**\n\n"
            "1. `M(MAR) → MDR`：从内存读取数据\n"
            "2. `MDR → R2`：将数据写入目标寄存器 R2\n\n"
            "**控制信号**：`Read, MDRout, R2in`\n\n"
            "数据通路：\n"
            "```\n"
            "   R1 ──→ MAR ──→ 内存 ──→ MDR ──→ R2\n"
            "```",
            "**【总结】**\n\n"
            "| 阶段 | 时钟周期数 | 主要控制信号 |\n"
            "|------|-----------|-------------|\n"
            "| 取指令(F) | 4 | PCout, MARin, Read, MDRout, IRin, PC+1 |\n"
            "| 地址计算(D) | 1 | R1out, MARin |\n"
            "| 取数(E) | 2 | Read, MDRout, R2in |\n\n"
            "**总时钟周期数：4 + 1 + 2 = 7 个周期**",
        ]
    elif instr_name == "STORE":
        steps = [
            "**【第 1 阶段：取指令】**\n"
            "（同上）",
            "**【第 2 阶段：准备数据 + 地址】**\n\n"
            "STORE R2, (R1) 表示将 R2 的内容存到以 R1 内容为地址的内存单元\n\n"
            "1. `R1 → MAR`：将 R1（地址指针）送地址寄存器\n"
            "2. `R2 → MDR`：将 R2（待存数据）送数据寄存器\n\n"
            "**控制信号**：`R1out, MARin, R2out, MDRin`",
            "**【第 3 阶段：写内存】**\n\n"
            "1. `MDR → M(MAR)`：将数据写入内存\n\n"
            "**控制信号**：`Write`\n\n"
            "数据通路：\n"
            "```\n"
            "   R1 ──→ MAR ──┐\n"
            "                  ├──→ 内存\n"
            "   R2 ──→ MDR ──┘\n"
            "```",
            "**【总结】**\n\n"
            "| 阶段 | 时钟周期数 | 主要控制信号 |\n"
            "|------|-----------|-------------|\n"
            "| 取指令(F) | 4 | PCout, MARin, Read, MDRout, IRin, PC+1 |\n"
            "| 准备(D) | 2 | R1out, MARin, R2out, MDRin |\n"
            "| 写存(E) | 1 | Write |\n\n"
            "**总时钟周期数：4 + 2 + 1 = 7 个周期**",
        ]
    else:  # SUB
        steps = [
            "**【第 1 阶段：取指令】**\n"
            "（同上）",
            "**【第 2 阶段：译码 + 取操作数】**\n\n"
            "1. 译码识别出 SUB R3, R4\n"
            f"2. `R4 → ALU_A`：被减数\n"
            "3. `R3 → ALU_B`：减数\n\n"
            "**控制信号**：`译码, R4out, ALU_Ain, R3out, ALU_Bin`",
            "**【第 3 阶段：执行 + 写回】**\n\n"
            "1. ALU 执行减法 `(R4) − (R3) = ALU_Output`\n"
            "2. `ALU_Output → R4`：结果写回目标寄存器\n\n"
            "**控制信号**：`ALU_SUB, ALUout, R4in`",
            "**【总结】**\n\n"
            "| 阶段 | 时钟周期数 | 主要控制信号 |\n"
            "|------|-----------|-------------|\n"
            "| 取指令(F) | 4 | PCout, MARin, Read, MDRout, IRin, PC+1 |\n"
            "| 译码+取数(D) | 2 | 译码, R4out, ALU_Ain, R3out, ALU_Bin |\n"
            "| 执行(E) | 2 | ALU_SUB, ALUout, R4in |\n\n"
            "**总时钟周期数：4 + 2 + 2 = 8 个周期**",
        ]

    answer = (
        f"指令 {instr}（{instr_desc}）执行流程分三阶段：\n"
        "① 取指令（4个周期）：PC→MAR→MDR→IR, PC+1\n"
        "② 译码+取操作数：指令译码，取源操作数\n"
        "③ 执行+写回：ALU运算/WR，结果写目标寄存器\n"
        f"总线结构：{bus_type}"
    )

    return CompProblem(
        topic_id="co_datapath",
        topic_name="数据通路分析",
        subject="计算机组成原理",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["数据通路", "CPU", "单总线", "控制信号", "微操作"],
    )


# ── 6. 指令流水线 — 冒险分析 ──

def _gen_co_pipeline_hazard() -> CompProblem:
    # 定义几组指令序列模板
    scenario = _rand_choice([
        {
            "name": "数据相关（RAW）",
            "instrs": ["I1: ADD R1, R2, R3   // R1 ← R2 + R3",
                       "I2: SUB R4, R1, R5   // R4 ← R1 − R5  (依赖I1的结果R1)",
                       "I3: OR  R6, R4, R7   // R6 ← R4 OR R7  (依赖I2的结果R4)"],
            "hazard_type": "数据冒险（RAW — 先写后读）",
            "solution": "转发（旁路）技术 + 插入气泡",
        },
        {
            "name": "数据相关 + 控制相关混合",
            "instrs": ["I1: LW   R1, 0(R2)   // R1 ← M[R2]",
                       "I2: ADD  R3, R1, R4  // R3 ← R1 + R4  (依赖I1的R1)",
                       "I3: SW   R3, 0(R5)   // M[R5] ← R3   (依赖I2的R3)",
                       "I4: SUB  R6, R7, R8  // R6 ← R7 − R8  (无依赖)"],
            "hazard_type": "数据冒险（RAW）+ 结构冒险",
            "solution": "LW → ADD 之间需阻塞一个周期（Load-Use 冒险），其余可转发解决",
        },
        {
            "name": "控制相关（分支指令）",
            "instrs": ["I1: ADD  R1, R2, R3",
                       "I2: BEQ  R1, R0, target   // if R1==R0 then jump",
                       "I3: SUB  R4, R5, R6       // 分支延迟槽",
                       "I4: OR   R7, R8, R9       // 分支目标处指令"],
            "hazard_type": "控制冒险",
            "solution": "分支预测 + 分支延迟槽",
        },
    ])

    stages = _rand_choice(["5段流水线（IF/ID/EX/MEM/WB）", "4段流水线（FI/DI/EI/WO）"])
    cycle_time = _rand_int(1, 3)  # ns
    n_instrs = len(scenario["instrs"])

    params = {
        "stages": stages,
        "cycle_time": cycle_time,
        "instrs": scenario["instrs"],
        "hazard_type": scenario["hazard_type"],
        "solution": scenario["solution"],
        "scenario_name": scenario["name"],
        "n_instrs": n_instrs,
    }

    instr_display = "\n".join(f"  {s}" for s in scenario["instrs"])

    question = (
        f"某计算机采用 **{stages}**，时钟周期为 **{cycle_time} ns**。\n\n"
        f"考虑以下指令序列：\n\n"
        f"{instr_display}\n\n"
        f"请：\n"
        f"(1) 分析该指令序列中存在哪些类型的**流水线冒险**\n"
        f"(2) 说明每种冒险的**产生原因**\n"
        f"(3) 设计**解决方案**（可结合转发、阻塞、分支预测等技术）\n"
        f"(4) 画出添加解决方案后的**流水线时空图**（文字描述）"
    )

    steps = [
        f"**【第 1 步：分析指令间的依赖关系】**\n\n"
        f"指令序列：{n_instrs} 条指令\n"
        f"{chr(10).join(f'  {s}' for s in scenario['instrs'])}\n\n"
        f"逐条分析：\n"
        + {
            0: "I1 写 R1 → I2 读 R1：RAW 依赖\nI2 写 R4 → I3 读 R4：RAW 依赖\n连续的数据流导致流水线阻塞",
            1: "I1 LW 写 R1 → I2 ADD 读 R1：Load-Use 数据冒险\n  （LW 在 MEM 阶段才得到数据，而 ADD 在 ID 阶段就需要）\nI2 写 R3 → I3 SW 读 R3：RAW 数据冒险",
            2: "I2 BEQ 是分支指令，需在 EX 阶段才能判断是否跳转\n  I3 和 I4 同时进入流水线会造成取指方向错误\n  此为控制冒险（Control Hazard）",
        }[0 if scenario["name"] == "数据相关（RAW）" else 1 if scenario["name"] == "数据相关 + 控制相关混合" else 2],
        f"**第 2 步：冒险类型识别**\n\n"
        f"检测到的冒险类型：**{scenario['hazard_type']}**\n\n"
        f"产生原因：\n" +
        {
            0: "I1 在 EX 阶段才计算出 R1 的值，而 I2 在 ID 阶段就需要 R1 的值。\n"
               "这导致 I2 必须在 ID 阶段阻塞，直到 I1 的 EX 阶段完成。\n"
               "I3 同理依赖 I2 的 R4，也需要等待。",
            1: "Load-Use 冒险是 RAW 的特殊情况——需要 1 个气泡（Bubble）才能解决。\n"
               "而一般的 ALU 操作（如 ADD→SUB）可以通过转发解决。\n"
               "此外，LW 和 SW 都访存可能引起结构冒险。",
            2: "BEQ 在 EX 阶段才能确定是否跳转，此时 I3 已经进入 ID 阶段。\n"
               "如果跳转成功，I3 就是错误取入的指令，必须冲刷（Flush）。",
        }[0 if scenario["name"] == "数据相关（RAW）" else 1 if scenario["name"] == "数据相关 + 控制相关混合" else 2],
        f"**第 3 步：设计方案**\n\n"
        f"解决方案：**{scenario['solution']}**\n\n"
        "具体设计：\n" +
        {
            0: "1. **转发（Forwarding/旁路）**：\n"
               "   - I1 在 EX 阶段计算出 R1 后，通过转发路径直接送给 I2 的 EX 阶段\n"
               "   - I2 在 EX 阶段计算出 R4 后，通过转发路径直接送给 I3 的 EX 阶段\n"
               "2. **转发路径**：ALU 输出 → ALU 输入（EX/MEM 旁路）\n"
               "3. 转发后无需插入气泡（阻塞），流水线全速运行",
            1: "1. **Load-Use 冒险处理**：\n"
               "   - I1(LW) 和 I2(ADD) 之间需**阻塞 1 个周期**（插入气泡）\n"
               "   - 因为 LW 在 MEM 阶段才得到数据，转发也无法完全消除该停顿\n"
               "2. **普通 RAW 处理**：\n"
               "   - I2(ADD)→I3(SW) 之间使用转发（EX/MEM 旁路）\n"
               "3. **结构冒险处理**：\n"
               "   - 如果 LW 和 SW 同时需要访存，可以通过分离指令/数据 Cache 解决",
            2: "1. **分支预测**：\n"
               "   - 静态预测：预测分支不跳转（继续顺序执行）\n"
               "   - 动态预测：使用分支历史表（BHT）或分支目标缓冲（BTB）\n"
               "2. **分支延迟槽**：\n"
               "   - 将 I3 放入分支延迟槽，无论分支是否成功都执行\n"
               "   - 前提是 I3 与分支条件无关\n"
               "3. **预测失败时的冲刷**：\n"
               "   - 若预测错误，则清空已进入流水线的错误指令（Flush）\n"
               "   - 从正确目标地址重新取指",
        }[0 if scenario["name"] == "数据相关（RAW）" else 1 if scenario["name"] == "数据相关 + 控制相关混合" else 2],
        f"**第 4 步：时空图描述**\n\n"
        "流水线执行情况（以 5 段流水线 IF → ID → EX → MEM → WB 为例）：\n\n"
        "```\n"
        "周期  |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |\n"
        "I1    | IF  | ID  | EX  | MEM | WB  |     |     |     |\n"
        f"I2    |     | IF  | ID  | {'ID*' if scenario['name'] == '数据相关（RAW）' else 'Bubble'}  | EX  | MEM | WB  |     |\n"
        f"I3    |     |     | {'IF' if scenario['name'] == '控制相关（分支指令）' else 'Bubble'}  | {'ID' if scenario['name'] == '控制相关（分支指令）' else 'Bubble'}  | {'ID*' if scenario['name'] == '数据相关（RAW）' else 'EX'}  | EX  | MEM | WB  |\n"
        "```\n"
        "（注：Bubble = 插入的气泡/空操作，ID* = 转发路径建立后的正常译码）",
        "**【408 考点提示】**\n"
        "1. 三种冒险类型：**结构冒险**（硬件资源冲突）、**数据冒险**（数据依赖）、**控制冒险**（分支跳转）\n"
        "2. 转发（Forwarding）可消除大多数 RAW 冒险，但 Load-Use 仍需 1 个气泡\n"
        "3. 分支预测策略是 408 常考热点，包括 1 位 / 2 位预测、BTB 等\n"
        "4. 流水线时空图是常见考题形式，需熟练绘制",
    ]

    answer = (
        f"冒险类型：{scenario['hazard_type']}。"
        f"解决方案：{scenario['solution']}。"
        f"通过转发消除数据相关，通过分支预测消除控制相关。"
    )

    return CompProblem(
        topic_id="co_pipeline_hazard",
        topic_name="指令流水线冒险分析",
        subject="计算机组成原理",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["流水线", "冒险", "数据相关", "控制相关", "转发", "分支预测"],
    )


# ── 7. 中断与异常 ──

def _gen_co_interrupt() -> CompProblem:
    n_interrupts = _rand_int(3, 5)
    priority_levels = [f"级别 {i}" for i in range(n_interrupts)]  # 0 = 最高
    interrupt_names = [f"中断源 {'ABCDEFGHIJKLMN'[i]}" for i in range(n_interrupts)]
    int_vectors = [_rand_int(0x10, 0xFF) for _ in range(n_interrupts)]

    # 一个中断请求场景
    current_priority = _rand_int(0, n_interrupts - 2)  # 当前正在处理的中断优先级
    requesting_mask = []
    for i in range(n_interrupts):
        if i != current_priority:
            requesting_mask.append(_rand_choice([True, False, False]))

    requesting = [i for i, r in enumerate(requesting_mask) if r]

    params = {
        "n_interrupts": n_interrupts,
        "int_names": interrupt_names,
        "int_vectors": int_vectors,
        "current_priority": current_priority,
        "requesting": requesting,
        "priority_levels": priority_levels,
    }

    int_table = "\n".join(
        f"| {interrupt_names[i]} | {priority_levels[i]} | 0x{int_vectors[i]:02X} |"
        for i in range(n_interrupts)
    )

    req_list = ", ".join(f"{interrupt_names[i]}" for i in requesting) if requesting else "无"

    question = (
        f"某计算机设有 **{n_interrupts} 级中断**，中断优先级和向量地址如下：\n\n"
        f"| 中断源 | 优先级 | 向量地址 |\n"
        f"|--------|--------|----------|\n"
        f"{int_table}\n\n"
        f"当前 CPU 正在处理 **{interrupt_names[current_priority]}**（{priority_levels[current_priority]}）的中断服务程序。\n"
        f"此时又有以下中断请求同时到达：**{req_list}**\n\n"
        f"请回答：\n"
        f"(1) CPU 的中断响应过程是怎样的？\n"
        f"(2) 最终会响应哪个中断？为什么？\n"
        f"(3) 画出中断响应和处理流程（文字描述）"
    )

    steps = [
        f"**【第 1 步：理解中断优先级机制】**\n\n"
        f"中断优先级从高到低：{' > '.join(priority_levels)}\n\n"
        f"规则：\n"
        f"- 当 CPU 正在处理某级中断时，**同级或更低级**的中断被屏蔽\n"
        f"- 只有**更高级**的中断才能打断当前处理（中断嵌套）\n\n"
        f"当前处理：**{interrupt_names[current_priority]}**（{priority_levels[current_priority]}）\n"
        f"同时到达的中断请求：**{req_list if requesting else '无'}**",
        f"**第 2 步：分析哪些中断可以被响应**\n\n"
        f"当前屏蔽级别为：{priority_levels[current_priority]} 及以下的全部中断\n\n"
        + ("\n".join(
            f"- {interrupt_names[i]}（{priority_levels[i]}）：{'**可以响应**——优先级更高' if i < current_priority else '**被屏蔽**——同级或更低'}"
            for i in range(n_interrupts)
            if i in requesting
        ) if requesting else "无其他中断请求，继续执行当前服务程序"),
        f"**第 3 步：中断响应过程**\n\n"
        "CPU 的中断响应遵循以下步骤：\n\n"
        "1. **关中断**：CPU 在响应中断时自动关闭中断允许标志（IF=0），防止干扰\n"
        "2. **保护断点**：将当前 PC（断点地址）压入堆栈\n"
        "3. **保护现场**：将通用寄存器和状态寄存器压入堆栈\n"
        "4. **查找中断向量**：CPU 通过硬件电路获取中断源对应的向量地址\n"
        "5. **转入中断服务程序**：根据向量地址找到中断服务程序的入口地址\n"
        "6. **开中断**：允许更高级的中断嵌套\n"
        "7. **执行中断服务程序**\n"
        "8. **中断返回**：恢复现场和断点，继续原程序",

        f"**第 4 步：确定最终响应的中断**\n\n"
        f"{'当前无其他中断请求，CPU 继续执行 ' + interrupt_names[current_priority] + ' 的服务程序' if not requesting else '比较请求中断的优先级：'}\n"
        + (
            "\n".join(
                f"- {interrupt_names[i]}（{priority_levels[i]}）：可响应"
                for i in requesting if i < current_priority
            )
            + "\n\n当前可响应的中断中，优先级最高的是："
            + (
                f"**{interrupt_names[min(requesting)]}**（{priority_levels[min(requesting)]}）"
                if any(i < current_priority for i in requesting)
                else "**没有可响应的中断**"
            )
            if requesting else ""
        )
        + "\n\nCPU 会 **暂停当前服务程序**，保存断点，然后转去执行优先级更高的中断服务程序。"
        + "处理完后返回原服务程序继续执行。",

        "**【408 考点提示】**\n"
        "1. 中断响应由**硬件（中断隐指令）**完成，主要是关中断、保护断点、查找中断向量\n"
        "2. 保护现场和恢复现场由**软件（中断服务程序）**完成\n"
        "3. 中断系统的设计原则：**高优先级可打断低优先级，同级别或低级别不能打断高级别**\n"
        "4. 向量中断 vs 查询中断：向量中断通过硬件提供向量地址快速定位；查询中断通过软件轮询\n"
        "5. 可屏蔽中断 vs 不可屏蔽中断（NMI）：NMI 优先级最高，用于紧急事件",
    ]

    answer = (
        f"CPU 正在处理 {interrupt_names[current_priority]}。"
        + (f"更高优先级的中断 {', '.join(interrupt_names[i] for i in requesting if i < current_priority)} 将打断当前程序，保存断点后优先处理。"
           if any(i < current_priority for i in requesting)
           else "无更高优先级中断，继续当前服务程序。")
    )

    return CompProblem(
        topic_id="co_interrupt",
        topic_name="中断与异常处理",
        subject="计算机组成原理",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["中断", "异常", "中断向量", "中断优先级", "嵌套中断", "断点保护"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 操作系统
# ═══════════════════════════════════════════════════════════════════════════

# ── 8. PV 操作 — 生产者-消费者 ──

def _gen_os_pv_producer_consumer() -> CompProblem:
    m = _rand_int(2, 5)     # 生产者数
    n = _rand_int(2, 5)     # 消费者数
    b = _rand_int(5, 15)    # 缓冲区大小

    params = {"m": m, "n": n, "b": b}

    question = (
        f"有 **{m} 个生产者**进程和 **{n} 个消费者**进程，\n"
        f"它们共享一个大小为 **{b}** 的环形缓冲区。\n\n"
        f"生产者每次向缓冲区写入一个数据单元，消费者每次从缓冲区读取一个数据单元。\n"
        f"要求生产者不能向满缓冲区写入，消费者不能从空缓冲区读取，且**互斥访问**缓冲区。\n\n"
        f"请用 **PV 操作（信号量机制）** 实现生产者和消费者的同步，要求：\n"
        f"(1) 定义所需的信号量及初值\n"
        f"(2) 写出生产者和消费者的程序代码（伪代码）\n"
        f"(3) 说明信号量的作用"
    )

    steps = [
        f"**第 1 步：定义信号量**\n\n"
        f"本题需要 {3} 个信号量：\n\n"
        f"| 信号量 | 初值 | 作用 |\n"
        f"|--------|------|------|\n"
        f"| `mutex` | 1 | 互斥访问缓冲区——保证任何时刻只有一个进程操作缓冲区 |\n"
        f"| `empty` | {b} | 缓冲区空闲单元数——生产者写入前 P(empty)，消费者读取后 V(empty) |\n"
        f"| `full` | 0 | 缓冲区已满单元数——消费者读取前 P(full)，生产者写入后 V(full) |",
        f"**第 2 步：生产者伪代码**\n\n"
        "```c\n"
        f"// 第 i 个生产者 (i = 0, 1, ..., {m - 1})\n"
        "void producer(int i) {{\n"
        "    while (1) {{\n"
        "        // 生产一个数据项\n"
        "        item = produce_item();\n\n"
        "        // 请求空缓冲区\n"
        "        P(empty);\n"
        "        // 互斥访问缓冲区\n"
        "        P(mutex);\n\n"
        "        // 将数据写入缓冲区\n"
        "        buffer[in] = item;\n"
        f"        in = (in + 1) % {b};\n\n"
        "        // 释放互斥锁\n"
        "        V(mutex);\n"
        "        // 增加满缓冲区计数\n"
        "        V(full);\n"
        "    }}\n"
        "}}\n"
        "```",
        f"**第 3 步：消费者伪代码**\n\n"
        "```c\n"
        f"// 第 j 个消费者 (j = 0, 1, ..., {n - 1})\n"
        "void consumer(int j) {{\n"
        "    while (1) {{\n"
        "        // 请求满缓冲区\n"
        "        P(full);\n"
        "        // 互斥访问缓冲区\n"
        "        P(mutex);\n\n"
        "        // 从缓冲区读取数据\n"
        "        item = buffer[out];\n"
        f"        out = (out + 1) % {b};\n\n"
        "        // 释放互斥锁\n"
        "        V(mutex);\n"
        "        // 增加空缓冲区计数\n"
        "        V(empty);\n\n"
        "        // 消费数据\n"
        "        consume_item(item);\n"
        "    }}\n"
        "}}\n"
        "```",
        f"**第 4 步：信号量作用分析**\n\n"
        f"1. **`mutex`（互斥信号量）**：\n"
        f"   保证 {m} 个生产者和 {n} 个消费者互斥访问缓冲区。\n"
        f"   P(mutex) 和 V(mutex) 之间的区域为**临界区**。\n\n"
        f"2. **`empty`（资源信号量）**：\n"
        f"   初值为 {b}，代表缓冲区有 {b} 个空位。\n"
        f"   生产者 P(empty) 申请空位，消费者 V(empty) 释放空位。\n\n"
        f"3. **`full`（资源信号量）**：\n"
        f"   初值为 0，代表缓冲区初始为空。\n"
        f"   消费者 P(full) 申请取数据，生产者 V(full) 释放数据。\n\n"
        f"**【注意】**P(empty) 和 P(mutex) 的顺序**不可交换**！\n"
        f"如果先 P(mutex) 再 P(empty)，当缓冲区满时生产者会占用互斥锁然后阻塞在 P(empty)，\n"
        f"导致消费者永远无法进入临界区取走数据——**死锁**！",
        "**【408 考点提示】**\n"
        "1. P(empty/full) 和 P(mutex) 的顺序是**经典考点**，必须先资源后互斥\n"
        "2. V 操作的顺序**可以交换**，不影响正确性\n"
        "3. 生产者-消费者模型是 408 信号量问题的**母题**，读者-写者、哲学家进餐都是其变体\n"
        "4. 理解信号量的本质：P = 申请资源（可能阻塞），V = 释放资源（唤醒等待者）",
    ]

    answer = (
        f"信号量：mutex=1（互斥），empty={b}（空位计数），full=0（数据计数）。\n"
        f"生产者：P(empty)→P(mutex)→写缓冲→V(mutex)→V(full)\n"
        f"消费者：P(full)→P(mutex)→读缓冲→V(mutex)→V(empty)\n"
        f"要点：先资源(P(empty/full))后互斥(P(mutex))，防止死锁。"
    )

    return CompProblem(
        topic_id="os_pv_producer_consumer",
        topic_name="PV操作：生产者-消费者",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["PV操作", "信号量", "生产者消费者", "同步", "互斥", "死锁"],
        has_pseudocode=True,
    )


# ── 9. 文件系统 — 混合索引分配 ──

# ═══════════════════════════════════════════════════════════════════════════
# ── 8-2. PV 操作 — 读者-写者问题（读者优先） ──

def _gen_os_pv_readers_writers() -> CompProblem:
    m = _rand_int(3, 6)     # 读者数
    n = _rand_int(1, 3)     # 写者数

    params = {"m": m, "n": n}

    question = (
        f"有 **{m} 个读者**进程和 **{n} 个写者**进程，它们共享一个数据文件。\n\n"
        f"要求：\n"
        f"1. 多个读者**可以同时**读取文件\n"
        f"2. 写者与任何其他进程**互斥**访问文件（写者写时读者不能读，读者读时写者不能写）\n"
        f"3. 采用**读者优先**策略：只要有一个读者在读，后续读者可以直接读，\n"
        f"   写者必须等待所有读者读完才能写\n\n"
        f"请用 **PV 操作（信号量机制）** 实现读者和写者的同步，要求：\n"
        f"(1) 定义所需的信号量及初值\n"
        f"(2) 写出读者和写者的程序代码（伪代码）\n"
        f"(3) 说明如果采用写者优先策略，应如何修改"
    )

    steps = [
        "**第 1 步：定义信号量**\n\n"
        "| 信号量 | 初值 | 作用 |\n"
        "|--------|------|------|\n"
        "| `rw_mutex` | 1 | 互斥访问文件——写者进入/离开时申请/释放，读者仅在第一个读者进入和最后一个读者离开时申请/释放 |\n"
        "| `mutex` | 1 | 保护读者计数器 `read_count` 的互斥信号量 |\n\n"
        "同时需要整型变量 `read_count = 0`，记录当前正在读的读者数量。",
        "**第 2 步：读者伪代码**\n\n"
        "```c\n"
        f"// 第 i 个读者 (i = 0, 1, ..., {m - 1})\n"
        "void reader(int i) {\n"
        "    while (1) {\n"
        "        P(mutex);              // 互斥访问 read_count\n"
        "        if (read_count == 0)   // 第一个读者\n"
        "            P(rw_mutex);       // 申请读权限（阻止写者进入）\n"
        "        read_count++;          // 读者计数 +1\n"
        "        V(mutex);              // 释放 read_count 互斥锁\n\n"
        "        // ----- 读文件 -----\n"
        "        read_file();\n"
        "        // ------------------\n\n"
        "        P(mutex);              // 互斥访问 read_count\n"
        "        read_count--;          // 读者计数 -1\n"
        "        if (read_count == 0)   // 最后一个读者\n"
        "            V(rw_mutex);       // 释放读权限（允许写者进入）\n"
        "        V(mutex);              // 释放 read_count 互斥锁\n"
        "    }\n"
        "}\n"
        "```",
        "**第 3 步：写者伪代码**\n\n"
        "```c\n"
        f"// 第 j 个写者 (j = 0, 1, ..., {n - 1})\n"
        "void writer(int j) {\n"
        "    while (1) {\n"
        "        P(rw_mutex);           // 申请写权限（必须等待所有读者读完）\n\n"
        "        // ----- 写文件 -----\n"
        "        write_file();\n"
        "        // ------------------\n\n"
        "        V(rw_mutex);           // 释放写权限\n"
        "    }\n"
        "}\n"
        "```",
        "**第 4 步：信号量作用分析**\n\n"
        "1. **`rw_mutex`**：文件读写权限信号量。\n"
        "   写者每次写都需要占用；读者仅在第一个读者进入时占用、最后一个读者离开时释放。\n"
        "   这保证了「多个读者可以同时读」的特性。\n\n"
        "2. **`mutex` + `read_count`**：保证多个读者对 `read_count` 的修改互斥进行，\n"
        "   防止计数竞争条件。\n\n"
        f"3. 当第一个读者执行 P(rw_mutex) 后，{n} 个写者都将阻塞在 P(rw_mutex) 上，\n"
        f"   而后续的读者可以直接进入——**读者优先**。\n\n"
        "**【写者优先策略】**\n\n"
        "若要实现写者优先，可以增加一个信号量和计数器：\n\n"
        "```c\n"
        "semaphore write_mutex = 1;     // 写者互斥信号量\n"
        "int write_count = 0;           // 等待写的写者数\n\n"
        "void writer(int j) {\n"
        "    P(write_mutex);\n"
        "    write_count++;\n"
        "    if (write_count == 1)      // 第一个写者\n"
        "        P(rw_mutex);           // 阻止新读者进入\n"
        "    V(write_mutex);\n\n"
        "    P(rw_mutex);               // 申请写权限\n"
        "    write_file();\n"
        "    V(rw_mutex);\n\n"
        "    P(write_mutex);\n"
        "    write_count--;\n"
        "    if (write_count == 0)      // 最后一个写者\n"
        "        V(rw_mutex);           // 允许读者进入\n"
        "    V(write_mutex);\n"
        "}\n"
        "```\n\n"
        "此时读者进入前需检查是否有写者在等待：\n"
        "```c\n"
        "void reader(int i) {\n"
        "    P(mutex);\n"
        "    if (read_count == 0)\n"
        "        P(rw_mutex);           // 读受阻于写者\n"
        "    read_count++;\n"
        "    V(mutex);\n"
        "    read_file();\n"
        "    P(mutex);\n"
        "    read_count--;\n"
        "    if (read_count == 0)\n"
        "        V(rw_mutex);\n"
        "    V(mutex);\n"
        "}\n"
        "```",
        "**【408 考点提示】**\n"
        "1. 读者-写者问题是**信号量应用的高频考点**，区分读者优先和写者优先\n"
        "2. 关键在于理解 `read_count` 的作用——它让多个读者只申请一次 `rw_mutex`\n"
        "3. 写者优先需要**对称结构**：写者计数器 + 写者互斥锁\n"
        "4. 注意死锁风险：若读者优先且写者一直得不到机会，会导致**写者饥饿**",
    ]

    answer = (
        "信号量：rw_mutex=1（文件互斥），mutex=1（保护read_count）。\n"
        "读者：P(mutex)→若read_count==0则P(rw_mutex)→read_count++→V(mutex)→读→P(mutex)→"
        "read_count--→若read_count==0则V(rw_mutex)→V(mutex)\n"
        "写者：P(rw_mutex)→写→V(rw_mutex)\n"
        "读者优先：第一个读者阻止写者，后续读者直接进入；写者优先需对称结构。"
    )

    return CompProblem(
        topic_id="os_pv_readers_writers",
        topic_name="PV操作：读者-写者问题",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["PV操作", "信号量", "读者写者", "同步", "互斥", "读者优先", "写者优先", "饥饿"],
        has_pseudocode=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# ── 8-3. PV 操作 — 哲学家进餐问题 ──

def _gen_os_pv_dining_philosophers() -> CompProblem:
    n = _rand_choice([5])  # 经典 5 位哲学家

    params = {"n": n}

    question = (
        f"有 **{n} 位哲学家**围坐在一张圆桌旁，每人面前有一碗面条，\n"
        f"每两位哲学家之间有一把叉子（共 {n} 把叉子）。\n\n"
        f"哲学家的行为是周期性循环：\n"
        f"1. **思考**（不占用任何资源）\n"
        f"2. **拿起两把叉子**（左右各一把）\n"
        f"3. **吃面条**（使用两把叉子）\n"
        f"4. **放下两把叉子**\n"
        f"5. 回到思考状态\n\n"
        f"请用 **PV 操作（信号量机制）** 实现，要求：\n"
        f"(1) 定义所需的信号量及初值\n"
        f"(2) 写出哲学家的程序代码\n"
        f"(3) 说明你的方案如何**防止死锁**"
    )

    steps = [
        "**第 1 步：定义信号量**\n\n"
        f"每把叉子对应一个互斥信号量：\n\n"
        "```c\n"
        f"semaphore chopstick[{n}] = {{1, 1, 1, 1, 1}};  // 每把叉子初值为 1\n"
        "semaphore mutex = 1;   // 互斥访问取叉子过程（防止死锁方案）\n"
        "```\n",
        "**第 2 步：可能产生死锁的错误方案**\n\n"
        "```c\n"
        "void philosopher(int i) {\n"
        "    while (1) {\n"
        "        think();\n"
        "        P(chopstick[i]);               // 拿左叉子\n"
        "        P(chopstick[(i + 1) % 5]);     // 拿右叉子\n"
        "        eat();\n"
        "        V(chopstick[i]);               // 放左叉子\n"
        "        V(chopstick[(i + 1) % 5]);     // 放右叉子\n"
        "    }\n"
        "}\n"
        "```\n\n"
        "**问题**：若所有哲学家同时拿起左叉子，则所有人都会阻塞在拿右叉子上——**死锁**。\n",
        f"**第 3 步：正确答案——使用互斥锁限制同时取叉子的人数**\n\n"
        "```c\n"
        f"// 第 i 位哲学家 (i = 0, 1, ..., {n - 1})\n"
        "void philosopher(int i) {\n"
        "    while (1) {\n"
        "        think();                     // 思考\n\n"
        "        P(mutex);                    // 进入临界区（保证一次只有一人拿叉子）\n"
        "        P(chopstick[i]);             // 拿左叉子\n"
        "        P(chopstick[(i + 1) % 5]);   // 拿右叉子\n"
        "        V(mutex);                    // 离开临界区\n\n"
        "        eat();                       // 吃面条\n\n"
        "        V(chopstick[i]);             // 放左叉子\n"
        "        V(chopstick[(i + 1) % 5]);   // 放右叉子\n"
        "    }\n"
        "}\n"
        "```\n\n"
        "此方案通过 `P(mutex)/V(mutex)` 保证一次**只有一位哲学家**尝试取叉子，\n"
        "从而避免了所有哲学家同时拿左叉子的情况，**彻底消除死锁**。\n",
        "**第 4 步：其他可行的防死锁方案**\n\n"
        "方案一：**限制同时吃饭的人数**（最多 4 人可以同时吃饭）\n"
        "```c\n"
        "semaphore room = 4;  // 最多 4 人同时进餐\n\n"
        "void philosopher(int i) {\n"
        "    while (1) {\n"
        "        think();\n"
        "        P(room);                     // 申请进入餐厅\n"
        "        P(chopstick[i]);             // 拿左叉子\n"
        "        P(chopstick[(i + 1) % 5]);   // 拿右叉子\n"
        "        eat();\n"
        "        V(chopstick[i]);\n"
        "        V(chopstick[(i + 1) % 5]);\n"
        "        V(room);                     // 离开餐厅\n"
        "    }\n"
        "}\n"
        "```\n\n"
        "方案二：**奇偶号哲学家拿叉子顺序不同**\n"
        "```c\n"
        "void philosopher(int i) {\n"
        "    while (1) {\n"
        "        think();\n"
        "        if (i % 2 == 0) {            // 偶数号：先左后右\n"
        "            P(chopstick[i]);\n"
        "            P(chopstick[(i + 1) % 5]);\n"
        "        } else {                     // 奇数号：先右后左\n"
        "            P(chopstick[(i + 1) % 5]);\n"
        "            P(chopstick[i]);\n"
        "        }\n"
        "        eat();\n"
        "        if (i % 2 == 0) {\n"
        "            V(chopstick[i]);\n"
        "            V(chopstick[(i + 1) % 5]);\n"
        "        } else {\n"
        "            V(chopstick[(i + 1) % 5]);\n"
        "            V(chopstick[i]);\n"
        "        }\n"
        "    }\n"
        "}\n"
        "```\n"
        "理由：偶数号哲学家先左后右，奇数号先右后左，不会出现「循环等待」的死锁条件。\n",
        "**【408 考点提示】**\n"
        "1. 哲学家进餐问题是**死锁预防/避免**的经典案例\n"
        "2. 死锁四个必要条件：互斥、请求与保持、不可剥夺、循环等待——打破任意一个即可防死锁\n"
        "3. 方案一打破「互斥」（限制人数），方案二打破「循环等待」（改变拿叉子顺序）\n"
        "4. 2023 年 408 真题考查了本题的变体形式，注意信号量初值的设置"
    ]

    answer = (
        f"信号量：chopstick[{n}]={{1,1,1,1,1}}（每把叉子互斥），加 mutex=1 限制同时拿叉子。\n"
        "哲学家：P(mutex)→P(左叉)→P(右叉)→V(mutex)→吃→V(左叉)→V(右叉)\n"
        "防死锁原理：mutex 保证一次只有一人拿叉子，打破循环等待。\n"
        "替代方案：限4人同时吃饭 / 奇偶号不同取叉顺序。"
    )

    return CompProblem(
        topic_id="os_pv_dining_philosophers",
        topic_name="PV操作：哲学家进餐问题",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["PV操作", "信号量", "哲学家进餐", "同步", "互斥", "死锁", "死锁预防"],
        has_pseudocode=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# ── 8-4. PV 操作 — 吸烟者问题 ──

def _gen_os_pv_smokers() -> CompProblem:
    params = {}

    question = (
        "假设一个系统中有 **三个吸烟者** 进程和一个 **供应者** 进程。\n\n"
        "每个吸烟者需要三种材料（烟草、纸、火柴）才能卷烟吸烟。\n"
        "三个吸烟者分别拥有其中一种材料的无限供应：\n"
        "- 吸烟者 A：拥有烟草（需要纸和火柴）\n"
        "- 吸烟者 B：拥有纸（需要烟草和火柴）\n"
        "- 吸烟者 C：拥有火柴（需要烟草和纸）\n\n"
        "供应者每次提供**两种材料**放在桌上，拥有第三种材料的吸烟者可以取走材料\n"
        "并卷烟吸烟（其他吸烟者因缺少材料必须等待）。\n\n"
        "请用 **PV 操作（信号量机制）** 实现同步，要求：\n"
        "(1) 定义所需的信号量及初值\n"
        "(2) 写出供应者和吸烟者的程序代码\n"
        "(3) 说明为什么不会产生死锁"
    )

    steps = [
        "**第 1 步：问题分析**\n\n"
        "供应者随机提供两种材料，只有拥有第三种材料的吸烟者能成功取走。\n"
        "这本质上是一个**生产者（供应者）-多消费者（三个吸烟者）**的同步问题，\n"
        "但每次产品类型不同，只能被特定的消费者消费。\n\n"
        "需要为每种可能的材料组合设置信号量，让供应者「通知」对应的吸烟者。",
        "**第 2 步：定义信号量**\n\n"
        "```c\n"
        "semaphore offer_A = 0;   // 桌上是否有供应给 A 的材料（纸+火柴）\n"
        "semaphore offer_B = 0;   // 桌上是否有供应给 B 的材料（烟草+火柴）\n"
        "semaphore offer_C = 0;   // 桌上是否有供应给 C 的材料（烟草+纸）\n"
        "semaphore finish = 0;    // 吸烟者是否吸完（通知供应者放下一组材料）\n"
        "int turn = 0;            // 表示当前提供的是哪种组合（0=A, 1=B, 2=C）\n"
        "```\n\n"
        "注意：桌上**同时最多只有一组材料**，吸烟者取走后才能放下一个。",
        "**第 3 步：供应者伪代码**\n\n"
        "```c\n"
        "void provider() {\n"
        "    while (1) {\n"
        "        // 随机生成材料组合\n"
        "        turn = random() % 3;   // 0, 1, 2\n\n"
        "        if (turn == 0) {\n"
        "            // 提供纸和火柴 → 通知 A\n"
        "            V(offer_A);\n"
        "        } else if (turn == 1) {\n"
        "            // 提供烟草和火柴 → 通知 B\n"
        "            V(offer_B);\n"
        "        } else {\n"
        "            // 提供烟草和纸 → 通知 C\n"
        "            V(offer_C);\n"
        "        }\n\n"
        "        P(finish);              // 等待吸烟者吸完\n"
        "    }\n"
        "}\n"
        "```",
        "**第 4 步：三个吸烟者伪代码**\n\n"
        "```c\n"
        "// 吸烟者 A（拥有烟草，需要纸和火柴）\n"
        "void smoker_A() {\n"
        "    while (1) {\n"
        "        P(offer_A);             // 等待供应者放纸和火柴\n"
        "        // 取走纸和火柴，卷烟\n"
        "        smoke();                // 吸烟\n"
        "        V(finish);              // 通知供应者已吸完\n"
        "    }\n"
        "}\n\n"
        "// 吸烟者 B（拥有纸，需要烟草和火柴）\n"
        "void smoker_B() {\n"
        "    while (1) {\n"
        "        P(offer_B);             // 等待供应者放烟草和火柴\n"
        "        smoke();\n"
        "        V(finish);\n"
        "    }\n"
        "}\n\n"
        "// 吸烟者 C（拥有火柴，需要烟草和纸）\n"
        "void smoker_C() {\n"
        "    while (1) {\n"
        "        P(offer_C);             // 等待供应者放烟草和纸\n"
        "        smoke();\n"
        "        V(finish);\n"
        "    }\n"
        "}\n"
        "```",
        "**第 5 步：信号量作用与为什么不会死锁**\n\n"
        "1. **`offer_A/offer_B/offer_C`** 是三类不同产品的资源信号量，初值为 0。\n"
        "   供应者 `V()` 生产产品（唤醒对应吸烟者），吸烟者 `P()` 消费产品（阻塞等待）。\n\n"
        "2. **`finish`** 初值为 0，吸烟者吸完后 `V(finish)` 通知供应者。\n"
        "   供应者 `P(finish)` 等待吸烟者完成——确保桌上始终只有**一组材料**。\n\n"
        "3. **不会死锁的原因**：\n"
        "   - 任何时候桌上只有一组材料（`finish` 保证供应者和吸烟者之间的同步）\n"
        "   - 每组材料只唤醒**唯一一个**对应的吸烟者\n"
        "   - 三个吸烟者各自阻塞在自己的 `offer` 信号量上，没有竞争同一资源\n"
        "   - 不存在循环等待的条件\n\n"
        "**【408 考点提示】**\n"
        "1. 吸烟者问题是「**多生产者-多消费者**」的变体，关键是为每种产品类型单独设信号量\n"
        "2. `finish` 信号量实现了「一次只有一组材料在桌上」的约束\n"
        "3. 供应者每次 `V()` 一个信号量，实现了**分类唤醒**——只有正确类型的吸烟者被唤醒\n"
        "4. 注意区分：此处是供应者生产三类不同产品，用三个信号量分别表示"
    ]

    answer = (
        "信号量：offer_A=0, offer_B=0, offer_C=0（三类材料组合），finish=0（同步信号量）。\n"
        "供应者：随机 V(offer_X) → P(finish)\n"
        "吸烟者A: P(offer_A)→吸→V(finish)\n"
        "吸烟者B: P(offer_B)→吸→V(finish)\n"
        "吸烟者C: P(offer_C)→吸→V(finish)\n"
        "不会死锁：每次只放一组材料，只唤醒一个吸烟者，无资源竞争/循环等待。"
    )

    return CompProblem(
        topic_id="os_pv_smokers",
        topic_name="PV操作：吸烟者问题",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["PV操作", "信号量", "吸烟者", "同步", "生产者消费者", "多消费者"],
        has_pseudocode=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# ── 8-5. PV 操作 — 理发师问题（Sleeping Barber） ──

def _gen_os_pv_barber() -> CompProblem:
    n_chairs = _rand_int(2, 5)   # 等待椅子数

    params = {"n_chairs": n_chairs}

    question = (
        f"一个理发店里有 **1 位理发师**、**1 把理发椅** 和 **{n_chairs} 把等待椅**。\n\n"
        f"规则如下：\n"
        f"1. 如果没有顾客，理发师在自己的椅子上**睡觉**\n"
        f"2. 当有顾客到达时：\n"
        f"   - 如果理发师在睡觉，则叫醒理发师理发\n"
        f"   - 如果理发师正在忙但有空等待椅，顾客在等待椅上等待\n"
        f"   - 如果等待椅全满，顾客直接**离开**\n"
        f"3. 理发师理完一个顾客后，如有等待顾客则叫下一个，否则继续睡觉\n\n"
        f"请用 **PV 操作（信号量机制）** 实现理发师与顾客之间的同步，要求：\n"
        f"(1) 定义所需的信号量及初值\n"
        f"(2) 写出理发师和顾客的程序代码\n"
        f"(3) 说明各信号量的作用"
    )

    steps = [
        f"**第 1 步：定义信号量**\n\n"
        "| 信号量 | 初值 | 作用 |\n"
        "|--------|------|------|\n"
        f"| `waiting_chairs` | {n_chairs} | 等待椅资源计数——顾客申请空椅，离开时释放 |\n"
        "| `barber_ready` | 0 | 理发师是否就绪——顾客坐定后 V() 通知理发师开始理发 |\n"
        "| `customer_ready` | 0 | 是否有顾客等待——理发师 P() 等待顾客，顾客 V() 通知理发师 |\n"
        "| `mutex` | 1 | 保护 `waiting` 变量的互斥信号量 |\n\n"
        "同时需要整型变量 `waiting = 0`，记录当前等待人数。",
        f"**第 2 步：理发师伪代码**\n\n"
        "```c\n"
        "void barber() {\n"
        "    while (1) {\n"
        "        P(customer_ready);       // 等待顾客到来（若无顾客则睡觉）\n"
        "        // 被顾客唤醒\n"
        "        cut_hair();              // 理发\n"
        "        V(barber_ready);         // 通知顾客理发结束\n"
        "    }\n"
        "}\n"
        "```\n\n"
        "理发师 `P(customer_ready)` 如果没有顾客，就**阻塞在此**——对应「睡觉」。\n"
        "顾客 `V(customer_ready)` 对应「叫醒理发师」。",
        f"**第 3 步：顾客伪代码**\n\n"
        "```c\n"
        "void customer() {\n"
        "    P(mutex);                    // 互斥访问 waiting\n"
        "    if (waiting < {n_chairs}) {{   // 还有空椅\n"
        "        waiting++;               // 等待人数 +1\n"
        "        V(mutex);\n"
        "        V(customer_ready);       // 通知理发师有顾客\n"
        "        P(barber_ready);         // 等待理发师理发\n"
        "        // ----- 理发中 -----\n"
        "        P(mutex);\n"
        "        waiting--;               // 等待人数 -1（离开等待椅）\n"
        "        V(mutex);\n"
        "    }} else {{\n"
        "        V(mutex);\n"
        "        // 没有空椅，直接离开\n"
        "    }}\n"
        "}\n"
        "```",
        f"**第 4 步：信号量作用分析**\n\n"
        f"1. **`customer_ready`**（初值 0）：\n"
        f"   顾客到达后 V()，理发师 P() 等待——实现了叫醒机制。\n"
        f"   理发师在无顾客时阻塞在此，不占用 CPU。\n\n"
        f"2. **`barber_ready`**（初值 0）：\n"
        f"   理发结束后 V()，顾客 P() 等待——实现理发师与顾客的一对一同步。\n\n"
        f"3. **`waiting_chairs + waiting` 计数**：\n"
        f"   控制同时最多 {n_chairs} 位顾客在等待椅上等待，超过则离开。\n\n"
        f"4. **`mutex`**：保护 `waiting` 变量修改的互斥。\n\n"
        f"**关键点：为什么不会死锁？**\n"
        f"- 顾客 `V(customer_ready)` 后 `P(barber_ready)` 等待理发——消息传递式同步\n"
        f"- 理发师 `P(customer_ready)` 后 `V(barber_ready)` 通知顾客——一一对应\n"
        f"- 每个信号量的 V 和 P 操作成对出现，且顺序正确",
        "**【408 考点提示】**\n"
        "1. 理发师问题是**「信号量实现同步」**的经典模型，类似生产者-消费者但更复杂\n"
        "2. 核心思路：用两个信号量实现双向通知（顾客叫醒理发师、理发师通知顾客结束）\n"
        "3. 等待椅限制是**资源计数信号量**的应用——控制并发访问的资源数量\n"
        "4. 此模型可扩展为**多理发师**场景（增加一个 `barber_count` 互斥信号量）"
    ]

    answer = (
        f"信号量：customer_ready=0（有顾客等待），barber_ready=0（理发师就绪），\n"
        f"waiting_chairs={n_chairs}（空椅数），mutex=1（保护 waiting）。\n"
        f"理发师：P(customer_ready)→理发→V(barber_ready)\n"
        f"顾客：P(mutex)→if有空椅→waiting++→V(mutex)→V(customer_ready)→\n"
        f"      P(barber_ready)→理发→P(mutex)→waiting--→V(mutex)\n"
        f"      无空椅则直接离开。"
    )

    return CompProblem(
        topic_id="os_pv_barber",
        topic_name="PV操作：理发师问题",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["PV操作", "信号量", "理发师", "同步", "互斥", "资源计数"],
        has_pseudocode=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# ── 8-6. PV 操作 — 水果盘问题（苹果橘子） ──

def _gen_os_pv_fruit_plate() -> CompProblem:
    plate_size = _rand_int(2, 5)  # 盘子容量
    plate_size_display = "足够大" if plate_size > 3 else str(plate_size)

    params = {"plate_size": plate_size}

    question = (
        "桌子上有一个盘子，每次只能放入一个水果。\n"
        f"爸爸专门向盘子中放**苹果**，妈妈专门向盘子中放**橘子**。\n"
        f"儿子专门等盘中的**橘子**，女儿专门等盘中的**苹果**。\n"
        f"盘子容量为 **{plate_size_display}**（可放多个水果）。\n\n"
        f"四个进程同时运行：\n"
        f"- 爸爸进程：生产苹果放入盘子\n"
        f"- 妈妈进程：生产橘子放入盘子\n"
        f"- 儿子进程：从盘中取橘子\n"
        f"- 女儿进程：从盘中取苹果\n\n"
        f"请用 **PV 操作（信号量机制）** 实现同步，要求：\n"
        f"(1) 定义所需的信号量及初值\n"
        f"(2) 写出四个进程的程序代码\n"
        f"(3) 说明你的解决方案与标准生产者-消费者问题的异同"
    )

    steps = [
        f"**第 1 步：定义信号量**\n\n"
        "需要 4 个信号量：\n\n"
        "| 信号量 | 初值 | 作用 |\n"
        "|--------|------|------|\n"
        "| `mutex` | 1 | 互斥访问盘子 |\n"
        f"| `empty` | {plate_size} | 盘子的空位数量 |\n"
        "| `apple` | 0 | 盘中苹果的数量（儿子等待此信号量） |\n"
        "| `orange` | 0 | 盘中橘子的数量（女儿等待此信号量） |\n\n"
        "本质上是「**两类产品的生产者-消费者**」，用两种不同的资源信号量区分产品。",
        "**第 2 步：爸爸（放苹果）与妈妈（放橘子）**\n\n"
        "```c\n"
        "// 爸爸进程：放苹果\n"
        "void dad() {\n"
        "    while (1) {\n"
        "        P(empty);                // 申请空位\n"
        "        P(mutex);                // 互斥访问盘子\n"
        "        put_apple_on_plate();    // 放苹果\n"
        "        V(mutex);                // 释放互斥锁\n"
        "        V(apple);                // 增加苹果数量\n"
        "    }\n"
        "}\n\n"
        "// 妈妈进程：放橘子\n"
        "void mom() {\n"
        "    while (1) {\n"
        "        P(empty);                // 申请空位\n"
        "        P(mutex);                // 互斥访问盘子\n"
        "        put_orange_on_plate();   // 放橘子\n"
        "        V(mutex);                // 释放互斥锁\n"
        "        V(orange);               // 增加橘子数量\n"
        "    }\n"
        "}\n"
        "```",
        "**第 3 步：儿子（取橘子）与女儿（取苹果）**\n\n"
        "```c\n"
        "// 儿子进程：取橘子\n"
        "void son() {\n"
        "    while (1) {\n"
        "        P(orange);               // 等待有橘子\n"
        "        P(mutex);                // 互斥访问盘子\n"
        "        take_orange();           // 取橘子\n"
        "        V(mutex);                // 释放互斥锁\n"
        "        V(empty);                // 增加空位\n"
        "        eat_orange();\n"
        "    }\n"
        "}\n\n"
        "// 女儿进程：取苹果\n"
        "void daughter() {\n"
        "    while (1) {\n"
        "        P(apple);                // 等待有苹果\n"
        "        P(mutex);                // 互斥访问盘子\n"
        "        take_apple();            // 取苹果\n"
        "        V(mutex);                // 释放互斥锁\n"
        "        V(empty);                // 增加空位\n"
        "        eat_apple();\n"
        "    }\n"
        "}\n"
        "```",
        "**第 4 步：与标准生产者-消费者问题的异同**\n\n"
        "**相同点**：\n"
        "- 都是通过 `mutex` 互斥访问共享缓冲区\n"
        "- 都使用 `empty` 空位信号量控制缓冲区容量\n"
        "- 都遵循「先资源后互斥」的原则防止死锁\n\n"
        "**不同点**：\n"
        "- 标准生产者-消费者：所有生产者生产同类产品，所有消费者消费同类产品\n"
        "  使用单一的 `full` 信号量计数\n"
        "- 水果盘问题：**两类产品**（苹果/橘子），用 `apple` 和 `orange` **两个**资源信号量\n"
        "  **特定的消费者只消费特定的产品**（儿子只取橘子，女儿只取苹果）\n"
        "- 本质上是「**多类**生产者-消费」模型，每类产品有独立的资源信号量\n\n"
        "更一般地，如果有 m 类产品，就需要 m 个资源信号量进行分类计数和唤醒。",
        "**【408 考点提示】**\n"
        "1. 水果盘问题（苹果橘子问题）是生产者-消费者的**经典变体**，考研常考\n"
        "2. 关键思路：不同产品 = 不同的资源信号量\n"
        "3. 当盘子里最多只能放一个水果时（容量为1），可省略 `mutex`（因为 `empty` 和 `apple/orange` 已保证互斥）\n"
        "4. 更复杂的变体：多个爸爸、多个妈妈、多个儿子、多个女儿同时运行——此时 `mutex` 不可省略"
    ]

    answer = (
        f"信号量：mutex=1（盘子互斥），empty={plate_size}（空位），apple=0（苹果计数），orange=0（橘子计数）。\n"
        "爸爸：P(empty)→P(mutex)→放苹果→V(mutex)→V(apple)\n"
        "妈妈：P(empty)→P(mutex)→放橘子→V(mutex)→V(orange)\n"
        "儿子：P(orange)→P(mutex)→取橘子→V(mutex)→V(empty)\n"
        "女儿：P(apple)→P(mutex)→取苹果→V(mutex)→V(empty)\n"
        "核心：不同产品用不同资源信号量分类消费。"
    )

    return CompProblem(
        topic_id="os_pv_fruit_plate",
        topic_name="PV操作：水果盘问题（苹果橘子）",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["PV操作", "信号量", "水果盘", "苹果橘子", "同步", "互斥", "多类生产者消费者"],
        has_pseudocode=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# ── 8-7. PV 操作 — 过桥问题（独木桥） ──

def _gen_os_pv_bridge() -> CompProblem:
    direction_names = ["东→西", "西→东"]
    d1, d2 = direction_names

    params = {}

    question = (
        f"有一座独木桥，同一时刻只允许**同一方向**的行人过桥，\n"
        f"不同方向的行人互斥使用桥。\n\n"
        f"行人有两种方向：{d1} 和 {d2}。\n\n"
        f"要求：\n"
        f"1. 同一方向的行人可以**同时**过桥\n"
        f"2. 两个方向的行人**互斥**使用桥（一个方向有人过桥时，另一方向的人不能上桥）\n"
        f"3. 不会出现**饥饿**（某一方向长时间被阻塞）\n\n"
        f"请用 **PV 操作（信号量机制）** 实现行人的过桥同步，要求：\n"
        f"(1) 定义所需的信号量及初值\n"
        f"(2) 写出两个方向行人的程序代码\n"
        f"(3) 说明你的方案如何防止死锁和饥饿"
    )

    steps = [
        "**第 1 步：问题分析**\n\n"
        "这个问题本质上是**「双向读者-写者」**问题：\n"
        "同一方向的行人相当于『读者』（可以同时过桥），\n"
        "两个方向之间需要互斥（相当于两个互斥的『写者』）。\n\n"
        "思路：对每个方向设置过桥人数计数器，\n"
        "只有当本方向有人时，才对另一个方向实施『封锁』。",
        "**第 2 步：定义信号量和变量**\n\n"
        "```c\n"
        "semaphore bridge = 1;        // 桥的互斥信号量\n"
        "semaphore mutex_east = 1;    // 保护东→西方向计数\n"
        "semaphore mutex_west = 1;    // 保护西→东方向计数\n"
        "int east_count = 0;          // 当前东→西方向过桥人数\n"
        "int west_count = 0;          // 当前西→东方向过桥人数\n"
        "```\n\n"
        "关键思想：对每个方向分别维护计数器，\n"
        "当某方向的第一个行人过桥时申请 `bridge`（阻止另一方向），\n"
        "最后一个行人离开时释放 `bridge`（允许另一方向进入）。",
        "**第 3 步：东→西方向行人伪代码**\n\n"
        "```c\n"
        "void east_to_west() {\n"
        "    P(mutex_east);\n"
        "    east_count++;\n"
        "    if (east_count == 1)     // 第一个东→西方向的行人\n"
        "        P(bridge);           // 申请桥（阻止西→东方向）\n"
        "    V(mutex_east);\n\n"
        "    // ----- 过桥中 -----\n"
        "    cross_bridge_east_to_west();\n"
        "    // ------------------\n\n"
        "    P(mutex_east);\n"
        "    east_count--;\n"
        "    if (east_count == 0)     // 最后一个东→西方向的行人\n"
        "        V(bridge);           // 释放桥（允许西→东方向）\n"
        "    V(mutex_east);\n"
        "}\n"
        "```",
        "**第 4 步：西→东方向行人伪代码**\n\n"
        "```c\n"
        "void west_to_east() {\n"
        "    P(mutex_west);\n"
        "    west_count++;\n"
        "    if (west_count == 1)     // 第一个西→东方向的行人\n"
        "        P(bridge);           // 申请桥（阻止东→西方向）\n"
        "    V(mutex_west);\n\n"
        "    // ----- 过桥中 -----\n"
        "    cross_bridge_west_to_east();\n"
        "    // ------------------\n\n"
        "    P(mutex_west);\n"
        "    west_count--;\n"
        "    if (west_count == 0)     // 最后一个西→东方向的行人\n"
        "        V(bridge);           // 释放桥（允许东→西方向）\n"
        "    V(mutex_west);\n"
        "}\n"
        "```",
        "**第 5 步：防死锁和饥饿分析**\n\n"
        "**1. 防止死锁**\n"
        "- 每个方向内部使用 `mutex_east`/`mutex_west` 保护各自的计数器——互斥访问\n"
        "- `bridge` 是桥的使用权，两个方向的第一个行人竞争申请\n"
        "- 不存在循环等待条件（只竞争一个资源 `bridge`）\n\n"
        "**2. 潜在的饥饿问题**\n"
        "- 上述方案是「**同方向优先**」的——只要一个方向不断有行人，\n"
        "  `bridge` 一直被占用，另一个方向无法过桥，可能**饥饿**\n\n"
        "**3. 改进：避免饥饿（公平调度）**\n\n"
        "增加一个互斥信号量 `fair_mutex`，强制两个方向交替使用桥：\n"
        "```c\n"
        "semaphore fair_mutex = 1;   // 公平调度信号量\n\n"
        "void east_to_west() {\n"
        "    P(fair_mutex);             // 排队（公平性保证）\n"
        "    P(mutex_east);\n"
        "    east_count++;\n"
        "    if (east_count == 1)\n"
        "        P(bridge);\n"
        "    V(mutex_east);\n"
        "    V(fair_mutex);             // 释放排队锁（允许另一个方向排队）\n"
        "    cross_bridge_east_to_west();\n"
        "    P(mutex_east);\n"
        "    east_count--;\n"
        "    if (east_count == 0)\n"
        "        V(bridge);\n"
        "    V(mutex_east);\n"
        "}\n"
        "```\n\n"
        "`fair_mutex` 保证了两个方向的行人**交替获得进入桥的机会**，\n"
        "避免了某一方向被无限期阻塞。",
        "**【408 考点提示】**\n"
        "1. 过桥问题是**读者-写者的对称变体**——两个方向各自是对内的『读者』、对外的『写者』\n"
        "2. 核心思路：每个方向独立计数器，仅在第1人和最后1人时申请/释放桥\n"
        "3. 与读者-写者的区别：读者-写者是『一群读者 vs 单个写者』，\n"
        "   过桥问题是『一群东向行人 vs 一群西向行人』\n"
        "4. 公平性问题常作为扩展考点——如何修改方案消除饥饿"
    ]

    answer = (
        "信号量+变量：bridge=1（桥互斥），mutex_east=1/mutex_west=1（保护方向计数器），\n"
        "east_count=0/west_count=0（各方向人数计数）。\n"
        "东→西：P(mutex_east)→east_count++→若==1则P(bridge)→V(mutex_east)→过桥→\n"
        "        P(mutex_east)→east_count--→若==0则V(bridge)→V(mutex_east)\n"
        "西→东同理。\n"
        "防饥饿：加 fair_mutex 强制交替排队。"
    )

    return CompProblem(
        topic_id="os_pv_bridge",
        topic_name="PV操作：过桥问题（独木桥）",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["PV操作", "信号量", "过桥", "同步", "互斥", "读者写者", "饥饿"],
        has_pseudocode=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 原 8-2 文件系统 — 混合索引分配（保持原内容不变，仅调整注释编号）
# ═══════════════════════════════════════════════════════════════════════════

def _gen_os_file_index() -> CompProblem:
    block_size_kb = _rand_choice([1, 2, 4])
    block_size = block_size_kb * 1024
    addr_per_block = block_size // 4  # 每个地址4字节

    # 索引节点结构：10个直接 + 1个一级间接 + 1个二级间接 + 1个三级间接
    direct_count = 10
    l1_blocks = addr_per_block
    l2_blocks = addr_per_block * addr_per_block
    l3_blocks = addr_per_block * addr_per_block * addr_per_block

    max_file_blocks = direct_count + l1_blocks + l2_blocks + l3_blocks
    max_file_size = max_file_blocks * block_size
    max_file_size_kb = max_file_size // 1024

    # 访问某个逻辑块
    target_block = _rand_int(5, direct_count + l1_blocks + 5)

    params = {
        "block_size_kb": block_size_kb, "block_size": block_size,
        "direct_count": direct_count, "addr_per_block": addr_per_block,
        "max_file_blocks": max_file_blocks,
        "max_file_size_kb": max_file_size_kb,
        "target_block": target_block,
    }

    # 计算访问该逻辑块所需的 I/O 次数
    if target_block < direct_count:  # 直接块
        io_count = 2  # 读磁盘i节点 + 读数据块
        io_desc = f"逻辑块号 {target_block} < {direct_count}（直接块范围）\n→ 从 i 节点直接地址读取 → ① 读 i 节点 → ② 读数据块\n→ **2 次 I/O**"
    elif target_block < direct_count + l1_blocks:  # 一级间接
        io_count = 3
        offset = target_block - direct_count
        io_desc = f"逻辑块号 {target_block} >= {direct_count}，属于一级间接块（0 ∼ {l1_blocks - 1}）\n→ ① 读 i 节点 → ② 读一级间接块（索引表） → ③ 读数据块\n→ **3 次 I/O**"
    elif target_block < direct_count + l1_blocks + l2_blocks:  # 二级间接
        io_count = 4
        io_desc = f"逻辑块号 {target_block} >= {direct_count + l1_blocks}，属于二级间接块\n→ ① 读 i 节点 → ② 读一级间接块 → ③ 读二级间接块 → ④ 读数据块\n→ **4 次 I/O**"
    else:
        io_count = 5
        io_desc = f"逻辑块号 {target_block} >= {direct_count + l1_blocks + l2_blocks}，属于三级间接块\n→ ① 读 i 节点 → ②~④ 读三级间接索引表 → ⑤ 读数据块\n→ **5 次 I/O**"

    question = (
        f"某 UNIX/Linux 文件系统采用 **混合索引分配** 方式管理文件存储空间。\n"
        f"磁盘块大小为 **{block_size_kb} KB**（即 {block_size} 字节），地址项占 **4 字节**。\n\n"
        f"i 节点（索引节点）中包含 **{direct_count} 个直接地址项**、**1 个一级间接地址项**、\n"
        f"**1 个二级间接地址项** 和 **1 个三级间接地址项**。\n\n"
        f"请计算：\n"
        f"(1) 该文件系统支持的**单个文件最大容量**\n"
        f"(2) 访问文件的**第 {target_block} 号逻辑块**（逻辑块号从 0 开始）需要多少次磁盘 I/O？\n"
        f"(3) 每个磁盘块最多可以存放多少个地址项？"
    )

    steps = [
        f"**第 1 步：计算每个磁盘块可存放的地址项数**\n\n"
        f"每个地址项 = 4 字节，每个磁盘块 = {block_size} 字节\n"
        f"每个磁盘块可存放的地址项数 = {block_size} / 4 = **{addr_per_block} 个**\n\n"
        f"（即：一个一级间接块可索引 {addr_per_block} 个数据块，\n"
        f" 一个二级间接块可索引 {addr_per_block}² = {addr_per_block * addr_per_block} 个数据块，\n"
        f" 一个三级间接块可索引 {addr_per_block}³ = {addr_per_block ** 3} 个数据块）",
        f"**第 2 步：计算文件最大容量**\n\n"
        f"文件系统支持的寻址方式：\n"
        f"- {direct_count} 个直接块：{direct_count} 个数据块\n"
        f"- 1 个一级间接块：索引 {addr_per_block} 个数据块\n"
        f"- 1 个二级间接块：索引 {addr_per_block} × {addr_per_block} = {l2_blocks} 个数据块\n"
        f"- 1 个三级间接块：索引 {addr_per_block} × {addr_per_block} × {addr_per_block} = {l3_blocks} 个数据块\n\n"
        f"最大数据块数 = {direct_count} + {addr_per_block} + {l2_blocks} + {l3_blocks}\n"
        f"= {direct_count} + {l1_blocks} + {l2_blocks} + {l3_blocks}\n"
        f"= **{max_file_blocks} 个数据块**\n\n"
        f"最大文件大小 = {max_file_blocks} × {block_size} 字节\n"
        f"= {max_file_size_kb} KB\n"
        f"= **约 {round(max_file_size_kb / 1024, 1)} MB**",
        f"**第 3 步：访问逻辑块 {target_block} 的 I/O 次数**\n\n"
        f"{io_desc}\n\n"
        f"说明：通常 i 节点已被缓存到内存中，但题目无特别说明时按磁盘 I/O（读 i 节点 + 读索引块 + 读数据块）计算。",
        f"**第 4 步：结论**\n\n"
        f"(1) 单个文件最大容量 ≈ **{round(max_file_size_kb / 1024, 1)} MB**（{max_file_size} 个数据块）\n"
        f"(2) 访问第 {target_block} 号逻辑块需要 **{io_count} 次**磁盘 I/O\n"
        f"(3) 每个磁盘块可存放 **{addr_per_block}** 个地址项",
        "**【408 考点提示】**\n"
        "1. 混合索引分配是 UNIX 文件系统的经典设计，408 中常考计算题\n"
        "2. 直接块适合小文件（无需索引块 I/O），间接块支持超大文件\n"
        "3. 访问逻辑块的 I/O 次数 = 索引层级数 + 1（读数据块）\n"
        "4. 注意区分『地址项大小』和『磁盘块大小』——它们共同决定间接块可索引的范围",
    ]

    answer = (
        f"(1) 最大文件 ≈ {round(max_file_size_kb / 1024, 1)} MB "
        f"（{direct_count} 直接 + {l1_blocks} 一级间接 + {l2_blocks} 二级间接 + {l3_blocks} 三级间接 = {max_file_blocks} 块）\n"
        f"(2) 访问第 {target_block} 号逻辑块需 {io_count} 次 I/O\n"
        f"(3) 每块可存放 {addr_per_block} 个地址项"
    )

    return CompProblem(
        topic_id="os_file_index",
        topic_name="文件系统：混合索引分配",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["文件系统", "i节点", "混合索引", "间接块", "磁盘IO", "UNIX"],
    )


# ── 10. FAT与簇大小计算 ──

def _gen_os_file_fat() -> CompProblem:
    disk_size_gb = _rand_choice([1, 2, 4, 8])
    disk_size_mb = disk_size_gb * 1024
    cluster_size_kb = _rand_choice([0.5, 1, 2, 4])
    cluster_size_bytes = int(cluster_size_kb * 1024)
    total_clusters = int(disk_size_mb * 1024 / cluster_size_bytes)

    # FAT 表项位数
    if total_clusters <= 0xFF + 1:
        fat_bits = 8
        fat_entry_size = 1
    elif total_clusters <= 0xFFFF + 1:
        fat_bits = 16
        fat_entry_size = 2
    else:
        fat_bits = 32
        fat_entry_size = 4

    # 文件大小
    file_size_kb = _rand_int(10, 100) * cluster_size_kb
    file_size_bytes = int(file_size_kb * 1024)
    clusters_needed = math.ceil(file_size_bytes / cluster_size_bytes)

    # 内部碎片（文件实际占用空间）
    actual_alloc = clusters_needed * cluster_size_bytes
    internal_frag = actual_alloc - file_size_bytes

    params = {
        "disk_size_gb": disk_size_gb, "cluster_size_kb": cluster_size_kb,
        "total_clusters": total_clusters,
        "fat_bits": fat_bits, "fat_entry_size": fat_entry_size,
        "file_size_kb": file_size_kb, "clusters_needed": clusters_needed,
        "internal_frag": internal_frag, "actual_alloc_kb": actual_alloc // 1024,
    }

    fat_size_bytes = total_clusters * fat_entry_size
    fat_size_kb = math.ceil(fat_size_bytes / 1024)

    question = (
        f"某磁盘容量为 **{disk_size_gb} GB**，操作系统采用 **FAT 文件系统**，\n"
        f"簇（Cluster）大小为 **{cluster_size_kb} KB**。\n\n"
        f"现有文件 **File_A.txt**，大小为 **{file_size_kb:.1f} KB**。\n\n"
        f"请计算：\n"
        f"(1) 磁盘共有多少个簇？FAT 表需要多少个表项？\n"
        f"(2) FAT 表至少需要 **FAT{disk_size_gb*2}**（几位）？每个 FAT 表项占用多少字节？\n"
        f"(3) FAT 表的总大小\n"
        f"(4) File_A.txt 实际占用的磁盘空间（含内部碎片）"
    )

    steps = [
        f"**第 1 步：计算磁盘簇数**\n\n"
        f"磁盘总容量 = {disk_size_gb} GB = {disk_size_gb * 1024} MB = {disk_size_gb * 1024 * 1024} KB\n"
        f"簇大小 = {cluster_size_kb} KB = {cluster_size_bytes} 字节\n\n"
        f"总簇数 = 磁盘容量 / 簇大小 = {disk_size_gb * 1024 * 1024} / {cluster_size_kb} = **{total_clusters} 个簇**\n\n"
        f"FAT 表项数 = 总簇数 = **{total_clusters}**（编号 0 ∼ {total_clusters - 1}）",
        f"**第 2 步：确定 FAT 位数**\n\n"
        f"FAT 表项需能容纳的最大编号为 {total_clusters - 1}（共 {total_clusters} 个表项）：\n"
        f"  - FAT8：最大 255 个表项 → {'够用' if total_clusters <= 256 else '不够'}\n"
        f"  - FAT16：最大 65535 个表项 → {'够用' if total_clusters <= 65536 else '不够'}\n"
        f"  - FAT32：最大 2³² 个表项 → 够用\n\n"
        f"因此需要 **FAT{fat_bits}**（{fat_bits} 位），每个表项占用 **{fat_entry_size} 字节**",
        f"**第 3 步：计算 FAT 表大小**\n\n"
        f"FAT 表大小 = 表项数 × 表项大小\n"
        f"= {total_clusters} × {fat_entry_size} B\n"
        f"= {fat_size_bytes} 字节\n"
        f"= **{fat_size_kb} KB**（向上取整）\n\n"
        f"（FAT 通常有两个备份——主 FAT + 备份 FAT，共占用 {fat_size_kb * 2} KB）",
        f"**第 4 步：计算文件实际占用空间**\n\n"
        f"文件大小 = {file_size_kb:.1f} KB = {file_size_bytes} 字节\n\n"
        f"所需簇数 = ⌈文件大小 / 簇大小⌉ = ⌈{file_size_bytes} / {cluster_size_bytes}⌉ = **{clusters_needed} 个簇**\n\n"
        f"实际占用空间 = {clusters_needed} × {cluster_size_bytes} 字节 = **{actual_alloc // 1024} KB**\n\n"
        f"内部碎片 = 实际占用 − 文件大小 = {actual_alloc} − {file_size_bytes} = **{internal_frag} 字节**\n\n"
        f"（这些空间被分配给文件但未被使用，是簇式分配不可避免的浪费）",
        "**【408 考点提示】**\n"
        "1. FAT 表项数 = 磁盘总簇数，每个表项存放下一个簇号或结束标记\n"
        "2. 簇大小选择是折中：簇大则内部碎片多（空间利用率低），簇小则 FAT 表大（元数据开销大）\n"
        "3. FAT 表在磁盘上通常有两份备份（主 FAT + 镜像 FAT）\n"
        "4. FAT32 每个表项占 4 字节，但只有低 28 位用于寻址（高 4 位保留）\n"
        "5. FAT 系文件系统（FAT12/16/32）在 U 盘和嵌入式系统中仍广泛使用",
    ]

    answer = (
        f"(1) 总簇数 = {total_clusters}，FAT 表项数 = {total_clusters}\n"
        f"(2) FAT{fat_bits}，每表项 {fat_entry_size} 字节\n"
        f"(3) FAT 表大小 = {fat_size_kb} KB\n"
        f"(4) 实际占用 = {actual_alloc // 1024} KB，内部碎片 = {internal_frag} 字节"
    )

    return CompProblem(
        topic_id="os_file_fat",
        topic_name="FAT文件系统与簇大小",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["FAT", "文件系统", "簇", "内部碎片", "磁盘管理"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 计算机网络
# ═══════════════════════════════════════════════════════════════════════════

# ── 11. TCP 拥塞控制 ──

def _gen_cn_tcp_congestion() -> CompProblem:
    initial_ssthresh = 2 ** _rand_int(4, 6)  # 16, 32, 64
    initial_cwnd = _rand_int(1, 4)
    mss = 1  # 以一个 MSS 为 cwnd 单位

    # 选择不同的场景
    scenario = _rand_choice([
        "slow_start",
        "slow_start_with_loss",
        "fast_recovery",
    ])

    params = {
        "initial_ssthresh": initial_ssthresh,
        "initial_cwnd": initial_cwnd,
        "scenario": scenario,
    }

    questions = {
        "slow_start": (
            f"TCP 拥塞控制中，初始 **ssthresh（慢开始门限）= {initial_ssthresh} MSS**，"
            f"初始拥塞窗口 **cwnd = {initial_cwnd} MSS**。\n\n"
            f"请描述从连接建立开始的拥塞窗口变化过程（按 RTT 轮次描述），直到 cwnd 增长到 "
            f"**{initial_ssthresh + _rand_int(2, 6)} MSS**。\n"
            f"要求分阶段说明：\n"
            f"(1) 慢开始阶段\n"
            f"(2) 拥塞避免阶段\n"
            f"(3) 说明 cwnd 和 ssthresh 在各阶段如何变化"
        ),
        "slow_start_with_loss": (
            f"TCP 拥塞控制中，初始 **ssthresh = {initial_ssthresh} MSS**，"
            f"初始 **cwnd = {initial_cwnd} MSS**。\n\n"
            f"假设当 cwnd 增长到 **{initial_ssthresh * 2} MSS** 时发生**超时事件**。\n\n"
            f"请描述从连接建立到超时恢复的完整拥塞控制过程，包括：\n"
            f"(1) 超时前各轮次的 cwnd 变化（按 RTT 描述）\n"
            f"(2) 超时后的处理（新的 ssthresh 和 cwnd）\n"
            f"(3) 超时恢复后又重新开始的过程"
        ),
        "fast_recovery": (
            f"TCP Reno 拥塞控制中，初始 **ssthresh = {initial_ssthresh} MSS**，"
            f"当前 **cwnd = {initial_ssthresh * 2} MSS**。\n\n"
            f"此时收到 **3 个重复的 ACK**，触发快重传算法。\n\n"
            f"请描述拥塞控制算法的执行过程：\n"
            f"(1) 快重传如何工作\n"
            f"(2) 快恢复如何设置新的 ssthresh 和 cwnd\n"
            f"(3) 写出从快重传恢复到拥塞避免的完整过程"
        ),
    }

    question = questions[scenario]

    steps = []

    if scenario == "slow_start":
        # 计算各轮次 cwnd
        rounds = []
        cwnd = initial_cwnd
        round_num = 0
        while cwnd < initial_ssthresh + _rand_int(2, 6):
            round_num += 1
            rounds.append((round_num, cwnd))
            if cwnd < initial_ssthresh:
                cwnd *= 2  # 慢开始：指数增长
                if cwnd > initial_ssthresh:
                    cwnd = initial_ssthresh
            else:
                cwnd += 1  # 拥塞避免：线性增长
            if round_num > 20:
                break

        steps = [
            "**【第 1 阶段：慢开始（Slow Start）】**\n\n"
            "TCP 连接建立后进入慢开始阶段，cwnd 从初始值开始，\n"
            "每收到一个 ACK，cwnd 增加 1 个 MSS，即**每经过一个 RTT，cwnd 翻倍**（指数增长）。\n\n"
            f"各轮次变化：\n"
            + "\n".join(
                f"  RTT {r}: cwnd = {c} MSS" + ("（慢开始）" if c < initial_ssthresh or (r == len(rounds) - 1) else "（进入拥塞避免）")
                for r, c in rounds[:8]
            ) +
            "\n  ...\n\n"
            f"当 cwnd 增长到 ssthresh = {initial_ssthresh} MSS 时，结束慢开始。",
            "**【第 2 阶段：拥塞避免（Congestion Avoidance）】**\n\n"
            f"cwnd 达到 ssthresh = {initial_ssthresh} 后，进入拥塞避免阶段。\n"
            f"每经过一个 RTT，cwnd **增加 1 个 MSS**（线性增长）。\n\n"
            f"各轮次变化：\n"
            + "\n".join(
                f"  RTT {r}: cwnd = {c} MSS" + ("（拥塞避免）" if c >= initial_ssthresh else "")
                for r, c in rounds[7:15] if c >= initial_ssthresh
            ) +
            "\n  ...",
            "**【总结】**\n\n"
            "| 阶段 | 增长方式 | 触发条件 |\n"
            "|------|---------|---------|\n"
            "| 慢开始 | 指数增长（×2/RTT） | 连接建立或超时恢复后 |\n"
            "| 拥塞避免 | 线性增长（+1/RTT） | cwnd ≥ ssthresh |\n\n"
            f"完整变化过程：cwnd: {initial_cwnd} → {' → '.join(str(c) for _, c in rounds[:6])} → …\n\n"
            "慢开始阶段增长速度很快，能迅速探测可用带宽；\n"
            "拥塞避免阶段则谨慎地线性增长，避免快速耗尽网络资源。",
            "**【408 考点提示】**\n"
            "1. 慢开始的'慢'并非增长慢，而是**初始窗口小**\n"
            "2. cwnd 的单位是 **MSS（最大报文段长度）**，而非字节\n"
            "3. ssthresh 的动态调整：超时后 ssthresh = cwnd/2\n"
            "4. TCP Tahoe（超时→慢开始）vs TCP Reno（超时→快恢复）的区别是常考点",
        ]
    elif scenario == "slow_start_with_loss":
        # 计算过程
        loss_cwnd = initial_ssthresh * 2
        new_ssthresh = loss_cwnd // 2
        new_cwnd_slow = 1  # 超时后初始 cwnd

        steps = [
            f"**【第 1 阶段：超时前的正常拥塞控制】**\n\n"
            f"初始：ssthresh = {initial_ssthresh}，cwnd = {initial_cwnd}\n\n"
            f"慢开始阶段：\n"
            f"  RTT 1: cwnd = {initial_cwnd}\n"
            f"  RTT 2: cwnd = {initial_cwnd * 2}\n"
            + (f"  RTT 3: cwnd = {initial_cwnd * 4}\n"
               f"  ...\n" if initial_cwnd * 4 < initial_ssthresh else "")
            + f"  （直到 cwnd = {initial_ssthresh}，达到 ssthresh）\n\n"
            f"拥塞避免阶段（线性增长）：\n"
            f"  cwnd 从 {initial_ssthresh} 开始，每 RTT 增加 1  MSS\n"
            f"  … → cwnd = {initial_ssthresh + 1} → {initial_ssthresh + 2} → …\n"
            f"  最终达到 {loss_cwnd} MSS 时发生**超时**",
            f"**第 2 阶段：超时事件处理**\n\n"
            f"TCP 检测到超时→认为网络拥堵严重，做出以下反应：\n\n"
            f"1. 更新 ssthresh：\n"
            f"   **新的 ssthresh = cwnd / 2 = {loss_cwnd} / 2 = {new_ssthresh}**\n\n"
            f"2. 重置 cwnd：\n"
            f"   **新的 cwnd = 1 MSS**（全部重来）\n\n"
            f"3. 重新进入**慢开始**阶段\n\n"
            f"（Tahoe 和 Reno 在超时时的处理相同）",
            f"**第 3 阶段：超时恢复后的过程**\n\n"
            f"超时恢复后重新开始慢开始：\n"
            f"  RTT 1: cwnd = 1（新的慢开始）\n"
            f"  RTT 2: cwnd = 2\n"
            f"  RTT 3: cwnd = 4\n"
            f"  RTT 4: cwnd = 8\n"
            f"  …\n"
            f"  当 cwnd = {new_ssthresh}（新 ssthresh）时，进入拥塞避免\n\n"
            f"之后 cwnd 线性增长（+1/RTT），直到再次发生丢包事件。",
            "**【总结】**\n\n"
            f"超时前的峰值 cwnd = {loss_cwnd}\n"
            f"超时后：ssthresh = {new_ssthresh}，cwnd = 1\n"
            f"恢复过程：慢开始（指数）→ 拥塞避免（线性）\n\n"
            "超时的触发条件：超时定时器到期（说明丢包严重，网络可能已拥塞崩溃）\n"
            "与快重传的区别：超时后 cwnd 重置为 1（完全重新开始），而快恢复后 cwnd = ssthresh",
        ]
    elif scenario == "fast_recovery":
        loss_cwnd = initial_ssthresh * 2
        new_ssthresh = loss_cwnd // 2

        steps = [
            f"**【第 1 步：检测到 3 个重复 ACK → 快重传】**\n\n"
            f"当前状态：ssthresh = {initial_ssthresh}，cwnd = {loss_cwnd}（拥塞避免阶段）\n\n"
            f"当发送方收到 **3 个相同的 ACK**（对同一序号的确认）时：\n"
            f"1. 判断该报文段已丢失（而非延迟）\n"
            f"2. 立即重传该丢失的报文段，**不等超时定时器**\n\n"
            f"这就是**快重传（Fast Retransmit）**算法——避免等待 RTO 超时而浪费带宽",
            f"**第 2 步：快恢复（Fast Recovery）— TCP Reno**\n\n"
            f"与快重传同时执行快恢复算法：\n\n"
            f"1. **更新 ssthresh**：\n"
            f"   ssthresh = cwnd / 2 = {loss_cwnd} / 2 = **{new_ssthresh}**\n\n"
            f"2. **更新 cwnd**：\n"
            f"   cwnd = ssthresh + 3 = {new_ssthresh} + 3 = **{new_ssthresh + 3}**\n"
            f"   （+3 是因为已收到 3 个重复 ACK，说明有 3 个报文段已离开网络）\n\n"
            f"3. 每收到一个重复的 ACK：\n"
            f"   cwnd += 1（表示又有一个报文段离开了网络）\n\n"
            f"4. 当收到对新发送数据的 ACK（恢复 ACK）时：\n"
            f"   cwnd = ssthresh（恢复为 {new_ssthresh}）\n"
            f"   进入**拥塞避免**阶段",
            f"**第 3 步：恢复后的拥塞避免**\n\n"
            f"快恢复后切换回拥塞避免：\n"
            f"  cwnd = ssthresh = {new_ssthresh}\n"
            f"  每 RTT cwnd += 1（线性增长）\n"
            f"  … → {new_ssthresh + 1} → {new_ssthresh + 2} → …\n\n"
            f"**与超时恢复的对比**：\n\n"
            f"| 事件 | cwnd 恢复值 | 进入阶段 | 效率 |\n"
            f"|------|------------|---------|------|\n"
            f"| 超时 | cwnd=1 | 慢开始 | 低（从头开始） |\n"
            f"| 快重传+快恢复 | cwnd=ssthresh+3→ssthresh | 拥塞避免 | 高（保留大部分带宽） |",
            "**【408 考点提示】**\n"
            "1. **TCP Tahoe** vs **TCP Reno**：\n"
            "   - Tahoe：收到 3 个重复 ACK 后→ssthresh=cwnd/2, cwnd=1→慢开始\n"
            "   - Reno：收到 3 个重复 ACK 后→ssthresh=cwnd/2, cwnd=ssthresh+3→快恢复\n"
            "2. 快重传的前提是收到 **3 个重复 ACK**（不只是 1-2 个）\n"
            "3. 快恢复的核心思想：既然还能收到 ACK，说明网络还没完全崩溃，不必重置到 1\n"
            "4. 408 中常要求画出 cwnd 随时间变化的折线图",
        ]

    answer = f"详见解题步骤。核心变化过程已在各阶段详细说明。"

    return CompProblem(
        topic_id="cn_tcp_congestion",
        topic_name="TCP拥塞控制分析",
        subject="计算机网络",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["TCP", "拥塞控制", "慢开始", "拥塞避免", "快重传", "快恢复", "cwnd"],
    )


# ── 12. 子网划分与路由聚合 ──

def _gen_cn_subnet() -> CompProblem:
    # 选择一个 IP 地址块
    ip_prefix = _rand_choice([  # 私有地址范围
        ("192.168", 24),
        ("10", 8),
        ("172.16", 16),
    ])
    ip_base, default_mask = ip_prefix

    if ip_base == "192.168":
        network_addr = f"192.168.{_rand_int(0, 254)}.0"
        prefix_len = 24
    elif ip_base == "10":
        network_addr = f"10.{_rand_int(0, 255)}.{_rand_int(0, 255)}.0"
        prefix_len = 24
    else:  # 172.16
        network_addr = f"172.16.{_rand_int(0, 255)}.0"
        prefix_len = 24

    # 子网划分参数
    n_subnets = _rand_choice([2, 4, 8])
    new_prefix = prefix_len + int(math.log2(n_subnets))

    # 格式化为点分十进制
    octets = [int(x) for x in network_addr.split(".")]

    # 生成子网地址
    subnet_hosts = []
    for i in range(n_subnets):
        new_host_bit = i << (32 - new_prefix)
        new_octets = list(octets)
        # 简单的位操作：只在最后一个相关的八位组修改
        step = 256 // n_subnets
        subnet_octets = list(octets)
        subnet_octets[3] = i * step
        network_part = ".".join(str(o) for o in subnet_octets)
        subnet_hosts.append({
            "net": f"{network_part}/{new_prefix}",
            "first": f"{network_part[:-1]}1",
            "last": f"{network_part.rsplit('.', 1)[0]}.{subnet_octets[3] + step - 2}",
            "broadcast": f"{network_part.rsplit('.', 1)[0]}.{subnet_octets[3] + step - 1}",
        })

    # 子网掩码
    mask_bits = new_prefix
    mask_octets = []
    for i in range(4):
        if mask_bits >= 8:
            mask_octets.append(255)
            mask_bits -= 8
        else:
            mask_octets.append(256 - (1 << (8 - mask_bits)))
            mask_bits = 0

    mask_str = ".".join(str(o) for o in mask_octets)
    hosts_per_subnet = (256 // n_subnets) - 2

    params = {
        "network_addr": f"{network_addr}/{prefix_len}",
        "prefix_len": prefix_len,
        "n_subnets": n_subnets,
        "new_prefix": new_prefix,
        "mask_str": mask_str,
        "hosts_per_subnet": hosts_per_subnet,
        "subnet_hosts": subnet_hosts,
    }

    question = (
        f"某单位有一个网络地址 **{network_addr}/{prefix_len}**。\n\n"
        f"现在需要划分成 **{n_subnets} 个**子网，要求每个子网的可用主机数尽可能均衡。\n\n"
        f"请回答：\n"
        f"(1) 新的子网掩码是什么？\n"
        f"(2) 每个子网的网络地址、广播地址和可用 IP 地址范围\n"
        f"(3) 每个子网有多少个可用主机地址？\n"
        f"(4) 若将来要把这些子网合并，如何进行路由聚合？（超网化）"
    )

    step_n = n_subnets
    step_prefix = new_prefix
    step_mask = mask_str
    step_hosts = hosts_per_subnet

    steps = [
        f"**第 1 步：确定新子网掩码**\n\n"
        f"原网络前缀长度 = {prefix_len}\n"
        f"需要划分 {n_subnets} 个子网 → 需要从主机号借 {int(math.log2(n_subnets))} 位\n\n"
        f"新前缀长度 = 原前缀 + 借位数 = {prefix_len} + {int(math.log2(n_subnets))} = **/{new_prefix}**\n\n"
        f"子网掩码：\n"
        f"  /{new_prefix} = {mask_str}\n\n"
        f"每个子网的主机位 = 32 − {new_prefix} = {32 - new_prefix} 位\n"
        f"可用主机数 = 2^{32 - new_prefix} − 2 = {2 ** (32 - new_prefix) - 2}（减 2 去掉网络地址和广播地址）",
        f"**第 2 步：列出各子网信息**\n\n"
        f"子网大小（每个子网的 IP 总数）= 256 / {n_subnets} = {256 // n_subnets}\n\n"
        + "\n".join(
            f"**子网 {i + 1}**：\n"
            f"  - 网络地址：**{subnet_hosts[i]['net']}**\n"
            f"  - 可用地址范围：{subnet_hosts[i]['first']} ∼ {subnet_hosts[i]['last']}\n"
            f"  - 广播地址：{subnet_hosts[i]['broadcast']}\n"
            for i in range(n_subnets)
        ),
        f"**第 3 步：验证**\n\n"
        f"每个子网可用主机数：2^{32 - new_prefix} − 2 = {2 ** (32 - new_prefix) - 2}\n"
        f"所有子网总主机数：{n_subnets} × {2 ** (32 - new_prefix) - 2} = {n_subnets * (2 ** (32 - new_prefix) - 2)}\n\n"
        f"子网间地址不重叠、不浪费（满足题目要求）。",
        f"**第 4 步：路由聚合（超网化）**\n\n"
        f"若要将这 {n_subnets} 个子网合并为一个更大的网络进行路由通告：\n\n"
        f"1. 检查所有子网的网络地址，取它们的**共同前缀**\n"
        f"2. 这些子网的网络地址前 {prefix_len} 位完全相同\n"
        f"3. 聚合后的网络地址为 **{network_addr}/{prefix_len}**\n\n"
        f"路由聚合的好处：\n"
        f"- 减少路由表条目数（1 条代替 {n_subnets} 条）\n"
        f"- 提高路由查找速度\n"
        f"- 减小路由协议（如 OSPF / BGP）的更新开销\n\n"
        f"聚合后的 CIDR 地址块：**{network_addr}/{prefix_len}**",
        "**【408 考点提示】**\n"
        "1. 子网划分的步骤：确定借位数 → 计算新掩码 → 列出子网地址范围\n"
        "2. **全 0 子网**和**全 1 子网**在 CIDR 中可用（已废弃老规则）\n"
        "3. 可用主机数 = 2^{主机位数} − 2（全 0 网络地址 + 全 1 广播地址）\n"
        "4. 路由聚合（Route Aggregation / Summarization）是 CIDR 的核心思想\n"
        "5. 注意子网掩码的写法：点分十进制 / CIDR 前缀长度两种形式都要会",
    ]

    answer = (
        f"(1) 子网掩码：{mask_str}（/{new_prefix}）\n"
        f"(2) 共 {n_subnets} 个子网，各子网信息见解题步骤\n"
        f"(3) 每个子网可用主机数：{2 ** (32 - new_prefix) - 2} 个\n"
        f"(4) 路由聚合：{network_addr}/{prefix_len}"
    )

    return CompProblem(
        topic_id="cn_subnet",
        topic_name="子网划分与路由聚合",
        subject="计算机网络",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["子网划分", "CIDR", "路由聚合", "子网掩码", "网络地址"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型注册表与公开 API
# ═══════════════════════════════════════════════════════════════════════════

GENERATORS = {
    # 数据结构 — 算法设计题
    "ds_list_reverse":        ("单链表逆转",               "数据结构",       _gen_ds_list_reverse),
    "ds_tree_inorder":        ("二叉树非递归中序遍历",     "数据结构",       _gen_ds_tree_inorder),
    "ds_topological_sort":    ("拓扑排序（Kahn算法）",     "数据结构",       _gen_ds_topological_sort),
    # 计算机组成原理
    "co_instruction_format":  ("指令格式与寻址方式",       "计算机组成原理", _gen_co_instruction_format),
    "co_datapath":            ("数据通路分析",             "计算机组成原理", _gen_co_datapath),
    "co_pipeline_hazard":     ("指令流水线冒险分析",       "计算机组成原理", _gen_co_pipeline_hazard),
    "co_interrupt":           ("中断与异常处理",           "计算机组成原理", _gen_co_interrupt),
    # 操作系统 — PV操作（同步与互斥）
    "os_pv_producer_consumer":("PV操作：生产者-消费者",    "操作系统",       _gen_os_pv_producer_consumer),
    "os_pv_readers_writers":  ("PV操作：读者-写者问题",    "操作系统",       _gen_os_pv_readers_writers),
    "os_pv_dining_philosophers":("PV操作：哲学家进餐问题", "操作系统",       _gen_os_pv_dining_philosophers),
    "os_pv_smokers":          ("PV操作：吸烟者问题",       "操作系统",       _gen_os_pv_smokers),
    "os_pv_barber":           ("PV操作：理发师问题",       "操作系统",       _gen_os_pv_barber),
    "os_pv_fruit_plate":      ("PV操作：水果盘问题",       "操作系统",       _gen_os_pv_fruit_plate),
    # 操作系统 — 其他
    "os_file_index":          ("文件系统：混合索引分配",   "操作系统",       _gen_os_file_index),
    "os_file_fat":            ("FAT文件系统与簇大小",      "操作系统",       _gen_os_file_fat),
    # 计算机网络
    "cn_tcp_congestion":      ("TCP拥塞控制分析",          "计算机网络",     _gen_cn_tcp_congestion),
    "cn_subnet":              ("子网划分与路由聚合",       "计算机网络",     _gen_cn_subnet),
}


def get_topic_list() -> list[dict]:
    """返回可用题型列表（供前端下拉菜单使用）"""
    return [
        {"id": tid, "name": name, "subject": subject}
        for tid, (name, subject, _gen) in GENERATORS.items()
    ]


def generate_problem(topic_id: str) -> Optional[CompProblem]:
    """为指定题型生成一道随机参数的大题"""
    entry = GENERATORS.get(topic_id)
    if entry is None:
        return None
    _name, _subject, gen_func = entry
    return gen_func()


# ═══════════════════════════════════════════════════════════════════════════
# CLI 测试入口
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    def _print_problem(p: CompProblem):
        print(f"\n{'=' * 60}")
        print(f"【{p.subject}】{p.topic_name}")
        print(f"{'=' * 60}")
        print(p.question)
        print(f"\n{'─' * 40}")
        for i, step in enumerate(p.solution_steps, 1):
            print(step)
        print(f"{'─' * 40}")
        print(f"\n答案：{p.answer}")

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for t in get_topic_list():
            print(f"  {t['id']:25s} {t['subject']:10s} {t['name']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--all":
        problems = [gen_func() for _name, _subject, gen_func in GENERATORS.values()]
        for p in problems:
            _print_problem(p)
    elif len(sys.argv) > 1:
        tid = sys.argv[1]
        p = generate_problem(tid)
        if p is None:
            print(f"未知题型: {tid}")
            print(f"可用: {', '.join(GENERATORS.keys())}")
        else:
            _print_problem(p)
    else:
        # 默认：测试 PV 操作和指令流水线两题
        for tid in ["os_pv_producer_consumer", "co_pipeline_hazard"]:
            p = generate_problem(tid)
            if p:
                _print_problem(p)
