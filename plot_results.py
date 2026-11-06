"""从三组已保存结果生成六张实验图，不调用算法或求解器。"""

import argparse
import json
import platform
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from statistics import mean, median

import matplotlib
matplotlib.use("Agg")  # 使用文件绘图后台，不弹出窗口；必须写在导入pyplot之前。
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

import analyze_real
import analyze_synthetic
from instance_io import ROOT


METHODS = analyze_real.METHODS[:-1]  # 图中的启发式不包括MILP自比较行。
COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#555555"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X"]
# dash元组依次给出画线与留空的长度；每种方法用不同虚线，保留颜色和点形状。
LINESTYLES = [(0, (6, 2)), (0, (2, 2)), (0, (6, 2, 1.2, 2)),
              (0, (6, 2, 1.2, 2, 1.2, 2)), (0, (8, 2, 2, 2)),
              (0, (1, 1.5)), (0, (8, 2, 1.2, 2, 1.2, 2, 1.2, 2))]
STYLE = {name: {"color": color, "marker": marker, "linestyle": linestyle,
                "linewidth": 1.7, "markersize": 5}
         for name, color, marker, linestyle in zip(METHODS, COLORS, MARKERS, LINESTYLES)}


def select(rows, method, **conditions):
    # **conditions将n=1000、alpha=0.3等关键字收成字典。
    return [row for row in rows if row["method"] == method
            and all(row[key] == value for key, value in conditions.items())]


def quality_point(rows, use_bound=False):
    field = "gap_to_bound" if use_bound else "gap_to_reference"
    valid = [row for row in rows if row["valid"] and row[field] is not None]
    return {"gap_percent": 100 * mean(row[field] for row in valid) if valid else None,
            "valid": len(valid), "total": len(rows),
            "unproven_references": None if use_bound else sum(not row["reference_is_optimal"] for row in valid)}


def time_point(rows):
    seconds = [row["seconds"] for row in rows if row["status"] == "completed" and row["seconds"] is not None]
    return {"seconds": median(seconds) if seconds else None,
            "completed": len(seconds), "total": len(rows),
            "timeouts": sum(row["status"] == "time_budget" for row in rows),
            "errors": sum(row["status"] == "error" for row in rows)}


def number_or_nan(value):
    # 缺失值画成断线；不能把超时画成0秒或600秒完成。
    return float("nan") if value is None else value


def style_axis(ax):
    ax.grid(axis="y", color="#dddddd", linewidth=.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)


def legend(fig, bottom=.025):
    handles = [Line2D([], [], label=name, **STYLE[name]) for name in METHODS]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, bottom),
               ncol=7, frameon=False, fontsize=9, handlelength=4)


def size_axis(ax, sizes, labels=None):
    ax.set_xscale("log")
    ax.set_xticks(sizes, labels or [f"{n:,}" for n in sizes])
    ax.minorticks_off()
    ax.set_xlabel("Requests (n)")


def save_figure(fig, output_dir, stem):
    # PNG便于直接查看，PDF保存矢量线条，便于文档和演示排版。
    for suffix in ("png", "pdf"):
        fig.savefig(output_dir / f"{stem}.{suffix}", dpi=180, facecolor="white")
    plt.close(fig)
    print("Saved:", stem + ".png / .pdf")


def real_quality(rows, output_dir, data):
    sizes = sorted({row["n"] for row in rows})
    fig, ax = plt.subplots(figsize=(10.6, 5.5))
    points = {method: [quality_point(select(rows, method, n=n)) for n in sizes] for method in METHODS}
    for method in METHODS:
        ax.plot(sizes, [number_or_nan(point["gap_percent"]) for point in points[method]], **STYLE[method])
    # 星号按该规模是否含未证优参照决定，不把MIP方案冒充OPT。
    uncertain = [any(row["optimum"] is None for row in select(rows, "MILP", n=n)) for n in sizes]
    size_axis(ax, sizes, [f"{n:,}" + ("*" if star else "") for n, star in zip(sizes, uncertain)])
    ax.set_ylabel("Mean gap to reference R (%)")
    ax.set_title("Real trace: placement quality", loc="left", fontweight="bold")
    ax.set_ylim(bottom=0)
    style_axis(ax)
    fig.subplots_adjust(left=.09, right=.98, top=.90, bottom=.28)
    legend(fig, .10)
    fig.text(.09, .025, "R = proven OPT, otherwise final MIP upper bound U. * includes unproven references.\n"
             "Six windows per n; DP has no valid n=100,000 result. Values are sample means, not approximation guarantees.", fontsize=8.5)
    data["01_real_quality"] = {"sizes": sizes, "points": points}
    save_figure(fig, output_dir, "01_real_quality")


