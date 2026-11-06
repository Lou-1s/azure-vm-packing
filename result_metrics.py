"""统一计算相对MIP最终方案的指标，保留求解器真实下界的原定义。"""


REFERENCE_FIELDS = [
    "reference_host_count", "reference_is_optimal",
    "ratio_to_reference", "gap_to_reference", "reaches_mip",
]


def attach_reference_metrics(rows):
    # 每个实例使用自己的MIP最终方案，不跨实例借用参照值。
    mip_rows = {
        row["instance_id"]: row for row in rows
        if row["method"] == "MILP" and row.get("valid") is True
        and row.get("host_count") is not None
    }
    for row in rows:
        mip = mip_rows.get(row["instance_id"])
        optimum = row.get("optimum")
        # 已证优用OPT；未证优用MIP最终有效台数U（可行解上界）。
        reference = optimum if optimum is not None else (mip["host_count"] if mip else None)
        count = row.get("host_count")
        valid = row.get("valid") is True and count is not None
        row.update(
            reference_host_count=reference,
            reference_is_optimal=(optimum is not None) if reference is not None else None,
            ratio_to_reference=count / reference if valid and reference is not None else None,
            gap_to_reference=(count - reference) / reference if valid and reference is not None else None,
            # 分母取全部条件，未返回有效方案的条件不能计为达到MIP效果。
            reaches_mip=(valid and count <= mip["host_count"]) if mip else None,
        )
    # 未运行MIP且OPT未知时不伪造参照，原ratio_to_bound等指标仍可使用。
    return rows
