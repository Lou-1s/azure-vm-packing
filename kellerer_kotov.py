from packing_algorithms import resource_totals


def kk_classify(requests):
    groups = {
        "big_both": [],
        "big_cpu": [],
        "big_memory": [],
        "small": [],
    }

    for request in requests:
        cpu, memory = request[3], request[4]

        if cpu > 0.5 and memory > 0.5:
            groups["big_both"].append(request)
        elif cpu > 0.5:
            groups["big_cpu"].append(request)
        elif memory > 0.5:
            groups["big_memory"].append(request)
        else:
            groups["small"].append(request)

    # lambda接收一条r，返回排序键。
    # 负号表示需求降序，同值时按请求ID升序。
    groups["big_cpu"].sort(key=lambda r: (-r[3], r[0]))
    groups["big_memory"].sort(key=lambda r: (-r[4], r[0]))
    groups["big_both"].sort(key=lambda r: r[0])
    groups["small"].sort(key=lambda r: r[0])

    return groups


def kk_fits(load, request):
    return (
        load[0] + request[3] <= 1 + 1e-9
        and load[1] + request[4] <= 1 + 1e-9
    )


def kk_place(host, load, request):
    # 修改传入的两个列表，保持主机内容和负载同步。
    host.append(request)
    load[0] += request[3]
    load[1] += request[4]


def kk_group_complete(hosts):
    cpu_total = 0
    memory_total = 0

    for host in hosts:
        cpu, memory = resource_totals(host)
        cpu_total += cpu
        memory_total += memory

    target = len(hosts) / 2

    # 沿用项目中1e-9的浮点计算容差。
    return (
        cpu_total + 1e-9 >= target
        and memory_total + 1e-9 >= target
    )


def kk_fill_pair(large, partner, small, axis):
    # axis=3对应P(v)：large为CPU大请求。
    # axis=4对应P(w)：large为内存大请求。
    # 第一台放large，第二台放partner；partner可以为None。
    hosts = [[large], []]
    loads = [[large[3], large[4]], [0, 0]]

    if partner is not None:
        kk_place(hosts[1], loads[1], partner)

    other_axis = 4 if axis == 3 else 3
    used_ids = set()

    # Add：能与large单独共存的小请求。
    # 此时第一台主机中只有large。
    add = [
        request for request in small
        if kk_fits(loads[0], request)
    ]

    # Not Add中，偏重另一种资源的小请求。
    outside = [
        request for request in small
        if not kk_fits(loads[0], request)
        and request[other_axis] >= request[axis]
    ]

    # 第一阶段：先尝试把outside中的请求放进第二台。
    for request in sorted(outside, key=lambda r: r[0]):
        if kk_fits(loads[1], request):
            kk_place(hosts[1], loads[1], request)
            used_ids.add(request[0])

    # P(v)按Memory/CPU降序；P(w)按CPU/Memory降序。
    add.sort(
        key=lambda r: (-r[other_axis] / r[axis], r[0])
    )

    stop_id = None

    # 第二阶段：按顺序尝试将Add中的请求放进第二台。
    for request in add:
        if kk_fits(loads[1], request):
            kk_place(hosts[1], loads[1], request)
            used_ids.add(request[0])
        else:
            # 此请求属于Add，因此能与large共存。
            # 放进第一台后，立即结束本次填充。
            kk_place(hosts[0], loads[0], request)
            used_ids.add(request[0])
            stop_id = request[0]
            break

    remaining = [
        request for request in small
        if request[0] not in used_ids
    ]

    # None表示没有发生“转入第一台后停止”。
    return hosts, remaining, stop_id