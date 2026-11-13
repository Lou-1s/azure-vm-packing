# Azure虚拟机双资源放置项目方案

更新日期：2026-11-06。

## 1. 目标与问题

面向运筹优化、决策算法岗位面试，展示三项能力：将问题落实为模型和程序；复现、比较经典启发式与论文算法；建立MIP并用Gurobi改进方案、证明最优或评价质量。

研究静态同型主机的CPU/内存二维向量装箱。请求i的需求为(c_i,m_i)，单机两维容量均归一化为1。每条请求恰好放置一次，每台两维需求总和均不超过1，目标是最小化主机数。

真实请求保留到达顺序，在批次内持续占用资源。在线系统可收集一个窗口内的请求后批量求解。项目固定硬件规格，比较这一离线子问题的装箱规则。

流程：`提取真实数据 / 生成随机实例 → 固定输入 → 七算法 → 对应MIP → 独立检查 → 保存 → 分析和展示`。

## 2. 算法与理论参照

| 方法 | 当前规则 | 二维近似比上界 |
|---|---|---|
| FF | 按输入顺序放入第一台可行主机 | 确定性、渐近2.7 |
| BF | 在可行主机中最小化放入后的剩余CPU与内存之和 | 确定性、渐近3，采用通用界 |
| FFD-max | 按max(CPU,Memory)降序，再执行FF | 确定性、渐近7/3 |
| FFD-sum | 按CPU+Memory降序，再执行FF | 确定性、渐近2.7，继承FF界 |
| BFD-max | 与FFD-max同样排序，再执行BF | 确定性、渐近3，采用通用界 |
| DP | 逐台扫描未放请求，选择可行且内积评分最高者 | 当前等权bin-centric版本适用确定性、渐近3的通用界 |
| KK2003 | Kellerer–Kotov分类、成组填充、调整和收尾，按论文七步实现 | 确定性、绝对2 |
| Bansal–Elias–Khan，SODA 2016 | 理论参照 | 确定性、绝对3/2+epsilon |
| Kulik–Mnich–Shachnai，FOCS 2023 | 理论参照 | 随机化、渐近4/3+epsilon |

统一以A/OPT表示比例。绝对保证约束每个实例，渐近保证允许低阶附加项。BF、BFD及当前DP的3界来自最终任意两箱不能整体合并的通用结论。FOCS 2023附录A指出SODA 2016第6节约1.405的分析存在漏洞。

正式对照为表中的前七种方法。

请求排序同分按请求ID，主机同分按创建编号，评分严格更优才替换候选；先确认两维可行，再比较评分。DP采用Panigrahy等(2011)的bin-centric等权配置，最大化`cpu_i*r_cpu + memory_i*r_mem`，放入后更新剩余容量，无请求可放才开启下一台。

KK保留论文分类、P(v)/P(w)、成组与小请求调整；显式清除空主机，并合并同组内确实可合放的主机，保留组请求、总资源及证明标记，只降低台数。相等需求小请求只归一侧，尾部FF先处理剩余主导资源总量较大的一侧。论文给出O(n log n)实现。本项目的Python实现使用重复扫描。实验同时评价台数和效率。

## 3. 固定实验输入

请求为五元组`(vmId, vmTypeId, starttime, cpu, memory)`。JSON另存来源、参数、n、资源统计、容量和排序规则；读回核对数量，保存SHA256。

### 3.1 真实数据

只读数据库为`data/raw/packing_trace_zone_a_v1.sqlite`。将vm与vmType按vmTypeId关联，固定machineId=12得到资源份额，再模拟多台同规格主机。machineId是硬件规格编号。份额是申请容量占单台该规格主机容量的比例。

规格12在实验前用[0,1)天校准窗口选定，兼容414634/436364条，约95.02%；与规格21覆盖数相同，按编号选12。

筛选两资源均在(0,1]、starttime属于左闭右开窗口，按`starttime ASC, vmId ASC`排序取前n条。各优先级使用同一套筛选条件。同窗口先读取100000条一次，再取嵌套前缀。

| 窗口（天） | 有效兼容请求数 |
|---|---:|
| [1,2) | 377970 |
| [2,3) | 317788 |
| [3,4) | 300228 |
| [6,7) | 301380 |
| [9,10) | 247139 |
| [12,13) | 329487 |

每窗口取n∈{200,1000,10000,20000,100000}，共30份，存于`data/instances/real_v2/`。每份比较七算法及类型聚合MIP。

