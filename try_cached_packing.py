import json
from time import perf_counter

from instance_io import ROOT, RESULT_DIR, load_instance
from packing_algorithms import (
    first_fit, best_fit, first_fit_decreasing,
    first_fit_decreasing_sum, best_fit_decreasing, dot_product,
)
from solution_checker import check_solution


METHODS = [
    ("FF", first_fit),
    ("BF", best_fit),
    ("FFD-max", first_fit_decreasing),
    ("FFD-sum", first_fit_decreasing_sum),
    ("BFD-max", best_fit_decreasing),
    ("DP", dot_product),
]

with (RESULT_DIR / "pilot_v2_placements.json").open(
    "r", encoding="utf-8"
) as file:
    saved = json.load(file)

compared = 0

for instance_id, saved_methods in saved.items():
    if instance_id.startswith("synthetic_v2_"):
        folder = "synthetic_alpha"
    elif instance_id.endswith("_n40"):
        folder = "real_small"
    else:
        folder = "real_large"

    path = ROOT / "data" / "instances" / folder / f"{instance_id}.json"
    requests = load_instance(path)["requests"]

    for name, algorithm in METHODS:
        hosts = algorithm(requests)

        # JSON中的记录是列表，恢复成与当前输出一致的元组。
        expected = [
            [tuple(request) for request in host]
            for host in saved_methods[name]
        ]

        # 比较完整分组，包括每台主机及其中请求的顺序。
        if hosts != expected:
            raise ValueError(
                instance_id + " / " + name + ": placement changed"
            )

        valid, message = check_solution(requests, hosts)
        if not valid:
            raise ValueError(message)

        compared += 1

    print(instance_id, "| Same placements: True | Valid: True")

print("Compared heuristic placements:", compared)

# 每条请求单独放一台，用于单独测量检查器。
large = load_instance(
    ROOT
    / "data/instances/synthetic_alpha/synthetic_v2_a50_s0_n100000.json"
)["requests"]

single_hosts = [[request] for request in large]

started = perf_counter()
result = check_solution(large, single_hosts)
seconds = perf_counter() - started

if result != (True, "OK"):
    raise ValueError(str(result))

print(
    "Large checker:", len(large),
    "|", result,
    "| Seconds:", seconds,
)