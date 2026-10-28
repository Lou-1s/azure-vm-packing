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

def best_fit(requests):
    hosts = []

    for request in requests:
        best_host = None
        best_score = 3

        for host in hosts:
            cpu_total, memory_total = resource_totals(host)

            fits = (
                cpu_total + request[3] <= 1 + 1e-9
                and memory_total + request[4] <= 1 + 1e-9
            )

            if fits:
                remaining_cpu = 1 - cpu_total - request[3]
                remaining_memory = 1 - memory_total - request[4]
                score = remaining_cpu + remaining_memory

                if score < best_score:
                    best_host = host
                    best_score = score

        if best_host is None:
            hosts.append([request])
        else:
            best_host.append(request)

    return hosts

def decreasing_key(request):
    return -max(request[3], request[4]), request[0]


def first_fit_decreasing(requests):
    ordered_requests = sorted(requests, key=decreasing_key)
    return first_fit(ordered_requests)


def best_fit_decreasing(requests):
    ordered_requests = sorted(requests, key=decreasing_key)
    return best_fit(ordered_requests)