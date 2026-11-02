# Python、SQL 与 Gurobi 速查

- [一、虚拟环境](#一虚拟环境)
- [二、常见文件格式](#二常见文件格式)
- [三、Python 基础](#三python-基础)
- [四、SQLite 与 SQL](#四sqlite-与-sql)
- [五、Gurobi](#五gurobi)

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

## 二、常见文件格式

文件名末尾的 `.py`、`.json` 等称为**扩展名**，用于提示文件的内容格式和常用处理方式。例如 `example.py` 中，`example` 是名称主体，`.py` 是扩展名。

| 扩展名 | 常见内容与用途 | 通常怎样查看或使用 |
|---|---|---|
| `.py` | Python 源代码；本项目的算法和实验程序 | VS Code 编辑，Python 解释器运行 |
| `.json` | 结构化文本，可保存键值、列表和多层嵌套数据；本项目保存实例、分组和运行信息 | VS Code 查看，Python 的 `json` 模块读写 |
| `.csv` | 行列形式的文本表格；本项目保存每种算法的汇总结果 | VS Code、Excel 或 WPS 查看，Python 的 `csv` 模块读写 |
| `.html` | 网页的内容与结构，如标题、段落、表格 | VS Code 编辑，浏览器解析并显示页面 |
| `.css`、`.js` | CSS 常用于网页样式；JavaScript 常用于网页交互逻辑 | VS Code 编辑，由浏览器等相应环境处理 |
| `.md` | Markdown 文本，用简单标记组织标题、列表和代码块 | VS Code 编辑或预览；常用于项目说明、复习资料 |
| `.txt` | 普通文本，可保存说明、记录或依赖清单 | 记事本、VS Code 等文本编辑器 |
| `.sqlite`、`.db` | 数据库文件常见后缀；`.db` 不一定是 SQLite | 本项目的 `.sqlite` 用 SQLite 工具或 Python 的 `sqlite3` 读取 |
| `.xlsx` | Excel 工作簿，可含多个工作表、公式和格式 | Excel、WPS 等表格软件 |
| `.zip` | 压缩包，可包含多个文件和文件夹 | 用解压工具展开后再使用内部文件 |
| `.ps1` | PowerShell 脚本；激活虚拟环境所用脚本属于此类 | PowerShell 执行，VS Code 可查看代码 |
| `.exe` | Windows 可执行程序，Python 解释器也属于此类 | 双击或从终端调用 |
| `.png`、`.jpg` | 图片，如图表或截图 | 图片查看器、浏览器等 |
| `.pdf` | 文档，通常保留固定的页面排版 | PDF 阅读器、浏览器等 |

例如，JSON 可以直接保存“每台主机上有哪些请求”这种多层结构：

```json
{
  "method": "FF",
  "hosts": [[10, 11], [12]]
}
```

CSV 适合保存每行列结构相同的结果：

```csv
method,host_count
FF,2
```

HTML 用标记表达网页内容；`<h1>` 表示一级标题，`<p>` 表示段落：

```html
<h1>实验结果</h1>
<p>FF 使用了 2 台主机。</p>
```

**改扩展名不会转换内容格式。** 把 `.csv` 改名为 `.xlsx`，文件内容仍是 CSV 文本。CSV 也不能保存 Excel 工作簿的多工作表、单元格样式等信息。

`.venv` 和 `.git` 是本项目中的**文件夹**：前者保存虚拟环境，后者保存 Git 版本信息。`.gitignore` 是一个文本配置**文件**，用于规定 Git 忽略哪些路径；它没有常规的扩展名。名称以点开头，并不等于某种文件格式。

## 三、Python 基础

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

```python
alpha = instance.get("alpha")  # 没有alpha这个键时返回None，不抛出KeyError
row.update({"lower_bound": 58, "optimum": None})  # 加入或覆盖这些键值
```

get只读取；update直接修改原字典，不需要把它的返回值重新赋给row。

函数定义中的 `time_limit=30` 指定默认值：调用时省略它就用 30，写 `time_limit=0` 则用 0。它与调用时的关键字参数写法相似，但默认值在定义函数时指定。

### 9. 测量耗时

```python
from time import perf_counter  # 引入适合测量短时间间隔的计时函数

started = perf_counter()       # 记录开始时的计时值
hosts = first_fit(requests)    # 实际运行要测量的代码
seconds = perf_counter() - started  # 两次计时值的差，单位为秒
```

`perf_counter()` 的单个数值不表示日期；两次调用之差才是经过的时间。计时起止位置决定包含哪些工作。[Python 文档](https://docs.python.org/zh-cn/3.12/library/time.html#time.perf_counter)

```python
from statistics import median  # Python 自带，无需安装

times = [0.04, 0.08, 0.05]
seconds = median(times)        # 排序后取中间值，得到 0.05
```

重复测量时，把每次耗时放进 `times`，再取中位数，减少某一次异常快慢的影响。此时 `seconds` 代表单次调用耗时的中位数，不是几次测量的时间总和。

### 10. while 循环与 pop

```python
remaining = [10, 20, 30]
while len(remaining) > 0:       # 每轮先判断；列表非空就继续
    selected = remaining.pop(0)  # 删除索引 0 的元素，并返回它
    print(selected, remaining)
```

`pop(位置)` 同时修改原列表并返回被删除的元素。删除位置 0 后，后续元素向前移动；位置与元素值不同，例如 `pop(0)` 取出的是第一项 10。

`while True:` 持续循环，直到执行其中的 `break`。嵌套循环中，`break` 只退出它所在的最内层循环。选择候选时先完整扫描，再删除选中项，避免遍历过程中索引发生移动。[Python 列表文档](https://docs.python.org/zh-cn/3.12/tutorial/datastructures.html)

### 11. 路径、文件与 JSON

```python
from pathlib import Path
import json

root = Path(__file__).resolve().parent  # 当前脚本所在目录
path = root / "results" / "demo.json"  # / 用于拼接路径
path.parent.mkdir(parents=True, exist_ok=True)  # 创建父目录，已存在则继续

with path.open("w", encoding="utf-8") as file:
    json.dump({"host_count": 2}, file, ensure_ascii=False, indent=2)

with path.open("r", encoding="utf-8") as file:
    result = json.load(file)
```

`with` 在代码块结束时自动关闭文件。`"w"` 创建或覆盖文件，`"r"` 读取现有文件；`encoding` 指定文字编码。

`json.dump(data, file)` 将第一项数据写进第二项文件；`json.load(file)` 从文件读回数据。`ensure_ascii=False` 让中文直接显示，`indent=2` 控制缩进；`allow_nan=False` 禁止写入NaN和无穷值。JSON中的数组读回为列表，需要时用 `tuple(row)` 恢复元组。

```python
n = 20
name = f"case_n{n}.json"        # f 字符串得到 case_n20.json
paths = sorted(root.glob("*.json"))  # 查找并排序匹配的文件路径
```

`path.name` 是文件名，`path.read_bytes()` 读取原始字节。`sha256(path.read_bytes()).hexdigest()` 可生成文件内容指纹，需要先 `from hashlib import sha256`。

[Path 文档](https://docs.python.org/zh-cn/3.12/library/pathlib.html) · [JSON 文档](https://docs.python.org/zh-cn/3.12/library/json.html)

### 12. 字典列表写入 CSV

```python
import csv

fields = ["method", "host_count"]  # 输出列名及顺序
rows = [{"method": "FF", "host_count": 2}]
path = root / "results" / "demo.csv"

with path.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()       # 写列名
    writer.writerows(rows)     # 把每个字典写成一行
```

`DictWriter` 第一个参数是已打开的文件，`fieldnames` 指定列名及顺序；每行按对应键名取值。`None` 或缺少的键写为空字段，不表示数值0。`newline=""` 交给CSV模块处理换行，`utf-8-sig` 便于Excel识别编码。CSV读回的单元格通常是字符串。[CSV 文档](https://docs.python.org/zh-cn/3.12/library/csv.html)

### 13. 把函数放入列表

```python
methods = [("FF", first_fit)]   # 不加括号，保存函数本身
for name, algorithm in methods:  # 分别接收元组中的名称和函数
    hosts = algorithm(requests)  # 在这里实际调用
```

若写成 `("FF", first_fit(requests))`，算法会在创建列表时执行；要测量调用耗时，应把计时放在实际调用的前后。

### 14. 固定随机种子

```python
import random

rng = random.Random(0)        # 用种子0创建独立生成器，放在取样循环之前
a = rng.randint(8, 48)        # 取得8到48之间的一个整数，包含两端
b = rng.randint(8, 48)        # 继续取得下一个数，并非每次都返回同一个值
```

在相同Python版本、代码和调用顺序下，使用同一种子可以重现同一串数据。种子不是样本数量；改种子通常会改变样本。固定种子用于复现实验，不意味着某一个种子代表全部情况。[random文档](https://docs.python.org/zh-cn/3.12/library/random.html)

```python
value_rng = random.Random("alpha_v2|n=100|seed=0|values")
direction_rng = random.Random("alpha_v2|n=100|seed=0|directions")
u = value_rng.random()       # 返回[0,1)内的浮点数
order = list(range(100))     # 编号0至99
direction_rng.shuffle(order) # 原地打乱；不要写成order = ...shuffle(order)
memory_ids = set(order[:20]) # 随机优先序的前20个编号
```

Random也接受字符串种子。项目把版本、n、seed、用途组成标签，分别控制取值与方向；标签中不放alpha，同一基础样本的五个alpha便可共享数值和方向优先序。只打乱用于选方向的order，输出请求仍按原ID排列。

采样循环中的continue跳过本轮剩余语句，进入下一轮；break则结束整个当前循环。sum(memory > cpu for ...)统计条件成立次数，因为True参与求和按1、False按0。

```python
if __name__ == "__main__":
    main()
```

直接运行这个.py文件时执行main()；被其他文件import时只提供定义，不自动执行main()。因此可以复用生成函数，而不重新生成整批文件。

### 15. enumerate、set与all

```python
for j, i in enumerate([3, 2]):
    print(j, i)          # 依次输出0 3、1 2：同时取得位置和元素

anchored = set([3, 2])   # 集合，用于快速判断元素是否存在
print(3 in anchored)     # True
anchored.add(4)          # 集合用add加入元素；重复加入不会产生第二份

print(all(x > 0 for x in [0.4, 0.7]))  # True：每一项都必须满足
```

all会逐项判断；遇到不满足的项就返回False，全部满足返回True。空集合中没有反例，所以all在空序列上返回True；贪心团因此可以加入第一个请求。

### 16. lambda与列表推导

```python
key = lambda i: (-requests[i][3], requests[i][0])
ordered = sorted(range(len(requests)), key=key)  # CPU降序，同分按ID
remaining = [i for i in range(len(requests)) if i not in anchored]
hosts = [[] for _ in range(3)]  # 创建三个不同的空列表
```

lambda写一个短函数，冒号前是参数，后面是返回值。列表推导把循环产生的值收集成列表，可用if筛选。此处i是列表位置；requests[i][0]才是请求ID。

### 17. 求和与向上取整

```python
import math
cpu_total = math.fsum(request[3] for request in requests)
resource_bound = math.ceil(cpu_total / (1 + 1e-9))
```

fsum对浮点数求和，减少累计舍入误差；ceil向上取整，例如ceil(2.1)=3。这里除以检查器采用的单机容量1+1e-9，再取整得到CPU资源下界；实际下界还要与内存、团下界取最大值。[math文档](https://docs.python.org/3.12/library/math.html)

### 18. 缓存主机负载与按ID查找

缓存是保存已经算出的结果，后续直接读取，数据变化时同步更新。

```python
hosts = [[request_a], [request_b]]
loads = [[request_a[3], request_a[4]],
         [request_b[3], request_b[4]]]

hosts[0].append(request_c)
loads[0][0] += request_c[3]  # CPU总量
loads[0][1] += request_c[4]  # 内存总量
```

hosts[j]与loads[j]描述同一台主机：前者保存请求，后者保存两项资源总量。loads[j][0]、[1]是缓存中的CPU、内存，与五字段请求的[3]、[4]分别对应。检查候选主机时直接读缓存；选中后更新该主机的列表和两项总量。

```python
originals = {request[0]: request for request in requests}
original = originals[vm_id]  # 用ID直接取完整记录
assigned_ids = set()
assigned_ids.add(vm_id)
```

vm_id in originals判断字典中是否有这个键；vm_id in assigned_ids判断集合中是否有这个元素。它们通常无需像列表查找那样逐项扫描。检查器仍逐条核对完整记录、放置次数和资源容量，不使用算法内部的负载缓存。

缓存FF/BF省去反复求和，仍需扫描候选主机，最坏时间仍可达到O(n²)。字典/集合检查器在正常哈希查找下随请求数近似线性增长。

### 19. 二分试探、负无穷与空列表

```python
middle = (left + right) // 2  # //返回向下取整的商，例如5 // 2为2
best_score = float("-inf")   # 负无穷，任何有限评分都比它大
used_hosts = [host for host in hosts if host]  # 只保留非空主机
```

空列表在条件中为False，因此while remaining表示还有未处理项时继续。函数返回None不会自动抛异常；调用处可以判断结果并选择后续操作。检查器返回(False,原因)时也只是返回结果，由调用处的raise决定是否抛错。

MB试放的None表示这次贪心未放完，并不证明给定主机数不可行。MIP固定K函数的feasible=False则表示已由预处理或求解器证明不可行。MB二分中的left是搜索位置，不能当作新的最优下界。

### 20. 列表参数与浅复制

```python
def append_item(items, item):
    items.append(item)  # 修改传入的列表

values = [1, 2]
before = list(values)   # 新建一份列表，内容先与values相同
append_item(values, 3)
print(values)           # [1, 2, 3]
print(before)           # [1, 2]
```

函数收到列表后，append等操作会作用于调用处传入的那个列表。KK子过程kk_place(host, load, request)因此能同时更新主机和负载；它没有return语句，默认返回None。

list(values)创建的是浅复制：外层列表独立，元素仍是原来的元素。请求记录使用不可修改的元组时，可用list(small)记录调用前的列表内容，再与调用后的small比较。

### 21. append与extend

```python
hosts = [["VM0"]]
bunch = [["VM1"], ["VM2"]]
hosts.extend(bunch)
print(hosts)  # [["VM0"], ["VM1"], ["VM2"]]
```

append把传入对象作为一个元素加入；extend把传入列表中的元素逐个加入。收集主机组时，每个元素是一台主机，因此用all_hosts.extend(bunch["hosts"])把组内各台主机加入总列表。

## 四、SQLite 与 SQL

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

## 五、Gurobi

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
| `GRB.SOLUTION_LIMIT` | 10 | 找到规定数量的解后结束；固定K找到方案即确认可行 |

`model.Status == GRB.OPTIMAL` 返回是否最优的布尔值。达到时限不等于证明最优；`SolCount=0` 表示尚无可用方案，不能记成用了 0 台主机。人工强制 `host_limit=1` 后不可行，仅说明该请求集装不进一台。

### 6. 封装后的结果与计时

项目封装接口为 `solve_milp(requests, upper_bound_hosts, time_limit=30)`：传入非空请求、已有可行分组和时限，返回结果字典。上界方案须通过检查，只用其主机数量限制候选数量，不固定原分组。

- `result["hosts"]`：求解器的主机分组；无可行解时为 `None`，不要对它调用 `len`。
- `result["objective"]`、`result["gap"]`：有可行解才填入数值，否则为 `None`；原贪心方案单独保留。
- `result["model_seconds"]`：从上界检查后开始，包含建模、求解、结果读取与分组重建，不含最终检查。
- `result["solve_seconds"]`：`model.Runtime`，仅求解器优化过程的耗时。

上述模型耗时也不含数据库读取或产生贪心上界的时间。做完整算法耗时比较时，要统一并说明这些范围。短时限下的 `bound=-inf` 表示尚未取得有限下界，不能据此说模型无界。

[Gurobi Python Model](https://docs.gurobi.com/projects/optimizer/en/current/reference/python/model.html) · [模型结果属性](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/model.html) · [求解状态](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html)


### 7. 固定K判定与稀疏变量

```python
pairs = [(0, 0), (0, 1), (4, 1)]
with gp.Model("fixed_k") as model:
    x = model.addVars(pairs, vtype=GRB.BINARY, name="x")
    model.setObjective(0, GRB.MINIMIZE)  # 只找可行分组
    model.Params.SolutionLimit = 1      # 找到一个可行解即可结束
    # 添加约束、optimize，并在with内部读取解
```

addVars第一个参数可以是索引对列表，此处只创建x[0,0]、x[0,1]、x[4,1]三个变量；没有x[4,0]。这用来省去无法放置的位置。with结束时释放模型；需要的状态、数值和分组先保存成普通Python数据。

固定K函数的feasible返回True表示找到有效方案，False表示已证明装不下，None表示尚未确定。solver_status保存Gurobi实际状态；预处理已经排除时没有调用求解器，保留None。目标常数0不表示用了0台，实际台数通过len(hosts)读取。

本轮solve_fixed_k(requests, host_limit, time_limit=300)处理一次给定K；后续外层搜索把300秒总优化预算分配到各次调用。返回prep_seconds、build_seconds、solve_seconds与total_seconds，最后一项包含结果恢复和独立检查。


### 8. 外层搜索与上下界

solve_synthetic_milp(requests, initial_hosts, time_limit=300)以初始有效分组确定上界U，以资源总量和团确定下界L。每次测试K=U-1：可行则更新U，不可行则L=K+1，尚未确定则保留现有结果。L=U时optimal=True。

remaining_time = time_limit - solve_seconds，其中solve_seconds累计各次Gurobi Runtime；因此每次调用取得剩余预算。total_seconds另外包含检查、团计算、建模和分组恢复。

返回objective是当前最好主机数、bound是有效下界、hosts是当前最好分组。即使时间预算为0，初始有效方案仍保留。proof_source说明证优方式：bound_match表示上下界相等，fixed_k_infeasible表示排除了少一台的可能；尚未证优时为None。

trials为字典列表，逐次保存K、可行性、状态和试探前后的上下界。gap_to_bound=(U-L)/L是相对下界的差距，与Gurobi原生MIPGap分开。固定K的solver_status=2说明该K可行，整个装箱问题的最优性由外层optimal及证据共同判断。

### 9. 类型聚合、整数变量与初始解

资源需求完全相同的请求可以按数量建模。例如同为(CPU=0.1,Memory=0.2)的100条请求是一组；保留原记录，求解后再恢复各自ID。这里的类型由资源二元组确定，不直接使用vmTypeId。

```python
groups = {}
for request in requests:
    demand = (request[3], request[4])
    if demand not in groups:
        groups[demand] = []           # 第一次遇到这个资源组合
    groups[demand].append(request)   # 保存该组的一条原始请求

types = sorted(groups)              # 排序字典的键，得到资源组合列表
counts = [len(groups[demand]) for demand in types]
type_index = {demand: t for t, demand in enumerate(types)}
```

types[t]是第t组的资源需求；counts[t]是该组的请求数量；type_index将资源组合反查为组编号。同一组内请求在当前模型中可以互换，因为约束和目标只使用CPU、内存需求。

```python
q = model.addVars(type_count, host_limit, vtype=GRB.INTEGER,
                  ub=upper_bounds, name="q")
q[0, 2].Start = 3
```

q[t,j]表示主机j接收第t类的数量，可以取0、1、2等整数，默认下界为0；ub按索引给出数量上限。若有T类、H台候选主机，就创建T×H个数量变量，另有H个主机启用变量y[j]。

.Start给求解器提供初始值；上述语句建议先在主机2放3条第0类请求，没有增加q[0,2]==3的约束。完整初始分组需要逐台统计各类数量，并分别赋给q[t,j].Start和y[j].Start。[Gurobi初始解说明](https://docs.gurobi.com/projects/optimizer/en/current/reference/attributes/variable.html#attr:Start)

```python
amount = int(round(q[t, j].X))
begin = positions[t]
end = begin + amount
host.extend(groups[demand][begin:end])
positions[t] = end
```

整数变量的.X仍是浮点数，round后转为Python整数。positions[t]记录第t组已经取走多少条；列表[begin:end]包含begin、不包含end；extend将这些记录逐条加入主机列表。每次推进位置，恢复后再由检查器核对ID、次数和容量。

参数Threads=1使用一个求解线程；Method=1为根节点松弛选择对偶单纯形；SoftMemLimit=2.0设置Gurobi约2GB软内存限额，停止后仍可读取已有解。[Gurobi参数说明](https://docs.gurobi.com/projects/optimizer/en/current/reference/parameters.html#parameter:SoftMemLimit)

### 10. 实验结果中的质量与计时

A是算法使用的主机数，OPT是已证明最优值，L是有效下界。

| 字段 | 计算方法 |
|---|---|
| ratio_to_opt | A/OPT，越接近1越好 |
| gap_to_opt | (A-OPT)/OPT |
| hit_optimum | A是否等于OPT；已知最优实例上的True比例为命中率 |
| ratio_to_bound | A/L，是相对下界的比值 |
| gap_to_bound | (A-L)/L |

只有证优后才填写optimum及前三个指标，否则保存None，在CSV中为空字段。ratio_to_bound在OPT未知时仍能计算，不能将下界冒充最优值。

启发式seconds为三次函数调用耗时的中位数。upper_bound_seconds累计各方法第一遍调用的实际耗时，对应产生初始上界；mip_total_seconds为MIP封装函数全程，solve_seconds仅为Gurobi优化时间。MILP行seconds为upper_bound_seconds+mip_total_seconds；其他重复调用只用于测量启发式时间，不再次计入初解生成。
