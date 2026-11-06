"""读取两组合成实验的现有结果，生成报告；不重新调用算法或Gurobi。"""

import argparse
import csv
import json
from statistics import mean, median

# 复用真实组报告的表格格式、方法顺序和项目路径。
from analyze_real import ROOT, METHODS, table, average, percentage, quality_table
from result_metrics import attach_reference_metrics


def read_results(directory, expected_suite):
    with (directory / "summary.csv").open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    with (directory / "metadata.json").open("r", encoding="utf-8") as file:
        metadata = json.load(file)
    if metadata["suite"] != expected_suite:
        raise ValueError("结果组别与指定目录不符")

    integer_fields = ["n", "seed", "host_count", "lower_bound", "optimum", "completed_repeats", "required_repeats",
                      "checkpoint_upper_bound", "checkpoint_lower_bound"]
    number_fields = ["alpha", "seconds", "solve_seconds", "mip_total_seconds", "upper_bound_seconds",
                     "ratio_to_bound", "gap_to_bound", "peak_private_mib"]
    for row in rows:
        for field in integer_fields:
            row[field] = int(row[field]) if row[field] != "" else None
        for field in number_fields:
            row[field] = float(row[field]) if row[field] != "" else None
        row["valid"] = row["valid"] == "True"
    # 按每个实例的MILP行重新计算参照；不把真实下界冒充MIP方案。
    attach_reference_metrics(rows)
    ids = {row["instance_id"] for row in rows}
    keys = {(row["instance_id"], row["method"]) for row in rows}
    if len(rows) != metadata["rows"] or len(ids) != metadata["instances"] or len(keys) != len(rows):
        raise ValueError("汇总不完整或存在重复结果")
    return rows, metadata


def groups(rows):
    # 先按规模，再按alpha排序。每组包含不同seed和全部方法。
    keys = sorted({(row["n"], row["alpha"]) for row in rows})
    return [(n, alpha, [row for row in rows if row["n"] == n and row["alpha"] == alpha])
            for n, alpha in keys]


def status_table(rows, methods):
    body = []
    for method in methods:
        selected = [row for row in rows if row["method"] == method]
        counts = {}
        for row in selected:
            status = row["status"]
            counts[status] = counts.get(status, 0) + 1
        valid = sum(row["valid"] for row in selected)
        complete = sum(row["status"] == "completed" for row in selected)
        # MILP没有三次重复的completed状态，另在求解表中统计证优情况。
        timing = "-" if method == "MILP" else f"{complete}/{len(selected)}"
        body.append([method, f"{valid}/{len(selected)}", timing,
                     "; ".join(f"{name}: {count}" for name, count in sorted(counts.items()))])
    return table(["方法", "有效方案/条件", "完整计时/条件", "状态与数量"], body)


def quality_by_condition(rows):
    body = []
    for n, alpha, group in groups(rows):
        cells = [n, f"{alpha:.1f}"]
        for method in METHODS:
            selected = [row for row in group if row["method"] == method and row["valid"]
                        and row["gap_to_reference"] is not None]
            proven = sum(row["reference_is_optimal"] is True for row in selected)
            unknown = len(selected) - proven
            counts = f"{proven}+{unknown}*" if unknown else str(proven)
            value = percentage(mean(row["gap_to_reference"] for row in selected)) if selected else "-"
            cells.append(f"{value} ({counts})" if selected else "-")
        body.append(cells)
    return table(["n", "alpha"] + METHODS, body)


def incomplete_conditions(rows):
    selected = [row for row in rows if row["method"] != "MILP" and row["status"] != "completed"]
    if not selected:
        return "全部启发式条件均完成规定重复。"
    body = [[row["instance_id"], row["method"], row["status"],
             "有" if row["valid"] else "无",
             f"{row['completed_repeats']}/{row['required_repeats']}"] for row in selected]
    return table(["实例", "方法", "状态", "有效首遍方案", "完成重复/规定重复"], body)


def timing_by_condition(rows):
    body = []
    for n, alpha, group in groups(rows):
        cells = [n, f"{alpha:.1f}"]
        for method in METHODS[:-1]:
            selected = [row for row in group if row["method"] == method]
            seconds = [row["seconds"] for row in selected
                       if row["status"] == "completed" and row["seconds"] is not None]
            value = f"{median(seconds):.6f}" if seconds else "-"
            cells.append(f"{value} ({len(seconds)}/{len(selected)})")
        body.append(cells)
    return table(["n", "alpha"] + METHODS[:-1], body)


