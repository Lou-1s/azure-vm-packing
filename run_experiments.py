import csv
import math
import sys
from hashlib import sha256       # 生成文件内容指纹。
from time import perf_counter
import gurobipy as gp
from gurobipy import GRB

from instance_io import INSTANCE_DIR, RESULT_DIR, load_instance, write_json
from packing_algorithms import (
    first_fit,
    best_fit,
    first_fit_decreasing,
    best_fit_decreasing,
    dot_product,
    first_fit_decreasing_sum,
)
from milp_solver import solve_milp
from solution_checker import check_solution

TIME_LIMIT = 30

# 保存函数本身，循环中再调用。
methods = [
    ("FF", first_fit),
    ("BF", best_fit),
    ("FFD-max", first_fit_decreasing),
    ("BFD", best_fit_decreasing),
    ("DP", dot_product),
    ("FFD-sum", first_fit_decreasing_sum),
]

# CSV 列名及排列顺序。
fields = [
    "instance_id", "n", "method", "host_count", "valid", "seconds",
    "prep_seconds", "model_seconds", "solve_seconds",
    "solver_status", "sol_count", "lower_bound", "solver_gap", "gap_to_opt",
]

# 只读取这个目录中硬件 12 的真实小实例。
paths = sorted(INSTANCE_DIR.glob("real_m12_*.json"))
if len(paths) != 9:
    raise ValueError("Expected 9 saved real-small instances")

all_rows = []
placements = {}
metadata = {
    "python": sys.version,
    "gurobi": gp.gurobi.version(),
    "time_limit": TIME_LIMIT,
    "timing_repetitions": 1,
    "heuristic_timing": "function call, including sorting; excludes checker",
    "milp_timing": "six heuristic calls plus model_seconds; excludes checker",
    "instance_sha256": {},
}

for path in paths:
    instance = load_instance(path)
    requests = instance["requests"]
    instance_id = instance["instance_id"]

    rows = []
    placements[instance_id] = {}

    # 记录文件内容指纹，便于确认结果对应哪份实例。
    metadata["instance_sha256"][instance_id] = sha256(
        path.read_bytes()
    ).hexdigest()

    prep_seconds = 0
    best_hosts = None

    # 每个元组中的两项分别交给 name 和 algorithm。
    for name, algorithm in methods:
        started = perf_counter()
        hosts = algorithm(requests)
        seconds = perf_counter() - started

        # 检查器放在计时之外。
        valid, message = check_solution(requests, hosts)
        if not valid:
            raise ValueError(name + ": " + message)

        prep_seconds += seconds

        if best_hosts is None:
            best_hosts = hosts
        elif len(hosts) < len(best_hosts):
            best_hosts = hosts

        rows.append({
            "instance_id": instance_id,
            "n": len(requests),
            "method": name,
            "host_count": len(hosts),
            "valid": valid,
            "seconds": seconds,
        })
        placements[instance_id][name] = hosts

    milp = solve_milp(requests, best_hosts, time_limit=TIME_LIMIT)

    host_count = None
    valid = None
    if milp["hosts"] is not None:
        valid, message = check_solution(requests, milp["hosts"])
        if not valid:
            raise ValueError("MILP: " + message)
        host_count = len(milp["hosts"])

    rows.append({
        "instance_id": instance_id,
        "n": len(requests),
        "method": "MILP",
        "host_count": host_count,
        "valid": valid,
        # MILP 的计算时间包含产生候选上界所需的六次算法调用。
        "seconds": prep_seconds + milp["model_seconds"],
        "prep_seconds": prep_seconds,
        "model_seconds": milp["model_seconds"],
        "solve_seconds": milp["solve_seconds"],
        "solver_status": milp["status"],
        "sol_count": milp["sol_count"],
        "solver_gap": milp["gap"],
    })
    placements[instance_id]["MILP"] = milp["hosts"]

    # 没有有限下界时留空。
    bound = None
    if math.isfinite(milp["bound"]):
        bound = milp["bound"]

    optimum = None
    if milp["status"] == GRB.OPTIMAL and milp["hosts"] is not None:
        optimum = len(milp["hosts"])

    for row in rows:
        row["lower_bound"] = bound
        row["gap_to_opt"] = None

        # 只有已证明最优，才计算相对最优值的差距。
        if optimum is not None and row["host_count"] is not None:
            row["gap_to_opt"] = (
                row["host_count"] - optimum
            ) / optimum

    # 把这一批的各个结果行加入总列表。
    all_rows += rows
    print(instance_id, "| Rows:", len(rows), "| Optimum:", optimum)

# 全部实例运行成功后，集中写入结果。
RESULT_DIR.mkdir(parents=True, exist_ok=True)
csv_path = RESULT_DIR / "small_real.csv"

with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(all_rows)

# 保存完整分组；不直接保存可能含 -inf 的整个求解结果字典。
write_json(RESULT_DIR / "small_real_placements.json", placements)
write_json(RESULT_DIR / "small_real_metadata.json", metadata)

print("Saved:", csv_path, "| Rows:", len(all_rows))