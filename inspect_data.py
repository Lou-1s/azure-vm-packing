# sqlite3 是 Python 自带的 SQLite 数据库模块，无需另外安装。
import sqlite3
# machineId 硬件规格；vmTypeId 类型编号

def show_rows(connection, sql):
    # connection 是已打开的连接，sql 是要执行的 SQL 字符串。
    # execute 把 SQL 交给数据库，返回可用于读取结果的游标 cursor。
    cursor = connection.execute(sql)
    # fetchall() 取出游标中尚未读取的全部结果，得到“列表中的元组”。
    rows = cursor.fetchall()
    # 每个元组是一行；各项顺序与 SELECT 里的字段顺序一致。
    print("Rows:", len(rows))
    for row in rows:
        print(row)

# mode=ro 以只读方式打开现有文件，避免误写或误建空数据库。
database = "file:D:/PythonProjects/azure-vm-packing/data/raw/packing_trace_zone_a_v1.sqlite?mode=ro"
# uri=True 表示按带选项的文件地址解析上面的字符串。
connection = sqlite3.connect(database, uri=True)

# sqlite_master 记录数据库结构；筛选表对象后，按名称升序列出实际表名。
sql = "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
show_rows(connection, sql)

# PRAGMA table_info(表名) 查看字段；返回行的 [1] 是字段名，[2] 是类型。
# 以下练习暂时注释掉，需要时可选择对应代码按 Ctrl+/ 恢复。
# print("Columns of vm:")
# show_rows(connection, "PRAGMA table_info(vm)")

# print("Columns of vmType:")
# show_rows(connection, "PRAGMA table_info(vmType)")

# SELECT 选字段，FROM 指定表，ORDER BY 排序，LIMIT 限制返回行数。
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

# GROUP BY 按相同值分组，COUNT(*) 计算每组行数；HAVING 筛选分组结果。
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

# WHERE 筛选行，AND 要求条件同时成立；DESC 降序，ASC 升序。
# 多个排序条件依次比较：先按 core 降序，同值时按 vmTypeId 升序。
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
# 三引号包住的多行内容是 SQL 字符串；print(sql) 只打印文本，不执行查询。
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

# JOIN ... ON 用相同 vmTypeId 关联两张表；表名.字段名说明字段来自哪里。
# 再固定 machineId，才能读到该类型在指定候选硬件上的容量份额。
sql = """
SELECT vm.vmId, vm.vmTypeId, vmType.machineId,
       vmType.core, vmType.memory
FROM vm
JOIN vmType ON vm.vmTypeId = vmType.vmTypeId
WHERE vm.vmId = 0 AND vmType.machineId = 0
"""
show_rows(connection, sql)

# 改筛选值为 100，重复“先查请求类型，再查硬件资源”的过程。
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

# 如果类型与硬件组合在目录中不存在，JOIN 查询会返回 0 行。
sql = """
SELECT vm.vmId, vm.vmTypeId, vmType.machineId,
       vmType.core, vmType.memory
FROM vm
JOIN vmType ON vm.vmTypeId = vmType.vmTypeId
WHERE vm.vmId = 100 AND vmType.machineId = 1
"""
show_rows(connection, sql)

# 全部查询结束后关闭连接；关闭后不能继续用它执行 SQL。
connection.close()
