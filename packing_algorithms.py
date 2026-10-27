def resource_totals(requests):
    cpu_total = 0
    memory_total = 0

    for request in requests:
        cpu_total = cpu_total + request[3]
        memory_total = memory_total + request[4]

    return cpu_total, memory_total


def first_fit(requests):
    hosts = []

    for request in requests:
        placed = False

        for host in hosts:
            cpu_total, memory_total = resource_totals(host)

            fits = (
                cpu_total + request[3] <= 1 + 1e-9
                and memory_total + request[4] <= 1 + 1e-9
            )

            if fits:
                host.append(request)
                placed = True
                break

        if not placed:
            hosts.append([request])

    return hosts