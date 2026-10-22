"""Load the unmodified starter_kit/fertility.py as a module (never edited).

The SHA-256 below is of the file as provided in the assignment kit; loading
refuses to proceed if the file has changed, so every "v0" number in the audit
comes from the original code.
"""
import hashlib
import importlib.util
from pathlib import Path

V0_PATH = Path(__file__).resolve().parents[2] / "starter_kit" / "fertility.py"
V0_SHA256 = "93528e332d552adad2bda677e82b6615a0d024be3a529fd146c6b4756e81d9d4"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_v0():
    got = sha256_of(V0_PATH)
    if got != V0_SHA256:
        raise RuntimeError(f"starter_kit/fertility.py was modified (sha256 {got})")
    spec = importlib.util.spec_from_file_location("fertility_v0", V0_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
