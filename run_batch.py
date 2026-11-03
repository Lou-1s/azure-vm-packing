import argparse
import csv
import json
import math
import platform
import sys
from hashlib import sha256
from pathlib import Path
from statistics import median

import gurobipy as gp
import benchmark_heuristics as benchmark
import milp_solver
import packing_algorithms
import kellerer_kotov
import instance_io
import run_experiments
import solution_checker
from instance_io import ROOT, RESULT_DIR, load_instance, write_json
from run_experiments import METHODS, FIELDS
from solution_checker import check_solution


BATCH_FIELDS = FIELDS + [
    "status", "required_repeats", "completed_repeats",
    "wall_seconds_total", "peak_private_mib",
]


def instance_paths(suite, real_dir):
    synthetic_dir = ROOT / "data/instances/synthetic_alpha"
    if suite == "smoke":
        # 两份真实实例和一份合成实例，先检查整个批量流程。
        return [real_dir / "real_m12_w1_2_n200.json",
                real_dir / "real_m12_w2_3_n1000.json",
                synthetic_dir / "synthetic_v2_a30_s0_n100.json"]
    if suite == "real":
        return [real_dir / f"real_m12_w{start}_{start+1}_n{n}.json"
                for start in (1, 2, 3, 6, 9, 12)
                for n in (200, 1000, 10000, 20000, 100000)]
    if suite == "synthetic-quality":
        return [synthetic_dir / f"synthetic_v2_a{a}_s{s}_n{n}.json"
                for n in (100, 200, 500, 1000)
                for s in range(10) for a in (10, 20, 30, 40, 50)]
    return [synthetic_dir / f"synthetic_v2_a{a}_s{s}_n{n}.json"
            for n in (5000, 10000, 20000, 100000)
            for s in (range(1) if n == 100000 else range(3))
            for a in (10, 20, 30, 40, 50)]


def resource_lower_bound(requests):
    # 与已有MIP一样，按1+1e-9单机容量计算资源总量下界。
    cpu = math.fsum(request[3] for request in requests)
    memory = math.fsum(request[4] for request in requests)
    return math.ceil(max(cpu, memory) / (1 + 1e-9))


def fallback_initial(requests):
    # 所有正式方法均未返回有效方案时，仅为MIP准备线性时间初解。
    # 不把这份后备方案记作某个正式算法的结果。
    hosts = []
    load = [0, 0]
    for request in requests:
        if not hosts or load[0] + request[3] > 1 + 1e-9 or load[1] + request[4] > 1 + 1e-9:
            hosts.append([])
            load = [0, 0]
        hosts[-1].append(request)
        load[0] += request[3]
        load[1] += request[4]
    return hosts


def evaluate_path(path, config):
    instance = load_instance(path)
    requests = instance["requests"]
    lookup = {request[0]: request for request in requests}
    repeats = 1 if len(requests) == 100000 else 3
    rows, placements, all_calls = [], {}, {}
    best_hosts = None
    initial_wall_seconds = 0

    for name, algorithm in METHODS:
        calls = []
        first_ids = None
        for repeat in range(repeats):
            call = benchmark.run_once(
                path, name, time_limit=config["heuristic_seconds"],
                memory_mib=config["memory_mib"], keep_placements=(repeat == 0),
            )
            # pop取出分组并删掉该键，避免在逐次元数据中再保存一份。
            ids = call.pop("placement_ids", None)
            call["repeat"] = repeat + 1
            calls.append(call)
            if repeat == 0:
                # 初值外部耗时包含首遍失败尝试，以及启动、读取和检查。
                initial_wall_seconds += call["wall_seconds"]
                if call["status"] == "completed":
                    first_ids = ids
            if call["status"] != "completed":
                break

        successful = [call for call in calls if call["status"] == "completed"]
        complete = len(successful) == repeats
        hosts = None
        if first_ids is not None:
            hosts = [[lookup[request_id] for request_id in host] for host in first_ids]
            valid, message = check_solution(requests, hosts)
            if not valid:
                raise ValueError(name + ": " + message)
            placements[name] = first_ids
            if best_hosts is None or len(hosts) < len(best_hosts):
                best_hosts = hosts
        rows.append({
            "method": name, "host_count": len(hosts) if hosts is not None else None,
            "valid": True if hosts is not None else None,
            "status": "completed" if complete else calls[-1]["status"],
            "seconds": median(call["seconds"] for call in successful) if complete else None,
            "required_repeats": repeats, "completed_repeats": len(successful),
            "wall_seconds_total": sum(call["wall_seconds"] for call in calls),
            "peak_private_mib": max(call["peak_private_mib"] for call in calls),
        })
        all_calls[name] = calls
        print(instance["instance_id"], "|", name, "|", rows[-1]["status"],
              "| Hosts:", rows[-1]["host_count"], flush=True)

    bound = resource_lower_bound(requests)
    mip_details = None
    use_mip = instance["source"] != "synthetic" or len(requests) <= 1000
    if use_mip:
        if best_hosts is None:
            best_hosts = fallback_initial(requests)
            initial_source = "fallback_next_fit"
        else:
            initial_source = "best_successful_first_call"
        # 所有新建模型继承默认环境的固定种子；模型内线程数仍按两条路径设置。
        gp.setParam("Seed", config["solver_seed"])
        solve = milp_solver.solve_synthetic_milp if instance["source"] == "synthetic" else milp_solver.solve_aggregated_milp
        mip = solve(requests, best_hosts, time_limit=config["mip_seconds"])
        valid, message = check_solution(requests, mip["hosts"])
        if not valid:
            raise ValueError("MILP: " + message)
        placements["MILP"] = [[request[0] for request in host] for host in mip["hosts"]]
        bound = mip["bound"]
        best_hosts = mip["hosts"]
        rows.append({
            "method": "MILP", "host_count": mip["objective"], "valid": True,
            "status": "optimal" if mip["optimal"] else mip["stop_reason"],
            "seconds": initial_wall_seconds + mip["total_seconds"],
            "upper_bound_seconds": initial_wall_seconds,
            "mip_total_seconds": mip["total_seconds"], "solve_seconds": mip["solve_seconds"],
            "proof_source": mip["proof_source"], "stop_reason": mip["stop_reason"],
            "solver_status": mip.get("solver_status"), "solver_gap": mip.get("solver_gap"),
        })
        mip_details = {key: value for key, value in mip.items() if key != "hosts"}
        mip_details["initial_source"] = initial_source

    # 无MIP的扩展实例也可以在有效方案达到独立下界时证明最优。
    optimum = len(best_hosts) if best_hosts is not None and len(best_hosts) == bound else None
    for row in rows:
        count = row["host_count"]
        row.update(instance_id=instance["instance_id"], source=instance["source"], n=instance["n"],
                   alpha=instance.get("alpha"), seed=instance.get("seed"), lower_bound=bound,
                   optimum=optimum, ratio_to_opt=None, gap_to_opt=None, hit_optimum=None,
                   ratio_to_bound=None, gap_to_bound=None)
        if count is not None:
            row["ratio_to_bound"] = count / bound
            row["gap_to_bound"] = (count - bound) / bound
            if optimum is not None:
                row.update(ratio_to_opt=count / optimum, gap_to_opt=(count - optimum) / optimum,
                           hit_optimum=count == optimum)
    return {"instance_id": instance["instance_id"], "rows": rows, "placement_format": "vmId_only",
            "placements": placements, "calls": all_calls, "mip_details": mip_details}