def synthetic_quality(rows, output_dir, data):
    sizes = sorted({row["n"] for row in rows})
    alphas = sorted({row["alpha"] for row in rows})
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.0), sharey=True)
    saved = {}
    for ax, n in zip(axes.flat, sizes):
        points = {method: [quality_point(select(rows, method, n=n, alpha=a)) for a in alphas]
                  for method in METHODS}
        for method in METHODS:
            ax.plot(alphas, [number_or_nan(point["gap_percent"]) for point in points[method]], **STYLE[method])
        uncertain = [any(row["optimum"] is None for row in select(rows, "MILP", n=n, alpha=a)) for a in alphas]
        ax.set_xticks(alphas, [f"{a:.1f}" + ("*" if star else "") for a, star in zip(alphas, uncertain)])
        ax.set_xlabel("Memory-heavy fraction (alpha)")
        ax.set_title(f"n = {n:,}", loc="left", fontsize=11)
        style_axis(ax)
        saved[str(n)] = points
    # 共享纵轴统一取全部子图的最大值，避免首个子图锁定范围后裁掉后续数据。
    maximum = max(point["gap_percent"] for points in saved.values()
                  for line in points.values() for point in line if point["gap_percent"] is not None)
    axes[0, 0].set_ylim(0, maximum * 1.08)
    for ax in axes[:, 0]:
        ax.set_ylabel("Mean gap to reference R (%)")
    fig.suptitle("Synthetic quality: resource balance and placement", x=.08, ha="left", fontweight="bold")
    fig.subplots_adjust(left=.08, right=.98, top=.91, bottom=.20, wspace=.13, hspace=.35)
    legend(fig, .075)
    fig.text(.08, .025, "Ten seeds per (n, alpha). R = proven OPT or final MIP upper bound U; * includes unproven references.\n"
             "The five alpha settings share base pairs within each (n, seed). Starred gaps can underestimate gaps to OPT.", fontsize=8.5)
    data["02_synthetic_quality"] = {"alphas": alphas, "points_by_n": saved}
    save_figure(fig, output_dir, "02_synthetic_quality")


def runtime_comparison(real, scale, configs, output_dir, data):
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.7))
    saved = {}
    for ax, rows, name in zip(axes, (real, scale), ("Real trace", "Synthetic scale")):
        sizes = sorted({row["n"] for row in rows})
        budget = configs[name]["heuristic_seconds"]
        points = {method: [time_point(select(rows, method, n=n)) for n in sizes] for method in METHODS}
        for method in METHODS:
            ax.plot(sizes, [number_or_nan(point["seconds"]) for point in points[method]], **STYLE[method])
            for n, point in zip(sizes, points[method]):
                if point["completed"] == 0 and point["timeouts"] == point["total"]:
                    # 空心三角独立于曲线，表示预算处被截断，并非完成时间。
                    ax.scatter([n], [budget], marker="^", s=72, facecolors="none", edgecolors=STYLE[method]["color"], linewidths=1.7)
                    ax.text(.02, .96, f"{method}: {point['timeouts']}/{point['total']} timeout",
                            transform=ax.transAxes, va="top", fontsize=8)
        ax.axhline(budget, color="#999999", linestyle=":", linewidth=1)
        ax.set_yscale("log")
        size_axis(ax, sizes, [f"{n/1000:g}k" if n >= 1000 else str(n) for n in sizes])
        ax.set_title(name, loc="left", fontweight="bold")
        ax.set_ylabel("Median algorithm time (seconds, log scale)")
        ax.set_ylim(top=budget * 2)
        style_axis(ax)
        saved[name] = {"sizes": sizes, "points": points, "algorithm_budget": budget}
    fig.subplots_adjust(left=.08, right=.98, top=.91, bottom=.28, wspace=.22)
    legend(fig, .10)
    fig.text(.08, .025, "Medians use only conditions completing all prescribed repetitions; coverage is shown in Figure 04.\n"
             "Hollow triangles mark the time budget, not completion times. At n=100,000 each instance was measured once.", fontsize=8.5)
    data["03_runtime"] = saved
    save_figure(fig, output_dir, "03_runtime")


