import _bootstrap  # 将项目根目录加入模块搜索路径。
from milp_solver import find_incompatible_clique, solve_fixed_k
from solution_checker import check_solution


def show_case(name, requests, k, time_limit=300):
    clique = find_incompatible_clique(requests)
    clique_ids = [requests[i][0] for i in clique]

    result = solve_fixed_k(requests, k, time_limit=time_limit)

    print("\nCase:", name)
    print("K:", k)
    print("Clique IDs:", clique_ids)
    print("Feasible:", result["feasible"])
    print("Reason:", result["reason"])
    print("Solver status:", result["solver_status"])
    print("Variables:", result["candidate_count"])
    print("Total seconds:", round(result["total_seconds"], 6))

    if result["hosts"] is not None:
        print("Host count:", len(result["hosts"]))
        print("Check:", check_solution(requests, result["hosts"]))

        for host in result["hosts"]:
            print([request[0] for request in host])


requests = [
    (0, 0, 0, 0.6, 0.2),
    (1, 1, 1, 0.5, 0.2),
    (2, 2, 2, 0.4, 0.7),
    (3, 3, 3, 0.1, 0.8),
    (4, 4, 4, 0.1, 0.1),
]

show_case("Original, K=1", requests, 1)
show_case("Original, K=2", requests, 2)

# 任意两条都可以同机，但每台最多装两条。
# 5条需要至少3台；请求ID特意不从0连续编号。
five_requests = [
    (10, 0, 0, 0.4, 0.3),
    (20, 0, 1, 0.4, 0.3),
    (30, 0, 2, 0.4, 0.3),
    (40, 0, 3, 0.4, 0.3),
    (50, 0, 4, 0.4, 0.3),
]

show_case("Five requests, K=2", five_requests, 2)
show_case("Five requests, K=3", five_requests, 3)
show_case("Zero time", five_requests, 3, time_limit=0)
