import sys
from pathlib import Path

# make partC/ importable (arithmetic.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
