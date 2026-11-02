import json
from pathlib import Path

# 当前模块所在的项目目录，不依赖终端当前在哪个文件夹。I/O表示input/output（输入/输出）。
ROOT = Path(__file__).resolve().parent
INSTANCE_DIR = ROOT / "data" / "instances" / "real_small"
RESULT_DIR = ROOT / "results"


def write_json(path, data):
    # path 是路径对象，data 是要保存的字典或列表。
    # 创建父目录；目录已存在时继续执行。
    path.parent.mkdir(parents=True, exist_ok=True)

    # with 在代码块结束时自动关闭文件；w 表示覆盖写入。
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2, allow_nan=False)


def load_instance(path):
    # 从文件读回数据，得到 Python 字典和列表。
    with path.open("r", encoding="utf-8") as file:
        instance = json.load(file)

    # JSON 没有元组，读回后恢复五字段元组。
    requests = []
    for row in instance["requests"]:
        requests.append(tuple(row))
    instance["requests"] = requests

    if len(requests) != instance["n"]:
        raise ValueError("Instance request count mismatch")

    return instance
