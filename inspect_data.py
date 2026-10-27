import sqlite3
# machineId 硬件规格；vmTypeId 类型编号

def show_rows(connection, sql):
    cursor = connection.execute(sql)
    rows = cursor.fetchall()
    print("Rows:", len(rows))
    for row in rows:
        print(row)

database = "file:D:/PythonProjects/azure-vm-packing/data/raw/packing_trace_zone_a_v1.sqlite?mode=ro"
connection = sqlite3.connect(database, uri=True)

sql = "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
show_rows(connection, sql)

# print("Columns of vm:")
# show_rows(connection, "PRAGMA table_info(vm)")

# print("Columns of vmType:")
# show_rows(connection, "PRAGMA table_info(vmType)")

# # 预览真实 VM 请求
# sql = """
# SELECT vmId, vmTypeId, priority, starttime
# FROM vm
# ORDER BY vmId
# LIMIT 5
# """
# show_rows(connection, sql)

# # 查看同一 VM 类型在不同硬件上的资源份额
# sql = """
# SELECT vmTypeId, machineId, core, memory
# FROM vmType
# WHERE vmTypeId = 0
# ORDER BY machineId
# LIMIT 5
# """
# show_rows(connection, sql)

# # 统计硬件规格，并检查组合键重复
# sql = """
# SELECT machineId, COUNT(*)
# FROM vmType
# GROUP BY machineId
# ORDER BY machineId
# """
# show_rows(connection, sql)

# sql = """
# SELECT vmTypeId, machineId, COUNT(*)
# FROM vmType
# GROUP BY vmTypeId, machineId
# HAVING COUNT(*) > 1
# """
# show_rows(connection, sql)

# print("My query:")

# sql = """
# SELECT vmTypeId, core, memory
# FROM vmType
# WHERE machineId = 0
# """
# print(sql)
# show_rows(connection, sql)

# # 练习1
# sql = """
# SELECT vmTypeId, memory
# FROM vmType
# WHERE machineId = 0
# """
# show_rows(connection, sql)

# # 练习2
# sql = """
# SELECT vmTypeId, memory
# FROM vmType
# WHERE machineId = 999
# """
# show_rows(connection, sql)

# sql = """
# SELECT vmTypeId, core, memory
# FROM vmType
# WHERE machineId = 0 AND core >= 0.5
# ORDER BY core DESC, vmTypeId ASC
# """
# show_rows(connection, sql)

# sql = """
# SELECT vmTypeId, core, memory
# FROM vmType
# WHERE machineId = 0 AND core < 0.05
# ORDER BY core DESC, vmTypeId ASC
# LIMIT 4
# """
# show_rows(connection, sql)


# 请求0 → 类型8 → 类型8在硬件0上的规格 → CPU与内存份额
sql ='''
SELECT vmId, vmTypeId
FROM vm
WHERE vmId = 0
'''
show_rows(connection, sql)

sql ='''
SELECT vmTypeId, machineId, core, memory
FROM vmType
WHERE vmTypeId = 8 AND machineId = 0
'''
show_rows(connection, sql)

sql = """
SELECT vm.vmId, vm.vmTypeId, vmType.machineId,
       vmType.core, vmType.memory
FROM vm
JOIN vmType ON vm.vmTypeId = vmType.vmTypeId
WHERE vm.vmId = 0 AND vmType.machineId = 0
"""
show_rows(connection, sql)

sql ='''
SELECT vmId, vmTypeId
FROM vm
WHERE vmId = 100
'''
show_rows(connection, sql)

sql ='''
SELECT vmTypeId, machineId, core, memory
FROM vmType
WHERE vmTypeId = 6 AND machineId = 0
'''
show_rows(connection, sql)

sql = """
SELECT vm.vmId, vm.vmTypeId, vmType.machineId,
       vmType.core, vmType.memory
FROM vm
JOIN vmType ON vm.vmTypeId = vmType.vmTypeId
WHERE vm.vmId = 100 AND vmType.machineId = 0
"""
show_rows(connection, sql)

sql = """
SELECT vm.vmId, vm.vmTypeId, vmType.machineId,
       vmType.core, vmType.memory
FROM vm
JOIN vmType ON vm.vmTypeId = vmType.vmTypeId
WHERE vm.vmId = 100 AND vmType.machineId = 1
"""
show_rows(connection, sql)

connection.close()