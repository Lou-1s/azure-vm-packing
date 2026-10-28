# 每台主机的 CPU、内存容量分别记为 1；下面的数值是请求的容量份额。
# 以 # 开头的行是注释，不执行；这些旧数值保留给改参数练习。
# a_cpu = 0.4
# a_memory = 0.3
# a_cpu = 0.8
# a_memory = 0.3
# a_cpu = 0.4
# a_memory = 0.7
# = 把右侧的值赋给左侧变量；后面重新赋值会覆盖旧值。
a_cpu = 0.65
a_memory = 0.3

b_cpu = 0.35
b_memory = 0.5

# 这里计算并保存当前的和；以后改变 a_cpu 不会自动重算 cpu_total。
cpu_total = a_cpu + b_cpu
memory_total = a_memory + b_memory

# print 同时输出说明文字与变量当前的值。
print("CPU total:", cpu_total)
print("Memory total:", memory_total)

# <= 表示小于或等于；and 要求两个条件都成立，结果是 True 或 False。
fits = (cpu_total <= 1) and (memory_total <= 1)
print("Fits:", fits)

# if 条件为真时执行缩进内的语句，否则执行 else 内的语句。
if fits:
    print("可以放进同一台主机")
else:
    print("不能放进同一台主机")
