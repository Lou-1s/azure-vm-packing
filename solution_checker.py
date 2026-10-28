# 输入原始请求列表和主机分组；返回 (是否可行, 检查结果说明)。
# 独立检查原始数据与放置结果，不调用待检查算法的资源求和函数。
def check_solution(requests, hosts):
    request_ids = []

    for request in requests:
        # 输入记录应有五项，且每个请求 ID 只出现一次。
        if len(request) != 5:
            return False, "Invalid input record"

        vm_id = request[0]

        if vm_id in request_ids:
            return False, "Duplicate input ID"

        # 请求自身的两种资源份额必须合法，单条请求才有可能放进一台主机。
        if not (0 < request[3] <= 1 and 0 < request[4] <= 1):
            return False, "Invalid resource demand"

        request_ids.append(vm_id)

    # 已放置的请求 ID 用于排查重复放置，最后也用于排查遗漏。
    assigned_ids = []

    for host in hosts:
        # hosts 只记录实际使用的主机，不应含空主机。
        if len(host) == 0:
            return False, "Empty host"

        cpu_total = 0
        memory_total = 0

        for placed_request in host:
            if len(placed_request) != 5:
                return False, "Invalid output record"

            vm_id = placed_request[0]

            # in / not in 判断某个 ID 是否已经存在于列表中。
            if vm_id not in request_ids:
                return False, "Unknown request ID"

            if vm_id in assigned_ids:
                return False, "Repeated placement"

            # index 找到该 ID 在原列表中的位置，再取出对应的完整原始请求。
            original = requests[request_ids.index(vm_id)]

            # 对比完整记录，防止算法只保留同一个 ID，却改变了需求等数据。
            if placed_request != original:
                return False, "Request data changed"

            assigned_ids.append(vm_id)
            cpu_total = cpu_total + original[3]
            memory_total = memory_total + original[4]

        # 每台主机分别核对两种容量；1e-9 容差用于浮点求和的舍入误差。
        if cpu_total > 1 + 1e-9:
            return False, "CPU capacity exceeded"

        if memory_total > 1 + 1e-9:
            return False, "Memory capacity exceeded"

    for vm_id in request_ids:
        # 每个原始请求都必须在分组中出现，不能通过少放请求来节省主机。
        if vm_id not in assigned_ids:
            return False, "Missing request"

    # 前面的 return 会在发现问题时立即结束函数；走到这里才表示全部通过。
    return True, "OK"
