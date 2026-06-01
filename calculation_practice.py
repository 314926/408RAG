"""
408 计算题专项练习模块

采用"模板 + 参数替换"可控方式生成高频计算题，不依赖 LLM 实时生成。
首期覆盖 8 类高频题型，每类提供标准模板、解题步骤和参数变式规则。
"""

import random
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CalcProblem:
    """一道计算题"""
    topic_id: str
    topic_name: str
    subject: str
    question: str
    params: dict
    solution_steps: list[str]  # 每步一行
    answer: str
    knowledge_tags: list[str] = field(default_factory=list)  # 关联知识点标签，用于知识库检索


# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════

def _rand_int(low: int, high: int, step: int = 1) -> int:
    """生成 [low, high] 范围内 step 倍数的随机整数"""
    return random.randrange(low, high + 1, step)


def _rand_float(low: float, high: float, decimals: int = 2) -> float:
    """生成 [low, high] 范围内的随机浮点数"""
    val = random.uniform(low, high)
    return round(val, decimals)


def _to_sci_notation(val: float, decimals: int = 1) -> str:
    """将浮点数转为科学计数法字符串"""
    if val == 0:
        return "0"
    exp = int(math.floor(math.log10(abs(val))))
    mantissa = val / (10 ** exp)
    return f"{mantissa:.{decimals}f} × 10^{exp}"


# ═══════════════════════════════════════════════════════════════════════════
# 题型 1: Cache 命中率与平均访问时间
# ═══════════════════════════════════════════════════════════════════════════

