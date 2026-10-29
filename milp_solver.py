from time import perf_counter  # 用于测量耗时，单位为秒。
import gurobipy as gp          # 给模块起简称。
from gurobipy import GRB       # 变量类型、优化方向和状态等常量。
from solution_checker import check_solution


def solve_milp(requests, upper_bound_hosts, time_limit=30):
    # 输入：请求、已有可行分组、求解时限。
    # 输出：保存分组、状态、目标、界和耗时的字典。
    if len(requests) == 0:
        raise ValueError("Empty request batch")

    # 上界方案必须能合法容纳全部请求。
    valid, message = check_solution(requests, upper_bound_hosts)
    if not valid:
        raise ValueError("Invalid upper bound: " + message)

    # 从上界检查之后开始计时。
    started = perf_counter()
    n = len(requests)
    host_limit = len(upper_bound_hosts)

    model = gp.Model("vm_packing")
    model.Params.OutputFlag = 0
    model.Params.TimeLimit = time_limit  # 使用调用时指定的秒数。
    model.Params.MIPGap = 0
    model.Params.FeasibilityTol = 1e-9  # 约束可行性容差。
    model.Params.IntFeasTol = 1e-9      # 整数变量容差。

    # i 是请求位置，j 是候选主机编号；变量只能取 0 或 1。
    x = model.addVars(n, host_limit, vtype=GRB.BINARY, name="x")
    y = model.addVars(host_limit, vtype=GRB.BINARY, name="y")

    # 最小化启用主机数。
    model.setObjective(
        gp.quicksum(y[j] for j in range(host_limit)),
        GRB.MINIMIZE,
    )

    for i in range(n):
        # 每条请求恰好放一次。
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(host_limit)) == 1
        )

    for j in range(host_limit):
        # CPU 和内存分别满足容量约束。
        model.addConstr(
            gp.quicksum(requests[i][3] * x[i, j] for i in range(n)) <= y[j]
        )
        model.addConstr(
            gp.quicksum(requests[i][4] * x[i, j] for i in range(n)) <= y[j]
        )

        # 启用须非空，请求只能放到已启用的主机。
        model.addConstr(
            y[j] <= gp.quicksum(x[i, j] for i in range(n))
        )
        for i in range(n):
            model.addConstr(x[i, j] <= y[j])

    model.optimize()

    # 先保存不依赖可行解的结果。
    # 无可行解时，objective、gap、hosts 保持 None。
    result = {
        "status": model.Status,
        "sol_count": model.SolCount,
        "objective": None,
        "bound": model.ObjBound,
        "gap": None,
        "solve_seconds": model.Runtime,
        "hosts": None,
    }

    if model.SolCount > 0:
        hosts = []

        for j in range(host_limit):
            host = []
            for i in range(n):
                # .X 读取求解后的数值。
                if x[i, j].X > 0.5:
                    host.append(requests[i])

            if len(host) > 0:
                hosts.append(host)

        # 按键名更新字典中的值。
        result["objective"] = model.ObjVal
        result["gap"] = model.MIPGap
        result["hosts"] = hosts

    # 包含建模、求解、读取结果和重建分组。
    result["model_seconds"] = perf_counter() - started

    # 所需结果已保存成普通 Python 数据，可以释放模型。
    model.dispose()

    # 最终检查放在计时之外。
    if result["hosts"] is not None:
        valid, message = check_solution(requests, result["hosts"])
        if not valid:
            raise ValueError("Invalid MILP solution: " + message)

    return result