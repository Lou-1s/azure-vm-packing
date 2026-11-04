import _bootstrap  # 将项目根目录加入模块搜索路径。
from gurobipy import GRB
from kellerer_kotov import kellerer_kotov
from packing_algorithms import first_fit, first_fit_decreasing
from solution_checker import check_solution
from milp_solver import solve_milp


def make_requests(vectors):
    # 给每对资源需求分配不同ID，补齐项目统一的五字段格式。
    return [(i, -1, 0, cpu, memory) for i, (cpu, memory) in enumerate(vectors)]


def mirror(vectors):
    # 交换CPU和内存，用相同示例覆盖算法的对称分支。
    return [(memory, cpu) for cpu, memory in vectors]


five = [(.65,.3),(.4,.3),(.35,.6),(.2,.7),(.1,.1)]
type_one = [(.6,.45),(.1,.8)] + [(.05,.15)] * 4 + [(.45,.3)] * 5
paired = [(.85,.45),(.05,.95),(.6,.1),(.45,.6)] + [(.005,.05)] * 12 + [(.2,.06)] * 3
keep = [(.45,.3)] * 2 + [(.3,.45)] * 2
merge = [(.4,.05)] * 2 + [(.05,.4)] * 2
transfer = [(.3,.05)] * 3 + [(.04,.5)] * 2

cases = [
    ("Five requests", five),
    ("Type 1 with extra hosts", type_one),
    ("Type 2 with extra hosts", mirror(type_one)),
    ("Pair type 1 and type 2", paired),
    ("Small: keep two", keep),
    ("Small: merge one", merge),
    ("Small: transfer second", transfer),
    ("Small: transfer first", mirror(transfer)),
    ("Feasible group merge", [(.8,.1),(.1,.1),(.3,.2)]),
]

for name, vectors in cases:
    requests = make_requests(vectors)
    before = list(requests)
    hosts, info = kellerer_kotov(requests, return_info=True)
    valid, message = check_solution(requests, hosts)
    if not valid:
        raise ValueError(message)

    print("\nCase:", name)
    print("KK hosts:", len(hosts), "| Check:", valid, message)
    print("Input unchanged:", requests == before)
    print("Type counts:", info["type_counts"], "| Paired:", info["paired_groups"])
    print("Small actions:", info["small_actions"])

    ff_hosts = first_fit(requests)
    ffd_hosts = first_fit_decreasing(requests)
    # 用三种方案中主机最少的一份限制候选主机数量。
    initial = min([ff_hosts, ffd_hosts, hosts], key=len)  # key=len按主机数比较。
    result = solve_milp(requests, initial, time_limit=15)
    if result["status"] == GRB.OPTIMAL:
        optimum = int(round(result["objective"]))
        print("FF / FFD-max / KK / OPT:",len(ff_hosts),len(ffd_hosts),len(hosts),optimum)
        print("KK/OPT:", round(len(hosts) / optimum, 6))
        print("Within 2*OPT:", len(hosts) <= 2 * optimum)
        if len(hosts) > 2 * optimum:
            raise ValueError("KK exceeds 2*OPT on this instance")
    else:
        print("MILP status:", result["status"], "| Bound:", result["bound"])

print("\nEmpty:", kellerer_kotov([]))
