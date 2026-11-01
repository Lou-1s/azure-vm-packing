import math
import random

from instance_io import ROOT, write_json, load_instance


GENERATOR_VERSION = 2
INSTANCE_DIR = ROOT / "data" / "instances" / "synthetic_alpha"
ALPHAS = (0.1, 0.2, 0.3, 0.4, 0.5)

# 每项为：(请求数、种子范围、实验用途)。
MATRIX = (
    [(n, range(10), "quality") for n in (100, 200, 500, 1000)]
    + [(n, range(3), "scale") for n in (5000, 10000, 20000)]
    + [(100000, range(1), "stress")]
)


def stream_seed(n, seed, purpose):
    # 不包含alpha：同一(n,seed)的五个alpha共享基础样本。
    return f"alpha_v{GENERATOR_VERSION}|n={n}|seed={seed}|{purpose}"


def generate_base(n, seed):
    # 分别控制资源取值与偏重方向。random可以直接使用字符串seed
    value_rng = random.Random(stream_seed(n, seed, "values"))
    direction_rng = random.Random(stream_seed(n, seed, "directions"))

    pairs = []
    while len(pairs) < n:
        u = value_rng.random()  # 返回[0,1)内的浮点数。
        v = value_rng.random()

        if u == 0 or v == 0 or u == v:
            continue  # 跳过本轮，重新采样。

        # 只排序当前这一对，保证0 < low < high < 1。
        pairs.append((min(u, v), max(u, v)))

    direction_order = list(range(n))
    direction_rng.shuffle(direction_order)  # 原地打乱编号。
    return pairs, direction_order


def make_instance(pairs, direction_order, alpha, seed, experiment_group):
    n = len(pairs)
    memory_count = round(alpha * n)  # 本矩阵所有n均为10的倍数。
    memory_ids = set(direction_order[:memory_count])

    requests = []
    for vm_id, (low, high) in enumerate(pairs):
        if vm_id in memory_ids:
            cpu, memory = low, high
        else:
            cpu, memory = high, low

        # 类型-1为合成占位；第三项表示生成顺序，不代表真实日期。
        requests.append((vm_id, -1, vm_id, cpu, memory))

    # 文件名a10表示alpha=0.10，即内存偏重占10%。
    alpha_percent = round(alpha * 100)
    instance_id = (
        f"synthetic_v{GENERATOR_VERSION}_a{alpha_percent:02d}"
        f"_s{seed}_n{n}"
    )

    # 条件成立时为True，参与sum时按1计算。
    cpu_heavy = sum(request[3] > request[4] for request in requests)
    memory_heavy = sum(request[4] > request[3] for request in requests)
    equal_count = sum(request[3] == request[4] for request in requests)

    if memory_heavy != memory_count or equal_count != 0:  #我们前面要求了没有equal_count的情况
        raise ValueError("Unexpected request directions")

    return {
        "instance_id": instance_id,
        "source": "synthetic",
        "kind": "uniform_pairs_alpha",
        "generator_version": GENERATOR_VERSION,
        "experiment_group": experiment_group,
        "n": n,
        "alpha": alpha,
        "seed": seed,
        "random_streams": {
            "values": stream_seed(n, seed, "values"),
            "directions": stream_seed(n, seed, "directions"),
        },
        "machine_id": None,
        "capacity": {"cpu": 1, "memory": 1},
        "field_order": ["vmId", "vmTypeId", "starttime", "core", "memory"],
        "order_by": ["vmId"],
        "time_unit": "synthetic_order_index",
        "model": "static_no_release",
        "cpu_total": math.fsum(request[3] for request in requests),
        "memory_total": math.fsum(request[4] for request in requests),
        "cpu_heavy": cpu_heavy,
        "memory_heavy": memory_heavy,
        "equal": equal_count,
        "requests": requests,
    }


def main():
    saved_counts = {"quality": 0, "scale": 0, "stress": 0}
    print("N | Seed | Alpha | CPU>Memory | Memory>CPU | Equal | Same")

    for n, seeds, experiment_group in MATRIX:
        for seed in seeds:
            # 放在alpha循环外，五个alpha共用基础对和方向优先序。
            pairs, direction_order = generate_base(n, seed)

            for alpha in ALPHAS:
                instance = make_instance(
                    pairs, direction_order, alpha, seed, experiment_group
                )
                path = INSTANCE_DIR / f"{instance['instance_id']}.json"
                write_json(path, instance)

                # 读回后比较整份数据，包括请求数值和顺序。
                restored = load_instance(path)
                if restored != instance:
                    raise ValueError("Saved instance changed")

                saved_counts[experiment_group] += 1
                print(
                    n, seed, alpha, instance["cpu_heavy"],
                    instance["memory_heavy"], instance["equal"], True,
                    sep=" | ",
                )

    print("Saved by group:", saved_counts)
    print("Total instances:", sum(saved_counts.values()))


if __name__ == "__main__":
    main()  # 直接运行时生成；被其他文件import时不自动生成。