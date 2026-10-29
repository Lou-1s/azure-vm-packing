# 每条 request 为 (vmId, vmTypeId, starttime, CPU 份额, 内存份额)。
# 下面的资源求和函数输入请求列表，返回 (CPU 总和, 内存总和)。
def resource_totals(requests):
    cpu_total = 0
    memory_total = 0

    for request in requests:
        cpu_total = cpu_total + request[3]
        memory_total = memory_total + request[4]

    return cpu_total, memory_total


def first_fit(requests):
    # hosts 是主机列表；其中每个 host 又是放到该主机上的请求列表。
    hosts = []

    for request in requests:
        # 每处理一条新请求，重新记录它是否已经找到位置。
        placed = False

        for host in hosts:
            # 按开启顺序检查已有主机，用两个变量接收当前的资源总量。
            cpu_total, memory_total = resource_totals(host)

            # 两种资源都不能超容量；1e-9 是处理浮点舍入误差的微小容差。
            fits = (
                cpu_total + request[3] <= 1 + 1e-9
                and memory_total + request[4] <= 1 + 1e-9
            )

            if fits:
                # append 直接把请求加进原来的 host 列表。
                host.append(request)
                placed = True
                # 找到第一个可放主机就退出内层循环，继续处理下一条请求。
                break

        if not placed:
            # 全部已有主机都放不下，才新增一台；[request] 表示它的首条请求。
            hosts.append([request])

    return hosts

def best_fit(requests):
    hosts = []

    for request in requests:
        # None 表示尚未找到可用主机；初始分数 3 大于可行主机的剩余份额和。
        best_host = None
        best_score = 3

        for host in hosts:
            cpu_total, memory_total = resource_totals(host)

            fits = (
                cpu_total + request[3] <= 1 + 1e-9
                and memory_total + request[4] <= 1 + 1e-9
            )

            if fits:
                # 先算“放入之后”的两种剩余份额；本项目选两者之和最小的主机。
                remaining_cpu = 1 - cpu_total - request[3]
                remaining_memory = 1 - memory_total - request[4]
                score = remaining_cpu + remaining_memory

                if score < best_score:
                    # 只在严格更小时更新；分数相同就保留先检查到的主机。
                    # best_host 指向原 hosts 中的那个列表，不是另建一个主机副本。
                    best_host = host
                    best_score = score

        if best_host is None:
            # is None 判断是否仍没有找到可行主机。
            hosts.append([request])
        else:
            best_host.append(request)

    return hosts

def decreasing_key(request):
    # sorted 默认升序；给 max(CPU, 内存) 加负号，就实现主资源份额降序。
    # 返回元组会先比第一项；同值时再按请求 ID 升序打破平局。
    return -max(request[3], request[4]), request[0]


def first_fit_decreasing(requests):
    # key 接收函数本身，sorted 会逐条调用它；返回新列表，不改原请求顺序。
    ordered_requests = sorted(requests, key=decreasing_key)
    # 排好序以后复用 First Fit，得到 FFD 的主机分组。
    return first_fit(ordered_requests)


def best_fit_decreasing(requests):
    # 使用与 FFD 相同的排序规则，再复用 Best Fit。
    ordered_requests = sorted(requests, key=decreasing_key)
    return best_fit(ordered_requests)

def request_id_key(request):
    return request[0]


def dot_product(requests):
    # 单条需求必须能放进空主机，避免反复开机却无法放置。
    for request in requests:
        if not (0 < request[3] <= 1 and 0 < request[4] <= 1):
            raise ValueError("Invalid resource demand")

    # sorted 返回新列表，不改变原输入。
    # 按 ID 排列，使后面评分相同时优先选择较小 ID。
    remaining = sorted(requests, key=request_id_key)
    hosts = []

    # 外层循环：还有未放置请求，就开始填一台新主机。
    while len(remaining) > 0:
        host = []
        cpu_total = 0
        memory_total = 0

        # 内层循环：不断为当前主机挑选下一条请求。
        while True:
            remaining_cpu = 1 - cpu_total
            remaining_memory = 1 - memory_total
            best_index = None
            best_score = -1

            # 先完整扫描候选，扫描过程中不删除元素。
            for i in range(len(remaining)):
                request = remaining[i]
                fits = (
                    cpu_total + request[3] <= 1 + 1e-9
                    and memory_total + request[4] <= 1 + 1e-9
                )

                if fits:
                    score = (
                        request[3] * remaining_cpu
                        + request[4] * remaining_memory
                    )

                    # 严格更高才更新，同分保留先扫描到的较小 ID。
                    if score > best_score:
                        best_index = i
                        best_score = score

            if best_index is None:
                # 没有请求还能放入，退出内层循环。
                break

            # 按位置删除并取出选中的请求。
            selected = remaining.pop(best_index)
            host.append(selected)
            cpu_total += selected[3]
            memory_total += selected[4]

            # 下一轮重新计算剩余容量，并重新扫描候选。

        hosts.append(host)

    return hosts


def sum_decreasing_key(request):
    # 对 CPU + 内存整体加负号；同分仍按 ID 升序。
    return -(request[3] + request[4]), request[0]


def first_fit_decreasing_sum(requests):
    ordered_requests = sorted(requests, key=sum_decreasing_key)
    return first_fit(ordered_requests)