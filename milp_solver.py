from time import perf_counter  # 用于测量耗时，单位为秒。
import gurobipy as gp          # 给模块起简称。
from gurobipy import GRB       # 变量类型、优化方向和状态等常量。
from solution_checker import check_solution
import math  # Python自带的数学工具，无需安装。


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


def incompatible(left, right):
    # 任意一种资源相加超过容量，两条请求就不能同机。
    return (
        left[3] + right[3] > 1 + 1e-9
        or left[4] + right[4] > 1 + 1e-9
    )


def find_incompatible_clique(requests):
    # i表示列表位置；requests[i][0]才是请求ID。
    keys = [
        lambda i: (-max(requests[i][3], requests[i][4]), requests[i][0]),
        lambda i: (-(requests[i][3] + requests[i][4]), requests[i][0]),
        lambda i: (-requests[i][3], -requests[i][4], requests[i][0]),
        lambda i: (-requests[i][4], -requests[i][3], requests[i][0]),
    ]

    best_clique = []

    for key in keys:
        clique = []

        for i in sorted(range(len(requests)), key=key):
            # 新请求必须与团中的每一条请求都不相容。
            if all(incompatible(requests[i], requests[h]) for h in clique):
                clique.append(i)

        if len(clique) > len(best_clique):
            best_clique = clique

    # 返回列表位置，不是请求ID。
    return best_clique


def solve_fixed_k(requests, host_limit, time_limit=300):
    # 输入已核验的五字段请求，判断能否装入至多host_limit台。
    started = perf_counter()
    clique = find_incompatible_clique(requests)

    result = {
        "feasible": None,
        "hosts": None,
        "solver_status": None,
        "clique_size": len(clique),
        "candidate_count": 0,
        "reason": "not_finished",
        "prep_seconds": 0,
        "build_seconds": 0,
        "solve_seconds": 0,
        "total_seconds": 0,
    }

    if len(clique) > host_limit:
        # 团请求各需一台，已经超过K，无需调用求解器。
        result["feasible"] = False
        result["reason"] = "clique_bound"
        result["prep_seconds"] = perf_counter() - started
        result["total_seconds"] = result["prep_seconds"]
        return result

    # 团中的请求固定到前几台主机，并扣除容量。
    residual_cpu = [1.0] * host_limit
    residual_memory = [1.0] * host_limit

    # j是主机编号，i是请求列表中的位置。
    for j, i in enumerate(clique):
        residual_cpu[j] -= requests[i][3]
        residual_memory[j] -= requests[i][4]

    # set转成集合，用于判断哪些请求已经固定。
    anchored = set(clique)
    remaining = [
        i for i in range(len(requests))
        if i not in anchored
    ]

    pairs = []
    choices = {}  # 请求位置i -> 可选主机编号列表。
    by_host = [[] for _ in range(host_limit)]  #主机j可以接收哪些剩余请求

    for i in remaining:
        choices[i] = []

        for j in range(host_limit):
            fits = (
                requests[i][3] <= residual_cpu[j] + 1e-9
                and requests[i][4] <= residual_memory[j] + 1e-9
            )

            if fits:
                pairs.append((i, j))
                choices[i].append(j)
                by_host[j].append(i)

        if not choices[i]:
            result["feasible"] = False
            result["reason"] = "no_candidate_host"
            result["candidate_count"] = len(pairs)
            result["prep_seconds"] = perf_counter() - started
            result["total_seconds"] = result["prep_seconds"]
            return result

    result["candidate_count"] = len(pairs)
    result["prep_seconds"] = perf_counter() - started
    build_started = perf_counter()

    # with结束时释放模型；解要在with内部取出。
    with gp.Model("fixed_k") as model:
        model.Params.OutputFlag = 0
        model.Params.Threads = 2
        model.Params.TimeLimit = time_limit
        model.Params.SolutionLimit = 1  # 找到一个可行解即可结束。
        model.Params.MIPFocus = 1 # 优先寻找可行解。
        model.Params.FeasibilityTol = 1e-9
        model.Params.IntFeasTol = 1e-9

        # 仅为pairs中的位置创建变量，不创建完整n*K矩阵。
        x = model.addVars(pairs, vtype=GRB.BINARY, name="x")

        for i in remaining:
            model.addConstr(
                gp.quicksum(x[i, j] for j in choices[i]) == 1
            )

        for j in range(host_limit):
            model.addConstr(
                gp.quicksum(
                    requests[i][3] * x[i, j]
                    for i in by_host[j]
                ) <= residual_cpu[j]
            )

            model.addConstr(
                gp.quicksum(
                    requests[i][4] * x[i, j]
                    for i in by_host[j]
                ) <= residual_memory[j]
            )

        # 仅对未锚定主机按CPU总负载降序排列，内存不要求同序。
        for j in range(len(clique), host_limit - 1):
            model.addConstr(
                gp.quicksum(
                    requests[i][3] * x[i, j]
                    for i in by_host[j]
                )
                >= gp.quicksum(
                    requests[i][3] * x[i, j + 1]
                    for i in by_host[j + 1]
                )
            )

        # K已经固定，只需找到可行分配。
        model.setObjective(0, GRB.MINIMIZE)
        model.update()
        result["build_seconds"] = perf_counter() - build_started

        model.optimize()

        result["solver_status"] = model.Status
        result["solve_seconds"] = model.Runtime

        if model.SolCount > 0:
            hosts = [[] for _ in range(host_limit)]

            # 先放回已经固定的团请求。
            for j, i in enumerate(clique):
                hosts[j].append(requests[i])

            # 再放入求解器分配的剩余请求。
            for i, j in pairs:
                if x[i, j].X > 0.5:
                    hosts[j].append(requests[i])

            result["hosts"] = [host for host in hosts if host]  #保留非空主机
            result["feasible"] = True
            result["reason"] = "solution_found"

        elif model.Status == GRB.INFEASIBLE:
            result["feasible"] = False
            result["reason"] = "solver_infeasible"

        else:
            # 没有方案，也没有不可行证明，保留None。
            result["reason"] = "not_proven"

    # 恢复分组后使用独立检查器复核。
    if result["hosts"] is not None:
        valid, message = check_solution(requests, result["hosts"])

        if not valid:
            raise ValueError("Invalid fixed-K solution: " + message)

    result["total_seconds"] = perf_counter() - started
    return result


