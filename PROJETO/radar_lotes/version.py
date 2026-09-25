from pathlib import Path
import sys


def _version_file() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / "VERSION"


try:
    __version__ = _version_file().read_text(encoding="utf-8").strip()
except OSError:
    __version__ = "0.0.0"
