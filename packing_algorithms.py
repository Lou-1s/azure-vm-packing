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
