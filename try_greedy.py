# 从同一个模块导入四种算法；括号允许导入语句分成多行。
from packing_algorithms import (
    first_fit,
    best_fit,
    first_fit_decreasing,
    best_fit_decreasing,
)
from solution_checker import check_solution

# 所有算法接收相同请求；每条依次为 ID、类型、时间、CPU、内存。
# requests = [
#     (0, 0, 0, 0.6, 0.2),
#     (1, 1, 1, 0.5, 0.2),
#     (2, 2, 2, 0.4, 0.7),
#     (3, 3, 3, 0.1, 0.8),
#     (4, 4, 4, 0.1, 0.1),
# ]

requests = [
    (21, 21, 0, 0.75, 0.125),
    (20, 20, 1, 0.75, 0.125),
    (22, 22, 2, 0.125, 0.125),
]

# 这一组用于检查排序平局：同样大小的请求按 ID 排序。
# requests = [
#     (21, 21, 0, 0.75, 0.125),
#     (20, 20, 1, 0.75, 0.125),
#     (22, 22, 2, 0.125, 0.125),
# ]

# 列表中每个元组保存 (算法名称, 本次返回的主机分组)。
results = [
    ("FF", first_fit(requests)),
    ("BF", best_fit(requests)),
    ("FFD", first_fit_decreasing(requests)),
    ("BFD", best_fit_decreasing(requests)),
]

for result in results:
    # [1] 取得分组，再把它与原始请求交给独立检查器。
    hosts = result[1]
    valid, message = check_solution(requests, hosts)

    print(
        result[0], "Hosts:", len(hosts),
        "| Valid:", valid,
        "|", message,
    )

    for host in hosts:
        # 内层循环取出本台主机上每个请求的 ID，按主机逐行展示。
        vm_ids = []

        for request in host:
            vm_ids.append(request[0])

        print(vm_ids)