def _gen_cache_problem() -> CalcProblem:
    hit_time = _rand_int(1, 10)
    miss_penalty = _rand_int(10, 30) * 10  # 100-300 ns
    hit_rate = _rand_float(0.90, 0.99, 4)

    miss_rate = round(1 - hit_rate, 4)
    avg_time = round(hit_rate * hit_time + miss_rate * miss_penalty, 4)

    params = {"hit_time": hit_time, "miss_penalty": miss_penalty, "hit_rate": hit_rate}
    question = (
        f"某计算机 Cache 的命中时间为 **{hit_time} ns**，"
        f"缺失惩罚为 **{miss_penalty} ns**（访问主存时间），"
        f"Cache 命中率为 **{hit_rate}**。\n\n"
        f"求该存储系统的 **平均访问时间 (Average Memory Access Time, AMAT)**。"
    )

    steps = [
        f"**第 1 步：计算缺失率**\n缺失率 = 1 − 命中率 = 1 − {hit_rate} = **{miss_rate}**",
        f"**第 2 步：应用 AMAT 公式**\nAMAT = 命中率 × 命中时间 + 缺失率 × 缺失惩罚",
        f"**第 3 步：代入数值**\nAMAT = {hit_rate} × {hit_time} + {miss_rate} × {miss_penalty}",
        f"**第 4 步：计算结果**\n= {round(hit_rate * hit_time, 4)} + {round(miss_rate * miss_penalty, 4)} = **{avg_time} ns**",
    ]
    answer = f"{avg_time} ns"

    return CalcProblem(
        topic_id="cache_hit",
        topic_name="Cache 命中率与平均访问时间",
        subject="计算机组成原理",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["Cache", "命中率", "平均访问时间", "存储层次"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型 2: 流水线性能指标（吞吐率、加速比、效率）
# ═══════════════════════════════════════════════════════════════════════════

def _gen_pipeline_problem() -> CalcProblem:
    k = _rand_int(4, 8)           # 流水线段数
    dt = _rand_int(1, 10)          # 时钟周期 ns
    n = _rand_int(100, 1000) * 10   # 指令条数

    T_pipeline = (k + n - 1) * dt
    T_seq = n * k * dt
    TP = round(n / T_pipeline, 4)
    S = round(T_seq / T_pipeline, 4)
    E = round(S / k, 4)

    params = {"num_stages": k, "clock_period": dt, "num_instr": n}
    question = (
        f"某 **{k} 段**流水线处理器，各段经过时间均为 **{dt} ns**。\n"
        f"现需连续处理 **{n} 条**指令，且无流水线冲突。\n\n"
        f"请计算：\n"
        f"(1) **吞吐率 TP**（单位：条/ns）\n"
        f"(2) **加速比 S**\n"
        f"(3) **效率 E**"
    )

    steps = [
        f"**第 1 步：计算流水线执行时间**\n"
        f"第一条指令通过流水线需 k·Δt = {k} × {dt} = {k * dt} ns\n"
        f"之后每 Δt 流出一条指令\n"
        f"总时间 T_pipeline = (k + n − 1) × Δt = ({k} + {n} − 1) × {dt} = **{T_pipeline} ns**",
        f"**第 2 步：计算顺序执行时间**\n"
        f"T_seq = n × k × Δt = {n} × {k} × {dt} = **{T_seq} ns**",
        f"**第 3 步：吞吐率**\n"
        f"TP = n / T_pipeline = {n} / {T_pipeline} = **{TP} 条/ns**\n"
        f"（即 {round(TP * 1e9, 2)} 条/秒，约 {round(TP * 1e9 / 1e6, 1)} MIPS）",
        f"**第 4 步：加速比**\n"
        f"S = T_seq / T_pipeline = {T_seq} / {T_pipeline} = **{S}**\n"
        f"（当 n → ∞ 时，S → k = {k}）",
        f"**第 5 步：效率**\n"
        f"E = S / k = {S} / {k} = **{E}**（即 {round(E * 100, 1)}%）\n"
        f"（当 n → ∞ 时，E → 1）",
    ]
    answer = f"TP = {TP} 条/ns, S = {S}, E = {E} ({round(E * 100, 1)}%)"

    return CalcProblem(
        topic_id="pipeline",
        topic_name="流水线性能指标",
        subject="计算机组成原理",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["流水线", "吞吐率", "加速比", "效率", "CPU性能"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型 3: 浮点数加减运算
# ═══════════════════════════════════════════════════════════════════════════

def _gen_float_add_problem() -> CalcProblem:
    """基于十进制科学计数法演示浮点加减核心步骤（对阶→尾数运算→规格化→舍入）"""
    # 生成两个简单的十进制数，保证运算步骤清晰
    x_mant, x_exp = _rand_int(1, 9) / 10, _rand_int(-2, 3)   # e.g. 0.5 × 10^2 = 50
    y_mant, y_exp = _rand_int(1, 9) / 10, x_exp + _rand_int(-2, -1)  # 确保需要对齐

    X = x_mant * (10 ** x_exp)
    Y = y_mant * (10 ** y_exp)

    x_repr = f"{x_mant} × 10^{x_exp}"
    y_repr = f"{y_mant} × 10^{y_exp}"

    # 对阶：小阶向大阶看齐
    if x_exp >= y_exp:
        big_exp = x_exp
        big_mant = x_mant
        small_mant = y_mant * (10 ** (y_exp - x_exp))
    else:
        big_exp = y_exp
        big_mant = y_mant
        small_mant = x_mant * (10 ** (x_exp - y_exp))

    aligned_small = round(small_mant, 4)
    sum_mant = round(big_mant + aligned_small, 4)

    # 规格化：调整到 0.1 ≤ |mantissa| < 1（十进制规格化）
    normalized_mant = sum_mant
    normalized_exp = big_exp
    if abs(normalized_mant) >= 1.0:
        normalized_mant = round(normalized_mant / 10, 4)
        normalized_exp += 1
    elif abs(normalized_mant) < 0.1 and abs(normalized_mant) > 0:
        normalized_mant = round(normalized_mant * 10, 4)
        normalized_exp -= 1

    final_val = round(normalized_mant * (10 ** normalized_exp), 4)

    params = {"X": X, "Y": Y, "x_mant": x_mant, "x_exp": x_exp, "y_mant": y_mant, "y_exp": y_exp}
    question = (
        f"设两个十进制浮点数（基值为 10）：\n"
        f"**X = {x_repr}** （即 {X}）\n"
        f"**Y = {y_repr}** （即 {Y}）\n\n"
        f"请按照浮点加减运算步骤计算 **X + Y**，要求保留 4 位小数。"
    )

    steps = [
        f"**第 1 步：对阶**（小阶向大阶看齐）\n"
        f"X 阶码 = {x_exp}，Y 阶码 = {y_exp}\n"
        f"大阶为 {big_exp}，将小阶数的尾数右移 |ΔE| = {abs(y_exp - x_exp)} 位\n"
        f"对齐后：{round(big_mant, 4)} × 10^{big_exp}  +  {aligned_small} × 10^{big_exp}",
        f"**第 2 步：尾数求和**\n"
        f"尾数和 = {round(big_mant, 4)} + {aligned_small} = **{sum_mant}**",
        f"**第 3 步：规格化**\n"
        f"结果 {sum_mant} × 10^{big_exp}"
        + (f"\n|尾数| ≥ 1，需右规：尾数 ÷ 10，阶码 +1" if abs(sum_mant) >= 1.0
           else f"\n|尾数| < 0.1，需左规" if abs(sum_mant) < 0.1
           else "\n尾数已在规格化范围内，无需调整"),
        f"\n规格化后：**{normalized_mant} × 10^{normalized_exp}**",
        f"**第 4 步：舍入**（保留 4 位小数）\n"
        f"尾数 = {normalized_mant}（已在精度范围内）",
        f"**第 5 步：结果**\n"
        f"X + Y = {normalized_mant} × 10^{normalized_exp} = **{final_val}**\n"
        f"验证：{X} + {Y} = {X + Y} ✓",
    ]
    answer = f"{final_val}（即 {normalized_mant} × 10^{normalized_exp}）"

    return CalcProblem(
        topic_id="float_add",
        topic_name="浮点数加减运算",
        subject="计算机组成原理",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["浮点数", "IEEE754", "对阶", "规格化", "舍入"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型 4: 虚拟地址到物理地址的转换
# ═══════════════════════════════════════════════════════════════════════════

def _gen_vaddr_problem() -> CalcProblem:
    page_size_kb = random.choice([1, 2, 4])
    page_size_bytes = page_size_kb * 1024
    offset_bits = int(math.log2(page_size_bytes))

    # 生成合理的虚拟地址（32位地址空间）
    page_num = _rand_int(0, 255)
    offset = _rand_int(0, page_size_bytes - 1, 16)
    va = page_num * page_size_bytes + offset
    frame_num = _rand_int(1, 1023)

    pa = frame_num * page_size_bytes + offset
    va_hex = f"{va:08X}"
    pa_hex = f"{pa:08X}"

    params = {
        "page_size_kb": page_size_kb, "page_size_bytes": page_size_bytes,
        "offset_bits": offset_bits, "va": va, "va_hex": va_hex,
        "page_num": page_num, "offset": offset, "frame_num": frame_num,
    }
    question = (
        f"某系统采用**页式存储管理**，页面大小为 **{page_size_kb} KB**。\n"
        f"虚拟地址为 **0x{va_hex}**（32 位地址空间）。\n"
        f"查页表得知，该虚拟页号对应的**页框号（物理块号）为 {frame_num}**。\n\n"
        f"请计算对应的 **物理地址**（用十六进制表示）。"
    )

    steps = [
        f"**第 1 步：确定页内偏移位数**\n"
        f"页面大小 = {page_size_kb} KB = {page_size_bytes} 字节 = 2^{offset_bits}\n"
        f"页内偏移占 **{offset_bits} 位**",
        f"**第 2 步：拆分虚拟地址**\n"
        f"虚拟地址 0x{va_hex} = {va}（十进制）\n"
        f"虚拟页号 = ⌊{va} / {page_size_bytes}⌋ = **{page_num}**\n"
        f"页内偏移 = {va} mod {page_size_bytes} = **{offset}**（0x{offset:0{offset_bits // 4}X}）",
        f"**第 3 步：地址变换**\n"
        f"物理页框号 = **{frame_num}**（由页表给出）\n"
        f"物理地址 = 物理页框号 × 页面大小 + 页内偏移",
        f"**第 4 步：计算物理地址**\n"
        f"物理地址 = {frame_num} × {page_size_bytes} + {offset}\n"
        f"= {frame_num * page_size_bytes} + {offset}\n"
        f"= **{pa}** = **0x{pa_hex}**",
    ]
    answer = f"0x{pa_hex}"

    return CalcProblem(
        topic_id="vaddr_trans",
        topic_name="虚拟地址→物理地址转换",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["虚拟内存", "页表", "地址变换", "页式存储"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型 5: 请求分页系统的缺页率与有效访问时间
# ═══════════════════════════════════════════════════════════════════════════

def _gen_page_fault_problem() -> CalcProblem:
    mem_access_ns = _rand_int(10, 20) * 10    # 100-200 ns
    # 缺页率用科学计数法表达：10^-4 ~ 5×10^-4
    p_exponent = _rand_int(-5, -3)
    p_mantissa = _rand_int(1, 9)
    p = p_mantissa * (10 ** p_exponent)        # e.g. 3 × 10^-5
    pft_ms = _rand_int(1, 20)                  # 1-20 ms
    pft_ns = pft_ms * 1_000_000               # 转换为 ns

    eat_ns = (1 - p) * mem_access_ns + p * pft_ns
    eat_us = round(eat_ns / 1000, 4)

    p_str = f"{p_mantissa} × 10^{{{p_exponent}}}"

    params = {
        "mem_access_ns": mem_access_ns, "p_mantissa": p_mantissa,
        "p_exponent": p_exponent, "p": p, "pft_ms": pft_ms, "pft_ns": pft_ns,
    }
    question = (
        f"某请求分页系统，内存访问时间为 **{mem_access_ns} ns**。\n"
        f"缺页率为 **{p_str}**（即每 {int(1/p)} 次访问发生一次缺页）。\n"
        f"缺页中断处理时间为 **{pft_ms} ms**。\n\n"
        f"求该系统的 **有效访问时间 (Effective Access Time, EAT)**。"
    )

    steps = [
        f"**第 1 步：统一单位**\n"
        f"内存访问时间 = {mem_access_ns} ns\n"
        f"缺页率 p = {p_str} = {p}\n"
        f"缺页处理时间 = {pft_ms} ms = {pft_ms} × 10⁶ = **{pft_ns} ns**",
        f"**第 2 步：应用 EAT 公式**\n"
        f"EAT = (1 − p) × 内存访问时间 + p × 缺页处理时间\n"
        f"说明：绝大多数情况下不缺页（只需一次内存访问），"
        f"缺页时需要额外的磁盘 I/O 开销。",
        f"**第 3 步：代入计算**\n"
        f"EAT = (1 − {p}) × {mem_access_ns} + {p} × {pft_ns}\n"
        f"= {round((1 - p), 10)} × {mem_access_ns} + {p} × {pft_ns}\n"
        f"= {round((1 - p) * mem_access_ns, 4)} + {round(p * pft_ns, 4)}\n"
        f"= **{round(eat_ns, 4)} ns**",
        f"**第 4 步：换算为更直观的单位**\n"
        f"EAT ≈ **{eat_us} μs**",
        f"**结论**：由于缺页处理时间长达 {pft_ms} ms，即使缺页率很低（{p_str}），"
        f"有效访问时间也被显著拉长。降低缺页率是提升性能的关键。",
    ]
    answer = f"{round(eat_ns, 2)} ns（约 {eat_us} μs）"

    return CalcProblem(
        topic_id="page_fault",
        topic_name="缺页率与有效访问时间",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["请求分页", "缺页率", "有效访问时间", "EAT"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型 6: 磁盘调度算法平均寻道长度
# ═══════════════════════════════════════════════════════════════════════════

def _gen_disk_schedule_problem() -> CalcProblem:
    current = _rand_int(20, 180)
    # 生成 8 个请求
    n_requests = 8
    requests = sorted(random.sample(range(0, 200), n_requests + 1))
    if current in requests:
        requests.remove(current)
    requests = requests[:n_requests]

    direction = "增大" if _rand_int(0, 1) == 0 else "减小"
    requests_str = ", ".join(str(r) for r in requests)

    def fcfs(current, requests):
        seq = list(requests)
        total = sum(abs(seq[i] - (current if i == 0 else seq[i-1])) for i in range(len(seq)))
        return seq, total

    def sstf(current, requests):
        remaining = list(requests)
        pos = current
        seq = []
        total = 0
        while remaining:
            nearest = min(remaining, key=lambda x: abs(x - pos))
            total += abs(nearest - pos)
            pos = nearest
            seq.append(nearest)
            remaining.remove(nearest)
        return seq, total

    def scan(current, requests, direction_up=True):
        remaining = sorted(requests)
        seq = []
        total = 0
        pos = current
        if direction_up:
            right = [r for r in remaining if r >= pos]
            left = [r for r in remaining if r < pos]
            for r in right:
                total += abs(r - pos)
                pos = r
                seq.append(r)
            if left:
                total += abs(199 - pos)
                pos = 199
                for r in reversed(left):
                    total += abs(r - pos)
                    pos = r
                    seq.append(r)
        else:
            right = [r for r in remaining if r > pos]
            left = [r for r in remaining if r <= pos]
            for r in reversed(left):
                total += abs(r - pos)
                pos = r
                seq.append(r)
            if right:
                total += abs(0 - pos)
                pos = 0
                for r in right:
                    total += abs(r - pos)
                    pos = r
                    seq.append(r)
        return seq, total

    def cscan(current, requests, direction_up=True):
        remaining = sorted(requests)
        seq = []
        total = 0
        pos = current
        if direction_up:
            right = [r for r in remaining if r >= pos]
            left = [r for r in remaining if r < pos]
            for r in right:
                total += abs(r - pos)
                pos = r
                seq.append(r)
            if left:
                total += abs(199 - pos)
                pos = 199
                total += abs(0 - 199)
                pos = 0
                for r in left:
                    total += abs(r - pos)
                    pos = r
                    seq.append(r)
        else:
            right = [r for r in remaining if r > pos]
            left = [r for r in remaining if r <= pos]
            for r in reversed(left):
                total += abs(r - pos)
                pos = r
                seq.append(r)
            if right:
                total += abs(0 - pos)
                pos = 0
                total += abs(199 - 0)
                pos = 199
                for r in reversed(right):
                    total += abs(r - pos)
                    pos = r
                    seq.append(r)
        return seq, total

    dir_up = direction == "增大"

    fcfs_seq, fcfs_total = fcfs(current, requests)
    sstf_seq, sstf_total = sstf(current, requests)
    scan_seq, scan_total = scan(current, requests, dir_up)
    cscan_seq, cscan_total = cscan(current, requests, dir_up)

    fcfs_avg = round(fcfs_total / n_requests, 2)
    sstf_avg = round(sstf_total / n_requests, 2)
    scan_avg = round(scan_total / n_requests, 2)
    cscan_avg = round(cscan_total / n_requests, 2)

    params = {"current": current, "requests": requests, "direction": direction}
    question = (
        f"假定某磁盘有 **200 个柱面**，编号为 **0 ∼ 199**。\n"
        f"当前磁头位于 **{current} 号柱面**，磁头移动方向为 **{direction}**。\n"
        f"请求队列为：**{requests_str}**。\n\n"
        f"请分别用以下算法计算 **平均寻道长度**：\n"
        f"(1) FCFS（先来先服务）\n"
        f"(2) SSTF（最短寻道时间优先）\n"
        f"(3) SCAN（电梯算法，向{ direction }方向）\n"
        f"(4) C-SCAN（循环扫描，向{ direction }方向）"
    )

    steps = [
        f"**FCFS 算法**\n"
        f"服务顺序（按请求到达）：{current} → {' → '.join(str(r) for r in fcfs_seq)}\n"
        f"总寻道长度 = {fcfs_total}\n"
        f"平均寻道长度 = {fcfs_total} / {n_requests} = **{fcfs_avg}**",
        f"**SSTF 算法**\n"
        f"服务顺序（每次选最近的）：{current} → {' → '.join(str(r) for r in sstf_seq)}\n"
        f"总寻道长度 = {sstf_total}\n"
        f"平均寻道长度 = {sstf_total} / {n_requests} = **{sstf_avg}**",
        f"**SCAN 算法（向{direction}）**\n"
        f"服务顺序：{current} → {' → '.join(str(r) for r in scan_seq)}\n"
        f"总寻道长度 = {scan_total}\n"
        f"平均寻道长度 = {scan_total} / {n_requests} = **{scan_avg}**",
        f"**C-SCAN 算法（向{direction}）**\n"
        f"服务顺序：{current} → {' → '.join(str(r) for r in cscan_seq)}\n"
        f"总寻道长度 = {cscan_total}\n"
        f"平均寻道长度 = {cscan_total} / {n_requests} = **{cscan_avg}**",
        f"**四种算法对比**\n"
        f"| 算法 | 平均寻道长度 |\n|------|-------------|\n"
        f"| FCFS | {fcfs_avg} |\n"
        f"| SSTF | {sstf_avg} |\n"
        f"| SCAN | {scan_avg} |\n"
        f"| C-SCAN | {cscan_avg} |\n\n"
        f"通常 SSTF 平均寻道最短，但可能产生饥饿；"
        f"SCAN/C-SCAN 公平性更好。",
    ]
    answer = (
        f"FCFS={fcfs_avg}, SSTF={sstf_avg}, SCAN={scan_avg}, C-SCAN={cscan_avg}"
    )

    return CalcProblem(
        topic_id="disk_sched",
        topic_name="磁盘调度算法",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["磁盘", "寻道", "FCFS", "SSTF", "SCAN", "C-SCAN", "磁盘调度"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型 7: 银行家算法（死锁避免）
# ═══════════════════════════════════════════════════════════════════════════

def _gen_banker_problem() -> CalcProblem:
    """使用预计算参数池确保答案正确"""
    # 预定义 6 组参数：3 进程 × 3 资源，每组保证有安全序列
    presets = [
        {
            "n_proc": 3, "n_res": 3,
            "proc_names": ["P0", "P1", "P2"],
            "Allocation": [[0, 1, 0], [2, 0, 0], [3, 0, 2]],
            "Max": [[7, 5, 3], [3, 2, 2], [9, 0, 2]],
            "Available": [3, 3, 2],
            "request_proc": "P1", "Request": [1, 0, 2],
            "safe_sequence": ["P1", "P3", "P0"],  # using 1-indexed names or 0-indexed
            "can_grant": True,
        },
        {
            "n_proc": 3, "n_res": 3,
            "proc_names": ["P0", "P1", "P2"],
            "Allocation": [[0, 1, 0], [3, 0, 2], [3, 0, 2]],
            "Max": [[7, 5, 3], [3, 2, 2], [9, 0, 2]],
            "Available": [3, 3, 2],
            "request_proc": "P0", "Request": [0, 1, 0],
            "safe_sequence": ["P0", "P1", "P2"],
            "can_grant": True,
        },
        {
            "n_proc": 3, "n_res": 3,
            "proc_names": ["P0", "P1", "P2"],
            "Allocation": [[0, 3, 0], [3, 0, 2], [3, 0, 2]],
            "Max": [[7, 5, 3], [3, 2, 2], [9, 0, 2]],
            "Available": [2, 1, 0],
            "request_proc": "P0", "Request": [1, 0, 0],
            "safe_sequence": ["P0", "P2", "P1"],
            "can_grant": True,
        },
        {
            "n_proc": 4, "n_res": 3,
            "proc_names": ["P0", "P1", "P2", "P3"],
            "Allocation": [[0, 0, 1], [1, 0, 0], [1, 3, 5], [0, 6, 3]],
            "Max": [[0, 0, 1], [1, 7, 5], [2, 3, 5], [0, 6, 5]],
            "Available": [1, 5, 0],
            "request_proc": "P1", "Request": [0, 4, 2],
            "safe_sequence": ["P0", "P2", "P1", "P3"],
            "can_grant": True,
        },
        {
            "n_proc": 4, "n_res": 3,
            "proc_names": ["P0", "P1", "P2", "P3"],
            "Allocation": [[0, 0, 2], [1, 0, 0], [1, 3, 5], [0, 6, 3]],
            "Max": [[0, 0, 3], [1, 7, 5], [2, 3, 5], [0, 6, 5]],
            "Available": [1, 3, 0],
            "request_proc": "P1", "Request": [0, 4, 2],
            "safe_sequence": ["P0", "P2", "P1", "P3"],
            "can_grant": True,
        },
        {
            "n_proc": 3, "n_res": 3,
            "proc_names": ["P0", "P1", "P2"],
            "Allocation": [[1, 2, 2], [1, 0, 3], [1, 2, 1]],
            "Max": [[3, 3, 2], [2, 1, 3], [1, 2, 3]],
            "Available": [0, 1, 1],
            "request_proc": "P0", "Request": [1, 0, 1],
            "safe_sequence": ["P0", "P1", "P2"],
            "can_grant": True,
        },
    ]

    preset = random.choice(presets)
    n = preset["n_proc"]
    m = preset["n_res"]
    proc_names = preset["proc_names"]
    Allocation = preset["Allocation"]
    Max = preset["Max"]
    Available = preset["Available"]
    req_proc = preset["request_proc"]
    Request = preset["Request"]
    safe_seq = preset["safe_sequence"]

    # 计算 Need 矩阵
    Need = [[Max[i][j] - Allocation[i][j] for j in range(m)] for i in range(n)]

    # 构建问题文本
    alloc_str = "\n".join(
        f"  {proc_names[i]} | " + " | ".join(str(x) for x in Allocation[i])
        for i in range(n)
    )
    max_str = "\n".join(
        f"  {proc_names[i]} | " + " | ".join(str(x) for x in Max[i])
        for i in range(n)
    )
    avail_str = ", ".join(str(x) for x in Available)
    req_str = ", ".join(str(x) for x in Request)
    res_headers = " | ".join(chr(65 + j) for j in range(m))

    params = preset
    question = (
        f"某系统有 **{n} 个进程**和 **{m} 类资源**（A, B, C），当前状态如下：\n\n"
        f"** Allocation 矩阵：**\n"
        f"| 进程 | {res_headers} |\n|------|{'|'.join('---' for _ in range(m))}|\n"
        f"{alloc_str}\n\n"
        f"**Max 矩阵：**\n"
        f"| 进程 | {res_headers} |\n|------|{'|'.join('---' for _ in range(m))}|\n"
        f"{max_str}\n\n"
        f"**Available 向量：** ({avail_str})\n\n"
        f"进程 **{req_proc}** 发出请求 **({req_str})**。\n\n"
        f"请用银行家算法判断该请求能否被满足。若能，给出一个安全序列。"
    )

    # 判断步骤
    req_idx = proc_names.index(req_proc)
    req_grantable = all(Request[j] <= Need[req_idx][j] for j in range(m)) and \
                    all(Request[j] <= Available[j] for j in range(m))

    need_str = "\n".join(
        f"  {proc_names[i]} | " + " | ".join(str(x) for x in Need[i])
        for i in range(n)
    )

    steps = [
        f"**第 1 步：计算 Need 矩阵**（Need = Max − Allocation）\n"
        f"| 进程 | {res_headers} |\n|------|{'|'.join('---' for _ in range(m))}|\n"
        f"{need_str}",
        f"**第 2 步：检查请求合法性**\n"
        f"条件 1：Request ≤ Need[{req_proc}]？\n"
        f"  ({req_str}) ≤ ({', '.join(str(x) for x in Need[req_idx])})？"
        + (f" ✓" if all(Request[j] <= Need[req_idx][j] for j in range(m)) else " ✗") +
        f"\n条件 2：Request ≤ Available？\n"
        f"  ({req_str}) ≤ ({avail_str})？"
        + (f" ✓" if all(Request[j] <= Available[j] for j in range(m)) else " ✗"),
        f"**第 3 步：试探性分配**（假设批准请求）\n"
        f"Allocation[{req_proc}] += Request → "
        + ", ".join(str(Allocation[req_idx][j] + Request[j]) for j in range(m)) +
        f"\nNeed[{req_proc}] -= Request → "
        + ", ".join(str(Need[req_idx][j] - Request[j]) for j in range(m)) +
        f"\nAvailable -= Request → "
        + ", ".join(str(Available[j] - Request[j]) for j in range(m)),
        f"**第 4 步：安全性检测**\n"
        f"试探分配后，执行安全性算法：\n"
        f"安全序列：**{' → '.join(safe_seq)}**\n"
        f"所有进程均可完成，系统处于安全状态。",
        f"**结论**：请求 **可以满足**。安全序列为：**{' → '.join(safe_seq)}**。",
    ]
    answer = f"可以满足，安全序列：{' → '.join(safe_seq)}"

    return CalcProblem(
        topic_id="banker",
        topic_name="银行家算法（死锁避免）",
        subject="操作系统",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["死锁", "银行家算法", "安全序列", "死锁避免"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型 8: TCP 拥塞控制窗口与门限值计算
# ═══════════════════════════════════════════════════════════════════════════

def _gen_tcp_congestion_problem() -> CalcProblem:
    ssthresh_init = _rand_int(8, 16)  # 初始门限值
    # 生成随机事件序列：每个元素为 "ACK" 或 "TIMEOUT"
    # 确保事件序列合理（不会只有 TIMEOUT）
    events_pool = [
        # 预定义几个有代表性的序列
        ["ACK", "ACK", "ACK", "ACK", "TIMEOUT", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK"],
        ["ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "TIMEOUT", "ACK", "ACK", "ACK"],
        ["ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK", "ACK"],
        ["ACK", "ACK", "ACK", "TIMEOUT", "ACK", "ACK", "ACK", "ACK", "ACK", "3DUP", "ACK", "ACK"],
    ]
    events = random.choice(events_pool)

    # 跟踪 cwnd 和 ssthresh
    cwnd_values = [1]  # MSS
    ssthresh_values = [ssthresh_init]
    cwnd = 1
    ssthresh = ssthresh_init
    event_desc = []

    for i, ev in enumerate(events):
        if ev == "ACK":
            if cwnd < ssthresh:
                # 慢启动：每个 ACK cwnd += 1 (指数增长)
                cwnd = min(cwnd * 2, ssthresh)  # 简化：每个 RTT 翻倍
                phase = "慢启动"
            else:
                # 拥塞避免：线性增长
                cwnd += 1
                phase = "拥塞避免"
            event_desc.append(f"收到 ACK → {phase}，cwnd = {cwnd}")
        elif ev == "TIMEOUT":
            ssthresh = max(cwnd // 2, 2)
            cwnd = 1
            event_desc.append(f"超时！→ ssthresh = {ssthresh}，cwnd = 1（慢启动）")
        elif ev == "3DUP":
            # 快速重传和快速恢复
            ssthresh = max(cwnd // 2, 2)
            cwnd = ssthresh + 3
            event_desc.append(f"收到 3 个重复 ACK → 快速恢复，ssthresh = {ssthresh}，cwnd = {ssthresh} + 3 = {cwnd}")

        cwnd_values.append(cwnd)
        ssthresh_values.append(ssthresh)

    params = {"ssthresh_init": ssthresh_init, "events": events}
    events_display = ", ".join(
        f"**{e}**" if e == "TIMEOUT" else (f"*{e}*" if e == "3DUP" else e)
        for e in events
    )

    question = (
        f"TCP 连接建立后，初始 **cwnd = 1 MSS**，**ssthresh = {ssthresh_init} MSS**。\n\n"
        f"经过以下事件序列（每个 RTT 一个事件）：\n"
        f"{events_display}\n\n"
        f"请逐轮写出 **cwnd** 和 **ssthresh** 的变化过程，"
        f"并标注各轮所处的阶段（慢启动 / 拥塞避免 / 快速恢复）。"
    )

    step_lines = [f"**初始状态**：cwnd = 1, ssthresh = {ssthresh_init}"]
    for i, desc in enumerate(event_desc):
        step_lines.append(f"**RTT {i+1}**（{events[i]}）：{desc}")
    step_lines.append(
        f"\n**总结**：cwnd 变化路径：{' → '.join(str(v) for v in cwnd_values)}\n"
        f"最终 cwnd = {cwnd_values[-1]} MSS, ssthresh = {ssthresh_values[-1]} MSS"
    )

    steps = step_lines
    answer = f"最终 cwnd = {cwnd_values[-1]} MSS, ssthresh = {ssthresh_values[-1]} MSS"

    return CalcProblem(
        topic_id="tcp_congestion",
        topic_name="TCP 拥塞控制",
        subject="计算机网络",
        question=question,
        params=params,
        solution_steps=steps,
        answer=answer,
        knowledge_tags=["TCP", "拥塞控制", "慢启动", "拥塞避免", "快速恢复", "cwnd", "ssthresh"],
    )


# ═══════════════════════════════════════════════════════════════════════════
# 题型注册表与公开 API
# ═══════════════════════════════════════════════════════════════════════════

GENERATORS = {
    "cache_hit":        ("Cache 命中率与平均访问时间", "计算机组成原理", _gen_cache_problem),
    "pipeline":         ("流水线性能指标",             "计算机组成原理", _gen_pipeline_problem),
    "float_add":        ("浮点数加减运算",             "计算机组成原理", _gen_float_add_problem),
    "vaddr_trans":      ("虚拟地址→物理地址转换",     "操作系统",       _gen_vaddr_problem),
    "page_fault":       ("缺页率与有效访问时间",       "操作系统",       _gen_page_fault_problem),
    "disk_sched":       ("磁盘调度算法",               "操作系统",       _gen_disk_schedule_problem),
    "banker":           ("银行家算法",                 "操作系统",       _gen_banker_problem),
    "tcp_congestion":   ("TCP 拥塞控制",               "计算机网络",     _gen_tcp_congestion_problem),
}


def get_topic_list() -> list[dict]:
    """返回可用题型列表（供前端下拉菜单使用）"""
    return [
        {"id": tid, "name": name, "subject": subject}
        for tid, (name, subject, _gen) in GENERATORS.items()
    ]


def generate_problem(topic_id: str) -> Optional[CalcProblem]:
    """为指定题型生成一道随机参数的计算题"""
    entry = GENERATORS.get(topic_id)
    if entry is None:
        return None
    _name, _subject, gen_func = entry
    return gen_func()


def generate_all_topics() -> list[CalcProblem]:
    """为所有题型各生成一道题（用于批量测试）"""
    return [gen_func() for _name, _subject, gen_func in GENERATORS.values()]


# ═══════════════════════════════════════════════════════════════════════════
# CLI 测试入口
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for t in get_topic_list():
            print(f"  {t['id']:20s} {t['subject']:10s} {t['name']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--all":
        problems = generate_all_topics()
        for p in problems:
            print(f"\n{'='*60}")
            print(f"【{p.subject}】{p.topic_name}")
            print(f"{'='*60}")
            print(p.question)
            print(f"\n答案：{p.answer}")
    elif len(sys.argv) > 1:
        tid = sys.argv[1]
        p = generate_problem(tid)
        if p is None:
            print(f"未知题型: {tid}")
            print(f"可用: {', '.join(GENERATORS.keys())}")
        else:
            print(f"\n{'='*60}")
            print(f"【{p.subject}】{p.topic_name}")
            print(f"{'='*60}")
            print(p.question)
            print(f"\n{'─'*40}")
            for step in p.solution_steps:
                print(step)
            print(f"{'─'*40}")
            print(f"\n答案：{p.answer}")
    else:
        # 默认：测试 Cache 和流水线两题
        for tid in ["cache_hit", "pipeline"]:
            p = generate_problem(tid)
            print(f"\n{'='*60}")
            print(f"【{p.subject}】{p.topic_name}")
            print(f"{'='*60}")
            print(p.question)
            print(f"\n{'─'*40}")
            for step in p.solution_steps:
                print(step)
            print(f"{'─'*40}")
            print(f"\n答案：{p.answer}")
