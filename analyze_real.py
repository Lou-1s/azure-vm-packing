import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median
from result_metrics import attach_reference_metrics


# 放到项目目录后，默认读取本项目已经保存的真实实验结果。
ROOT = Path(__file__).resolve().parent
METHODS = ["FF", "BF", "FFD-max", "FFD-sum", "BFD-max", "DP", "KK2003", "MILP"]


def read_results(results_dir):
    # utf-8-sig 同时处理普通 UTF-8 和带 BOM 的 CSV。
    with (results_dir / "summary.csv").open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    with (results_dir / "metadata.json").open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    # CSV 读出的每一格最初都是字符串；空字段保留为 None，不能当作 0。
    integer_fields = ["n", "host_count", "optimum", "lower_bound", "solver_status",
                      "checkpoint_upper_bound", "checkpoint_lower_bound"]
    number_fields = ["seconds", "solve_seconds", "mip_total_seconds", "upper_bound_seconds",
                     "ratio_to_opt", "ratio_to_bound", "gap_to_opt", "gap_to_bound",
                     "checkpoint_gap_to_bound"]
    for row in rows:
        for field in integer_fields:
            row[field] = int(row[field]) if row[field] != "" else None
        for field in number_fields:
            row[field] = float(row[field]) if row[field] != "" else None
        row["valid"] = row["valid"] == "True"

    # 旧CSV也从本实例MILP行重建新指标，不改写旧CSV和求解记录。
    attach_reference_metrics(rows)

    # metadata 记录本批计划的实例数；summary 是一实例一方法一行。
    instance_ids = {row["instance_id"] for row in rows}
    keys = {(row["instance_id"], row["method"]) for row in rows}
    if len(rows) != metadata["rows"] or len(instance_ids) != metadata["instances"]:
        raise ValueError("结果尚未完整：summary 与 metadata 的行数或实例数不同")
    if len(keys) != len(rows):
        raise ValueError("存在重复的实例与方法组合")
    if metadata["suite"] != "real":
        raise ValueError("本阶段程序用于真实组，请传入真实组的结果目录")
    return rows, metadata


def table(headers, body):
    # join 将各列连接成 Markdown 表格的一行。
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join(["---"] * len(headers)) + " |"]
    for cells in body:
        lines.append("| " + " | ".join(str(cell) for cell in cells) + " |")
    return "\n".join(lines)


def average(values, digits=6):
    # 空列表表示没有可统计的结果；用 - 显示，不能伪造为零。
    return f"{mean(values):.{digits}f}" if values else "-"


def percentage(value):
    return f"{100 * value:.4f}%" if value is not None else "-"


def quality_table(rows):
    body = []
    for method in METHODS:
        selected = [row for row in rows if row["method"] == method]
        valid = [row for row in selected if row["valid"] and row["host_count"] is not None]
        comparable = [row for row in valid if row["reference_host_count"] is not None]
        # 分母保持全部条件，无方案不能计为达到MIP最终效果。
        hits = sum(row["reaches_mip"] is True for row in selected)
        marker = "*" if any(not row["reference_is_optimal"] for row in comparable) else ""
        worst_gap = max((row["gap_to_reference"] for row in comparable), default=None)
        body.append([method, f"{len(valid)}/{len(selected)}",
                     f"{hits}/{len(selected)}",
                     average([row["ratio_to_reference"] for row in comparable]) + marker,
                     percentage(worst_gap) + marker])
    return table(["方法", "有效方案/条件", "达到MIP效果", "平均A/OPT(L)",
                  "最大已知差距"], body)


def quality_by_size(rows, sizes):
    body = []
    for n in sizes:
        cells = [n]
        for method in METHODS:
            selected = [row for row in rows if row["n"] == n and row["method"] == method
                        and row["valid"] and row["gap_to_reference"] is not None]
            gaps = [row["gap_to_reference"] for row in selected]
            proven = sum(row["reference_is_optimal"] is True for row in selected)
            unproven = len(selected) - proven
            counts = f"{proven}+{unproven}*" if unproven else str(proven)
            cells.append(f"{percentage(mean(gaps))} ({counts})" if gaps else "-")
        body.append(cells)
    return table(["n"] + METHODS, body)


def timing_by_size(rows, sizes):
    body = []
    for n in sizes:
        cells = [n]
        for method in METHODS[:-1]:
            selected = [row for row in rows if row["n"] == n and row["method"] == method]
            # 只统计规定重复全部成功的条件。超时行的 seconds 为空，不把 60 填进去。
            seconds = [row["seconds"] for row in selected
                       if row["status"] == "completed" and row["seconds"] is not None]
            value = f"{median(seconds):.6f}" if seconds else "-"
            cells.append(f"{value} ({len(seconds)}/{len(selected)})")
        body.append(cells)
    return table(["n"] + METHODS[:-1], body)


