def check_solution(requests, hosts):
    request_ids = []

    for request in requests:
        if len(request) != 5:
            return False, "Invalid input record"

        vm_id = request[0]

        if vm_id in request_ids:
            return False, "Duplicate input ID"

        if not (0 < request[3] <= 1 and 0 < request[4] <= 1):
            return False, "Invalid resource demand"

        request_ids.append(vm_id)

    assigned_ids = []

    for host in hosts:
        if len(host) == 0:
            return False, "Empty host"

        cpu_total = 0
        memory_total = 0

        for placed_request in host:
            if len(placed_request) != 5:
                return False, "Invalid output record"

            vm_id = placed_request[0]

            if vm_id not in request_ids:
                return False, "Unknown request ID"

            if vm_id in assigned_ids:
                return False, "Repeated placement"

            original = requests[request_ids.index(vm_id)]

            if placed_request != original:
                return False, "Request data changed"

            assigned_ids.append(vm_id)
            cpu_total = cpu_total + original[3]
            memory_total = memory_total + original[4]

        if cpu_total > 1 + 1e-9:
            return False, "CPU capacity exceeded"

        if memory_total > 1 + 1e-9:
            return False, "Memory capacity exceeded"

    for vm_id in request_ids:
        if vm_id not in assigned_ids:
            return False, "Missing request"

    return True, "OK"