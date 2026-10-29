from packing_algorithms import (
    dot_product,
    first_fit_decreasing,
    first_fit_decreasing_sum,
)
from solution_checker import check_solution

requests = [
    (0, 0, 0, 0.75, 0.125),
    (1, 1, 1, 0.25, 0.5),
    (2, 2, 2, 0.125, 0.625),
]

results = [
    ("FFD-max", first_fit_decreasing(requests)),
    ("FFD-sum", first_fit_decreasing_sum(requests)),
    ("DP", dot_product(requests)),
]

for result in results:
    hosts = result[1]
    valid, message = check_solution(requests, hosts)

    if not valid:
        raise ValueError(result[0] + ": " + message)

    print(
        result[0], "Hosts:", len(hosts),
        "| Valid:", valid, "|", message,
    )

    for host in hosts:
        vm_ids = []
        for request in host:
            vm_ids.append(request[0])
        print(vm_ids)

# 查看算法运行后，原输入顺序是否保持。
input_ids = []
for request in requests:
    input_ids.append(request[0])

print("Input IDs:", input_ids)
print("Empty:", dot_product([]))