def sorting_comparison(rows):
    by_instance = {}
    for row in rows:
        by_instance.setdefault(row["instance_id"], {})[row["method"]] = row
    body = []
    for n, alpha, _ in groups(rows):
        differences = []
        for methods in by_instance.values():
            maximum, total = methods["FFD-max"], methods["FFD-sum"]
            if maximum["n"] != n or maximum["alpha"] != alpha:
                continue
            if maximum["valid"] and total["valid"]:
                differences.append(total["host_count"] - maximum["host_count"])
        body.append([n, f"{alpha:.1f}", len(differences), sum(value > 0 for value in differences),
                     sum(value < 0 for value in differences), sum(value == 0 for value in differences),
                     average(differences, digits=3)])
    return table(["n", "alpha", "有效配对", "max更省", "sum更省", "相同", "平均(sum台数-max台数)"], body)


def mip_summary(rows):
    body = []
    for n, alpha, group in groups(rows):
        selected = [row for row in group if row["method"] == "MILP"]
        cutoff_opt = sum(row["checkpoint_upper_bound"] == row["checkpoint_lower_bound"] for row in selected)
        final_opt = sum(row["optimum"] is not None for row in selected)
        improved = sum(row["host_count"] < row["checkpoint_upper_bound"] for row in selected)
        saved_hosts = sum(row["checkpoint_upper_bound"] - row["host_count"] for row in selected)
        bound_improved = sum(row["lower_bound"] > row["checkpoint_lower_bound"] for row in selected)
        body.append([n, f"{alpha:.1f}", f"{cutoff_opt}/{len(selected)}", f"{final_opt}/{len(selected)}",
                     improved, saved_hosts, bound_improved,
                     f"{median(row['solve_seconds'] for row in selected):.3f}",
                     percentage(max(row["gap_to_bound"] for row in selected))])
    return table(["n", "alpha", "截止已证优", "最终已证优", "截止后改善实例", "截止后共省台数",
                  "截止后提高L实例", "优化秒数中位数", "最终最大(U-L)/L"], body)


def mip_timing(rows):
    body = []
    for n, alpha, group in groups(rows):
        selected = [row for row in group if row["method"] == "MILP"]
        body.append([n, f"{alpha:.1f}"] + [f"{median(row[field] for row in selected):.3f}" for field in
                                         ("upper_bound_seconds", "mip_total_seconds", "seconds")])
    return table(["n", "alpha", "初解外部秒数中位数", "MIP封装秒数中位数", "两者之和的中位数"], body)


def scale_quality(rows):
    body = []
    for method in METHODS[:-1]:
        selected = [row for row in rows if row["method"] == method]
        valid = [row for row in selected if row["valid"]]
        maximum = max((row["gap_to_bound"] for row in valid), default=None)
        body.append([method, f"{len(valid)}/{len(selected)}",
                     average([row["ratio_to_bound"] for row in valid]), percentage(maximum)])
    return table(["方法", "有效方案/条件", "平均A/L", "最大(A-L)/L"], body)


def scale_gap_by_condition(rows):
    body = []
    for n, alpha, group in groups(rows):
        cells = [n, f"{alpha:.1f}"]
        for method in METHODS[:-1]:
            selected = [row for row in group if row["method"] == method and row["valid"]]
            value = percentage(mean(row["gap_to_bound"] for row in selected)) if selected else "-"
            cells.append(f"{value} ({len(selected)})" if selected else "-")
        body.append(cells)
    return table(["n", "alpha"] + METHODS[:-1], body)


def memory_by_size(rows):
    body = []
    for n in sorted({row["n"] for row in rows}):
        cells = [n]
        for method in METHODS[:-1]:
            values = [row["peak_private_mib"] for row in rows if row["n"] == n and row["method"] == method
                      and row["peak_private_mib"] is not None]
            # 包含成功与失败尝试，报告采样最大值，而非声称精确内存峰值。
            cells.append(f"{max(values):.2f}" if values else "-")
        body.append(cells)
    return table(["n"] + METHODS[:-1], body)


