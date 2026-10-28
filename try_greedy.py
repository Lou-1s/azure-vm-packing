from packing_algorithms import (
    first_fit,
    best_fit,
    first_fit_decreasing,
    best_fit_decreasing,
)
from solution_checker import check_solution

requests = [
    (0, 0, 0, 0.6, 0.2),
    (1, 1, 1, 0.5, 0.2),
    (2, 2, 2, 0.4, 0.7),
    (3, 3, 3, 0.1, 0.8),
    (4, 4, 4, 0.1, 0.1),
]

# requests = [
#     (21, 21, 0, 0.75, 0.125),
#     (20, 20, 1, 0.75, 0.125),
#     (22, 22, 2, 0.125, 0.125),
# ]

results = [
    ("FF", first_fit(requests)),
    ("BF", best_fit(requests)),
    ("FFD", first_fit_decreasing(requests)),
    ("BFD", best_fit_decreasing(requests)),
]

for result in results:
    hosts = result[1]
    valid, message = check_solution(requests, hosts)

    print(
        result[0], "Hosts:", len(hosts),
        "| Valid:", valid,
        "|", message,
    )

    for host in hosts:
        vm_ids = []

        for request in host:
            vm_ids.append(request[0])

        print(vm_ids)