def save_atomic(path, data):
    # 先完整写临时文件，再改名；中途停止不会留下半份正式检查点。
    temporary = path.with_suffix(".tmp")
    write_json(temporary, data)
    temporary.replace(path)


def main(args):
    paths = instance_paths(args.suite, args.real_dir)
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Build instances first: " + missing[0])
    config = {"version": "batch_v1", "heuristic_seconds": args.heuristic_seconds,
              "memory_mib": 2048, "mip_seconds": args.mip_seconds, "solver_seed": 0,
              "repeats": "3 except n=100000: 1", "methods": [name for name, _ in METHODS],
              "upper_bound_timing": "sum of first-call wall times, including failed attempts",
              "solver_threads": {"synthetic": 2, "real": 1},
              "python": sys.version, "gurobi": list(gp.gurobi.version()),
              "platform": platform.platform(), "processor": platform.processor(),
              "snapshot_60s": "pending implementation; this stage uses the smoke suite"}
    # 将本批实际使用的源码指纹记入配置，避免修改代码后误续用旧检查点。
    sources = [Path(__file__)] + [Path(module.__file__) for module in (
        benchmark, milp_solver, packing_algorithms, kellerer_kotov,
        instance_io, run_experiments, solution_checker)]
    config["code_sha256"] = {path.name: sha256(path.read_bytes()).hexdigest() for path in sources}
    output_dir = args.output_dir or RESULT_DIR / ("batch_" + args.suite)
    all_rows = []
    for path in paths:
        instance_hash = sha256(path.read_bytes()).hexdigest()
        checkpoint = output_dir / "instances" / (path.stem + ".json")
        if checkpoint.exists():
            record = json.loads(checkpoint.read_text(encoding="utf-8"))
            if record["instance_sha256"] != instance_hash or record["config"] != config:
                raise ValueError("Checkpoint differs; choose a new --output-dir: " + str(checkpoint))
            print("Resumed:", path.stem, flush=True)
        else:
            record = evaluate_path(path, config)
            record.update(instance_sha256=instance_hash, config=config)
            save_atomic(checkpoint, record)
        all_rows.extend(record["rows"])
        # 每完成一份实例更新汇总，后续可从实例检查点继续。
        csv_temporary = output_dir / "summary.tmp"
        with csv_temporary.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=BATCH_FIELDS)
            writer.writeheader()
            writer.writerows(all_rows)
        csv_temporary.replace(output_dir / "summary.csv")
        print("Saved:", path.stem, "| Rows:", len(record["rows"]), flush=True)
    save_atomic(output_dir / "metadata.json", {
        "suite": args.suite, "python": sys.version, "platform": platform.platform(),
        "gurobi": gp.gurobi.version(), "config": config,
        "instance_ids": [path.stem for path in paths], "instances": len(paths), "rows": len(all_rows)})
    print("Saved:", output_dir / "summary.csv", "| Instances:", len(paths), "| Rows:", len(all_rows))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=("smoke", "real", "synthetic-quality", "synthetic-scale"), default="smoke")
    parser.add_argument("--real-dir", type=Path, default=ROOT / "data/instances/real_v2")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--heuristic-seconds", type=float, default=60)
    parser.add_argument("--mip-seconds", type=float, default=300)
    main(parser.parse_args())