def build_report(rows, metadata):
    quality = metadata["suite"] == "synthetic-quality"
    title = "合成质量实验分析" if quality else "合成规模实验分析"
    methods = METHODS if quality else METHODS[:-1]
    config = metadata["config"]
    parts = [f"# {title}",
             f"本批{metadata['instances']}个实例、{len(rows)}行方法结果。"
             "来源为同目录summary.csv与metadata.json；不重新求解。",
             f"启发式每次预算{config['heuristic_seconds']:g}秒；"
             + (f"MIP每实例累计优化预算{config['mip_seconds']:g}秒，截止记录点{config['snapshot_seconds']:g}秒。"
                if quality else "本组没有运行MIP。"),
             "## 1. 完成情况", status_table(rows, methods), incomplete_conditions(rows),
             "time_budget是触及算法预算，error是执行错误，具体堆栈保存在对应实例JSON的calls中。"
             "首遍成功但后续失败时，保留有效方案用于质量评价，中位耗时仍留空。"]
    if quality:
        known = {row["instance_id"] for row in rows if row["optimum"] is not None}
        parts += ["## 2. 放置质量", f"本组已证明最优{len(known)}/{metadata['instances']}个实例。",
                  quality_table(rows),
                  "已证优使用OPT，未证优使用MIP最终有效台数U作参照。"
                  "平均值先逐实例计算再汇总；包含未证优参照时标*，只表示相对MIP方案的表现，"
                  "可能低估距真正OPT的差距。达到MIP效果按A不大于MIP最终台数计数，分母保留全部实例。"
                  "MILP自比较的比值1和差距0不代表全部已证优。",
                  "### 按规模和alpha的平均差距",
                  "单元格为平均(A-OPT)/OPT或(A-U)/U；例如(3+7*)表示3个已证优、7个未证优MIP参照。"
                  "-表示没有可评价的有效方案。", quality_by_condition(rows)]
    else:
        parts += ["## 2. 相对有效下界的质量", scale_quality(rows),
                  "L是真实有效下界，不是MIP方案。A/L是A/OPT的上界，不能与质量组的A/OPT(U)混称。"
                  "各方法只统计有有效方案的实例，阅读平均值时须同时查看覆盖率。",
                  "### 按规模和alpha的平均下界差距",
                  "单元格为平均(A-L)/L，括号是有效实例数；没有方案不填0。",
                  scale_gap_by_condition(rows)]
    parts += ["## 3. 启发式耗时",
              "单位秒；单元格为中位数(完成规定重复的实例数/该条件全部实例数)。"
              "先取每实例保存的重复中位数，再取不同seed间的中位数。"
              "100000条每条件仅一个seed、每实例仅测一次，其余规模每实例测三次。"
              f"一次失败后不补跑；只比较成功条件的耗时须同时报告覆盖率，不以预算{config['heuristic_seconds']:g}秒或0填补超时。",
              timing_by_condition(rows), "## 4. FFD两种排序的配对比较",
              "同一(n,alpha,seed)配对比较台数；正差表示max更省，负差表示sum更省。",
              sorting_comparison(rows)]
    if quality:
        parts += ["## 5. MIP截止与最终结果", mip_summary(rows),
                  "截止后改善实例是上界减少的实例数，共省台数是这些差值之和；提高L表示证明推进。"
                  "提前结束使用实际截止记录，没有另跑第二次模型。真实下界始终记L。",
                  "### MIP完整流程计时", mip_timing(rows),
                  "初解时间包含七方法首遍外部尝试；封装时间包含预处理、建模、优化及恢复。"
                  "逐实例先相加再取中位数，不把两个中位数直接相加；这些时间与启发式纯函数耗时分开解释。"]
    else:
        parts += ["## 5. 采样私有内存最大值（MiB）", memory_by_size(rows),
                  "统计包含成功及失败尝试，是进程私有内存的采样最大值，不是精确峰值或Gurobi内存。"]
    parts += ["## 6. 统计解释",
              "同一(n,seed)的五个alpha共用基础数对、方向优先序和输入顺序，属于配对条件；"
              "不同seed是不同随机实例，三次计时调用不是三个质量样本。按(n,alpha)分层阅读，"
              "不把所有规模混成一个总体结论。FFD的比较仅改变排序规则，不能将有限样本性能比当作理论近似保证。"]
    return "\n\n".join(parts) + "\n"


def main(suite):
    suites = ("synthetic-quality", "synthetic-scale") if suite == "both" else (suite,)
    for name in suites:
        suffix = "quality" if name == "synthetic-quality" else "scale"
        directory = ROOT / "results" / f"formal_synthetic_{suffix}_600_1200"
        rows, metadata = read_results(directory, name)
        report = build_report(rows, metadata)
        output = directory / "analysis.md"
        # 派生报告可以重新生成；原CSV和逐实例JSON不改动。
        output.write_text(report, encoding="utf-8")
        print(name, "| Instances:", metadata["instances"], "| Rows:", len(rows))
        print("Saved:", output.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="分析已完成的两组合成实验")
    parser.add_argument("--suite", choices=("both", "synthetic-quality", "synthetic-scale"), default="both")
    main(parser.parse_args().suite)
