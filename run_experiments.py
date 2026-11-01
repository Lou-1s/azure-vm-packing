import csv
import math
import sys
from hashlib import sha256       # 生成文件内容指纹。
from time import perf_counter
import gurobipy as gp
from gurobipy import GRB

from instance_io import ROOT, RESULT_DIR, load_instance, write_json
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
from statistics import median  # Python自带，用于计算中位数。

# # 保存函数本身，循环中再调用。
# methods = [
#     ("FF", first_fit),
#     ("BF", best_fit),
#     ("FFD-max", first_fit_decreasing),
#     ("BFD", best_fit_decreasing),
#     ("DP", dot_product),
#     ("FFD-sum", first_fit_decreasing_sum),
# ]

# DATASET = "real_large"
# TIME_LIMIT = 30
# 旧三组合成实验已清理；新alpha实验完成后再接入对应配置。
DATASET = "real_large"
TIME_LIMIT = 30

# 真实数据默认使用这个文件名模式。
file_pattern = "real_m12_*.json"

methods = [
    ("FF", first_fit),
    ("BF", best_fit),
    ("FFD-max", first_fit_decreasing),
    ("BFD", best_fit_decreasing),
    ("DP", dot_product),
]

if DATASET == "real_small":
    expected_instances = 9
    run_milp = True
    repeats = 1
    result_prefix = "small_real"
    methods.append(("FFD-sum", first_fit_decreasing_sum))
elif DATASET == "real_large":
    expected_instances = 6
    run_milp = False
    repeats = 3
    result_prefix = "large_real"
else:
    raise ValueError("Unknown dataset")

INSTANCE_DIR = ROOT / "data" / "instances" / DATASET

# CSV 列名及排列顺序。
fields = [
    "instance_id", "n", "method", "host_count", "valid", "seconds",
    "prep_seconds", "model_seconds", "solve_seconds",
    "solver_status", "sol_count", "lower_bound", "solver_gap", "gap_to_opt",
]

# # 只读取这个目录中硬件 12 的真实小实例。
# paths = sorted(INSTANCE_DIR.glob("real_m12_*.json"))
# if len(paths) != 9:
#     raise ValueError("Expected 9 saved real-small instances")
# paths = sorted(INSTANCE_DIR.glob("real_m12_*.json"))
paths = sorted(INSTANCE_DIR.glob(file_pattern))
if len(paths) != expected_instances:
    raise ValueError("Saved instance count mismatch")

# rows	当前实例的七条汇总结果
# all_rows	九个实例的全部 63 条汇总结果
# placements	每个实例、每种方法的完整主机分组
# metadata	软件版本、时限、计时规则和实例指纹
all_rows = []
placements = {}
# metadata = {
#     "python": sys.version,
#     "gurobi": gp.gurobi.version(),
#     "time_limit": TIME_LIMIT,
#     "timing_repetitions": 1,
#     "heuristic_timing": "function call, including sorting; excludes checker",
#     "milp_timing": "six heuristic calls plus model_seconds; excludes checker",
#     "instance_sha256": {},
# }
metadata = {
    "python": sys.version,
    "gurobi": gp.gurobi.version(),
    "time_limit": TIME_LIMIT,
    "dataset": DATASET,
    "run_milp": run_milp,
    "timing_repetitions": repeats,
    "heuristic_timing":
        "median of timed function calls, including sorting; excludes checker",
    "milp_timing":
        "sum of upper-bound heuristic call times plus model_seconds; excludes checker",
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
        # started = perf_counter()
        # hosts = algorithm(requests)
        # seconds = perf_counter() - started

        # # 检查器放在计时之外。
        # valid, message = check_solution(requests, hosts)
        # if not valid:
        #     raise ValueError(name + ": " + message)
        times = []

        # 每次调用独立计时；检查器仍在计时之外。
        for repeat in range(repeats):
            started = perf_counter()
            hosts = algorithm(requests)
            elapsed = perf_counter() - started

            valid, message = check_solution(requests, hosts)
            if not valid:
                raise ValueError(name + ": " + message)

            times.append(elapsed)

        seconds = median(times)

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

    # milp = solve_milp(requests, best_hosts, time_limit=TIME_LIMIT)

    # host_count = None
    # valid = None
    # if milp["hosts"] is not None:
    #     valid, message = check_solution(requests, milp["hosts"])
    #     if not valid:
    #         raise ValueError("MILP: " + message)
    #     host_count = len(milp["hosts"])

    # rows.append({
    #     "instance_id": instance_id,
    #     "n": len(requests),
    #     "method": "MILP",
    #     "host_count": host_count,
    #     "valid": valid,
    #     # MILP 的计算时间包含产生候选上界所需的六次算法调用。
    #     "seconds": prep_seconds + milp["model_seconds"],
    #     "prep_seconds": prep_seconds,
    #     "model_seconds": milp["model_seconds"],
    #     "solve_seconds": milp["solve_seconds"],
    #     "solver_status": milp["status"],
    #     "sol_count": milp["sol_count"],
    #     "solver_gap": milp["gap"],
    # })
    # placements[instance_id]["MILP"] = milp["hosts"]

    # # 没有有限下界时留空。
    # bound = None
    # if math.isfinite(milp["bound"]):
    #     bound = milp["bound"]

    # optimum = None
    # if milp["status"] == GRB.OPTIMAL and milp["hosts"] is not None:
    #     optimum = len(milp["hosts"])

    # 未求最优值时保持 None。
    bound = None
    optimum = None

    if run_milp:
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
            "seconds": prep_seconds + milp["model_seconds"],
            "prep_seconds": prep_seconds,
            "model_seconds": milp["model_seconds"],
            "solve_seconds": milp["solve_seconds"],
            "solver_status": milp["status"],
            "sol_count": milp["sol_count"],
            "solver_gap": milp["gap"],
        })
        placements[instance_id]["MILP"] = milp["hosts"]

        if math.isfinite(milp["bound"]):
            bound = milp["bound"]

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
# csv_path = RESULT_DIR / "small_real.csv"
csv_path = RESULT_DIR / f"{result_prefix}.csv"

# 缺少的键和 None 会写为空字段
with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(all_rows)

# # 保存完整分组；不直接保存可能含 -inf 的整个求解结果字典。
# write_json(RESULT_DIR / "small_real_placements.json", placements)
# write_json(RESULT_DIR / "small_real_metadata.json", metadata)
write_json(
    RESULT_DIR / f"{result_prefix}_placements.json",
    placements,
)
write_json(
    RESULT_DIR / f"{result_prefix}_metadata.json",
    metadata,
)

print("Saved:", csv_path, "| Rows:", len(all_rows))
# CSV 适合查看平整的行列表格，JSON 适合保存“实例 → 方法 → 主机 → 请求”这种多层结构
