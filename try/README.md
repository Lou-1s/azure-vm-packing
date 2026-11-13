# 演示与核对脚本

这些脚本用于学习、分支示例和独立核对。正式批量实验使用项目根目录的 `run_batch.py`。

从项目根目录运行，例如：

```powershell
& ".\.venv\Scripts\python.exe" ".\try\try_greedy.py"
```

也可以在VS Code中直接打开任一脚本运行。`_bootstrap.py`根据脚本所在位置找到项目根目录，用于导入模块和查找实例。

| 脚本 | 内容 |
|---|---|
| `try_first_fit.py` | FF手算案例、遗漏/重复及容量检查 |
| `try_greedy.py` | FF、BF、FFD与BFD的分组对照 |
| `try_dot_product.py` | DP及两种FFD排序的对照 |
| `try_cached_packing.py` | 五种缓存方法与独立无缓存参照核对；十万条检查器计时 |
| `try_milp.py` | 基础指派MIP与解读取 |
| `try_fixed_k.py` | 给定K的可行性判定 |
| `try_synthetic_milp.py` | 固定K外层搜索与累计预算 |
| `try_aggregated_milp.py` | 类型聚合MIP与当前真实实例 |
| `try_mip_progress.py` | 同次求解的截止/最终记录；输出到 `results/checks/try/` |
| `try_kk_basics.py` | KK分类和P子程序 |
| `try_kk_large.py` | KK大请求阶段 |
| `try_kk_complete.py` | KK九个完整分支例与小规模MIP核对 |

需要真实数据的示例从 `data/instances/real_v2` 读取。需要合成数据的示例从 `data/instances/synthetic_alpha` 读取。
