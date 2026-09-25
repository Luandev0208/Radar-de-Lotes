import os
from pathlib import Path

APP_NAME = "Radar de Lotes"
APP_AUTHOR = "JG Empreendimentos"
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share")) / APP_NAME
DB_PATH = DATA_DIR / "radar.db"
BACKUP_DIR = DATA_DIR / "backups"
LOG_DIR = DATA_DIR / "logs"

PRIORITY_NEIGHBORHOODS = [
    "Nacional", "Xangri-lá", "Parque Xangri-lá",
    "Vale das Amendoeiras", "Bom Jesus", "Arvoredo",
]
MAX_PRICE = 420_000
MIN_AREA = 350
MAX_AREA = 380


def ensure_dirs() -> None:
    for path in (DATA_DIR, BACKUP_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
