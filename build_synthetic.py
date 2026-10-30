import random
from instance_io import ROOT, write_json, load_instance
from packing_algorithms import first_fit, resource_totals
from solution_checker import check_solution

N = 80
SEEDS = [0, 1, 2]
KINDS = ["positive", "independent", "complementary"]
OUT_DIR = ROOT / "data" / "instances" / "synthetic"

for kind in KINDS:
    for seed in SEEDS:
        # 每个实例新建生成器，固定种子用于复现。
        rng = random.Random(seed)

        # 先生成全部 CPU。
        # 同一种子的三类实例因此使用相同 CPU 序列。
        cpus = []
        for i in range(N):
            cpus.append(rng.randint(8, 48) / 64)

        requests = []
        for i in range(N):
            cpu = cpus[i]

            if kind == "positive":
                memory = cpu
            elif kind == "independent":
                memory = rng.randint(8, 48) / 64
            elif kind == "complementary":
                memory = 56 / 64 - cpu
            else:
                raise ValueError("Unknown synthetic kind")

            # 类型0只是占位；i是生成顺序，不是真实Azure时间。
            requests.append((i, 0, i, cpu, memory))

        # 先验证生成的请求能形成合法方案。
        valid, message = check_solution(requests, first_fit(requests))
        if not valid:
            raise ValueError(message)

        cpu_total, memory_total = resource_totals(requests)
        instance_id = f"synthetic_{kind}_s{seed}_n{N}"

        instance = {
            "instance_id": instance_id,
            "source": "synthetic",
            "machine_id": None,
            "kind": kind,
            "seed": seed,
            "n": N,
            "field_order": ["vmId", "vmTypeId", "starttime", "core", "memory"],
            "order_by": ["vmId"],
            "model": "static_no_release",
            "capacity_cpu": 1,
            "capacity_memory": 1,
            "generator_version": 1,
            "cpu_integer_min": 8,
            "cpu_integer_max": 48,
            "denominator": 64,
            "memory_rule": kind,
            "vmTypeId_note": "0 is a placeholder, not an Azure type",
            "starttime_note": "generated order index, not elapsed days",
            "cpu_total": cpu_total,
            "memory_total": memory_total,
            "requests": requests,
        }

        path = OUT_DIR / f"{instance_id}.json"
        write_json(path, instance)

        restored = load_instance(path)
        if restored["requests"] != requests:
            raise ValueError("Saved requests changed")

        print("Saved:", path.name, "| Rows:", N, "| Same: True")