def timing_coverage(real, scale, output_dir, data):
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.1))
    saved = {}
    for ax, rows, name in zip(axes, (real, scale), ("Real trace", "Synthetic scale")):
        sizes = sorted({row["n"] for row in rows})
        points = [[time_point(select(rows, method, n=n)) for n in sizes] for method in METHODS]
        rates = [[100 * point["completed"] / point["total"] for point in line] for line in points]
        im = ax.imshow(rates, vmin=0, vmax=100, cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(sizes)), [f"{n:,}" for n in sizes])
        ax.set_yticks(range(len(METHODS)), METHODS)
        ax.set_title(name, loc="left", fontweight="bold")
        ax.set_xlabel("Requests (n)")
        for i, line in enumerate(points):
            for j, point in enumerate(line):
                marker = "!" if point["errors"] else ""
                label = f"{point['completed']}/{point['total']}{marker}"
                ax.text(j, i, label, ha="center", va="center", fontsize=9,
                        color="white" if rates[i][j] >= 65 else "black")
        saved[name] = {"sizes": sizes, "points": dict(zip(METHODS, points))}
    fig.subplots_adjust(left=.09, right=.98, top=.88, bottom=.31, wspace=.25)
    color_axis = fig.add_axes([.30, .195, .40, .025])
    fig.colorbar(im, cax=color_axis, orientation="horizontal", label="Full timing coverage (%)")
    fig.text(.09, .065, "Cells = conditions completing prescribed repetitions / all conditions.\n"
             "! BF at n=10,000: one third repetition hit a temporary-file access error; its first valid placement is retained.", fontsize=8.5)
    data["04_timing_coverage"] = saved
    save_figure(fig, output_dir, "04_timing_coverage")


def scale_quality(rows, output_dir, data):
    sizes = sorted({row["n"] for row in rows})
    fig, ax = plt.subplots(figsize=(10.6, 5.5))
    points = {method: [quality_point(select(rows, method, n=n), use_bound=True) for n in sizes]
              for method in METHODS}
    for method in METHODS:
        ax.plot(sizes, [number_or_nan(point["gap_percent"]) for point in points[method]], **STYLE[method])
    size_axis(ax, sizes)
    ax.set_ylabel("Mean gap to valid lower bound L (%)")
    ax.set_title("Synthetic scale: quality relative to a lower bound", loc="left", fontweight="bold")
    ax.set_ylim(bottom=0)
    style_axis(ax)
    fig.subplots_adjust(left=.09, right=.98, top=.90, bottom=.28)
    legend(fig, .10)
    fig.text(.09, .025, "No MIP was run here. (A-L)/L is an upper bound on the true optimality gap.\n"
             "15 instances per n below 100,000; 5 at n=100,000. DP has no valid 100,000-request placement.", fontsize=8.5)
    data["05_scale_quality"] = {"sizes": sizes, "points": points}
    save_figure(fig, output_dir, "05_scale_quality")


def proof_point(rows):
    return {"total": len(rows),
            "at_checkpoint": sum(row["checkpoint_upper_bound"] == row["checkpoint_lower_bound"] for row in rows),
            "at_end": sum(row["optimum"] is not None for row in rows)}


