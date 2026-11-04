import _bootstrap  # 将项目根目录加入模块搜索路径。
# 从项目模块中导入已有函数，避免在每个实验文件里重复定义。
from packing_algorithms import first_fit, resource_totals
from solution_checker import check_solution

# 请求格式为 (ID, 类型 ID, 开始时间, CPU 份额, 内存份额)。
requests = [
    (0, 0, 0, 0.6, 0.2),
    (1, 1, 1, 0.5, 0.2),
    # (2, 2, 2, 0.3, 0.7),
    (2, 2, 2, 0.4, 0.7),
    (3, 3, 3, 0.1, 0.8),
    (4, 4, 4, 0.1, 0.1),
]

# requests = [
#     (10, 10, 0, 0.2, 0.2),
#     (11, 11, 1, 0.9, 0.1),
#     (12, 12, 2, 0.1, 0.1),
# ]

# FF 返回“主机列表”，每个元素是该主机上的完整请求列表。
hosts = first_fit(requests)

print("Host count:", len(hosts))

for host in hosts:
    # 单独收集 ID 便于阅读；求和与检查仍使用完整请求记录。
    vm_ids = []

    for request in host:
        vm_ids.append(request[0])

    cpu_total, memory_total = resource_totals(host)

    # round(..., 6) 让显示更简洁，不改变已经生成的放置结果。
    print(
        "VM IDs:", vm_ids,
        "| CPU:", round(cpu_total, 6),
        "| Memory:", round(memory_total, 6),
    )

# 没有请求时应返回空主机列表。
print("Empty input:", first_fit([]))

# 每项为 (情形名称, 主机分组)；手算解应通过，其余错误情形应被拒绝。
# requests[0] 是列表中的第一条完整请求，不只是请求 ID。
checks = [
    ("FF", hosts),
    ("Manual", [
        [requests[0], requests[3]],
        [requests[1], requests[2], requests[4]],
    ]),
    ("Missing", [
        [requests[0], requests[2]],
        [requests[1], requests[3]],
    ]),
    ("Duplicate", [
        [requests[0], requests[2]],
        [requests[1], requests[3]],
        [requests[0]],
    ]),
    # CPU 超载案例保留其他请求各自单放，便于单独定位 CPU 容量检查。
    ("CPU Overload", [
        [requests[0], requests[1]],
        [requests[2]],
        [requests[3]],
        [requests[4]],
    ]),
    # 内存超载同理：只让指定的一台主机违反内存容量。
    ("Memory Overload", [
        [requests[2], requests[3]],
        [requests[0]],
        [requests[1]],
        [requests[4]],
    ]),
]

for case in checks:
    # case[0] 是名称，case[1] 是待检查的分组；输出检查器返回的二元组。
    print(case[0], check_solution(requests, case[1]))

print("Empty:", check_solution([], []))
