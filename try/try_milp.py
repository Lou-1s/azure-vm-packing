import _bootstrap  # 将项目根目录加入模块搜索路径。
# as gp 给 gurobipy 模块起简短名称，后面用 gp.Model、gp.quicksum 等调用。
import gurobipy as gp
# GRB 提供固定常量，如二元变量 BINARY、最小化 MINIMIZE、最优状态 OPTIMAL。
from gurobipy import GRB
from packing_algorithms import first_fit
from solution_checker import check_solution
from milp_solver import solve_milp       # 导入刚定义的求解函数。

# 每条为 (请求 ID, 类型 ID, 开始时间, CPU 份额, 内存份额)。
requests = [
    (0, 0, 0, 0.6, 0.2),
    (1, 1, 1, 0.5, 0.2),
    (2, 2, 2, 0.4, 0.7),
    (3, 3, 3, 0.1, 0.8),
    (4, 4, 4, 0.1, 0.1),
]
# requests = [
#     (10, 10, 0, 0.6, 0.7),
#     # (11, 11, 1, 0.4, 0.4),
#     (11, 11, 1, 0.4, 0.3),
# ]

# # version() 返回当前 Python 接口对应的 Gurobi 版本元组。
# print("Gurobi version:", gp.gurobi.version())

# # 先用 FF 生成可行方案，它的主机数用作候选主机数量上界。
# initial_hosts = first_fit(requests)
# valid, message = check_solution(requests, initial_hosts)

# if not valid:
#     # raise 主动抛出错误并停止；没有通过检查的方案不能拿来当可行上界。
#     raise ValueError(message)

# # n 是请求数；host_limit 是候选主机数，不是数据里的硬件规格 machineId。
# n = len(requests)
# host_limit = len(initial_hosts)
# # host_limit = 1
# print("Candidate hosts:", host_limit)

# # Model 创建模型对象；字符串只是这个模型的名称。
# model = gp.Model("vm_packing")
# model.Params.OutputFlag = 0  # 关闭常规求解日志，保留下面自己打印的结果。
# model.Params.TimeLimit = 30  # 最多求解 30 秒；超时并不意味着已经证明最优。
# model.Params.MIPGap = 0  # 相对间隙目标设为 0，仍受时间限制和数值容差影响。
# model.Params.FeasibilityTol = 1e-9  # 收紧线性约束的可行性容差。
# model.Params.IntFeasTol = 1e-9  # 收紧整数变量的整数性容差。

# # addVars(n, host_limit, ...) 创建 n×host_limit 个变量；vtype 指定只能取 0/1。
# # x[i, j]=1 表示把第 i 条请求放到候选主机 j；i 是列表位置，不一定等于请求 ID。
# x = model.addVars(n, host_limit, vtype=GRB.BINARY, name="x")
# # y[j]=1 表示启用候选主机 j；name 是变量在模型中的显示名称。
# y = model.addVars(host_limit, vtype=GRB.BINARY, name="y")

# # setObjective 接收“目标表达式”和“优化方向”；这里最小化启用主机数。
# # range(host_limit) 依次给出 0 到 host_limit-1；quicksum 把对应变量加起来。
# model.setObjective(
#     gp.quicksum(y[j] for j in range(host_limit)),
#     GRB.MINIMIZE,
# )

# for i in range(n):
#     # addConstr 接收约束关系；对固定 i，把所有候选主机上的 x 相加等于 1。
#     # 例如三台候选主机时：x[i, 0] + x[i, 1] + x[i, 2] == 1。
#     model.addConstr(
#         gp.quicksum(x[i, j] for j in range(host_limit)) == 1
#     )

# for j in range(host_limit):
#     # 固定主机 j，累加放到它上面的 CPU 需求；未启用时 y[j]=0，容量也为 0。
#     model.addConstr(
#         gp.quicksum(requests[i][3] * x[i, j] for i in range(n)) <= y[j]
#     )
#     # 内存容量约束与 CPU 独立，必须同时满足。
#     model.addConstr(
#         gp.quicksum(requests[i][4] * x[i, j] for i in range(n)) <= y[j]
#     )
#     # 启用的主机至少放一条请求，避免结果包含空的已启用主机。
#     model.addConstr(
#         y[j] <= gp.quicksum(x[i, j] for i in range(n))
#     )

#     for i in range(n):
#         # 未启用主机不能接收请求；该连接约束也有助于收紧模型。
#         model.addConstr(x[i, j] <= y[j])

# # 上面只是在描述模型；optimize() 才开始求解。
# model.optimize()

# # Status 是结束原因：OPTIMAL=2、INFEASIBLE=3、TIME_LIMIT=9。
# print("Status:", model.Status)
# print("Optimal:", model.Status == GRB.OPTIMAL)
# print("Solutions:", model.SolCount)  # 存储的可行解数量；0 表示没有可读取的方案。
# print("Bound:", model.ObjBound)  # 最小化问题中，对最优目标值的全局下界。

# # 先确认有解，再读取目标值、间隙和变量的数值；超时也可能已有可行解。
# if model.SolCount > 0:
#     # ObjVal 是当前最好可行解的目标值；MIPGap 是该值与全局界的相对差距。
#     print("Objective:", model.ObjVal)
#     print("Gap:", model.MIPGap)

#     hosts = []

#     for j in range(host_limit):
#         host = []

#         for i in range(n):
#             # .X 读取求解后变量的数值；用 0.5 区分数值上接近 0 和接近 1 的结果。
#             if x[i, j].X > 0.5:
#                 host.append(requests[i])

#         if len(host) > 0:
#             # 只保留实际放了请求的主机，使分组格式与贪心算法一致。
#             hosts.append(host)

#     # 求解器返回后仍做独立检查，核对每条请求和两种实际资源总和。
#     valid, message = check_solution(requests, hosts)
#     print("Valid:", valid, "|", message)

#     for host in hosts:
#         vm_ids = []

#         for request in host:
#             vm_ids.append(request[0])

#         print("VM IDs:", vm_ids)
# else:
#     # 没有可行解与“用了 0 台主机”不同，不能读取 ObjVal 或变量 .X。
#     print("No feasible solution available.")

# # 结果已提取完毕，释放模型占用的求解器资源。
# model.dispose()
initial_hosts = first_fit(requests)
result = solve_milp(requests, initial_hosts)  # 未指定时限，使用默认 30 秒。
# result = solve_milp(requests, initial_hosts, time_limit=0) 

print("Candidate hosts:", len(initial_hosts))
print("Status:", result["status"])
print("Optimal:", result["status"] == GRB.OPTIMAL)
print("Solutions:", result["sol_count"])
print("Objective:", result["objective"])
print("Bound:", result["bound"])
print("Gap:", result["gap"])
print("ModelSeconds:", round(result["model_seconds"], 6))
print("SolveSeconds:", round(result["solve_seconds"], 6))

# 无解时 hosts 是 None，不能对它调用 len 或遍历。
if result["hosts"] is None:
    print("No feasible solution available.")
else:
    print("Check:", check_solution(requests, result["hosts"]))

    for host in result["hosts"]:
        vm_ids = []
        for request in host:
            vm_ids.append(request[0])
        print("VM IDs:", vm_ids)