def solve_synthetic_milp(requests, initial_hosts, time_limit=300):
    # 已有方案提供上界；整个函数始终保留一个有效方案。
    started = perf_counter()

    valid, message = check_solution(requests, initial_hosts)
    if not valid:
        raise ValueError("Invalid initial solution: " + message)

    best_hosts = initial_hosts
    initial_count = len(initial_hosts)
    upper = initial_count

    cpu_total = math.fsum(request[3] for request in requests)
    memory_total = math.fsum(request[4] for request in requests)

    # 沿用检查器的单机容量容差，再向上取整。
    resource_bound = math.ceil(
        max(cpu_total, memory_total) / (1 + 1e-9)
    )

    clique_bound = len(find_incompatible_clique(requests))
    lower = max(resource_bound, clique_bound)

    if lower > upper:
        raise ValueError("Lower bound exceeds valid upper bound")

    solve_seconds = 0.0
    trials = []
    proof_source = None
    stop_reason = "not_started"

    while lower < upper:
        # 扣除前面各次Gurobi优化已消耗的时间。
        remaining_time = time_limit - solve_seconds

        if remaining_time <= 0:
            stop_reason = "time_budget"
            break

        k = upper - 1
        lower_before = lower
        upper_before = upper

        trial = solve_fixed_k(
            requests,
            k,
            time_limit=remaining_time,
        )

        solve_seconds += trial["solve_seconds"]

        if trial["feasible"] is True:
            # 找到了更少主机的方案，替换当前最好方案。
            best_hosts = trial["hosts"]
            upper = len(best_hosts)

        elif trial["feasible"] is False:
            # K不可行，最优值至少为K+1。
            lower = max(lower, k + 1)
            proof_source = "fixed_k_infeasible"

        else:
            # 未确定时保留原有方案和上下界。
            stop_reason = "not_proven"

        # 只保存本次试探摘要，完整最好分组放在best_hosts中。
        trials.append({
            "k": k,
            "feasible": trial["feasible"],
            "solver_status": trial["solver_status"],
            "reason": trial["reason"],
            "candidate_count": trial["candidate_count"],
            "solve_seconds": trial["solve_seconds"],
            "total_seconds": trial["total_seconds"],
            "lower_before": lower_before,
            "upper_before": upper_before,
            "lower_after": lower,
            "upper_after": upper,
        })

        if trial["feasible"] is None:
            break

    optimal = lower == upper

    if optimal:
        stop_reason = "optimal"

        if proof_source is None:
            proof_source = "bound_match"
   
    #二次校验
    valid, message = check_solution(requests, best_hosts)
    if not valid:
        raise ValueError("Invalid final solution: " + message)

    gap_to_bound = 0 if lower == 0 else (upper - lower) / lower

    return {
        "hosts": best_hosts,
        "initial_host_count": initial_count,
        "objective": upper,
        "bound": lower,
        "optimal": optimal,
        "proof_source": proof_source,
        "stop_reason": stop_reason,
        "gap_to_bound": gap_to_bound,
        "solve_seconds": solve_seconds,
        "total_seconds": perf_counter() - started,
        "trials": trials,
    }


