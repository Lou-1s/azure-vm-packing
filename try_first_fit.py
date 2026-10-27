from packing_algorithms import first_fit, resource_totals

requests = [
    (0, 0, 0, 0.6, 0.2),
    (1, 1, 1, 0.5, 0.2),
    # (2, 2, 2, 0.3, 0.7),
    (2, 2, 2, 0.4, 0.7),
    (3, 3, 3, 0.1, 0.8),
    (4, 4, 4, 0.1, 0.1),
]

# requests = [
#     (10, 10, 0, 0.2, 0.2),
#     (11, 11, 1, 0.9, 0.1),
#     (12, 12, 2, 0.1, 0.1),
# ]

hosts = first_fit(requests)

print("Host count:", len(hosts))

for host in hosts:
    vm_ids = []

    for request in host:
        vm_ids.append(request[0])

    cpu_total, memory_total = resource_totals(host)

    print(
        "VM IDs:", vm_ids,
        "| CPU:", round(cpu_total, 6),
        "| Memory:", round(memory_total, 6),
    )

print("Empty input:", first_fit([]))