单zone数据[0,14)天新增请求平均约3.885条/秒，按硬件12筛选后约3.715条/秒，1000条约为4.5分钟平均到达量。六窗口是固定工作负载，同窗不同n是嵌套前缀。

### 3.2 随机合成数据

alpha∈{0.1,0.2,0.3,0.4,0.5}，表示内存偏重请求比例。

对每个(n,seed)，每条请求独立采样两个U(0,1)数，排除端点和相等值，仅在该对内部排序得到(l,h)。独立固定随机流打乱请求编号，前alpha*n个编号取(CPU,Memory)=(l,h)，其余取(h,l)；输入仍按原ID排列。

同一(n,seed)的各alpha共用基础数对、方向优先序、ID与输入顺序，只改变方向。跨alpha每条请求的sum与max不变，alpha条件配对。各n分别生成实例。

E[l]=1/3、E[h]=2/3，因此E[CPU]=(2-alpha)/3、E[Memory]=(1+alpha)/3。两维的边际分布由l和h按方向比例混合。alpha增加使预期需求从CPU主导趋于均衡。

| 用途 | n | 每个(n,alpha)的seed | 实例数 | 求解安排 |
|---|---|---|---:|---|
| 合成质量 | 100、200、500、1000 | 0—9，共10个 | 200 | 七算法及固定K MIP |
| 合成规模 | 5000、10000、20000 | 0—2，共3个 | 45 | 七算法及有效下界 |
| 合成压力 | 100000 | 0 | 5 | 七算法及有效下界 |

合计250份，存于`data/instances/synthetic_alpha/`；加真实组共280个条件。种子重复评价分布下的稳定性。每份实例贡献一个质量样本。

## 4. MIP模型

初值取七算法首遍有效方案中台数最少的一份，保留完整分组。原逐请求指派模型保留为教学代码，正式实验按来源使用两条路径。

### 4.1 合成：团锚定固定K可行性模型

上界U来自有效方案；下界L取资源总量下界与贪心不相容团大小的最大值。任一维需求之和超过1的请求对不能同机。按max、sum、CPU优先、内存优先四种固定顺序分别贪心构团，取最大的有效团。构团时按需检查请求对的相容性。

将团请求锚定到不同主机并扣除容量，只对可放入剩余容量的请求—主机组合创建二元变量；未锚定主机按CPU负载非增序破除对称性。给定K、剩余请求I与剩余容量C_j、M_j：

```text
find x[i,j] in {0,1}
subject to
    sum(j) x[i,j] = 1                 for each i in I
    sum(i) cpu[i] * x[i,j] <= C[j]    for each host j
    sum(i) mem[i] * x[i,j] <= M[j]    for each host j
```

目标恒0，判断至多K台是否可行。L<U时测试K=U-1；找到方案按非空台数更新U，证不可行则L=K+1；L=U即证优。到预算或未判定时保留当前界和方案。各K共享1200秒累计优化预算。

### 4.2 真实：类型聚合主机启用模型

相同(cpu,memory)合成类型t，数量b_t。整数q[t,j]是主机j接收的类型t数量，二元y[j]表示启用；候选数H由初值确定。

```text
min sum(j) y[j]
subject to
    sum(j) q[t,j] = b[t]                 for each type t
    sum(t) cpu[t] * q[t,j] <= y[j]       for each host j
    sum(t) mem[t] * q[t,j] <= y[j]       for each host j
    0 <= q[t,j] <= per_host_limit[t], integer
    y[j] in {0,1}
```

加入资源下界、顺序启用和MIP start；per_host_limit由类型数量与单机容量确定。聚合消除同需求请求互换的对称性；求解后按类型数量恢复原ID，再独立检查。每实例一次聚合任务，优化预算1200秒。

### 4.3 证明与参数

独立检查身份、无重无漏及逐台两维容量。方案达到独立下界、聚合模型证优，或U-1不可行且已有U台方案，均可提供最优证明。

Gurobi Seed=0，真实Threads=1、合成Threads=2，SoftMemLimit=2.0GB，容量与整数容差1e-9。检查器使用一致容量容差，下界计算处理整数附近浮点误差。聚合模型可能启用空主机，回调恢复分组后按非空台数比较，保留已验证的最好方案。

## 5. 预算、计时与60秒记录点

