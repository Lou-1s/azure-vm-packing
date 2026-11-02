def check_solution(requests, hosts):
    originals = {}  # 请求ID -> 完整原始记录。

    for request in requests:
        if len(request) != 5:
            return False, "Invalid input record"

        vm_id = request[0]

        # in判断字典中是否已经存在这个键。
        if vm_id in originals:
            return False, "Duplicate input ID"

        if not (0 < request[3] <= 1 and 0 < request[4] <= 1):
            return False, "Invalid resource demand"

        originals[vm_id] = request

    assigned_ids = set()

    for host in hosts:
        if len(host) == 0:
            return False, "Empty host"

        cpu_total = 0
        memory_total = 0

        for placed_request in host:
            if len(placed_request) != 5:
                return False, "Invalid output record"

            vm_id = placed_request[0]

            if vm_id not in originals:
                return False, "Unknown request ID"

            if vm_id in assigned_ids:
                return False, "Repeated placement"

            original = originals[vm_id]  # 直接按ID取回记录。

            if placed_request != original:
                return False, "Request data changed"

            assigned_ids.add(vm_id)  # 集合用add增加元素。
            cpu_total += original[3]
            memory_total += original[4]

        if cpu_total > 1 + 1e-9:
            return False, "CPU capacity exceeded"

        if memory_total > 1 + 1e-9:
            return False, "Memory capacity exceeded"

    # 遍历字典时，依次取得各个键。
    for vm_id in originals:
        if vm_id not in assigned_ids:
            return False, "Missing request"

    return True, "OK"