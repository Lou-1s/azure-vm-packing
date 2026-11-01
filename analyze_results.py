import csv

from instance_io import RESULT_DIR

# 固定展示顺序；某组没有运行的方法显示为 -。
METHODS = ["FF", "BF", "FFD-max", "BFD", "DP", "FFD-sum", "MILP"]


def read_results(filename):
    path = RESULT_DIR / filename

    # utf-8-sig 与之前保存 CSV 时的编码对应。
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        # DictReader 根据表头，把每行读成一个字典。
        # list 取出全部数据，关闭文件后仍可使用。
        rows = list(csv.DictReader(file))

    return rows


def show_comparison(rows):
    # 收集实例编号，每个编号只保留一次。
    instance_ids = []
    for row in rows:
        if row["instance_id"] not in instance_ids:
            instance_ids.append(row["instance_id"])

    # join 把多个字符串用指定分隔符连接起来。
    print("Instance | " + " | ".join(METHODS))

    for instance_id in instance_ids:
        # 保存当前实例的“方法名 → 主机数”。
        counts = {}

        for row in rows:
            if row["instance_id"] == instance_id:
                counts[row["method"]] = row["host_count"]

        values = []
        for method in METHODS:
            # 找到方法就取主机数；没有这个方法就返回 "-"。
            values.append(counts.get(method, "-"))

        print(instance_id + " | " + " | ".join(values))


def show_optimal_hits(rows):
    for method in METHODS:
        known = 0
        hits = 0

        for row in rows:
            if row["method"] != method:
                # 跳过其他方法，继续检查下一行。
                continue

            if row["gap_to_opt"] == "":
                # 空字段表示没有已知最优差距，不参加统计。
                continue

            known += 1

            # CSV 读出的数值也是字符串，需要转成数字再比较。
            if float(row["gap_to_opt"]) == 0:
                hits += 1

        if known > 0:
            print(f"{method}: {hits}/{known}")


for filename in ("small_real.csv", "large_real.csv"):
    print("\n" + filename)

    rows = read_results(filename)
    show_comparison(rows)

    print("Reached known optimum:")
    show_optimal_hits(rows)
