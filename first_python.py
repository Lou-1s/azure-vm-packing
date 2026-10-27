# a_cpu = 0.4
# a_memory = 0.3
# a_cpu = 0.8
# a_memory = 0.3
# a_cpu = 0.4
# a_memory = 0.7
a_cpu = 0.65
a_memory = 0.3

b_cpu = 0.35
b_memory = 0.5

cpu_total = a_cpu + b_cpu
memory_total = a_memory + b_memory

print("CPU total:", cpu_total)
print("Memory total:", memory_total)

fits = (cpu_total <= 1) and (memory_total <= 1)
print("Fits:", fits)

if fits:
    print("可以放进同一台主机")
else:
    print("不能放进同一台主机")