| 项目 | 当前设置 |
|---|---|
| 启发式预算 | 每种方法、每实例、每次调用600秒（10分钟） |
| 计时重复 | n≤20000时3次，全完成才取中位数；n=100000时1次 |
| 启发式内存 | 2048MiB私有内存采样保护，间隔0.05秒 |
| 启动与结果检查 | 各30秒，独立于算法预算 |
| MIP预算 | 每实例累计Gurobi优化1200秒（20分钟） |
| MIP进度 | 同次求解的60秒截止记录与最终记录 |

一次预算终止后停止该方法剩余重复。首遍已有方案仍可评价质量，重复未全完成则中位耗时留空。MIP可因证优、内存等原因提前结束，优化预算只计Gurobi优化时间。

60秒点评价继续求解是否减少台数、提高下界或新增最优证明。当前真实批次60秒后有7份方案继续改善、合计少用48台，并新增2份证优。图06比较同一次求解的60秒记录与最终证优比例。真实组由19/30提高到21/30，合成质量组由174/200提高到179/200。

回调非固定频率。跨过60秒时先冻结此前已观测状态，再接收新信息；requested、effective、observed分别记录目标、有效截止位置和最近观测时间。提前结束用实际时刻。截止和结束两份ID分组均可恢复检查。

启发式seconds只测算法函数。upper_bound_seconds为七方法首遍外部时间之和，含启动、读取、检查和失败尝试；mip_total_seconds为MIP封装全程；solve_seconds只计优化。MILP行seconds是初解外部时间加MIP封装时间，与启发式函数时间分开解释。

## 6. 指标与统计

A为算法有效台数，U为MIP当前最好有效方案台数，L为已证下界，满足L≤OPT≤U。已证优时参照R=OPT；未证优时参照R=U。

| 指标 | 定义 |
|---|---|
| 有效方案/条件 | 返回有效方案数 / 全部条件数 |
| 达到MIP效果 | A≤本实例MIP最终台数的数量 / 全部条件数；真实组xx/30 |
| 平均A/OPT(U) | 逐实例计算A/R，再对有效、可比较结果取平均 |
| 最大已知差距 | 逐实例计算(A-R)/R后取最大值 |
| 按规模平均差距 | 该规模平均(A-R)/R，并标注已证优/未证优参照数量 |
| 已知最优覆盖率 | 已证OPT数 / 全部实例数 |
| 证明进度 | L≤OPT≤U、(U-L)/L、截止后上界改进与下界提升 |
| 效率 | 完整计时完成率、算法/流程时间、终止状态、模型规模、采样内存 |

均值或最大差距包含未证优参照时标*。例如`xxx% (3+2*)`表示3个已证优参照与2个未证优MIP参照的有效实例。无方案的条目显示为缺失。

带星号数值使用MIP方案作为参照，可能低估距OPT的差距。合成规模组使用下界指标。方案达到独立下界即可证优。

新字段为reference_host_count、reference_is_optimal、ratio_to_reference、gap_to_reference、reaches_mip。原lower_bound、ratio_to_bound、gap_to_bound保留真实下界语义，原OPT字段只在证优时填写。Gurobi原生gap与(U-L)/L分别记录。

按n、窗口或alpha分层；逐实例计算质量，再汇总均值、最大差距及有效样本数。时间先取每实例重复中位数，再取同规模窗口/种子间中位数。FFD-max与sum逐实例配对统计胜平负及台数差。

## 7. 文件与复现

| 路径 | 用途 |
|---|---|
| data/raw/packing_trace_zone_a_v1.sqlite | 唯一原始数据库，只读、本地保留 |
| data/instances/real_v2/ | 30份当前真实输入 |
| data/instances/synthetic_alpha/ | 250份当前合成输入 |
| results/ | 新预算正式输出，检查脚本临时输出放checks/ |
| try/ | 12个教学/检查脚本、导入辅助和简短说明 |
| packing_algorithms.py、kellerer_kotov.py | 七种构造算法 |
| milp_solver.py、mip_progress.py | 两条正式MIP路径、原学习模型及进度观测 |
| solution_checker.py、result_metrics.py | 独立校验与统一MIP参照指标 |
| instance_io.py、build_instance.py、build_synthetic.py | 输入读写、提取和生成 |
| benchmark_heuristics.py、run_batch.py | 监督式运行、正式矩阵及续跑 |
| run_experiments.py | 共用方法/字段及小规模试跑 |
| analyze_real.py、analyze_synthetic.py | 已验收的三组分析报告入口，按n、alpha及窗口组织质量、计时和MIP结果 |
| plot_results.py | 从已保存结果生成六组PNG/PDF、逐点数据与图注 |
| README.md | 项目入口、主要结论、运行方法、指标、限制与数据来源 |
| INTERVIEW_GUIDE.md | 一分钟介绍、简历表述、模型和实验追问及讲解练习 |
| DATABASE_GUIDE.md、PROJECT_PLAN.md | 复习速查与唯一当前方案 |
| requirements.txt | 固定项目依赖 |

