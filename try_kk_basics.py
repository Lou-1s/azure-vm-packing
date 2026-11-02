from kellerer_kotov import (
    kk_classify,
    kk_fill_pair,
    kk_group_complete,
)
from packing_algorithms import resource_totals
from solution_checker import check_solution


requests = [
    (0, -1, 0, 0.7, 0.7),
    (1, -1, 0, 0.8, 0.2),
    (2, -1, 0, 0.6, 0.1),
    (3, -1, 0, 0.2, 0.9),
    (4, -1, 0, 0.1, 0.6),
    (5, -1, 0, 0.5, 0.5),
    (6, -1, 0, 0.4, 0.2),
    (7, -1, 0, 0.1, 0.3),
    (8, -1, 0, 0.5, 0.7),
]

groups = kk_classify(requests)

# items()每次给出一组“字典键、对应的值”。
for name, group in groups.items():
    print(name, [request[0] for request in group])


def show_pair(name, large, partner, small, axis):
    # 新建列表，保存调用之前的内容。
    before = list(small)

    hosts, remaining, stop_id = kk_fill_pair(
        large, partner, small, axis
    )

    print("\nCase:", name)

    for host in hosts:
        print(
            "IDs:", [request[0] for request in host],
            "Load:", resource_totals(host),
        )

    print("Remaining:", [r[0] for r in remaining])
    print("Stop ID:", stop_id)
    print("Group complete:", kk_group_complete(hosts))
    print("Input unchanged:", small == before)

    originals = [large] + small
    if partner is not None:
        originals.append(partner)

    # 将剩余请求临时各放一台，仅用于检查身份和容量。
    # 这个检查分组不是KK完整算法的输出。
    check_hosts = [host for host in hosts if host]
    check_hosts += [[request] for request in remaining]

    print(
        "Partial check:",
        check_solution(originals, check_hosts),
    )


large = (0, -1, 0, 0.7, 0.1)
partner = (1, -1, 0, 0.4, 0.6)

small = [
    (2, -1, 0, 0.4, 0.2),
    (3, -1, 0, 0.35, 0.4),
    (4, -1, 0, 0.2, 0.1),
    (5, -1, 0, 0.1, 0.3),
]

show_pair("P(v): stop", large, partner, small, 3)


mirrored_large = (0, -1, 0, 0.1, 0.7)
mirrored_partner = (1, -1, 0, 0.6, 0.4)

# 交换CPU与内存，保留原请求ID。
mirrored_small = [
    (r[0], r[1], r[2], r[4], r[3])
    for r in small
]

show_pair(
    "P(w): mirror",
    mirrored_large,
    mirrored_partner,
    mirrored_small,
    4,
)


show_pair(
    "P(v): all Add placed",
    large,
    partner,
    [
        (12, -1, 0, 0.1, 0.1),
        (13, -1, 0, 0.15, 0.1),
    ],
    3,
)


show_pair(
    "P(v): no partner",
    (20, -1, 0, 0.8, 0.2),
    None,
    [
        (21, -1, 0, 0.3, 0.4),
        (22, -1, 0, 0.1, 0.2),
        (23, -1, 0, 0.2, 0.05),
    ],
    3,
)