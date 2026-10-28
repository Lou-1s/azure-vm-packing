import gurobipy as gp
from gurobipy import GRB
from packing_algorithms import first_fit
from solution_checker import check_solution

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

print("Gurobi version:", gp.gurobi.version())

initial_hosts = first_fit(requests)
valid, message = check_solution(requests, initial_hosts)

if not valid:
    raise ValueError(message)
    # 如果上界方案检查失败，主动报错并停止。

n = len(requests)
host_limit = len(initial_hosts)
# host_limit = 1
print("Candidate hosts:", host_limit)

model = gp.Model("vm_packing")
model.Params.OutputFlag = 0
model.Params.TimeLimit = 30
model.Params.MIPGap = 0
model.Params.FeasibilityTol = 1e-9
model.Params.IntFeasTol = 1e-9

x = model.addVars(n, host_limit, vtype=GRB.BINARY, name="x")
y = model.addVars(host_limit, vtype=GRB.BINARY, name="y")

model.setObjective(
    gp.quicksum(y[j] for j in range(host_limit)),
    GRB.MINIMIZE,
)

for i in range(n):
    model.addConstr(
        gp.quicksum(x[i, j] for j in range(host_limit)) == 1
    )

for j in range(host_limit):
    model.addConstr(
        gp.quicksum(requests[i][3] * x[i, j] for i in range(n)) <= y[j]
    )
    model.addConstr(
        gp.quicksum(requests[i][4] * x[i, j] for i in range(n)) <= y[j]
    )
    model.addConstr(
        y[j] <= gp.quicksum(x[i, j] for i in range(n))
    )

    for i in range(n):
        model.addConstr(x[i, j] <= y[j])

model.optimize()

print("Status:", model.Status)
print("Optimal:", model.Status == GRB.OPTIMAL)
print("Solutions:", model.SolCount)
print("Bound:", model.ObjBound)

if model.SolCount > 0:
    print("Objective:", model.ObjVal)
    print("Gap:", model.MIPGap)

    hosts = []

    for j in range(host_limit):
        host = []

        for i in range(n):
            if x[i, j].X > 0.5:
                host.append(requests[i])

        if len(host) > 0:
            hosts.append(host)

    valid, message = check_solution(requests, hosts)
    print("Valid:", valid, "|", message)

    for host in hosts:
        vm_ids = []

        for request in host:
            vm_ids.append(request[0])

        print("VM IDs:", vm_ids)
else:
    print("No feasible solution available.")

model.dispose()