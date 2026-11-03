import math
from solution_checker import check_solution


class MipProgress:
    """同一次求解任务的观测记录；时间是累计Gurobi优化秒数。"""

    def __init__(self, requests, initial_hosts, lower_bound, target_seconds=60):
        if target_seconds < 0:
            raise ValueError("Negative snapshot time")
        self.requests = requests
        self.hosts = initial_hosts
        self.lower = lower_bound
        self.target = target_seconds
        self.observed_seconds = 0.0
        self.solution_seconds = 0.0
        self.bound_seconds = 0.0
        self.checkpoint = None
        self.error = None
        self.callback_events = 0

    def snapshot(self, effective_seconds, reason):
        upper = len(self.hosts)
        return {
            "requested_seconds": self.target,
            "effective_seconds": effective_seconds,
            "observed_seconds": self.observed_seconds,
            "solution_observed_seconds": self.solution_seconds,
            "bound_observed_seconds": self.bound_seconds,
            "upper_bound": upper, "lower_bound": self.lower,
            "optimal": upper == self.lower,
            "gap_to_bound": (upper - self.lower) / self.lower if self.lower else 0.0,
            "reason": reason,
            "placement_ids": [[request[0] for request in host] for host in self.hosts],
        }

    def observe(self, seconds, hosts=None, lower_bound=None):
        # 先冻结截止时点之前的状态，再接收本次事件，避免写入未来信息。
        if self.checkpoint is None and seconds > self.target:
            self.checkpoint = self.snapshot(self.target, "observed_cutoff")
        if hosts is not None and len(hosts) < len(self.hosts):
            valid, message = check_solution(self.requests, hosts)
            if not valid:
                raise ValueError("Invalid progress incumbent: " + message)
            self.hosts = hosts
            self.solution_seconds = seconds
        if lower_bound is not None and lower_bound > self.lower:
            self.lower = lower_bound
            self.bound_seconds = seconds
        if self.lower > len(self.hosts):
            raise ValueError("Progress lower bound exceeds valid upper bound")
        self.observed_seconds = seconds

    def callback(self, restore_hosts, time_offset=0.0, objective_is_bin_count=False):
        # 返回一个函数，Gurobi在优化过程中调用它；闭包保留上述参数。
        from gurobipy import GRB

        def observe_model(model, where):
            try:
                if where not in (GRB.Callback.MIP, GRB.Callback.MIPSOL):
                    return
                self.callback_events += 1
                seconds = time_offset + model.cbGet(GRB.Callback.RUNTIME)
                bound = None
                if objective_is_bin_count:
                    code = GRB.Callback.MIP_OBJBND if where == GRB.Callback.MIP else GRB.Callback.MIPSOL_OBJBND
                    value = model.cbGet(code)
                    if math.isfinite(value) and abs(value) < GRB.INFINITY:
                        bound = math.ceil(value - 1e-6)
                hosts = None
                if where == GRB.Callback.MIPSOL:
                    # 只在整数方案事件取分配，不能把节点LP松弛当作可行分组。
                    # sum(y)可能包含空主机，因此按恢复后的实际台数比较。
                    hosts = restore_hosts(model)
                self.observe(seconds, hosts, bound)
            except Exception as error:
                # Gurobi回调中的异常不能只打印后继续；停止后由外层重新抛出。
                self.error = error
                model.terminate()

        return observe_model

    def raise_if_failed(self):
        if self.error is not None:
            raise RuntimeError("MIP progress callback failed") from self.error

    def finish(self, seconds, hosts, lower_bound):
        self.raise_if_failed()
        self.observe(seconds, hosts, lower_bound)
        if self.checkpoint is None:
            reason = "early_optimal" if len(self.hosts) == self.lower else "ended_before_target"
            if seconds >= self.target:
                reason = "observed_cutoff"
            self.checkpoint = self.snapshot(min(seconds, self.target), reason)
        return {
            "time_basis": "cumulative Gurobi Runtime; preprocessing/building excluded",
            "observation_policy": "best verified state observed at or before the requested cutoff",
            "callback_events": self.callback_events,
            "checkpoint": self.checkpoint,
            "final": self.snapshot(seconds, "solver_end"),
        }