旧结果、预检输出、重复旧实例与学习过程日志已清理，保留原SQLite、280份输入、源码、环境和复习资料。历史提交可在本地Git查阅；try脚本读取当前输入小前缀或自带人工例。Python入门练习脚本仍供复习。

### 7.1 环境与教学检查

在项目根目录打开 PowerShell。虚拟环境的创建步骤见 [README](README.md#1-创建环境与安装依赖)。

```powershell
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

# 如需手动指定许可证，取消下一行注释并换成自己的文件路径。
# $env:GRB_LICENSE_FILE = "C:\path\to\gurobi.lic"

& ".\.venv\Scripts\python.exe" ".\try\try_first_fit.py"
& ".\.venv\Scripts\python.exe" ".\try\try_mip_progress.py"
```

环境为Python3.12、gurobipy13.0.3及有效Gurobi许可证。固定输入已存在，可直接运行；需要重建时使用build_instance.py和build_synthetic.py。

### 7.2 正式实验命令

在项目根目录打开已配置 Gurobi 许可证的 PowerShell。三组串行执行，可分不同日期运行。

```powershell
& ".\.venv\Scripts\python.exe" ".\run_batch.py" --suite real --output-dir ".\results\formal_real_600_1200" --heuristic-seconds 600 --mip-seconds 1200 --snapshot-seconds 60

& ".\.venv\Scripts\python.exe" ".\run_batch.py" --suite synthetic-quality --output-dir ".\results\formal_synthetic_quality_600_1200" --heuristic-seconds 600 --mip-seconds 1200 --snapshot-seconds 60

& ".\.venv\Scripts\python.exe" ".\run_batch.py" --suite synthetic-scale --output-dir ".\results\formal_synthetic_scale_600_1200" --heuristic-seconds 600 --mip-seconds 1200 --snapshot-seconds 60
```

| 组别 | 实例数 | 方法 | 完整汇总行数 |
|---|---:|---|---:|
| real | 30 | 七算法+类型聚合MIP | 240 |
| synthetic-quality | 200 | 七算法+固定K MIP | 1600 |
| synthetic-scale | 50 | 七算法，无MIP | 350 |
| 合计 | 280 | | 2190 |

超时也保留状态行。每实例一个检查点，summary.csv为汇总，metadata.json为参数环境；完整分组只存ID，由固定输入恢复。

相同命令可续跑，要求输入SHA、十份源码SHA、配置环境一致。运行中保持源码参数一致；Saved为完成保存，Resumed为续用，尚未保存实例中断后需重跑。batch版本batch_v3_mip_reference，默认目录包含启发式/MIP预算。

运行以下命令生成真实组报告。

```powershell
& ".\.venv\Scripts\python.exe" ".\analyze_real.py" --results-dir ".\results\formal_real_600_1200"
```

运行以下命令生成两组合成报告。

```powershell
& ".\.venv\Scripts\python.exe" ".\analyze_synthetic.py"
```

脚本读取现有结果，分别生成质量组和规模组目录中的analysis.md。质量组使用OPT/MIP最终方案混合参照及星号；规模组使用下界L指标。按(n,alpha)分层，保留缺失计时和有效覆盖。

### 7.3 跨组图表

项目根目录的plot_results.py及六组图表已生成并核对；重新生成时执行：

```powershell
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" ".\plot_results.py"
```

项目虚拟环境已安装matplotlib==3.10.7。自行安装时，在PowerShell进入项目后执行`& ".\.venv\Scripts\python.exe" -m pip install matplotlib==3.10.7`。也可用上面的`-r requirements.txt`安装项目依赖。新终端可直接调用项目的虚拟环境解释器。

默认结果目录为results/figures，包含六组PNG/PDF：真实质量、合成质量与alpha、规模耗时、完整计时覆盖、合成规模相对L质量、MIP截止/最终证优率。另存plot_data.json及FIGURE_GUIDE.md，记录逐点样本数、版本和结果指纹。

质量图纵轴采用线性刻度，含未证优MIP参照的条件标星；规模L图独立解释。耗时采用对数轴、缺失值断线，预算处空心三角标记超时。BF执行错误记为缺失计时。七算法使用各不相同的虚线形式，同时保留固定颜色和标记；逐点计数与原CSV可核对。图表从原实验结果生成。

实验元数据保存正式运行时的源码指纹。plot_data保存生成图表时使用的分析和绘图源码指纹。

## 8. 进度与后续

当前交付完成度估算为95%。三组运行、三份报告及六组图表已验收；结果结论、README、复现说明和面试讲解稿已完成并核对。待用户阅读、核对个人贡献表述及练习讲解后，再做最终交付检查。

| 模块 | 权重 | 已完成分值 |
|---|---:|---:|
| 问题定义、环境与工具 | 10 | 10 |
| 数据提取、生成与固定输入 | 15 | 15 |
| 七算法及效率组件 | 20 | 20 |
| MIP模型、恢复、检查及进度 | 25 | 25 |
| 实验运行与结果分析 | 20 | 20 |
| 图表、README及复现交付 | 10 | 5 |
| 合计 | 100 | 95 |

本批280条件/2190行、输入及十份源码指纹、配置、CSV/JSON字段和全部2639份主/时点分组均核对通过。真实组MIP证优21/30，合成质量组179/200，规模组无MIP且无独立证优实例。真实组DP六个10万条条件、规模组DP五个10万条条件均触及600秒预算，无完整方案；质量组七种算法全部完成。

规模组中，synthetic_v2_a40_s0_n10000的BF第三遍读取临时started.json时发生PermissionError，前两遍成功且5691台方案有效。正式记录保留有效质量、2/3重复及空中位耗时。工程收尾时可单独验证有界读取重试。

真实组60秒后7例上界改善，共少用48台，新增2份证优；合成质量组60秒后1例再省1台、5例提高下界并新增5份证优。质量组FFD-max达到MIP效果191/200，较FFD-sum为145胜55平。

README已汇总模型、实验设计、结果结论、数据来源和运行方法；INTERVIEW_GUIDE已给出一分钟介绍、三条简历表述及模型、指标、异常和AI辅助的常见追问。关键数字已按正式CSV及报告交叉核对。

后续由用户核对个人贡献表述，练习讲清一条MIP路径和两张图；再检查文档、结果文件与本地Git保存状态，完成交付。需要独立重跑时按README使用新输出目录。当前报告可直接重建。

## 9. 主要来源

- [Azure Packing Trace数据说明](https://github.com/Azure/AzurePublicDataset/blob/master/AzureTracesForPacking2020.md)：数据结构、归属及CC BY许可。
- [Panigrahy等，2011](https://www.microsoft.com/en-us/research/wp-content/uploads/2011/01/VBPackingESA11.pdf)：DP框架。
- [Kellerer–Kotov，ORL 2003](https://doi.org/10.1016/S0167-6377(02)00173-6)、[公开全文](https://www.labri.fr/perso/eyraud/pmwiki/uploads/Main/Kellerer2003-VectorPacking2Approx.pdf)：绝对2近似及七步算法。
- [Bansal–Elias–Khan，SODA 2016](https://doi.org/10.1137/1.9781611974331.ch106)、[全文](https://elias.id/papers/2016-SODA_Vector_packing.pdf)：第5节确定性绝对3/2+epsilon。
- [Kulik–Mnich–Shachnai，FOCS 2023](https://arxiv.org/abs/2205.12828)、[全文](https://arxiv.org/html/2205.12828v3)：随机化渐近4/3+epsilon与对旧分析问题的说明。
- [COR 2025第8节](https://eprints.whiterose.ac.uk/id/eprint/218204/8/1-s2.0-S0305054824003320-main.pdf)、[Csirik等1990](https://repub.eur.nl/pub/11738/On_the_multidimensional_vector_binpacking.pdf)：FF/FFD界与最大坐标排序。
- [Galambos等1993命题1.1](https://acta.bibl.u-szeged.hu/12518/1/cybernetica_011_numb_001_002_023-034.pdf)：不可整体合并装箱的通用界。
- [Gurobi模型](https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html)、[状态码](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html)、[参数](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html)：求解接口。

语法查阅 [DATABASE_GUIDE.md](DATABASE_GUIDE.md)，教学脚本查阅 [try/README.md](try/README.md)。
