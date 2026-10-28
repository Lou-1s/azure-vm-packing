# 赋值保存的是当时算出的结果，不会建立一个自动更新的公式。
a_cpu = 0.4
b_cpu = 0.35
cpu_total = a_cpu + b_cpu

# a_cpu 改变后，cpu_total 仍保留先前的 0.75。
a_cpu = 0.8
print(a_cpu, cpu_total)

# 再执行一次加法，才会用当前的 a_cpu 重算 cpu_total。
cpu_total = a_cpu + b_cpu
print(a_cpu, cpu_total)

# [] 是列表；每个 (CPU, 内存) 是一个二元组，列表中保存三条请求。
vms = [
    (0.4, 0.3),
    (0.35, 0.5),
    (0.2, 0.1),
]

print(vms)
# 索引从 0 开始：vms[0] 是第一条请求，vms[0][1] 是它的内存份额。
print(vms[0])
print(vms[0][1])
print(vms[2][0])

cpu_total = 0
memory_total = 0

# for 依次取出每条请求；每轮把当前请求的资源加到累计值上。
for vm in vms:
    cpu_total = cpu_total + vm[0]
    memory_total = memory_total + vm[1]

fits = (cpu_total <= 1) and (memory_total <= 1)

print("CPU total:", cpu_total)
print("Memory total:", memory_total)
print("Fits:", fits)

# def 定义函数；调用时传入请求列表，返回 (CPU 总和, 内存总和)。
def resource_totals(requests):
    # 每次调用都从 0 开始；这些变量属于函数内部。
    cpu_total = 0
    memory_total = 0

    for vm in requests:
        cpu_total = cpu_total + vm[0]
        memory_total = memory_total + vm[1]

    # return 把两个结果作为元组交回调用处，并结束本次函数调用。
    return cpu_total, memory_total

# 用两个变量分别接收返回元组中的两项，这叫拆包。
cpu_total, memory_total = resource_totals(vms)
print(cpu_total, memory_total)

def can_share_one_host(requests):
    # 接住当前 requests 的计算结果，不依赖函数外面的同名累计变量。
    # 不要把 resource_totals 当作左侧变量名，否则会遮住要调用的函数名。
    resource_total = (resource_totals(requests))
    fits = (resource_total[0] <= 1) and (resource_total[1] <= 1)

    return fits 

print(can_share_one_host(vms))

# 列表里还可以放列表；每个 case 是一组独立的请求。
cases = [
    [(0.4, 0.3), (0.35, 0.5), (0.2, 0.1)],
    [(0.6, 0.2), (0.5, 0.2)],
    [(0.2, 0.7), (0.2, 0.4)],
    [(0.65, 0.3), (0.35, 0.5)],
    [],
]

# 同一个函数依次处理不同输入，便于检查 CPU 超限、内存超限和空列表。
for case in cases:
    print(resource_totals(case))
    print(can_share_one_host(case))

# 改变函数外的变量不会改变 can_share_one_host 内部接收的计算结果。
cpu_total = 99
memory_total = 99
print(can_share_one_host([(0.2, 0.2)]))
