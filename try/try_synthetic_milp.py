import _bootstrap  # 将项目根目录加入模块搜索路径。
from packing_algorithms import first_fit
from milp_solver import solve_synthetic_milp
from solution_checker import check_solution


def show_search(name, requests, time_limit=300):
    # 本轮用FF起步，便于观察求解器如何改进已有方案。
    initial_hosts = first_fit(requests)

    result = solve_synthetic_milp(
        requests,
        initial_hosts,
        time_limit=time_limit,
    )

    print("\nCase:", name)
    print("Initial hosts:", result["initial_host_count"])
    print("Best hosts:", result["objective"])
    print("Lower bound:", result["bound"])
    print("Optimal:", result["optimal"])
    print("Proof source:", result["proof_source"])
    print("Stop reason:", result["stop_reason"])
    print("Gap to bound:", result["gap_to_bound"])
    print("Calls:", len(result["trials"]))
    print("Solve seconds:", round(result["solve_seconds"], 6))
    print("Total seconds:", round(result["total_seconds"], 6))
    print("Check:", check_solution(requests, result["hosts"]))

    for trial in result["trials"]:
        print(
            "K:", trial["k"],
            "| Feasible:", trial["feasible"],
            "| Bounds before:",
            trial["lower_before"], trial["upper_before"],
            "| Bounds after:",
            trial["lower_after"], trial["upper_after"],
        )

    for host in result["hosts"]:
        print([request[0] for request in host])


requests = [
    (0, 0, 0, 0.6, 0.2),
    (1, 1, 1, 0.5, 0.2),
    (2, 2, 2, 0.4, 0.7),
    (3, 3, 3, 0.1, 0.8),
    (4, 4, 4, 0.1, 0.1),
]

five_requests = [
    (10, 0, 0, 0.4, 0.3),
    (20, 0, 1, 0.4, 0.3),
    (30, 0, 2, 0.4, 0.3),
    (40, 0, 3, 0.4, 0.3),
    (50, 0, 4, 0.4, 0.3),
]

show_search("Improve initial solution", requests)
show_search("Prove initial solution optimal", five_requests)
show_search("Keep initial solution with zero budget",
            five_requests, time_limit=0)
