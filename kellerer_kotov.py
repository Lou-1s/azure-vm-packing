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


# 将本文件全部内容追加到项目的kellerer_kotov.py末尾。
# 这里复用该模块中已有的resource_totals、kk_fits等函数。
from collections import deque  # 双端队列，支持高效地从头部取出/放回请求。
from packing_algorithms import first_fit


def kk_axis_total(hosts, axis):
    total = 0
    for host in hosts:
        for request in host:
            total += request[axis]
    return total


def kk_merge_group(hosts):
    # 可行的组内合并：总负载不变，使用的主机数只会减少。
    # 两层for依次展开“组 -> 主机 -> 请求”，得到一层请求列表。
    requests = [request for host in hosts for request in host]
    cpu, memory = resource_totals(requests)
    if cpu <= 1 + 1e-9 and memory <= 1 + 1e-9:
        return [requests] if requests else []
    return [host for host in hosts if host]


def kk_fill_two(queue):
    # 第5步：按既定次序尝试两台空主机，首次两台均放不下时停止。
    hosts = [[], []]
    loads = [[0, 0], [0, 0]]
    while queue:
        request = queue[0]  # 只查看队首，放置成功后才删除。
        if kk_fits(loads[0], request):
            kk_place(hosts[0], loads[0], queue.popleft())
        elif kk_fits(loads[1], request):
            kk_place(hosts[1], loads[1], queue.popleft())
        else:
            break
    return hosts


def kk_group_phase(state):
    axis = state["axis"]
    other_axis = 4 if axis == 3 else 3
    # last_semi[axis]记录相应方向最后一个半完整组的编号。
    # P(主轴)放完全部Add意味着另一轴半完整，并不表示两轴都完整。
    last_semi = {3: 0, 4: 0}
    for bunch in state["bunches"]:
        fill_axis = bunch["fill_axis"]
        if fill_axis is not None and bunch["stop_id"] is None:
            semi_axis = 4 if fill_axis == 3 else 3
            last_semi[semi_axis] = bunch["rank"]

    ready = []
    type_one = []
    type_two = []
    for bunch in state["bunches"]:
        # 先清理可行合并与空主机，再按实际组大小判断。
        hosts = kk_merge_group(bunch["hosts"])
        rank = bunch["rank"]
        if len(hosts) == 2 and rank > last_semi[axis] and kk_axis_total(hosts, axis) < 1 - 1e-9:
            type_one.append(hosts)
        elif len(hosts) == 2 and rank > last_semi[other_axis] and kk_axis_total(hosts, other_axis) < 1 - 1e-9:
            type_two.append(hosts)
        else:
            ready.append(hosts)

    counts = (len(type_one), len(type_two))
    paired = min(len(type_one), len(type_two))
    # 第4步：两类各取一个双主机组，组成四主机组。
    for i in range(paired):
        ready.append(type_one[i] + type_two[i])

    if len(type_one) > paired:
        pending = type_one[paired:]
        need_axis = axis
    else:
        pending = type_two[paired:]
        need_axis = other_axis

    other_need = 4 if need_axis == 3 else 3
    small = state["remaining"]
    fillers = [r for r in small if r[need_axis] >= r[other_need]]
    fillers.sort(key=lambda r: (-r[need_axis], r[0]))
    queue = deque(fillers)
    used_ids = set()
    # 第5步：剩余同类组各配两台新主机，装入相应方向的小请求。
    for hosts in pending:
        if queue:
            extra = kk_fill_two(queue)
            for host in extra:
                used_ids.update(r[0] for r in host)  # 将该主机上的所有ID加入集合。
            ready.append(hosts + extra)
        else:
            ready.append(hosts)

    remaining = [r for r in small if r[0] not in used_ids]
    info = {"last_semi": last_semi, "type_counts": counts, "paired_groups": paired}
    return ready, remaining, info


def kk_fill_front(queue):
    # 第6步分别填充两个方向的请求；遇到首个放不下的队首即停止。
    host = []
    load = [0, 0]
    while queue and kk_fits(load, queue[0]):
        kk_place(host, load, queue.popleft())
    return host


def kk_small_phase(small, axis):
    other_axis = 4 if axis == 3 else 3
    # 需求相等的小请求归入第一组，保证两组不重叠。
    first = deque(r for r in small if r[axis] >= r[other_axis])
    second = deque(r for r in small if r[axis] < r[other_axis])
    first_total = sum(r[axis] for r in first)  # 缓存总量，避免每轮重新遍历整个队列。
    second_total = sum(r[other_axis] for r in second)
    groups = []
    actions = []

    while first_total > 0.5 + 1e-9 and second_total > 0.5 + 1e-9:
        first_host = kk_fill_front(first)
        second_host = kk_fill_front(second)
        first_total -= sum(r[axis] for r in first_host)
        second_total -= sum(r[other_axis] for r in second_host)
        x_total = kk_axis_total([first_host, second_host], axis)
        y_total = kk_axis_total([first_host, second_host], other_axis)

        if x_total > 1 + 1e-9 and y_total > 1 + 1e-9:
            groups.append([first_host, second_host])
            actions.append("keep_two")
        elif x_total <= 1 + 1e-9 and y_total <= 1 + 1e-9:
            groups.append([first_host + second_host])
            actions.append("merge_one")
        elif x_total <= 1 + 1e-9:
            # 第6.3步：从第二台转入第一台，直至另一维达到0.5。
            kept = first_host
            load = list(resource_totals(kept))
            take = 0
            while load[other_axis - 3] < 0.5 - 1e-9:
                kk_place(kept, load, second_host[take])
                take += 1
            returned = second_host[take:]
            # 逆序appendleft，恢复请求原先在队首的次序。
            for request in reversed(returned):
                second.appendleft(request)
            second_total += sum(r[other_axis] for r in returned)
            groups.append([kept])
            actions.append("transfer_second")
        else:
            # 对称分支：第一台的一部分请求转入第二台。
            kept = second_host
            load = list(resource_totals(kept))
            take = 0
            while load[axis - 3] < 0.5 - 1e-9:
                kk_place(kept, load, first_host[take])
                take += 1
            returned = first_host[take:]
            for request in reversed(returned):
                first.appendleft(request)
            first_total += sum(r[axis] for r in returned)
            groups.append([kept])
            actions.append("transfer_first")

    # 第7步：先处理总量较大的方向，再以FF处理另一方向。
    if first_total >= second_total:
        tail = list(first) + list(second)
    else:
        tail = list(second) + list(first)
    return groups, first_fit(tail), actions


def kellerer_kotov(requests, return_info=False):
    # 默认只返回分组，保持与FF、FFD等算法相同的调用接口。
    state = kk_large_phase(requests)
    groups, small, group_info = kk_group_phase(state)
    small_groups, tail_hosts, actions = kk_small_phase(small, state["axis"])

    hosts = list(state["fixed_hosts"])
    for group in groups + small_groups:
        hosts.extend(host for host in group if host)  # 空主机不计入最终方案。
    hosts.extend(tail_hosts)

    if return_info:
        # **group_info将已有字典的各项展开，再加上小请求阶段记录。
        return hosts, {**group_info, "small_actions": actions}
    return hosts