def sorting_comparison(rows, sizes):
    # 将同一实例的记录放在同一个字典里，保证 max 与 sum 是配对比较。
    by_instance = {}
    for row in rows:
        by_instance.setdefault(row["instance_id"], {})[row["method"]] = row

    body = []
    for n in sizes:
        differences = []
        for methods in by_instance.values():
            max_row, sum_row = methods["FFD-max"], methods["FFD-sum"]
            if max_row["n"] != n or not max_row["valid"] or not sum_row["valid"]:
                continue
            # 正值表示 max 比 sum 省主机；负值表示 sum 更省。
            differences.append(sum_row["host_count"] - max_row["host_count"])
        body.append([n, len(differences), sum(value > 0 for value in differences),
                     sum(value < 0 for value in differences), sum(value == 0 for value in differences),
                     average(differences, digits=3)])
    return table(["n", "有效配对", "max更省", "sum更省", "相同", "平均(sum台数-max台数)"], body)


def mip_tables(rows, sizes):
    mip_rows = [row for row in rows if row["method"] == "MILP"]
    initial_counts = {}
    for row in rows:
        if row["method"] != "MILP" and row["valid"]:
            key = row["instance_id"]
            count = row["host_count"]
            initial_counts[key] = min(initial_counts.get(key, count), count)
    summary = []
    for n in sizes:
        selected = [row for row in mip_rows if row["n"] == n]
        cutoff_opt = sum(row["checkpoint_upper_bound"] == row["checkpoint_lower_bound"]
                         for row in selected)
        final_opt = sum(row["optimum"] is not None for row in selected)
        improved = sum(row["host_count"] < initial_counts[row["instance_id"]] for row in selected)
        fewer_hosts = sum(row["host_count"] < row["checkpoint_upper_bound"] for row in selected)
        stronger_bound = sum(row["lower_bound"] > row["checkpoint_lower_bound"] for row in selected)
        summary.append([n, len(selected), cutoff_opt, final_opt, improved, fewer_hosts, stronger_bound,
                        f"{median(row['solve_seconds'] for row in selected):.3f}",
                        percentage(max(row["gap_to_bound"] for row in selected))])

    timing = []
    for n in sizes:
        selected = [row for row in mip_rows if row["n"] == n]
        timing.append([n] + [f"{median(row[field] for row in selected):.3f}" for field in
                            ("upper_bound_seconds", "mip_total_seconds", "seconds")])

    # 这里直接使用保存的状态码，不必导入或启动 Gurobi。
    status_names = {2: "OPTIMAL", 9: "TIME_LIMIT", 17: "MEM_LIMIT"}
    details = []
    # 数字 n 作为第一排序条件，避免把 100000 排在 200 前面。
    for row in sorted(mip_rows, key=lambda item: (item["n"], item["instance_id"])):
        details.append([row["instance_id"], initial_counts[row["instance_id"]],
                        row["checkpoint_upper_bound"], row["checkpoint_lower_bound"],
                        row["host_count"], row["lower_bound"],
                        row["optimum"] if row["optimum"] is not None else "-",
                        percentage(row["gap_to_bound"]), f"{row['solve_seconds']:.3f}",
                        status_names.get(row["solver_status"], str(row["solver_status"]))])

    return (table(["n", "实例数", "截止已证优", "最终已证优", "相比初值减少台数", "截止后减少台数", "截止后提高下界",
                   "优化秒数中位数", "最终最大(U-LB)/LB"], summary),
            table(["n", "初解外部秒数中位数", "MIP封装秒数中位数", "两者之和的中位数"], timing),
            table(["实例", "初始U", "截止U", "截止LB", "最终U", "最终LB", "OPT", "最终(U-LB)/LB", "优化秒数", "求解状态"], details))


