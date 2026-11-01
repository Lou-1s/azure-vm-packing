from instance_io import ROOT, load_instance
from packing_algorithms import first_fit
from milp_solver import solve_aggregated_milp
from solution_checker import check_solution


def show_case(name, requests, time_limit=300):
    initial_hosts = first_fit(requests)
    result = solve_aggregated_milp(
        requests, initial_hosts, time_limit=time_limit
    )

    print("\nCase:", name)
    print("Requests:", len(requests))
    print("Resource types:", result["type_count"])
    print("Count variables:", result["count_variables"])
    print("Binary variables:", result["binary_variables"])
    print("Initial hosts:", result["initial_host_count"])
    print("Best hosts:", result["objective"])
    print("Lower bound:", result["bound"])
    print("Optimal:", result["optimal"])
    print("Proof source:", result["proof_source"])
    print("Solver status:", result["solver_status"])
    print("Solve seconds:", result["solve_seconds"])
    print("Total seconds:", result["total_seconds"])
    print("Check:", check_solution(requests, result["hosts"]))


# 两类需求，各有三条请求。
toy = [
    (0, 0, 0, 0.6, 0.2),
    (1, 0, 1, 0.6, 0.2),
    (2, 0, 2, 0.6, 0.2),
    (3, 1, 3, 0.4, 0.7),
    (4, 1, 4, 0.4, 0.7),
    (5, 1, 5, 0.4, 0.7),
]

# 只读取已有实例，不重新提取或覆盖结果。
small = load_instance(
    ROOT / "data" / "instances" / "real_small"
    / "real_m12_w2_3_n40.json"
)["requests"]

large = load_instance(
    ROOT / "data" / "instances" / "real_large"
    / "real_m12_w1_2_n1000.json"
)["requests"]

show_case("Two resource types", toy)
show_case("Real 40", small)
show_case("Real 1000", large)
show_case("Zero budget", small, time_limit=0)