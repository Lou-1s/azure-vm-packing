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


def kk_try_single(large, small, axis):
    host = [large]
    load = [large[3], large[4]]
    other_axis = 4 if axis == 3 else 3

    add = [
        request for request in small
        if kk_fits(load, request)
    ]
    add.sort(
        key=lambda r: (-r[other_axis] / r[axis], r[0])
    )

    used_ids = set()

    for request in add:
        if kk_fits(load, request):
            kk_place(host, load, request)
            used_ids.add(request[0])

    remaining = [
        request for request in small
        if request[0] not in used_ids
    ]

    return host, remaining


def kk_large_phase(requests):
    groups = kk_classify(requests)

    # 论文假定BigX数量不少于BigY。
    # 我们选择数量更多的一侧作为主轴，不修改请求元组。
    if len(groups["big_cpu"]) >= len(groups["big_memory"]):
        axis = 3
        major = groups["big_cpu"]
        minor = groups["big_memory"]
    else:
        axis = 4
        major = groups["big_memory"]
        minor = groups["big_cpu"]

    other_axis = 4 if axis == 3 else 3

    # 第1步：两种资源都超过0.5的请求，各放一台。
    fixed_hosts = [
        [request] for request in groups["big_both"]
    ]

    small = groups["small"]
    bunches = []

    for i, large in enumerate(major):
        partner = minor[i] if i < len(minor) else None
        fill_axis = None
        stop_id = None

        if partner is None:
            # 第3步：没有配对大请求时，先尝试单机填充。
            trial_host, trial_remaining = kk_try_single(
                large, small, axis
            )

            if kk_group_complete([trial_host]):
                # 试放达到完整组要求，采用这一结果。
                hosts = [trial_host]
                small = trial_remaining
                reason = "single_complete"
            else:
                # 放弃试放结果，从原small重新调用P。
                hosts, small, stop_id = kk_fill_pair(
                    large, None, small, axis
                )
                fill_axis = axis
                reason = "unpaired_fill"

        elif kk_fits([large[3], large[4]], partner):
            # 第2.1步：两个大请求能合放，组成单主机组。
            hosts = [[large, partner]]
            reason = "pair_one_host"

        else:
            hosts = [[large], [partner]]

            if kk_group_complete(hosts):
                # 第2.2步：双主机组已经完整。
                reason = "pair_two_complete"

            elif large[axis] + partner[axis] > 1 + 1e-9:
                # 第2.3步：主轴合计超过1，调用P(large)。
                hosts, small, stop_id = kk_fill_pair(
                    large, partner, small, axis
                )
                fill_axis = axis
                reason = "fill_major"

            else:
                # 另一维合计超过1，调用P(partner)。
                filled, small, stop_id = kk_fill_pair(
                    partner, large, small, other_axis
                )

                # P将自己的large放第一台。
                # 恢复为主轴大请求所在主机排在前面的次序。
                hosts = [filled[1], filled[0]]
                fill_axis = other_axis
                reason = "fill_minor"

        # rank从1编号，表示主机组次序，不是请求ID。
        # 保留P调用方向和停止位置，供后续组分类使用。
        bunches.append({
            "rank": i + 1,
            "hosts": hosts,
            "reason": reason,
            "fill_axis": fill_axis,
            "stop_id": stop_id,
        })

    return {
        "axis": axis,
        "fixed_hosts": fixed_hosts,
        "bunches": bunches,
        "remaining": small,
    }