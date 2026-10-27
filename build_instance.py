import sqlite3

machine_id = 12

database = "file:D:/PythonProjects/azure-vm-packing/data/raw/packing_trace_zone_a_v1.sqlite?mode=ro"
connection = sqlite3.connect(database, uri=True)

sql = """
SELECT vm.vmId, vm.vmTypeId, vm.starttime,
       vmType.core, vmType.memory
FROM vm
JOIN vmType ON vm.vmTypeId = vmType.vmTypeId
WHERE vmType.machineId = ?
  AND vm.starttime >= ?
  AND vm.starttime < ?
  AND vmType.core > 0 AND vmType.core <= 1
  AND vmType.memory > 0 AND vmType.memory <= 1
ORDER BY vm.starttime ASC, vm.vmId ASC
LIMIT ?
"""

def load_requests(connection, sql, parameters):
    cursor = connection.execute(sql, parameters)
    return cursor.fetchall()

def summarize_requests(requests):
    cpu_total = 0
    memory_total = 0
    cpu_heavy = 0
    memory_heavy = 0
    equal_count = 0

    for request in requests:
        cpu = request[3]
        memory = request[4]

        cpu_total = cpu_total + cpu
        memory_total = memory_total + memory

        if cpu > memory:
            cpu_heavy = cpu_heavy + 1

        if memory > cpu:
            memory_heavy = memory_heavy + 1

        if cpu == memory:
            equal_count = equal_count + 1

    return cpu_total, memory_total, cpu_heavy, memory_heavy, equal_count

cases = [
    (1, 2, 20),
    (1, 2, 40),
    (1, 2, 80),
    (2, 3, 20),
    (3,4,20),
]

print("Start | End | N | CPU | Memory | CPU>Memory | Memory>CPU | Equal")

for case in cases:
    parameters = (
        machine_id,
        case[0],
        case[1],
        case[2],
    )

    requests = load_requests(connection, sql, parameters)
    totals = summarize_requests(requests)

    print(
        case[0],
        case[1],
        len(requests),
        round(totals[0], 6),
        round(totals[1], 6),
        totals[2],
        totals[3],
        totals[4],
        sep=" | ",
    )

print(summarize_requests([(0, 0, 0, 0.2, 0.2)]))

connection.close()