# Python 与 SQL 速查

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

cursor = connection.execute(sql, (12, 5))
rows = cursor.fetchall()
connection.close()

for row in rows:
    print(row)
```

- `uri=True`：按文件 URI 格式解析地址；`file:` 指向文件，`?` 后是连接选项。
- `mode=ro`：只读打开数据库。

**`execute` 接收什么？**

```python
cursor = connection.execute(sql, (12, 5))
```

这个调用有两个参数：

1. `sql`：要执行的 SQL 字符串。它写明查哪张表、返回哪些字段、怎样筛选和排序。
2. `(12, 5)`：一个参数元组，提供 SQL 中两个 `?` 对应的实际值。

元组里的 12 和 5 按 `?` 出现的先后顺序对应：

```sql
WHERE machineId = ?   -- 第一个值 12：选择硬件 12
LIMIT ?               -- 第二个值 5：最多取五条
```

因此，这次执行的查询含义等同于：

```sql
SELECT vmTypeId, core, memory
FROM vmType
WHERE machineId = 12
ORDER BY vmTypeId ASC
LIMIT 5
```

外层是两个参数：`sql` 与 `(12, 5)`；元组内部的两个数是一次查询所需的两个值。12 和 5 的用途由它们对应的 SQL 位置决定。如果写成 `(5, 12)`，含义就变成“硬件 5，最多十二条”。

**`execute` 返回什么？游标是什么？**

`execute` 将这条查询交给数据库执行，并返回一个游标对象，由左侧的 `cursor` 接收。可以把游标理解为“本次查询结果的读取器”：通过它取出记录，它会记录结果读到了哪里。

此时的 `cursor` 还不是我们熟悉的结果列表。要把记录取回成 Python 列表，接着写：

```python
rows = cursor.fetchall()
```

`fetchall()` 不需要再传入 `sql`，因为 `cursor` 已经对应刚才执行的那次查询。它把尚未取出的记录组织成一个列表并返回，由 `rows` 接收。第一次读取前还没取过记录，所以这里会得到本次查询的全部五条。

本例第一条结果是 `(0, 0.00275, 0.00146484375)`，依次对应 `SELECT` 中的类型编号、CPU、内存。取回后就可以使用列表的常见操作：

```python
print(len(rows))       # 5：取回五条记录
print(rows[0])         # 第一条记录
print(rows[0][1])      # 第一条记录的 CPU：0.00275
for row in rows:
    print(row)
```

**“剩余结果”是什么意思？**

游标读取后会前进，不会每次自动从头开始。在连接尚未关闭时，可以用下面这段代码观察：

```python
cursor = connection.execute(sql, (12, 5))  # 执行一次查询，获得新游标
rows = cursor.fetchall()                 # 取完五条记录
again = cursor.fetchall()                # 已经取完，返回 []

print(len(rows))                         # 5
print(again)                             # []
```

第二次取回为空，不会清空先前的 `rows`。如果需要重新查询，就再次调用 `execute`；如果查询本来没有匹配记录，第一次 `fetchall()` 就返回 `[]`。

`connection.close()` 放在查询和取结果之后，用于关闭连接。已经取回的 `rows` 仍可使用。`print(sql)` 只显示查询文本，不会执行查询。

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

这和 `connection.execute(sql, (12, 5))` 是同一种用法，只是把参数元组先保存到了变量 `parameters` 中。

需要根据需求改值时，可以写成：

```python
machine_id = 1
request_count = 10
parameters = (machine_id, request_count)
cursor = connection.execute(sql, parameters)
rows = cursor.fetchall()
```

现在查的是硬件 1，最多十条；SQL 结构不需要改变。参数数量必须与 `?` 的数量一致，顺序也要对应。

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
