# from 模块名 import 函数名：复用同目录文件中已经定义好的函数。
from packing_algorithms import (
    first_fit,
    best_fit,
    first_fit_decreasing,
    best_fit_decreasing,
    dot_product,
    first_fit_decreasing_sum,
)
from solution_checker import check_solution
from milp_solver import solve_milp
import sqlite3

# 固定候选硬件规格，不表示这些请求在原系统中实际部署到了硬件 12。
machine_id = 12

# mode=ro 只读；uri=True 让 connect 识别地址里的文件选项。
database = "file:D:/PythonProjects/azure-vm-packing/data/raw/packing_trace_zone_a_v1.sqlite?mode=ro"
connection = sqlite3.connect(database, uri=True)

# 查询返回五项元组：(请求 ID, 类型 ID, 开始时间, CPU 份额, 内存份额)。
# JOIN 按类型关联；四个 ? 依次接收硬件、窗口起点、窗口终点、请求数量。
# 时间窗口左闭右开 [start, end)；各资源份额必须大于 0 且不超过 1。
# ASC 升序：先按开始时间，同一时间再按请求 ID；LIMIT 取排序后的前 N 条。
sql = """
SELECT vm.vmId, vm.vmTypeId, vm.starttime,
       vmType.core, vmType.memory
FROM vm
JOIN vmType ON vm.vmTypeId = vmType.vmTypeId
WHERE vmType.machineId = ?
  AND vm.starttime >= ?
  AND vm.starttime < ?
  AND vmType.core > 0 AND vmType.core <= 1
  AND vmType.memory > 0 AND vmType.memory <= 1
ORDER BY vm.starttime ASC, vm.vmId ASC
LIMIT ?
"""

def load_requests(connection, sql, parameters):
    # execute 的第一个参数是 SQL 字符串，第二个是按 ? 出现顺序提供的值元组。
    cursor = connection.execute(sql, parameters)
    # fetchall 取回全部剩余行；此函数把这些请求交回调用处。
    return cursor.fetchall()

def summarize_requests(requests):
    # 分别累计资源总量，以及 CPU 偏重、内存偏重、两者相等的请求数。
    cpu_total = 0
    memory_total = 0
    cpu_heavy = 0
    memory_heavy = 0
    equal_count = 0

    for request in requests:
        # 索引从 0 开始；[3]、[4] 对应查询结果的第四、第五列。
        cpu = request[3]
        memory = request[4]

        cpu_total = cpu_total + cpu
        memory_total = memory_total + memory

        if cpu > memory:
            cpu_heavy = cpu_heavy + 1

        if memory > cpu:
            memory_heavy = memory_heavy + 1

        if cpu == memory:
            equal_count = equal_count + 1

    return cpu_total, memory_total, cpu_heavy, memory_heavy, equal_count

# 每组为 (窗口起点, 窗口终点, 请求数量)；同一窗口的大批次包含小批次前缀。
# cases = [
#     (1, 2, 20),
#     (1, 2, 40),
#     (1, 2, 80),
#     (2, 3, 20),
#     (3,4,20),
# ]
cases = [
    (1, 2, 20),
    (1, 2, 40),
    (1, 2, 80),
    (2, 3, 20),
    (2, 3, 40),
    (2, 3, 80),
    (3, 4, 20),
    (3, 4, 40),
    (3, 4, 80),
]

print("Start | End | N | CPU | Memory | CPU>Memory | Memory>CPU | Equal")

for case in cases:
    # 例如第一组形成 (12, 1, 2, 20)，与 SQL 中四个 ? 一一对应。
    parameters = (
        machine_id,
        case[0],
        case[1],
        case[2],
    )

    requests = load_requests(connection, sql, parameters)

    # 防止实际只取到较少记录，却仍把它当成指定规模的实验。
    if len(requests) != case[2]:
        raise ValueError("Not enough compatible requests")

    totals = summarize_requests(requests)

    # round(..., 6) 只调整本次输出的小数位，不改 requests 中的原始数值。
    # sep=" | " 指定 print 各项之间的分隔文字。
    print(
        case[0],
        case[1],
        len(requests),
        round(totals[0], 6),
        round(totals[1], 6),
        totals[2],
        totals[3],
        totals[4],
        sep=" | ",
    )
    # # 每项保存 (算法名称, 该算法返回的主机分组)，供下面统一检查和输出。
    # results = [
    #     ("FF", first_fit(requests)),
    #     ("BF", best_fit(requests)),
    #     ("FFD", first_fit_decreasing(requests)),
    #     ("BFD", best_fit_decreasing(requests)),
    # ]

    # for result in results:
    #     hosts = result[1]
    #     # 检查器返回 (是否可行, 原因)，不能只凭主机数判断算法是否正确。
    #     valid, message = check_solution(requests, hosts)

    #     print(
    #         result[0], "Hosts:", len(hosts),
    #         "| Valid:", valid,
    #         "|", message,
    #     )
    # results = [
    #     ("FF", first_fit(requests)),
    #     ("BF", best_fit(requests)),
    #     ("FFD", first_fit_decreasing(requests)),
    #     ("BFD", best_fit_decreasing(requests)),
    # ]

    results = [
        ("FF", first_fit(requests)),
        ("BF", best_fit(requests)),
        ("FFD-max", first_fit_decreasing(requests)),
        ("BFD", best_fit_decreasing(requests)),
        ("DP", dot_product(requests)),
        ("FFD-sum", first_fit_decreasing_sum(requests)),
    ]

    # 先以 FF 为候选；各方案通过检查后，比较主机数。
    best_hosts = results[0][1]

    for result in results:
        hosts = result[1]
        valid, message = check_solution(requests, hosts)
        if not valid:
            raise ValueError(result[0] + ": " + message)

        # 保留使用主机最少的贪心方案；相同时保留原候选。
        if len(hosts) < len(best_hosts):
            best_hosts = hosts

        print(
            result[0], "Hosts:", len(hosts),
            "| Valid:", valid, "|", message,
        )

    # 以上启发式均检查完成后，再把最佳方案交给 MILP 提供上界。
    milp = solve_milp(requests, best_hosts)

    print(
        "MILP Status:", milp["status"],
        "| Solutions:", milp["sol_count"],
        "| Objective:", milp["objective"],
        "| Bound:", milp["bound"],
        "| Gap:", milp["gap"],
    )
    print(
        "ModelSeconds:", round(milp["model_seconds"], 6),
        "| SolveSeconds:", round(milp["solve_seconds"], 6),
    )

    if milp["hosts"] is None:
        print("MILP: No feasible solution available.")
    else:
        valid, message = check_solution(requests, milp["hosts"])
        print(
            "MILP Hosts:", len(milp["hosts"]),
            "| Valid:", valid, "|", message,
        )
    
# 单独核对 CPU 与内存份额相等的请求是否计入 equal_count。
# print(summarize_requests([(0, 0, 0, 0.2, 0.2)]))

# 结束所有查询后释放数据库连接。
connection.close()
