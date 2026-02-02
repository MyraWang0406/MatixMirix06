"""统一 samples 路径：始终使用仓库根目录 /samples。Streamlit Cloud 部署时 repo 根目录即工作目录。"""
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent
SAMPLES_DIR = REPO_ROOT / "samples"

# 确保根目录在 sys.path 中
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
