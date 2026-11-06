# Azure 虚拟机 CPU / 内存二维装箱

把一批虚拟机请求放入尽量少的同规格主机，同时满足每台主机的 CPU 与内存容量限制。项目使用 Python、SQLite 和 Gurobi，完成数据提取、七种确定性算法实现、两条 MIP 求解路径，以及结果检查、保存与可视化。

当前实验覆盖 **280 个实例、2190 行方法结果**，单实例最多 **100000 条请求**。真实组 MIP 证明了 **21/30** 个实例最优，合成质量组证明了 **179/200** 个实例最优。

## 主要结果

| 观察 | 实验依据 | 可以支持的结论 |
|---|---|---|
| FFD-max 适合本批合成质量分布 | 达到 MIP 最终方案效果 191/200；对 FFD-sum 为 145 胜、55 平、0 负 | max 排序在该生成机制下表现突出 |
| 排序效果依赖数据结构 | 真实组 FFD-max 对 FFD-sum 为 1 胜、23 平、6 负 | 合成分布上的优势不能直接推广到真实负载 |
| 更强最坏保证不等于更好样本表现 | KK2003 在合成质量组的平均 A/OPT(U) 为 1.209118*，FFD-max 为 1.000494* | 理论保证与实测质量应分别评价 |
| 继续优化能增加最优证明 | 60 秒记录到结束：真实组 19→21，合成质量组 174→179 | 较长预算在部分实例上带来证明收益 |

胜、平、负均比较同一实例的主机数，越少越好。`*` 表示均值纳入尚未证优的 MIP 方案参照；**191/200 是达到 MIP 效果，不是 191 个已证最优**。仅在合成质量组已证优的 179 个实例上，FFD-max 命中最优 172 个。

十万条合成实例的五个条件中，KK2003 的纯算法耗时中位数为 93.47 秒，FFD-max 为 419.54 秒；对应平均 A/L 为 1.33522、1.05841，体现速度与装箱质量的取舍。该组没有运行 MIP，A/L 使用有效下界，不能直接解释成实际最优差距。

完整结果：[真实数据报告](results/formal_real_600_1200/analysis.md)、[合成质量报告](results/formal_synthetic_quality_600_1200/analysis.md)、[合成规模报告](results/formal_synthetic_scale_600_1200/analysis.md)。

![真实与合成规模的算法耗时](results/figures/03_runtime.png)

[六组图表说明](results/figures/FIGURE_GUIDE.md)同时给出质量、耗时、完成覆盖率及 MIP 证优进度；逐点数据保存在 `results/figures/plot_data.json`。

## 问题与建模范围

请求 i 的资源需求为 `(cpu_i, memory_i)`，每台主机的两维容量归一化为 `(1, 1)`。每条请求恰好分配一次，每台主机两维总需求均不超过 1，目标是最小化使用的主机数。

真实数据固定 `machineId=12`，取兼容请求的资源份额，再模拟多台这种规格的主机。它表示本项目选择的硬件规格，不代表原系统只有这一种硬件，也不表示请求在原系统中的实际部署位置。资源份额表示申请容量，不是运行时利用率。

这是静态、同构、批次离线问题：请求在批次内不释放资源，未建模迁移、异构硬件成本或生命周期重放。它可作为批量放置的研究子问题；实验中的一天窗口用于选取工作负载，**不等同于已验证的一秒生产调度系统**。

## 算法与 MIP

| 方法 | 本项目的具体规则 |
|---|---|
| FF | 按输入顺序放入第一台两维均可行的主机 |
| BF | 在可行主机中最小化放入后的剩余 CPU 与内存之和 |
| FFD-max | 按 max(CPU, Memory) 降序，再执行 FF |
| FFD-sum | 按 CPU+Memory 降序，再执行 FF |
| BFD-max | 按 max(CPU, Memory) 降序，再执行 BF |
| DP | 等权 bin-centric：为当前主机选择可行且“需求·剩余容量”最大的请求 |
| KK2003 | Kellerer–Kotov 的分类、成组填充与调整算法 |

