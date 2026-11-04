import _bootstrap  # 将项目根目录加入模块搜索路径。
from kellerer_kotov import kk_large_phase
from solution_checker import check_solution


cases = [
    ("Pair fits", [
        (0, -1, 0, 0.7, 0.7),
        (1, -1, 0, 0.8, 0.2),
        (2, -1, 0, 0.2, 0.8),
        (3, -1, 0, 0.1, 0.1),
    ]),

    ("Call P", [
        (0, -1, 0, 0.7, 0.1),
        (1, -1, 0, 0.4, 0.6),
        (2, -1, 0, 0.4, 0.2),
        (3, -1, 0, 0.35, 0.4),
        (4, -1, 0, 0.2, 0.1),
        (5, -1, 0, 0.1, 0.3),
    ]),

    ("Single host succeeds", [
        (10, -1, 0, 0.7, 0.3),
        (11, -1, 0, 0.2, 0.3),
        (12, -1, 0, 0.4, 0.1),
    ]),

    ("Discard single trial", [
        (20, -1, 0, 0.8, 0.2),
        (21, -1, 0, 0.3, 0.4),
        (22, -1, 0, 0.1, 0.2),
        (23, -1, 0, 0.2, 0.05),
    ]),

    ("Memory is major", [
        (0, -1, 0, 0.7, 0.7),
        (1, -1, 0, 0.8, 0.2),
        (2, -1, 0, 0.6, 0.1),
        (3, -1, 0, 0.2, 0.9),
        (4, -1, 0, 0.1, 0.6),
        (5, -1, 0, 0.5, 0.5),
        (6, -1, 0, 0.4, 0.2),
        (7, -1, 0, 0.1, 0.3),
        (8, -1, 0, 0.5, 0.7),
    ]),

    ("Empty", []),
]


for name, requests in cases:
    before = list(requests)
    state = kk_large_phase(requests)

    print("\nCase:", name)
    print(
        "Major axis:",
        "CPU" if state["axis"] == 3 else "Memory",
    )
    print(
        "Fixed:",
        [[r[0] for r in host]
         for host in state["fixed_hosts"]],
    )

    for bunch in state["bunches"]:
        print(
            bunch["rank"],
            bunch["reason"],
            [[r[0] for r in host]
             for host in bunch["hosts"]],
            "P axis:", bunch["fill_axis"],
            "Stop:", bunch["stop_id"],
        )

    remaining = state["remaining"]
    print("Remaining:", [r[0] for r in remaining])
    print("Input unchanged:", requests == before)

    all_hosts = list(state["fixed_hosts"])

    for bunch in state["bunches"]:
        # extend把组内各台主机逐个加入总列表。
        all_hosts.extend(bunch["hosts"])

    check_hosts = [host for host in all_hosts if host]

    # 剩余小请求暂时各放一台，仅用于局部检查。
    check_hosts += [[request] for request in remaining]

    print(
        "Partial check:",
        check_solution(requests, check_hosts),
    )
