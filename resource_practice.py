a_cpu = 0.4
b_cpu = 0.35
cpu_total = a_cpu + b_cpu

a_cpu = 0.8
print(a_cpu, cpu_total)

cpu_total = a_cpu + b_cpu
print(a_cpu, cpu_total)

vms = [
    (0.4, 0.3),
    (0.35, 0.5),
    (0.2, 0.1),
]

print(vms)
print(vms[0])
print(vms[0][1])
print(vms[2][0])

cpu_total = 0
memory_total = 0

for vm in vms:
    cpu_total = cpu_total + vm[0]
    memory_total = memory_total + vm[1]

fits = (cpu_total <= 1) and (memory_total <= 1)

print("CPU total:", cpu_total)
print("Memory total:", memory_total)
print("Fits:", fits)

def resource_totals(requests):
    cpu_total = 0
    memory_total = 0

    for vm in requests:
        cpu_total = cpu_total + vm[0]
        memory_total = memory_total + vm[1]

    return cpu_total, memory_total

cpu_total, memory_total = resource_totals(vms)
print(cpu_total, memory_total)

def can_share_one_host(requests):
    resource_total = (resource_totals(requests))
    fits = (resource_total[0] <= 1) and (resource_total[1] <= 1)

    return fits 

print(can_share_one_host(vms))

cases = [
    [(0.4, 0.3), (0.35, 0.5), (0.2, 0.1)],
    [(0.6, 0.2), (0.5, 0.2)],
    [(0.2, 0.7), (0.2, 0.4)],
    [(0.65, 0.3), (0.35, 0.5)],
    [],
]

for case in cases:
    print(resource_totals(case))
    print(can_share_one_host(case))

cpu_total = 99
memory_total = 99
print(can_share_one_host([(0.2, 0.2)]))