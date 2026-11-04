import argparse
import csv
import ctypes
import json
import os
import subprocess
import sys
import tempfile
import traceback
from ctypes import wintypes
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from statistics import median
from time import perf_counter, sleep

from instance_io import ROOT, RESULT_DIR, load_instance, write_json
from run_experiments import METHODS  # 复用七种算法的同一份清单。
from solution_checker import check_solution

TIME_LIMIT = 600  # 每种方法、每个实例、每次调用的算法预算：10分钟。
MEMORY_MIB = 2048
STAGE_LIMIT = 30
POLL_SECONDS = 0.05


def publish(directory, name, data):
    # 每个阶段只发布一次；先写完临时文件，再改名，父进程不会读到半段JSON。
    path = directory / name
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class PrivateMemory:
    """读取指定Windows进程的私有提交内存，不是工作集大小。"""

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")
        ]

    def __init__(self, pid):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        # 明确句柄和参数类型，防止64位句柄被截断。
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(self.Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        self.close_handle = kernel.CloseHandle
        self.get_info = psapi.GetProcessMemoryInfo
        self.handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def sample(self):
        counters = self.Counters()
        counters.cb = ctypes.sizeof(counters)
        if not self.get_info(self.handle, ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.PrivateUsage

    def close(self):
        if self.handle:
            self.close_handle(self.handle)
            self.handle = None


def worker(directory):
    job = read_json(directory / "job.json")
    elapsed = None
    try:
        instance = load_instance(Path(job["path"]))
        requests = instance["requests"]
        before = list(requests)
        algorithm = dict(METHODS)[job["method"]]
        publish(directory, "started.json", {"clock": perf_counter(), "pid": os.getpid()})
        started = perf_counter()
        hosts = algorithm(requests)
        elapsed = perf_counter() - started  # 只测算法；读取、检查、保存均在计时之外。
        publish(directory, "finished.json", {"clock": perf_counter(), "seconds": elapsed})
        if elapsed > job["time_limit"]:
            result = {"status": "time_budget", "seconds": None, "valid": None}
        else:
            valid, message = check_solution(requests, hosts)
            unchanged = requests == before
            passed = valid and unchanged
            result = {"status": "completed" if passed else "invalid_solution",
                      "seconds": elapsed if passed else None, "valid": passed,
                      "host_count": len(hosts), "input_unchanged": unchanged, "message": message}
            if passed and job.get("keep_placements", False):
                # 批量入口需要完整分组；只传请求ID，避免重复保存五个字段。
                result["placement_ids"] = [[request[0] for request in host] for host in hosts]
    except Exception as error:
        result = {"status": "memory_error" if isinstance(error, MemoryError) else "error",
                  "seconds": None, "valid": None, "error": traceback.format_exc()}
    result["algorithm_elapsed_seconds"] = elapsed
    # 默认只传统计；批量调用可附带ID分组，完整方案已在工作进程内检查。
    publish(directory, "result.json", result)


def run_once(path, method, time_limit=TIME_LIMIT, memory_mib=MEMORY_MIB, keep_placements=False):
    """一次受监督调用；method为METHODS中的名称，返回统计字典。"""
    if time_limit < 0 or memory_mib <= 0:
        raise ValueError("Invalid execution budget")
    if method not in dict(METHODS):
        raise ValueError("Unknown method: " + method)
    result = {"status": "error", "seconds": None, "valid": None}
    peak = 0
    started = perf_counter()
    with tempfile.TemporaryDirectory(prefix="packing_benchmark_") as temporary:
        directory = Path(temporary)
        publish(directory, "job.json", {"path": str(Path(path).resolve()),
                "method": method, "time_limit": time_limit, "keep_placements": keep_placements})
        process = None
        memory = None
        with (directory / "worker.log").open("w", encoding="utf-8") as log:
            try:
                # 启动真正的Python进程，避免仅监测到.venv重定向器。
                environment = dict(os.environ)
                # 将父进程可用的项目、虚拟环境依赖路径交给子进程。
                environment["PYTHONPATH"] = os.pathsep.join(path for path in sys.path if path)
                process = subprocess.Popen(
                    [sys._base_executable, str(Path(__file__).resolve()), "--worker", str(directory)],
                    stdout=log, stderr=log, env=environment,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                memory = PrivateMemory(process.pid)
                phase, phase_started = "startup", started
                while True:
                    if (directory / "result.json").exists():
                        result = read_json(directory / "result.json")
                        break
                    if (directory / "finished.json").exists():
                        data = read_json(directory / "finished.json")
                        phase, phase_started = "check", data["clock"]
                        if data["seconds"] > time_limit:
                            result.update(status="time_budget", algorithm_elapsed_seconds=data["seconds"])
                            break
                    elif (directory / "started.json").exists():
                        data = read_json(directory / "started.json")
                        if data["pid"] != process.pid:
                            raise RuntimeError("Supervisor PID differs from actual worker PID")
                        phase, phase_started = "algorithm", data["clock"]
                    if process.poll() is not None:
                        # 检查期间刚结束时，再读一次最终结果。
                        if (directory / "result.json").exists():
                            result = read_json(directory / "result.json")
                        else:
                            result["error"] = "Worker exited without a result"
                        break
                    try:
                        peak = max(peak, memory.sample())
                    except OSError:
                        if process.poll() is None:
                            raise  # 进程存活却读不到内存时，明确报错，不关闭保护后继续。
                        continue
                    if peak > memory_mib * 1024 * 1024:
                        result["status"] = "memory_budget"
                        break
                    budget = time_limit if phase == "algorithm" else STAGE_LIMIT
                    if perf_counter() - phase_started > budget:
                        result["status"] = {"startup": "startup_budget", "algorithm": "time_budget",
                                            "check": "check_budget"}[phase]
                        break
                    sleep(POLL_SECONDS)
            except Exception:
                result.update(status="error", seconds=None, error=traceback.format_exc())
            finally:
                if process is not None:
                    if result["status"] == "completed":
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            result.update(status="error", seconds=None, error="Worker did not exit after publishing its result")
                    if process.poll() is None:
                        process.kill()
                    process.wait()
                    result["exit_code"] = process.returncode
                    if result["status"] == "completed" and process.returncode != 0:
                        result.update(status="error", seconds=None, error="Worker exited abnormally")
                if memory is not None:
                    memory.close()
        if result["status"] != "completed":
            result["seconds"] = None
            result["worker_log"] = (directory / "worker.log").read_text(encoding="utf-8", errors="replace")[-4000:]
    result.update(method=method, wall_seconds=perf_counter() - started,
                  peak_private_mib=peak / 1024 / 1024)
    return result


def main(output_dir):
    paths = [ROOT / "data/instances/real_large/real_m12_w1_2_n1000.json"] + [
        ROOT / "data/instances/synthetic_alpha" / f"synthetic_v2_a30_s0_n{n}.json"
        for n in (1000, 5000, 10000)]
    rows = []
    metadata = {"created_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
                "algorithm_budget_seconds": TIME_LIMIT, "startup_check_budget_seconds": STAGE_LIMIT,
                "memory_budget_mib": MEMORY_MIB, "memory_metric": "sampled Windows PrivateUsage",
                "poll_seconds": POLL_SECONDS, "timing": "median only when all required calls complete",
                "partial_quality": "host_count/valid refer to the first completed call, if any",
                "instance_sha256": {}, "calls": {}}
    for path in paths:
        instance = load_instance(path)
        name, n = instance["instance_id"], instance["n"]
        repeats = 1 if n == 100000 else 3
        metadata["instance_sha256"][name] = sha256(path.read_bytes()).hexdigest()
        metadata["calls"][name] = {}
        for method, algorithm in METHODS:
            calls = []
            for repeat in range(repeats):
                call = run_once(path, method)
                call["repeat"] = repeat + 1
                calls.append(call)
                if call["status"] != "completed":
                    break  # 预算失败后不补跑，不用成功子集冒充三次中位数。
            successful = [call for call in calls if call["status"] == "completed"]
            complete = len(successful) == repeats
            first = successful[0] if successful else {}
            row = {"instance_id": name, "n": n, "method": method,
                   "status": "completed" if complete else calls[-1]["status"],
                   "host_count": first.get("host_count"), "valid": first.get("valid"),
                   "seconds": median(call["seconds"] for call in successful) if complete else None,
                   "required_repeats": repeats, "completed_repeats": len(successful),
                   "wall_seconds_total": sum(call["wall_seconds"] for call in calls),
                   "peak_private_mib": max(call["peak_private_mib"] for call in calls),
                   "stop_reason": calls[-1]["status"]}
            rows.append(row)
            metadata["calls"][name][method] = calls
            print(name, "|", method, "|", row["status"], "| Hosts:", row["host_count"],
                  "| Seconds:", round(row["seconds"], 6) if complete else None,
                  "| Repeats:", f"{len(successful)}/{repeats}", flush=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "benchmark_kk.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_json(output_dir / "benchmark_kk_metadata.json", metadata)
    print("Saved: benchmark_kk.csv | Rows:", len(rows))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--output-dir", type=Path, default=RESULT_DIR)
    args = parser.parse_args()
    if args.worker is not None:
        worker(args.worker)
    else:
        main(args.output_dir)
