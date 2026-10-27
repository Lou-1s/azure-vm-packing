import sys

print("Python:", sys.executable)
print("Environment:", sys.prefix)
print("Is venv:", sys.prefix != sys.base_prefix)