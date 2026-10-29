# Python、SQL 与 Gurobi 速查

- [一、虚拟环境](#一虚拟环境)
- [二、Python 基础](#二python-基础)
- [三、SQLite 与 SQL](#三sqlite-与-sql)
- [四、Gurobi](#四gurobi)

## 一、虚拟环境

虚拟环境用于隔离项目依赖。创建一次，新终端按需激活。[官方文档](https://docs.python.org/zh-cn/3.12/tutorial/venv.html)

在 PowerShell 中执行：

```powershell
# 进入项目目录
Set-Location "D:\PythonProjects\azure-vm-packing"

# 创建 .venv，使用现有的 Python 3.12
& "D:\python\python312\python.exe" -m venv .venv

# 激活当前终端的环境
.\.venv\Scripts\Activate.ps1

# 检查解释器、pip，运行程序
python -c "import sys; print(sys.executable)"
python -m pip --version
python .\first_python.py

# 退出当前终端的环境
deactivate
```

激活后通常出现 `(.venv)`。解释器路径应指向项目的 `.venv\Scripts\python.exe`；`deactivate` 不会删除环境。

不激活时，也可以直接指定环境中的 Python：

```powershell
& ".\.venv\Scripts\python.exe" ".\first_python.py"
```

`&` 用于调用引号中的程序路径；`-m` 表示运行模块，例如 `venv`、`pip`。

VS Code：`Ctrl+Shift+P` → `Python: Select Interpreter` → 选择项目 `.venv\Scripts\python.exe`。选择解释器与激活终端是两项操作。

## 二、Python 基础

### 1. 赋值、输出与注释

```python
cpu = 0.4                    # 小数
machine_id = 12              # 整数
name = "vm"                  # 字符串
fits = True                  # 布尔值：True 或 False
print("CPU:", cpu)           # 输出 CPU: 0.4
```

`=` 赋值，`==` 比较是否相等，`#` 后面是注释。`"""..."""` 可以保存多行字符串。

赋值先计算右侧，再保存结果；之后修改输入变量不会自动更新旧结果：

```python
a_cpu = 0.4
b_cpu = 0.35
cpu_total = a_cpu + b_cpu

a_cpu = 0.8
print(cpu_total)              # 0.75
cpu_total = a_cpu + b_cpu     # 重新计算
print(cpu_total)              # 1.15
```

### 2. 列表、元组与索引

```python
vm = (0.4, 0.3)              # 元组：(CPU, 内存)
vms = [                      # 列表：存放多条记录
    (0.4, 0.3),
    (0.35, 0.5),
    (0.2, 0.1),
]

print(vms[0])                # 第一条：(0.4, 0.3)
print(vms[0][1])             # 第一条的内存：0.3
print(vms[2][0])             # 第三条的 CPU：0.2
print(len(vms))              # 记录数：3
```

索引从 `0` 开始。列表用 `[]`，可以修改；元组用 `()`，其中的元素不能重新赋值。单元素元组写作 `(12,)`。

### 3. 条件判断

`<`、`<=`、`>`、`>=`、`==`、`!=` 用于比较。`and` 要求两个条件同时成立。

```python
cpu_total = 0.75
memory_total = 0.8
fits = (cpu_total <= 1) and (memory_total <= 1)

if fits:
    print("可以放进同一台主机")
else:
    print("不能放进同一台主机")
```

`if`、`else` 后加冒号，代码块统一缩进四个空格。

### 4. for 循环与累计

```python
vms = [(0.4, 0.3), (0.35, 0.5)]
cpu_total = 0
memory_total = 0

for vm in vms:
    cpu_total = cpu_total + vm[0]
    memory_total = memory_total + vm[1]

print(cpu_total, memory_total)  # 0.75 0.8
```

`for` 逐个取出列表元素。累计变量在循环外初始化，避免每次都清零；数值累计也可写成 `cpu_total += vm[0]`。

### 5. 函数、参数与返回值

```python
def resource_totals(requests):
    cpu_total = 0
    memory_total = 0
    for vm in requests:
        cpu_total += vm[0]
        memory_total += vm[1]
    return cpu_total, memory_total

vms = [(0.4, 0.3), (0.35, 0.5)]
totals = resource_totals(vms)
print(totals)                 # (0.75, 0.8)

# 也可以把返回的两个值分别接收
cpu_total, memory_total = resource_totals(vms)
```

`def` 定义函数，参数接收输入，`return` 交回结果；`print` 只负责显示。函数内部赋值的变量通常是局部变量，结果需要返回并接收。

```python
def can_share_one_host(requests):
    totals = resource_totals(requests)
    return (totals[0] <= 1) and (totals[1] <= 1)
```

不要用结果变量覆盖函数名，例如在函数内写 `resource_totals = resource_totals(requests)`。

模块使用 `import` 引入，例如 `import sqlite3`、`import sys`。

### 6. 多项输出与数值显示

```python
cpu_total = 3.0199999999999996
memory_total = 1.1484375

print("CPU", "Memory", sep=" | ")
print(round(cpu_total, 6), round(memory_total, 6), sep=" | ")
```

输出：

```text
CPU | Memory
3.02 | 1.148438
```

`print` 可以接收多个待显示的值；`sep=" | "` 指定它们之间用什么分隔，默认是空格。

`round(数值, 6)` 返回按六位小数舍入的数值，不会重新赋值给原变量。这里仅用于显示，算法继续使用原始需求数据。

[官方教程：基本用法](https://docs.python.org/zh-cn/3.12/tutorial/introduction.html) · [控制流与函数](https://docs.python.org/zh-cn/3.12/tutorial/controlflow.html)

### 7. 列表操作、循环控制与排序

```python
hosts = []
hosts.append([request])       # 追加一个装有 request 的新主机；request 是一条已有请求
print(len(hosts))             # 主机数

best_host = None              # 暂时没有选中的主机
if best_host is None:
    print("需要新开主机")

vm_ids = [10, 11, 12]
print(11 in vm_ids)           # True：是否存在
print(11 not in vm_ids)       # False：是否不存在
print(vm_ids.index(11))       # 1：该值第一次出现的位置
```

`append(元素)` 修改原列表，不要写成 `hosts = hosts.append(...)`。`break` 退出当前所在的最内层循环；`return` 结束整个函数。`None` 表示暂时没有值，不等于空列表 `[]`。

本项目的请求记录为 `(vmId, vmTypeId, starttime, core, memory)`：

```python
def decreasing_key(request):
    return -max(request[3], request[4]), request[0]

ordered_requests = sorted(requests, key=decreasing_key)
```

`sorted(待排序列表, key=评分函数)` 返回新列表，不改变原列表；它会逐条调用评分函数。上例按 CPU/内存较大值降序，同分按请求编号升序。负号将“大值优先”转换成默认的升序比较。

```python
for i in range(3):            # 依次取 0、1、2；不包含 3
    print(i)

valid, message = check_solution(requests, hosts)  # 接收检查器返回的两个值
if not valid:                # valid 为 False 时进入
    raise ValueError(message)  # 抛出错误；未被捕获时停止程序
```

`from packing_algorithms import first_fit` 从同目录模块导入函数；文件应先保存，且函数名要对应。

### 8. 字典与默认参数

```python
result = {"status": 2, "objective": 2.0, "gap": 0.0}  # 用“键: 值”保存结果
print(result["objective"])     # 按键名读取：2.0
result["gap"] = None           # 修改该键对应的值；None 表示暂时没有值
```

字典用 `{}`，每项是 `键: 值`，各项之间用逗号分开。`result["objective"]` 按名称取值；键名必须与保存时一致。

函数定义中的 `time_limit=30` 指定默认值：调用时省略它就用 30，写 `time_limit=0` 则用 0。它与调用时的关键字参数写法相似，但默认值在定义函数时指定。

### 9. 测量耗时

```python
from time import perf_counter  # 引入适合测量短时间间隔的计时函数

started = perf_counter()       # 记录开始时的计时值
hosts = first_fit(requests)    # 实际运行要测量的代码
seconds = perf_counter() - started  # 两次计时值的差，单位为秒
```

`perf_counter()` 的单个数值不表示日期；两次调用之差才是经过的时间。计时起止位置决定包含哪些工作。[Python 文档](https://docs.python.org/zh-cn/3.12/library/time.html#time.perf_counter)

### 10. while 循环与 pop

```python
remaining = [10, 20, 30]
while len(remaining) > 0:       # 每轮先判断；列表非空就继续
    selected = remaining.pop(0)  # 删除索引 0 的元素，并返回它
    print(selected, remaining)
```

`pop(位置)` 同时修改原列表并返回被删除的元素。删除位置 0 后，后续元素向前移动；位置与元素值不同，例如 `pop(0)` 取出的是第一项 10。

`while True:` 持续循环，直到执行其中的 `break`。嵌套循环中，`break` 只退出它所在的最内层循环。选择候选时先完整扫描，再删除选中项，避免遍历过程中索引发生移动。[Python 列表文档](https://docs.python.org/zh-cn/3.12/tutorial/datastructures.html)

## 三、SQLite 与 SQL

### 1. 用 Python 读取数据库

`sqlite3` 是 Python 自带的模块，无需另外安装。

```python
import sqlite3

database = "file:D:/PythonProjects/azure-vm-packing/data/raw/packing_trace_zone_a_v1.sqlite?mode=ro"
connection = sqlite3.connect(database, uri=True)

sql = """
SELECT vmTypeId, core, memory
FROM vmType
WHERE machineId = ?
ORDER BY vmTypeId ASC
LIMIT ?
"""

cursor = connection.execute(sql, (12, 5))  # SQL 文本；两个 ? 按顺序取 12 和 5
rows = cursor.fetchall()                  # 取回结果，得到“列表中的元组”
connection.close()                       # 关闭连接，已取回的 rows 仍可使用

for row in rows:
    print(row)
```

- `uri=True`：按文件 URI 格式解析地址；`file:` 指向文件，`?` 后是连接选项。
- `mode=ro`：只读打开数据库。

- `execute(sql, 参数元组)`：执行查询，返回用于读取结果的游标。这里 `sql` 是查询文本，`(12, 5)` 分别对应硬件编号与最多返回的行数。
- `fetchall()`：把游标尚未取出的记录取回为列表；无结果或已经取完时返回 `[]`。
- `len(rows)` 是结果行数，`rows[0]` 是第一行，`rows[0][1]` 是第一行第二项。
- `print(sql)` 只显示 SQL 字符串；查询在 `execute` 时执行。

[Python sqlite3 文档](https://docs.python.org/3.12/library/sqlite3.html#how-to-work-with-sqlite-uris)

### 2. 选列、筛行、排序与数量

| 写法 | 作用 |
|---|---|
| `SELECT` | 选择返回字段 |
| `FROM` | 指定来源表 |
| `WHERE` | 筛选记录 |
| `AND` | 条件同时成立 |
| `ORDER BY` | 指定排序规则 |
| `ASC` | 升序，小到大；默认方向 |
| `DESC` | 降序，大到小 |
| `LIMIT n` | 最多返回 n 行 |

```sql
SELECT vmTypeId, core, memory
FROM vmType
WHERE machineId = 12 AND core <= 0.1
ORDER BY core DESC, vmTypeId ASC
LIMIT 3
```

查询硬件 12 中 CPU 份额不超过 0.1 的规格，按 CPU 降序；CPU 相同时按类型编号升序，最多取三条。

排序条件从左到右决定优先级。`LIMIT` 只限制数量；没有 `ORDER BY`，返回顺序不保证。

SQL 条件中 `=` 表示相等。时间窗口写作 `starttime >= 1 AND starttime < 2`，表示 `[1,2)`，避免与下一个窗口重复包含边界。

### 3. 两表关联：JOIN ON

`vm` 保存请求，`vmType` 保存类型在不同主机规格上的资源份额。

```sql
SELECT vm.vmId, vm.vmTypeId, vm.starttime,
       vmType.core, vmType.memory
FROM vm
JOIN vmType ON vm.vmTypeId = vmType.vmTypeId
WHERE vmType.machineId = 12
  AND vm.starttime >= 1 AND vm.starttime < 2
ORDER BY vm.starttime ASC, vm.vmId ASC
LIMIT 3
```

`ON` 按相同的类型编号配对；`表名.字段名` 标明字段来源。还需固定 `machineId`，因为同一类型可能支持多种硬件；缺少匹配规格时，这种内连接不返回该请求。

结果按 `SELECT` 的顺序排列：`row[0]` 请求编号、`row[1]` 类型、`row[2]` 时间、`row[3]` CPU、`row[4]` 内存。

`vmId` 是请求编号，`vmTypeId` 是虚拟机类型编号，`machineId` 是候选主机规格编号。`core`、`memory` 表示申请容量占相应单台主机的比例。

### 4. 参数占位符 ?

在已打开的连接上：

```python
sql = "SELECT vmTypeId, memory FROM vmType WHERE machineId = ? LIMIT ?"
parameters = (12, 5)
cursor = connection.execute(sql, parameters)
```

`parameters` 保存要传入的值；修改元组即可改变硬件与数量，不必改 SQL 结构。值的数量和顺序必须与 `?` 对应。

只有一个 `?` 时，使用单元素元组：

```python
sql = "SELECT vmTypeId, memory FROM vmType WHERE machineId = ?"
cursor = connection.execute(sql, (12,))
```

SQL 里没有参数占位符时，可以只传第一个参数：`cursor = connection.execute(sql)`。

`?` 不加引号，用于传值，不能代替表名或字段名。绑定参数不会改写原来的 `sql` 字符串，所以打印它时仍看到 `?`。

### 5. 分组统计：GROUP BY、COUNT、HAVING

```sql
SELECT machineId, COUNT(*)
FROM vmType
GROUP BY machineId
HAVING COUNT(*) >= 100
ORDER BY COUNT(*) DESC, machineId ASC
LIMIT 5
```

按硬件编号分组，统计每组规格记录数；保留至少 100 条的组，按数量降序取前五组。

- `GROUP BY`：相同字段值归为一组。
- `COUNT(*)`：统计行数。
- `WHERE`：筛原始记录；`HAVING`：筛分组结果。

这里数的是规格目录行数。`len(rows)` 数返回结果的行数，例如 `[(15,)]` 只有一行，其中的统计值是 15。

检查重复的“类型＋硬件”组合：

```sql
SELECT vmTypeId, machineId, COUNT(*)
FROM vmType
GROUP BY vmTypeId, machineId
HAVING COUNT(*) > 1
```

### 6. 查看表名和字段

```sql
SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name
```

```sql
PRAGMA table_info(vmType)
```

第一个查询列出表名；第二个查看字段结构，其结果中 `[1]` 是字段名、`[2]` 是声明类型。

[SQLite SELECT 文档](https://www.sqlite.org/lang_select.html) · [聚合函数](https://www.sqlite.org/lang_aggfunc.html) · [字段结构](https://www.sqlite.org/pragma.html#pragma_table_info)

## 四、Gurobi

### 1. 导入模块与许可证

```python
import gurobipy as gp          # 给模块起简称，后面用 gp 调用
from gurobipy import GRB       # 导入变量类型、优化方向和状态等常量
from packing_algorithms import first_fit  # 导入已有的 FF 算法
from solution_checker import check_solution  # 导入独立检查器

print(gp.gurobi.version())     # 查看 Gurobi 版本
```

`gurobipy` 是 Python 调用 Gurobi 的接口，需安装在当前解释器的环境中。本项目依赖已记在 `requirements.txt`：

```powershell
Set-Location "D:\PythonProjects\azure-vm-packing"
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

# 指定已有许可证文件，再运行模型
$env:GRB_LICENSE_FILE = "D:\gurobi1302\gurobi.lic"
& ".\.venv\Scripts\python.exe" ".\try_milp.py"
```

### 2. 创建模型、变量与参数

请求列表 `requests` 沿用 [try_milp.py](D:/PythonProjects/azure-vm-packing/try_milp.py) 中的人工例；每条为 `(vmId, vmTypeId, starttime, core, memory)`。

```python
initial_hosts = first_fit(requests)       # 先取得 FF 可行方案
valid, message = check_solution(requests, initial_hosts)
if not valid:
    raise ValueError(message)            # 上界方案不合法时停止

model = gp.Model("vm_packing")  # 新建模型，括号内是模型名称
model.Params.OutputFlag = 0     # 关闭求解过程日志
model.Params.TimeLimit = 30     # 求解时间上限：30 秒
model.Params.MIPGap = 0         # 将相对 gap 停止阈值设为 0
model.Params.FeasibilityTol = 1e-9  # 约束可行性容差
model.Params.IntFeasTol = 1e-9      # 整数变量容差

n = len(requests)              # 请求数
host_limit = len(initial_hosts)  # 已通过检查的 FF 方案提供候选主机数上界
x = model.addVars(n, host_limit, vtype=GRB.BINARY, name="x")
y = model.addVars(host_limit, vtype=GRB.BINARY, name="y")
```

`addVars` 创建变量并返回可按索引访问的变量集合。前面的数字指定各维长度；`vtype` 指定类型，`GRB.BINARY` 表示只能取 0 或 1；`name` 是变量名称前缀。

- `x[i, j] = 1`：第 `i` 条请求放到候选主机 `j`；共有 `n × host_limit` 个变量。
- `y[j] = 1`：启用主机 `j`；共有 `host_limit` 个变量。
- `i` 是请求列表位置，`j` 是候选主机编号，分别区别于 `vmId`、`machineId`。

此时创建的是待求值的变量；求解后才能读取具体取值。

### 3. 目标与约束

```python
model.setObjective(
    gp.quicksum(y[j] for j in range(host_limit)),  # 目标表达式：启用主机数
    GRB.MINIMIZE,                                # 优化方向：最小化
)

for i in range(n):
    model.addConstr(
        gp.quicksum(x[i, j] for j in range(host_limit)) == 1  # 每条请求恰好放一次
    )

for j in range(host_limit):
    model.addConstr(
        gp.quicksum(requests[i][3] * x[i, j] for i in range(n)) <= y[j]  # CPU 容量
    )
    model.addConstr(
        gp.quicksum(requests[i][4] * x[i, j] for i in range(n)) <= y[j]  # 内存容量
    )
    model.addConstr(y[j] <= gp.quicksum(x[i, j] for i in range(n)))  # 启用须非空
    for i in range(n):
        model.addConstr(x[i, j] <= y[j])  # 只有启用的主机才能接收请求
```

`quicksum(逐项表达式)` 构造求和表达式，例如三台主机时 `quicksum(y[j] for j in range(3))` 对应 `y[0] + y[1] + y[2]`。`addConstr(约束关系)` 把等式或不等式加入模型，并返回约束对象。

CPU 和内存分别以 1 为单机容量；`y[j]=0` 时不接收请求，`y[j]=1` 时允许使用容量 1。候选主机数限制搜索范围，不固定 FF 的分组。

### 4. 求解、读取结果与重建方案

```python
model.optimize()               # 按已建立的目标、约束和参数求解
print(model.Status)            # 求解状态
print(model.SolCount)          # 已保存的可行解数量
print(model.ObjBound)          # 最小化问题的全局下界

if model.SolCount > 0:         # 有可行解才读取解属性
    print(model.ObjVal)        # 当前最好可行解的目标值，即主机数
    print(model.MIPGap)        # 当前可行目标与下界之间的相对差距

    hosts = []
    for j in range(host_limit):
        host = []
        for i in range(n):
            if x[i, j].X > 0.5:  # .X 读取数值；将二元解判断为 1
                host.append(requests[i])
        if len(host) > 0:
            hosts.append(host)

    valid, message = check_solution(requests, hosts)  # 用独立检查器复核方案
    print(valid, message)
else:
    print("No feasible solution available.")

model.dispose()                # 释放模型占用的资源
```

在当前主机数最小化模型中，相对 gap 为 `|ObjVal - ObjBound| / |ObjVal|`；目标为 0 等特殊情况按 Gurobi 的定义处理。`Solutions` 是解的数量，`Objective` 才是主机数。数值容差设置不能代替方案检查。

### 5. 常见求解状态

| 状态 | 数值 | 含义 |
|---|---|---|
| `GRB.OPTIMAL` | 2 | 在求解容差内证明最优 |
| `GRB.INFEASIBLE` | 3 | 当前模型没有可行解 |
| `GRB.TIME_LIMIT` | 9 | 达到时间上限；是否已有解需看 `SolCount` |

`model.Status == GRB.OPTIMAL` 返回是否最优的布尔值。达到时限不等于证明最优；`SolCount=0` 表示尚无可用方案，不能记成用了 0 台主机。人工强制 `host_limit=1` 后不可行，仅说明该请求集装不进一台。

### 6. 封装后的结果与计时

项目封装接口为 `solve_milp(requests, upper_bound_hosts, time_limit=30)`：传入非空请求、已有可行分组和时限，返回结果字典。上界方案须通过检查，只用其主机数量限制候选数量，不固定原分组。

- `result["hosts"]`：求解器的主机分组；无可行解时为 `None`，不要对它调用 `len`。
- `result["objective"]`、`result["gap"]`：有可行解才填入数值，否则为 `None`；原贪心方案单独保留。
- `result["model_seconds"]`：从上界检查后开始，包含建模、求解、结果读取与分组重建，不含最终检查。
- `result["solve_seconds"]`：`model.Runtime`，仅求解器优化过程的耗时。

上述模型耗时也不含数据库读取或产生贪心上界的时间。做完整算法耗时比较时，要统一并说明这些范围。短时限下的 `bound=-inf` 表示尚未取得有限下界，不能据此说模型无界。

[Gurobi Python Model](https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html) · [模型结果属性](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/model.html) · [求解状态](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html)