def solve_aggregated_milp(requests, initial_hosts, time_limit=300):
    started = perf_counter()

    valid, message = check_solution(requests, initial_hosts)
    if not valid:
        raise ValueError("Invalid initial solution: " + message)
    if not requests:
        raise ValueError("Empty request batch")

    # 一、按完全相同的CPU、内存需求分组，保存原始请求。
    groups = {}
    for request in requests:
        demand = (request[3], request[4])
        if demand not in groups:
            groups[demand] = []
        groups[demand].append(request)

    types = sorted(groups)  # 排序字典的键，得到资源组合列表。
    type_count = len(types)
    counts = [len(groups[demand]) for demand in types]

    # 通过资源组合，反查对应的类型编号。
    type_index = {demand: t for t, demand in enumerate(types)}
    host_limit = len(initial_hosts)

    # 每种类型在单台主机上的数量上限。
    limits = []
    for t, (cpu, memory) in enumerate(types):
        limits.append(min(
            counts[t],
            math.floor((1 + 1e-9) / cpu),
            math.floor((1 + 1e-9) / memory),
        ))

    # 由两种资源总量取得主机数下界。
    resource_bound = math.ceil(max(
        math.fsum(request[3] for request in requests),
        math.fsum(request[4] for request in requests),
    ) / (1 + 1e-9))

    # 先保留有效初解，求解停止时仍有可用方案。
    result = {
        "hosts": initial_hosts,
        "initial_host_count": host_limit,
        "objective": host_limit,
        "bound": resource_bound,
        "solver_status": None,
        "solver_bound": None,
        "solver_gap": None,
        "type_count": type_count,
        "count_variables": type_count * host_limit,
        "binary_variables": host_limit,
        "prep_seconds": perf_counter() - started,
    }
    build_started = perf_counter()

    with gp.Model("type_count_packing") as model:
        model.Params.OutputFlag = 0
        model.Params.Threads = 1
        model.Params.Method = 1       # 根节点松弛使用对偶单纯形。
        model.Params.TimeLimit = time_limit
        model.Params.MIPGap = 0
        model.Params.SoftMemLimit = 2.0  # Gurobi约2GB软内存限额。
        model.Params.FeasibilityTol = 1e-9
        model.Params.IntFeasTol = 1e-9

        # 二、创建数量整数变量q和主机启用变量y。
        upper_bounds = {
            (t, j): limits[t]
            for t in range(type_count)
            for j in range(host_limit)
        }
        q = model.addVars(
            type_count, host_limit,
            vtype=GRB.INTEGER,       # 可取0、1、2等整数。
            ub=upper_bounds,         # 每个变量的数量上限。
            name="q",
        )
        y = model.addVars(host_limit, vtype=GRB.BINARY, name="y")
        model.setObjective(gp.quicksum(y.values()), GRB.MINIMIZE)

        # 三、每类请求全部放完。
        for t in range(type_count):
            model.addConstr(
                gp.quicksum(q[t, j] for j in range(host_limit))
                == counts[t]
            )

        # 每台主机的CPU、内存容量。
        for j in range(host_limit):
            model.addConstr(
                gp.quicksum(
                    types[t][0] * q[t, j] for t in range(type_count)
                ) <= y[j]
            )
            model.addConstr(
                gp.quicksum(
                    types[t][1] * q[t, j] for t in range(type_count)
                ) <= y[j]
            )

        # 启用的主机排在前面，减少编号交换造成的对称性。
        for j in range(host_limit - 1):
            model.addConstr(y[j] >= y[j + 1])

        # 目标值不可能比 resource_bound 更小，剪枝。
        model.addConstr(gp.quicksum(y.values()) >= resource_bound)

        # 四、把初始分组转换为各主机的类型数量。
        for j, host in enumerate(initial_hosts):
            amounts = [0] * type_count
            for request in host:
                t = type_index[(request[3], request[4])]
                amounts[t] += 1

            for t in range(type_count):
                q[t, j].Start = amounts[t]  # 提供初值。
            y[j].Start = 1

        model.update()
        result["build_seconds"] = perf_counter() - build_started
        model.optimize()

        result["solver_status"] = model.Status
        result["solve_seconds"] = model.Runtime

        if math.isfinite(model.ObjBound):
            result["solver_bound"] = model.ObjBound
            # 减去微小数，避免整数附近的浮点误差造成错误进位。
            result["bound"] = max(
                resource_bound, math.ceil(model.ObjBound - 1e-6)
            )

        # 五、有求解器方案时，按数量恢复原始请求。
        if model.SolCount > 0:
            if math.isfinite(model.MIPGap):
                result["solver_gap"] = model.MIPGap

            positions = [0] * type_count  # 每类已经取走多少条。
            hosts = []
            for j in range(host_limit):
                host = []
                for t, demand in enumerate(types):
                    amount = int(round(q[t, j].X))
                    begin = positions[t]
                    end = begin + amount
                    host.extend(groups[demand][begin:end])
                    positions[t] = end

                if host:
                    hosts.append(host)

            result["hosts"] = hosts
            result["objective"] = len(hosts)

        if model.Status == GRB.OPTIMAL:
            result["bound"] = result["objective"]

    # 六、独立检查恢复后的完整方案。
    valid, message = check_solution(requests, result["hosts"])
    if not valid:
        raise ValueError("Invalid aggregated solution: " + message)
    if result["bound"] > result["objective"]:
        raise ValueError("Lower bound exceeds valid upper bound")

    result["optimal"] = result["bound"] == result["objective"]
    if result["optimal"]:
        result["stop_reason"] = "optimal"
        result["proof_source"] = (
            "solver_optimal"
            if result["solver_status"] == GRB.OPTIMAL
            else "bound_match"
        )
    else:
        result["stop_reason"] = "solver_stopped"
        result["proof_source"] = None

    result["gap_to_bound"] = (
        result["objective"] - result["bound"]
    ) / result["bound"]
    result["total_seconds"] = perf_counter() - started
    return result