# sys 是 Python 自带模块，用于查看当前解释器和环境信息。
import sys

print("Python:", sys.executable)  # 当前实际运行的 python.exe 完整路径。
print("Environment:", sys.prefix)  # 当前 Python 环境所在目录。
# base_prefix 是基础 Python 的目录；两者不同，说明当前运行在虚拟环境中。
print("Is venv:", sys.prefix != sys.base_prefix)