请求评分同分按 ID，主机同分按创建顺序处理。FFD 两版本只改变排序分数，便于配对比较。DP 是指定的等权配置；KK2003 按论文流程实现并检查分组，但当前 Python 重复扫描实现不宣称达到论文的 O(n log n) 复杂度。理论近似比及来源见 [项目方案第 2 节](PROJECT_PLAN.md#2-算法与理论参照)；SODA 2016、FOCS 2023 仅作为理论参照，未实现。

MIP 初值取七种算法首遍有效方案中台数最少的一份。正式求解按数据结构分为两条路径：

- **真实数据：类型聚合模型。** 相同 `(CPU, Memory)` 的请求合为类型 t，用整数 `q[t,j]` 表示主机 j 接收该类的数量，用二元 `y[j]` 表示主机启用，最小化 `sum(y)`。约束覆盖各类型数量、两维容量和主机顺序，提供 MIP start。求解后恢复原请求 ID。
- **合成质量数据：不相容团锚定的固定 K 模型。** 团中的请求两两不能同机，将它们固定到不同主机，扣除容量，仅对可能的请求—主机组合创建二元变量。当前上界为 U 时测试 K=U−1；找到方案则改善 U，证明不可行则提高 L，未知则保留现有界。各次优化共享预算。

类型聚合减少重复请求的指派对称性；团锚定与固定 K 减少主机标签对称性和变量。项目未做不同 MIP 建模方法的受控消融，不能据此声称固定 K 在所有实例上必然更快。完整约束见 [项目方案第 4 节](PROJECT_PLAN.md#4-mip模型)。

`solution_checker.py` 独立检查请求身份、无重无漏及逐台两维容量。达到有效下界、优化模型证优或证明 U−1 台不可行，才记为已证最优。

## 数据与实验设计

| 实验组 | 规模 n | 条件 | 实例数 | 方法结果行数 |
|---|---|---|---:|---:|
| 真实 | 200、1000、10000、20000、100000 | 6 个时间窗口 | 30 | 240 |
| 合成质量 | 100、200、500、1000 | 5 个 alpha × 10 个 seed | 200 | 1600 |
| 合成规模 | 5000、10000、20000 | 5 个 alpha × 3 个 seed | 45 | 315 |
| 合成压力（归入规模组） | 100000 | 5 个 alpha × 1 个 seed | 5 | 35 |

真实数据将 `vm` 与 `vmType` 关联，筛选规格 12、两维资源在 `(0,1]` 的请求，按 `starttime, vmId` 升序取窗口前 n 条。窗口为 `[1,2)`、`[2,3)`、`[3,4)`、`[6,7)`、`[9,10)`、`[12,13)` 天。同窗不同 n 是嵌套前缀，不能当作独立随机样本。

合成数据每条请求独立采样两个 `(0,1)` 数，在该对内排序为 `l<h`；随机选取恰好 alpha×n 条设为 `(l,h)`，其余为 `(h,l)`。alpha 取 `{0.1,0.2,0.3,0.4,0.5}`，表示内存偏重比例。同一 `(n,seed)` 的不同 alpha 共用基础数对、方向优先序和输入顺序，支持配对比较。最终 CPU 与内存边际不应称为各自独立均匀分布。

启发式每次调用预算 **600 秒**；除 n=100000 测一次外，每实例测三次。MIP 每实例累计优化预算 **1200 秒**，保留同次任务的 60 秒记录。真实 MIP 使用 1 线程，合成 MIP 使用 2 线程；Seed=0。启发式私有内存采样限额 2048 MiB，Gurobi SoftMemLimit=2.0 GB。运行平台与版本详见各组 `metadata.json`。

## 指标与计时

记 A 为算法有效台数，L 为有效下界，U 为 MIP 最终最好有效方案台数，满足 `L ≤ OPT ≤ U`。参照 R 在已证优时取 OPT，否则取 U。

| 指标 | 含义 |
|---|---|
| 达到 MIP 效果 | `A ≤ U` 的实例数 / 全部条件数 |
| 平均 A/OPT(U) | 逐实例计算 A/R 后取平均；含未证优参照时标 `*` |
| 平均或最大参照差距 | `(A-R)/R`；带星时可能低估实际最优差距 |
| A/L、(A-L)/L | 相对有效下界的比值及差距，分别是对应最优指标的上界 |
| 已证优数量、(U-L)/L | 评价 MIP 的证明进度与当前界的距离 |
| 有效方案覆盖、完整计时覆盖 | 区分返回可用方案和完成全部规定计时重复 |

质量先逐实例算比值再平均；计时先取每实例重复中位数，再取同规模窗口或种子间中位数。计时重复不增加质量样本数。启发式时间只测算法函数；MILP 行时间包括七方法首遍外部尝试与 MIP 封装全程，不能与启发式纯函数时间混用。`solve_seconds` 仅计 Gurobi 优化。

本批正式记录包含以下未完成情况：

- DP 在真实组六个、合成规模组五个十万条条件中均触及 600 秒预算，没有完整方案。
- 合成规模组 `synthetic_v2_a40_s0_n10000` 的 BF 第三次计时遇到临时控制文件读取 `PermissionError`；前两次成功，5691 台首遍方案有效。质量保留，完整计时为 2/3，中位耗时留空。
- 真实组 9 个 MIP 未证优：4 个 TIME_LIMIT、5 个 MEM_LIMIT；合成质量组 21 个未证优，均为 TIME_LIMIT。真实十万条 MIP 为 1/6 证优，不能表述为全部十万条实例精确求解完成。

超时、错误或缺失结果均保留状态，不填 0 或预算秒数，不以补跑成功值覆盖原观测。

## 运行与复现

当前环境为 Windows PowerShell、Python 3.12.10、gurobipy 13.0.3、Matplotlib 3.10.7。批量监督器使用 Windows 私有内存采样，尚未验证其他操作系统。MIP 需要有效 Gurobi 许可。

### 1. 创建环境与安装依赖

```powershell
Set-Location "D:\PythonProjects\azure-vm-packing"
& "D:\Python\python312\python.exe" -m venv .venv
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
```

已有 `.venv` 时跳过创建。命令显式指定虚拟环境解释器，无需先激活。`requirements.txt` 固定直接依赖，历史元数据另记录实际运行环境；不宣称跨环境运行时间完全相同。

### 2. 直接阅读或重生成现有报告

已有正式结果时执行以下命令即可，不调用算法或求解器：

```powershell
& ".\.venv\Scripts\python.exe" ".\analyze_real.py"
& ".\.venv\Scripts\python.exe" ".\analyze_synthetic.py"
& ".\.venv\Scripts\python.exe" ".\plot_results.py"
```

三个 `analysis.md` 保存在对应正式目录；六组 PNG/PDF、图注与逐点 JSON 保存在 `results/figures/`。

### 3. 从原始数据构建输入（按需）

从下方官方数据页面下载并解压 SQLite，将所用文件放到 `data/raw/packing_trace_zone_a_v1.sqlite`。当前 `build_instance.py` 的数据库 URI 使用本项目的绝对路径；更换项目位置时需同步修改该 URI。

```powershell
& ".\.venv\Scripts\python.exe" ".\build_instance.py"
& ".\.venv\Scripts\python.exe" ".\build_synthetic.py"
```

分别生成 30 份真实实例和 250 份合成实例。已有固定输入可直接使用；生成命令会覆盖同名输入文件。

### 4. 从头重跑实验（按需）

先完成 Gurobi 许可配置。这三条命令会执行整组实验，使用与正式组不同的输出目录：

```powershell
& ".\.venv\Scripts\python.exe" ".\run_batch.py" --suite real --output-dir ".\results\reproduce_real_600_1200" --heuristic-seconds 600 --mip-seconds 1200 --snapshot-seconds 60
& ".\.venv\Scripts\python.exe" ".\run_batch.py" --suite synthetic-quality --output-dir ".\results\reproduce_quality_600_1200" --heuristic-seconds 600 --mip-seconds 1200 --snapshot-seconds 60
& ".\.venv\Scripts\python.exe" ".\run_batch.py" --suite synthetic-scale --output-dir ".\results\reproduce_scale_600_1200" --heuristic-seconds 600 --mip-seconds 1200 --snapshot-seconds 60
```

规模组按入口逻辑不运行 MIP，即使命令包含统一预算参数。每完成一个实例就原子保存检查点；程序中断后，在源码、输入、环境及配置不变时可用同一命令续跑。源码 SHA256、输入 SHA256 或配置变化会拒绝复用检查点，应选择新目录。中断时尚未保存的实例需要重跑。

本批实验后调整过展示符号和源码注释，原始运行指纹仍保留在历史结果中；当前源码不能直接续跑旧正式目录。报告和绘图使用当前分析代码并记录相应指纹。上面的新目录重跑结果也不会自动替代报告脚本默认读取的正式目录。

## 文件导航

| 文件或目录 | 用途 |
|---|---|
| `packing_algorithms.py`、`kellerer_kotov.py` | 七种算法 |
| `milp_solver.py`、`mip_progress.py` | 模型、界、解恢复及进度观测 |
| `solution_checker.py`、`result_metrics.py` | 独立放置检查及统一质量指标 |
| `build_instance.py`、`build_synthetic.py`、`instance_io.py` | 输入构建与读写 |
| `benchmark_heuristics.py`、`run_batch.py` | 预算监督、重复测量、正式矩阵与续跑 |
| `analyze_real.py`、`analyze_synthetic.py`、`plot_results.py` | 派生报告与图表 |
| `data/instances/` | 固定输入 JSON |
| `results/formal_*_600_1200/` | 汇总 CSV、环境元数据、逐实例状态与 ID 分组 |
| `try/` | 教学和小例子检查；使用方法见其 README |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | 唯一项目方案、完整模型与理论参照 |
| [DATABASE_GUIDE.md](DATABASE_GUIDE.md) | 环境、Python、SQL、文件读写与 Gurobi 用法回顾 |
| [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md) | 简历表述、项目介绍与面试追问 |

原始 SQLite、虚拟环境、缓存和个人编辑器配置由 `.gitignore` 排除；固定实验输入与正式结果可保存在本地 Git 中。

## 数据来源与算法参考

真实数据来自 Microsoft Azure **Azure Trace for Packing 2020**。官方说明数据采用 CC-BY Attribution License，并要求使用时引用配套论文：Ori Hadary et al., *Protean: VM Allocation Service at Scale*, OSDI 2020。本项目选取其中一个 zone 的请求与资源规格，构建上述静态二维子问题。[官方数据说明、许可与下载入口](https://github.com/Azure/AzurePublicDataset/blob/master/AzureTracesForPacking2020.md)

- Panigrahy et al., *Heuristics for Vector Bin Packing*, 2011：[论文](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/01/VBPackingESA11.pdf)。DP 使用本文框架中的指定等权配置。
- Kellerer and Kotov, *An approximation algorithm with absolute worst-case performance ratio 2 for two-dimensional vector packing*, Operations Research Letters, 2003：[DOI](https://doi.org/10.1016/S0167-6377(02)00173-6)、[公开全文](https://www.labri.fr/perso/eyraud/pmwiki/uploads/Main/Kellerer2003-VectorPacking2Approx.pdf)。KK2003 为确定性绝对 2 近似理论参照与实现来源。

合成数据由本项目生成，不表示 Azure 的真实需求分布。算法实现、模型与实验流程分别承担方法复现、求解和比较的作用，未提出新的近似算法。