def build_report(rows, metadata):
    sizes = sorted({row["n"] for row in rows})
    known_ids = {row["instance_id"] for row in rows if row["optimum"] is not None}
    statuses = []
    for method in METHODS:
        counts = {}
        for row in rows:
            if row["method"] == method:
                status = row["status"]
                counts[status] = counts.get(status, 0) + 1
        statuses.append([method, "; ".join(f"{name}: {count}" for name, count in sorted(counts.items()))])

    mip_summary, mip_timing, mip_details = mip_tables(rows, sizes)
    target = metadata["config"]["snapshot_seconds"]
    heuristic_budget = metadata["config"]["heuristic_seconds"]
    mip_budget = metadata["config"]["mip_seconds"]
    parts = [
        "# 真实数据实验分析",
        f"本批{metadata['instances']}个实例、{len(rows)}行方法结果；其中{len(known_ids)}个实例已证最优。"
        "来源为同目录的summary.csv与metadata.json。",
        f"本批实际预算：启发式每次{heuristic_budget:g}秒，MIP每实例累计优化{mip_budget:g}秒。"
        "报告使用这批实际保存的结果；修改程序默认预算不会追溯改变历史测量。",
        "## 1. 完成情况",
        table(["方法", "状态与数量"], statuses),
        "time_budget表示该次启发式调用触及算法预算。solver_stopped表示MIP停止时未证优；"
        "具体求解器状态见第5节逐实例表。TIME_LIMIT(9)为时间限制，MEM_LIMIT(17)为软内存限制，"
        f"后者可在{mip_budget:g}秒前结束。两种停止状态本身均不提供最优证明。"
        "[Gurobi状态说明](https://docs.gurobi.com/projects/optimizer/en/current/reference/numericcodes/statuscodes.html)",
        "## 2. 放置质量",
        quality_table(rows),
        "A为有效方案台数。已证优时参照值为OPT；未证优时按约定记L，表示MIP最终有效方案台数，"
        "它是可行解上界。真实已证下界在第5节记为LB，内部lower_bound字段含义保持不变。"
        "平均A/OPT(L)逐实例计算比值再取算术平均；最大已知差距使用相同参照计算(A-OPT)/OPT或(A-L)/L。",
        "达到MIP效果统计A不大于本实例MIP最终台数的数量，分母为全部条件；无有效方案计为未达到。"
        "星号*表示该统计包含未证优的MIP参照，带星差距仅表示相对MIP方案的差距，可能低估距真正OPT的差距。"
        "MILP与自身比较天然达到相同效果，平均比值为1、差距为0，这不代表全部证优。"
        "不同有效子集的均值须结合有效覆盖阅读。",
        "### 按规模的平均差距",
        "单元格先逐实例计算(A-OPT)/OPT或(A-L)/L，再取平均。"
        "例如xxx% (3+2*)表示3个已证优参照与2个未证优MIP参照。"
        "括号只统计有有效方案的实例，-表示没有有效方案，不能伪造差距为0。",
        quality_by_size(rows, sizes),
        "## 3. 启发式耗时",
        "单元格单位为秒，括号为完成规定重复的实例数/该规模实例数。"
        "先使用每实例已保存的重复测量中位数，再取六个窗口之间的中位数。"
        f"n=100000每实例只测一次。未完成条件不填0，也不以预算{heuristic_budget:g}秒代替实际完成耗时；"
        "只比较成功条件的时间须同时查看覆盖率。",
        timing_by_size(rows, sizes),
        "## 4. FFD的排序对照",
        "同一实例比较FFD-max与FFD-sum的主机数；两者仅改变排序分数，不需要已知OPT。",
        sorting_comparison(rows, sizes),
        "## 5. MIP的截止与最终状态",
        f"截止目标为累计优化{target:g}秒。提前证优使用提前结束状态；跨过目标时保留目标前已观测的状态。"
        "优化时间不含初解、预处理和建模。",
        mip_summary,
        "减少台数表示找到了更好的有效方案；提高下界表示缩小了最优值的可能范围。"
        "两者都能缩小差距。初始U取本实例七方法有效首遍方案中的最少台数；"
        "表中减少台数的汇总列统计受改善的实例数量。最终仍未证优时，以[ LB, U ]和(U-LB)/LB报告。"
        "此处LB始终是真实下界，与第2节未证优MIP参照L含义不同。",
        "### MIP完整流程计时",
        mip_timing,
        "初解外部时间包括七种方法首遍尝试的进程启动、读取、检查及失败尝试。"
        "MIP封装时间包括预处理、建模和优化。逐实例先把二者相加再取中位数，"
        "不把两个中位数相加。上述流程耗时与启发式纯函数耗时含义不同。",
        "### MIP逐实例明细",
        mip_details,
        "## 6. 解释范围",
        "六个窗口是六组工作负载；同窗口不同n为嵌套前缀，不能当作30个独立随机样本。"
        "每实例的三次调用是计时重复，不是新增质量样本。当前报告仅描述真实组；"
        "整体算法结论需结合随后完成的合成质量和规模实验。",
    ]
    return "\n\n".join(parts) + "\n"


def main(args):
    rows, metadata = read_results(args.results_dir)
    report = build_report(rows, metadata)
    output = args.output or args.results_dir / "analysis.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    # 只写派生报告；summary.csv和求解结果JSON保持原样。
    output.write_text(report, encoding="utf-8")
    print(report)
    print("Saved:", output.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="分析已经完成的真实数据组，不重新运行算法或MIP")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results/formal_real_600_1200")
    parser.add_argument("--output", type=Path)
    main(parser.parse_args())
