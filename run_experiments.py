import csv
import sys
from hashlib import sha256
from statistics import median
from time import perf_counter

import gurobipy as gp

from instance_io import ROOT, RESULT_DIR, load_instance, write_json
from packing_algorithms import (
    first_fit, best_fit, first_fit_decreasing,
    first_fit_decreasing_sum, best_fit_decreasing, dot_product,
)
from kellerer_kotov import kellerer_kotov
from milp_solver import solve_synthetic_milp, solve_aggregated_milp
from solution_checker import check_solution
from result_metrics import REFERENCE_FIELDS, attach_reference_metrics


TIME_LIMIT = 1200  # MIP累计优化预算：20分钟。
REPEATS = 3
RESULT_PREFIX = "pilot"  # 小规模联调输出集中到checks，不混入正式结果。

# 保存函数本身，在循环中调用。
METHODS = [
    ("FF", first_fit),
    ("BF", best_fit),
    ("FFD-max", first_fit_decreasing),
    ("FFD-sum", first_fit_decreasing_sum),
    ("BFD-max", best_fit_decreasing),
    ("DP", dot_product),
    ("KK2003", kellerer_kotov),  # 默认返回主机列表，与其他算法接口一致。
]

FIELDS = [
    "instance_id", "source", "n", "alpha", "seed", "method",
    "host_count", "valid", "seconds", "upper_bound_seconds",
    "mip_total_seconds", "solve_seconds", "lower_bound", "optimum",
    "ratio_to_opt", "gap_to_opt", "hit_optimum",
    "ratio_to_bound", "gap_to_bound", "proof_source", "stop_reason",
    "solver_status", "solver_gap",
] + REFERENCE_FIELDS


def measure_heuristic(algorithm, requests):
    times = []
    first_hosts = None
    first_seconds = None

    for repeat in range(REPEATS):
        started = perf_counter()
        hosts = algorithm(requests)
        elapsed = perf_counter() - started

        # 每次检查均在算法计时之外。
        valid, message = check_solution(requests, hosts)
        if not valid:
            raise ValueError(message)

        times.append(elapsed)
        if repeat == 0:
            first_hosts = hosts
            first_seconds = elapsed

    # 第一遍方案用于产生初解；三遍中位数用于比较算法耗时。
    return first_hosts, median(times), first_seconds


def evaluate_instance(instance):
    requests = instance["requests"]
    rows = []
    placements = {}
    best_hosts = None
    upper_bound_seconds = 0

    for name, algorithm in METHODS:
        hosts, seconds, first_seconds = measure_heuristic(
            algorithm, requests
        )
        upper_bound_seconds += first_seconds
        placements[name] = hosts

        rows.append({
            "method": name,
            "host_count": len(hosts),
            "valid": True,
            "seconds": seconds,
        })

        # 台数相同时保留先得到的方案。
        if best_hosts is None or len(hosts) < len(best_hosts):
            best_hosts = hosts

    # 两条MIP路径都接收当前最好有效初解。
    if instance["source"] == "synthetic":
        mip = solve_synthetic_milp(
            requests, best_hosts, time_limit=TIME_LIMIT
        )
    else:
        mip = solve_aggregated_milp(
            requests, best_hosts, time_limit=TIME_LIMIT
        )

    valid, message = check_solution(requests, mip["hosts"])
    if not valid:
        raise ValueError("MILP: " + message)

    placements["MILP"] = mip["hosts"]
    rows.append({
        "method": "MILP",
        "host_count": mip["objective"],
        "valid": True,
        "seconds": upper_bound_seconds + mip["total_seconds"],
        "upper_bound_seconds": upper_bound_seconds,
        "mip_total_seconds": mip["total_seconds"],
        "solve_seconds": mip["solve_seconds"],
        "proof_source": mip["proof_source"],
        "stop_reason": mip["stop_reason"],
        # 合成外层没有单一Gurobi状态，各次状态保存在trials。
        "solver_status": mip.get("solver_status"),
        "solver_gap": mip.get("solver_gap"),
    })

    bound = mip["bound"]
    optimum = mip["objective"] if mip["optimal"] else None

    for row in rows:
        # update将这些键值加入原字典；同名键会被覆盖。
        row.update({
            "instance_id": instance["instance_id"],
            "source": instance["source"],
            "n": len(requests),
            "alpha": instance.get("alpha"),
            "seed": instance.get("seed"),
            "lower_bound": bound,
            "optimum": optimum,
            "ratio_to_opt": None,
            "gap_to_opt": None,
            "hit_optimum": None,
            "ratio_to_bound": row["host_count"] / bound,
            "gap_to_bound": (row["host_count"] - bound) / bound,
        })

        # 只有证明最优，才计算与OPT有关的指标。
        if optimum is not None:
            row["ratio_to_opt"] = row["host_count"] / optimum
            row["gap_to_opt"] = (
                row["host_count"] - optimum
            ) / optimum
            row["hit_optimum"] = row["host_count"] == optimum

    attach_reference_metrics(rows)

    # 分组单独保存；其余模型字段保留，包括固定K的trials。
    details = {
        key: value for key, value in mip.items()
        if key != "hosts"
    }
    return rows, placements, details


def main():
    paths = [
        ROOT / "data/instances/real_v2/real_m12_w2_3_n200.json",
        ROOT / "data/instances/real_v2/real_m12_w1_2_n1000.json",
    ] + [
        ROOT / "data/instances/synthetic_alpha"
        / f"synthetic_v2_a{percent}_s0_n100.json"
        for percent in (10, 20, 30, 40, 50)
    ]

    all_rows = []
    all_placements = {}

    metadata = {
        "stage": "small_pipeline_pilot",
        "python": sys.version,
        "gurobi": gp.gurobi.version(),
        "time_limit": TIME_LIMIT,
        "timing_repetitions": REPEATS,
        "heuristic_timing":
            "median of calls; sorting included, checker excluded",
        "upper_bound_timing":
            "sum of first call times of all seven heuristics",
        "milp_timing":
            "upper_bound_seconds + mip_total_seconds",
        "instance_sha256": {},
        "mip_details": {},
        "methods": [name for name, algorithm in METHODS],
        "kk_variant": "seven steps with feasible within-bunch merge",
        # 本入口当前只运行七个小规模联调实例；扩展规模由独立效率脚本限时运行。
        "execution_scope": "small pilot; direct calls; benchmark has process supervision",
    }

    for path in paths:
        instance = load_instance(path)
        instance_id = instance["instance_id"]
        rows, placements, details = evaluate_instance(instance)

        all_rows.extend(rows)
        all_placements[instance_id] = placements
        metadata["instance_sha256"][instance_id] = sha256(
            path.read_bytes()
        ).hexdigest()
        metadata["mip_details"][instance_id] = details

        print(
            instance_id,
            "| Rows:", len(rows),
            "| Best:", details["objective"],
            "| LB:", details["bound"],
            "| Optimal:", details["optimal"],
        )

    output_dir = RESULT_DIR / "checks/pilot"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{RESULT_PREFIX}.csv"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    write_json(
        output_dir / f"{RESULT_PREFIX}_placements.json",
        all_placements,
    )
    write_json(
        output_dir / f"{RESULT_PREFIX}_metadata.json",
        metadata,
    )

    print(
        "Saved:", csv_path.name,
        "| Instances:", len(paths),
        "| Rows:", len(all_rows),
    )


if __name__ == "__main__":
    main()
