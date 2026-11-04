"""让独立运行的演示脚本能够导入项目根目录中的模块。"""

import sys
from pathlib import Path


# __file__是本文件的位置；两层parent分别是try目录和项目根目录。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