def mip_coverage(real, quality, output_dir, data):
    fig, axes = plt.subplots(1, 3, figsize=(15.6, 5.2), sharey=True)
    saved = {}
    specifications = [(real, "n", "Real trace: by size"),
                      (quality, "n", "Synthetic quality: by size"),
                      (quality, "alpha", "Synthetic quality: by alpha")]
    for ax, (rows, key, title) in zip(axes, specifications):
        mip = [row for row in rows if row["method"] == "MILP"]
        values = sorted({row[key] for row in mip})
        points = [proof_point([row for row in mip if row[key] == value]) for value in values]
        x = list(range(len(values)))
        for offset, field, label, color in [(-.22, "at_checkpoint", "60s checkpoint", "#9ca3af"),
                                             (.22, "at_end", "End (1200s budget)", "#0072B2")]:
            heights = [100 * point[field] / point["total"] for point in points]
            bars = ax.bar([position + offset for position in x], heights, width=.40, label=label, color=color)
            for bar, point in zip(bars, points):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                        f"{point[field]}/{point['total']}", ha="center", fontsize=7.0)
        ax.set_xticks(x, [f"{value:g}" for value in values])
        ax.set_xlabel("Requests (n)" if key == "n" else "Memory-heavy fraction (alpha)")
        ax.set_title(title, loc="left", fontsize=10.5, fontweight="bold")
        ax.set_ylim(0, 116)
        ax.set_yticks([0, 25, 50, 75, 100])
        style_axis(ax)
        saved[title] = {"key": key, "values": values, "points": points}
    axes[0].set_ylabel("Proven-optimal instances (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(.5, .095), ncol=2, frameon=False)
    fig.subplots_adjust(left=.06, right=.99, top=.88, bottom=.28, wspace=.16)
    fig.text(.06, .025, "Counts come from the same MIP task: an observed 60s checkpoint and its final state.\n"
             "Early optimal endings are retained. Time and memory limits may stop a task before the full budget.", fontsize=8.5)
    data["06_mip_coverage"] = saved
    save_figure(fig, output_dir, "06_mip_coverage")


def pair_counts(rows):
    pairs = {}
    for row in rows:
        if row["method"] in ("FFD-max", "FFD-sum") and row["valid"]:
            pairs.setdefault(row["instance_id"], {})[row["method"]] = row["host_count"]
    differences = [pair["FFD-sum"] - pair["FFD-max"] for pair in pairs.values()
                   if "FFD-max" in pair and "FFD-sum" in pair]
    return (sum(value > 0 for value in differences), sum(value == 0 for value in differences),
            sum(value < 0 for value in differences))


def write_guide(output_dir, real, quality, scale):
    text = """# 实验图表说明

七种算法使用不同虚线，并保留固定颜色与点形状；图片标签采用英文，便于导出和避免字体依赖。PNG用于直接查看，PDF用于文档排版。

| 图 | 阅读内容 |
|---|---|
| 01_real_quality | 真实数据各规模的平均参照差距。R取OPT或最终MIP方案上界U，带星规模包含未证优参照。 |
| 02_synthetic_quality | 四种规模下，alpha与平均参照差距的关系；每个点10个seed。 |
| 03_runtime | 真实及合成规模组的纯算法中位耗时。空心三角是预算终止，不是完成时间。 |
| 04_timing_coverage | 与耗时图配套的完整计时条件数/总条件数。BF的感叹号标记执行错误。 |
| 05_scale_quality | 未运行MIP的规模组，相对有效下界L的差距。 |
| 06_mip_coverage | 同次求解60秒记录与最终的证优率；按规模及alpha分层。 |

R与L含义不同：(A-R)/R在未证优时可能低估距OPT的差距；(A-L)/L则给出差距上界。两者不能混成同一类“最优差距”。MILP不进入启发式质量折线，避免自比较的0差距被误作全部证优。

耗时只使用完成规定重复的条件，质量只使用有效方案；缺失结果画成断线。DP没有十万条结果，不能凭较小规模均值宣布其整体最好。BF一次控制文件访问错误保留首遍有效方案，但对应中位耗时不补值。

plot_data.json保存每个绘图点、有效/完成数量及输入指纹，便于将图追溯到原始结果。图表属于样本实验结论，不替代理论近似保证。
"""
    synthetic_pairs = pair_counts(quality)
    real_pairs = pair_counts(real)
    ffd = select(quality, "FFD-max")
    reached = sum(row["reaches_mip"] is True for row in ffd)
    real_proof = proof_point(select(real, "MILP"))
    quality_proof = proof_point(select(quality, "MILP"))
    text += f"""
## 当前数据支持的结果

1. 合成质量组中，FFD-max相对FFD-sum为{synthetic_pairs[0]}胜、{synthetic_pairs[1]}平、{synthetic_pairs[2]}负；达到MIP最终效果{reached}/{len(ffd)}。这支持max排序适合本批合成分布，不是所有分布上的支配证明。
2. 真实组中，同样的FFD-max相对FFD-sum为{real_pairs[0]}胜、{real_pairs[1]}平、{real_pairs[2]}负，说明排序规则的效果依赖数据结构。
3. MIP在真实组从60秒记录的{real_proof['at_checkpoint']}/{real_proof['total']}证优提高到最终{real_proof['at_end']}/{real_proof['total']}；合成质量组从{quality_proof['at_checkpoint']}/{quality_proof['total']}提高到{quality_proof['at_end']}/{quality_proof['total']}。这是同一次求解继续运行带来的证明收益。

十万条合成实例的速度与质量取舍如下，两方法均完成同一组五个实例：

| 方法 | 纯算法中位秒数 | 平均A/L |
|---|---:|---:|
"""
    for method in ("KK2003", "FFD-max"):
        rows = select(scale, method, n=100000)
        valid = [row for row in rows if row["valid"]]
        text += f"| {method} | {time_point(rows)['seconds']:.2f} | {mean(row['ratio_to_bound'] for row in valid):.5f} |\n"
    text += "\nKK在该组更快，但相对下界的质量比值更大；不能用较好的最坏理论保证代替实测比较。当前DP实现未在十万条条件的600秒预算内返回完整方案，因此图中不报告其完成时间。\n"
    (output_dir / "FIGURE_GUIDE.md").write_text(text, encoding="utf-8")


def main(output_dir):
    real_dir = ROOT / "results/formal_real_600_1200"
    quality_dir = ROOT / "results/formal_synthetic_quality_600_1200"
    scale_dir = ROOT / "results/formal_synthetic_scale_600_1200"
    real, real_meta = analyze_real.read_results(real_dir)
    quality, quality_meta = analyze_synthetic.read_results(quality_dir, "synthetic-quality")
    scale, scale_meta = analyze_synthetic.read_results(scale_dir, "synthetic-scale")
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "pdf.fonttype": 42, "axes.titlepad": 12})
    data = {"definitions": {"reference": "proven OPT; otherwise final valid MIP upper bound U",
                             "L": "valid lower bound", "U": "final valid MIP host count (upper bound)",
                             "time": "median over complete conditions only"},
            "line_styles": {name: pattern for name, pattern in zip(METHODS, LINESTYLES)},
            "environment": {"python": platform.python_version(), "matplotlib": matplotlib.__version__, "numpy": version("numpy")},
            "source_sha256": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                              for directory in (real_dir, quality_dir, scale_dir)
                              for path in (directory / "summary.csv", directory / "metadata.json")},
            "analysis_source_sha256": {name: sha256((ROOT / name).read_bytes()).hexdigest()
                                       for name in ("analyze_real.py", "analyze_synthetic.py", "instance_io.py", "result_metrics.py")},
            "plot_script_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    real_quality(real, output_dir, data)
    synthetic_quality(quality, output_dir, data)
    runtime_comparison(real, scale, {"Real trace": real_meta["config"], "Synthetic scale": scale_meta["config"]}, output_dir, data)
    timing_coverage(real, scale, output_dir, data)
    scale_quality(scale, output_dir, data)
    mip_coverage(real, quality, output_dir, data)
    (output_dir / "plot_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    write_guide(output_dir, real, quality, scale)
    print("Saved: 6 PNG + 6 PDF + plot_data.json + FIGURE_GUIDE.md")
    print("Output:", output_dir.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从三组已完成实验生成图表")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/figures")
    main(parser.parse_args().output_dir)
