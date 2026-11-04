import _bootstrap  # 将项目根目录加入模块搜索路径。
from time import perf_counter

from instance_io import ROOT, load_instance
from packing_algorithms import (
    first_fit, best_fit, first_fit_decreasing,
    first_fit_decreasing_sum, best_fit_decreasing,
)
from solution_checker import check_solution


def uncached_load(host):
    # 慢速参照每次重新求和，不读取生产算法的负载缓存。
    return sum(request[3] for request in host), sum(request[4] for request in host)


def uncached_first_fit(requests):
    hosts = []
    for request in requests:
        for host in hosts:
            cpu, memory = uncached_load(host)
            if cpu + request[3] <= 1 + 1e-9 and memory + request[4] <= 1 + 1e-9:
                host.append(request)
                break
        else:
            # for循环未遇到break，说明没有现有主机可以接收。
            hosts.append([request])
    return hosts


def uncached_best_fit(requests):
    hosts = []
    for request in requests:
        best_index = None
        best_score = float("inf")
        for index, host in enumerate(hosts):
            cpu, memory = uncached_load(host)
            if cpu + request[3] <= 1 + 1e-9 and memory + request[4] <= 1 + 1e-9:
                score = (1 - cpu - request[3]) + (1 - memory - request[4])
                # 严格更小才更新，同分保留先开启的主机。
                if score < best_score:
                    best_index, best_score = index, score
        if best_index is None:
            hosts.append([request])
        else:
            hosts[best_index].append(request)
    return hosts


def uncached_decreasing(requests, algorithm, use_sum=False):
    # 独立复写排序规则：降序分数，相同时按请求ID升序。
    def key(request):
        score = request[3] + request[4] if use_sum else max(request[3], request[4])
        return -score, request[0]
    return algorithm(sorted(requests, key=key))


METHODS = [
    ("FF", first_fit, uncached_first_fit),
    ("BF", best_fit, uncached_best_fit),
    ("FFD-max", first_fit_decreasing,
     lambda requests: uncached_decreasing(requests, uncached_first_fit)),
    ("FFD-sum", first_fit_decreasing_sum,
     lambda requests: uncached_decreasing(requests, uncached_first_fit, use_sum=True)),
    ("BFD-max", best_fit_decreasing,
     lambda requests: uncached_decreasing(requests, uncached_best_fit)),
]

cases = [
    ("real_m12_w2_3_n200_prefix40", load_instance(
        ROOT / "data/instances/real_v2/real_m12_w2_3_n200.json")["requests"][:40]),
    ("real_m12_w1_2_n1000", load_instance(
        ROOT / "data/instances/real_v2/real_m12_w1_2_n1000.json")["requests"]),
]
for alpha in (10, 20, 30, 40, 50):
    instance = load_instance(ROOT / "data/instances/synthetic_alpha"
                             / f"synthetic_v2_a{alpha}_s0_n100.json")
    cases.append((instance["instance_id"], instance["requests"]))

compared = 0
for instance_id, requests in cases:
    before = list(requests)
    for name, algorithm, reference in METHODS:
        hosts = algorithm(requests)
        expected = reference(requests)
        # 核对完整分组，包括主机顺序和每台主机内的请求顺序。
        if hosts != expected:
            raise ValueError(instance_id + " / " + name + ": cached placement differs")
        if check_solution(requests, hosts) != (True, "OK") or requests != before:
            raise ValueError(instance_id + " / " + name + ": invalid or changed input")
        compared += 1
    print(instance_id, "| Matches uncached reference: True | Valid: True")

print("Compared cached / uncached placements:", compared)

# 每条请求单独放一台，用于单独测量检查器。
large = load_instance(
    ROOT
    / "data/instances/synthetic_alpha/synthetic_v2_a50_s0_n100000.json"
)["requests"]

single_hosts = [[request] for request in large]

started = perf_counter()
result = check_solution(large, single_hosts)
seconds = perf_counter() - started

if result != (True, "OK"):
    raise ValueError(str(result))

print(
    "Large checker:", len(large),
    "|", result,
    "| Seconds:", seconds,
)
