import _bootstrap  # 将项目根目录加入模块搜索路径。
import argparse
from pathlib import Path

from instance_io import ROOT, RESULT_DIR, load_instance, write_json
from packing_algorithms import first_fit, first_fit_decreasing
from milp_solver import solve_aggregated_milp, solve_synthetic_milp
from solution_checker import check_solution


def inspect_progress(name, requests, result):
    lookup = {request[0]: request for request in requests}
    progress = result["progress"]
    checkpoint, final = progress["checkpoint"], progress["final"]
    for state in (checkpoint, final):
        hosts = [[lookup[request_id] for request_id in host] for host in state["placement_ids"]]
        valid, message = check_solution(requests, hosts)
        if not valid:
            raise ValueError(message)
        assert len(hosts) == state["upper_bound"]
        assert state["lower_bound"] <= state["upper_bound"]
    assert checkpoint["observed_seconds"] <= checkpoint["effective_seconds"] + 1e-8
    assert final["upper_bound"] <= checkpoint["upper_bound"]
    assert final["lower_bound"] >= checkpoint["lower_bound"]
    assert final["upper_bound"] == result["objective"]
    assert final["lower_bound"] == result["bound"]

    print("\nCase:", name)
    print("Target seconds:", checkpoint["requested_seconds"])
    print("Effective / observed:", round(checkpoint["effective_seconds"], 6),
          round(checkpoint["observed_seconds"], 6))
    print("Checkpoint U / LB:", checkpoint["upper_bound"], checkpoint["lower_bound"])
    print("Checkpoint reason:", checkpoint["reason"])
    print("Final U / LB:", final["upper_bound"], final["lower_bound"])
    print("Callback events:", progress["callback_events"])
    print("Fixed-K trials:", len(result.get("trials", [])))
    print("Both placements valid: True")
    return {"case": name, "objective": result["objective"], "bound": result["bound"],
            "optimal": result["optimal"], "solve_seconds": result["solve_seconds"],
            "solver_parameters": result["solver_parameters"], "progress": progress}


def main(output_path):
    records = []
    real = load_instance(ROOT / "data/instances/real_v2/real_m12_w2_3_n200.json")["requests"][:40]
    records.append(inspect_progress(
        "Real 40: ends before 60 seconds", real,
        solve_aggregated_milp(real, first_fit(real), time_limit=5),
    ))

    synthetic = load_instance(ROOT / "data/instances/synthetic_alpha/synthetic_v2_a30_s0_n1000.json")["requests"]
    records.append(inspect_progress(
        "Synthetic 1000: shortened test cutoff", synthetic,
        # 测试时点缩短到0.01秒，正式批量运行仍使用60秒。
        solve_synthetic_milp(synthetic, first_fit_decreasing(synthetic),
                             time_limit=1, snapshot_seconds=0.01),
    ))

    five = [(i, -1, 0, .4, .3) for i in range(5)]
    records.append(inspect_progress(
        "Zero optimization budget", five,
        solve_synthetic_milp(five, first_fit(five), time_limit=0),
    ))
    records.append(inspect_progress(
        "Multiple fixed-K models share the clock", five,
        # 用5台单独放置作较松初解，外层会执行至少两次K判定。
        solve_synthetic_milp(five, [[request] for request in five],
                             time_limit=5, snapshot_seconds=0.0001),
    ))
    write_json(output_path, {"cases": records})
    print("\nSaved:", output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-path", type=Path, default=RESULT_DIR / "checks/try/mip_progress_check.json")
    main(parser.parse_args().output_path)
