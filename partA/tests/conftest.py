import sys
from pathlib import Path

# make partA/ importable as a flat package root (units.py, corpus/...)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
