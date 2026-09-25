import json
import re
import shutil
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path

from .models import Listing
from .settings import BACKUP_DIR, DB_PATH, ensure_dirs


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def token_similarity(left: str, right: str) -> float:
    a, b = set(normalize(left).split()), set(normalize(right).split())
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


class Database:
    SCHEMA_VERSION = 2

    def __init__(self, path: Path = DB_PATH):
        ensure_dirs()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _migration_backup(self) -> Path:
        backup_dir = BACKUP_DIR if self.path == DB_PATH else self.path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / f"pre-migration-{datetime.now():%Y%m%d-%H%M%S-%f}.db"
        shutil.copy2(self.path, target)
        return target

    def migrate(self):
        existed = self.path.exists() and self.path.stat().st_size > 0
        current = 0
        if existed:
            with self.connect() as db:
                has_versions = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
                ).fetchone()
                if has_versions:
                    row = db.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
                    current = row[0] or 0
        if existed and current < self.SCHEMA_VERSION:
            self._migration_backup()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                self._create_schema(db)
                db.execute(
                    "CREATE TABLE IF NOT EXISTS schema_migrations "
                    "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
                )
                for version in range(current + 1, self.SCHEMA_VERSION + 1):
                    db.execute(
                        "INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(?,?)",
                        (version, datetime.now().isoformat(timespec="seconds")),
                    )
                db.commit()
            except Exception:
                db.rollback()
                raise

    def create_schema(self):
        self.migrate()

    def _create_schema(self, db):
        db.executescript("""
        CREATE TABLE IF NOT EXISTS listings (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, neighborhood TEXT NOT NULL,
          city TEXT NOT NULL DEFAULT 'Contagem', price REAL, area REAL,
          dimensions TEXT, topography TEXT, walled TEXT, cab TEXT, cam TEXT,
          address TEXT, url TEXT, source TEXT, image_url TEXT, contact TEXT,
          notes TEXT, status TEXT NOT NULL DEFAULT 'new', classification TEXT,
          fingerprint TEXT NOT NULL UNIQUE, found_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS price_history (
          id INTEGER PRIMARY KEY, listing_id INTEGER NOT NULL, price REAL NOT NULL,
          recorded_at TEXT NOT NULL, FOREIGN KEY(listing_id) REFERENCES listings(id)
        );
        CREATE TABLE IF NOT EXISTS app_state (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS listing_sources (
          id INTEGER PRIMARY KEY, listing_id INTEGER NOT NULL,
          source TEXT NOT NULL, url TEXT NOT NULL DEFAULT '', listing_code TEXT NOT NULL DEFAULT '',
          found_at TEXT NOT NULL,
          FOREIGN KEY(listing_id) REFERENCES listings(id) ON DELETE CASCADE,
          UNIQUE(listing_id, source, url)
        );
        """)
        existing = {row[1] for row in db.execute("PRAGMA table_info(listings)")}
        for column in (
            "description", "listing_code", "phone", "whatsapp", "email",
            "agency", "broker", "photos",
        ):
            if column not in existing:
                db.execute(f"ALTER TABLE listings ADD COLUMN {column} TEXT DEFAULT ''")

    @staticmethod
    def fingerprint(item: Listing) -> str:
        if item.url:
            return "url:" + normalize(item.url.split("?")[0].rstrip("/"))
        parts = [
            item.neighborhood, item.city, str(round(item.price or 0, -3)),
            str(round(item.area or 0)), item.dimensions, item.address,
        ]
        return "data:" + "|".join(normalize(x) for x in parts)

    def _find_duplicate(self, db, item: Listing):
        clean_url = normalize(item.url.split("?")[0].rstrip("/")) if item.url else ""
        if clean_url:
            row = db.execute(
                "SELECT id, price FROM listings WHERE fingerprint=?",
                ("url:" + clean_url,),
            ).fetchone()
            if row:
                return row
        if item.listing_code:
            row = db.execute(
                "SELECT id, price FROM listings WHERE listing_code=? AND source=?",
                (item.listing_code, item.source),
            ).fetchone()
            if row:
                return row
        if item.area and item.neighborhood:
            candidates = db.execute(
                "SELECT * FROM listings WHERE area BETWEEN ? AND ?",
                (item.area - 1, item.area + 1),
            ).fetchall()
            for row in candidates:
                if normalize(row["neighborhood"]) != normalize(item.neighborhood):
                    continue
                evidence = 0
                if item.address and row["address"]:
                    if (
                        normalize(item.address) == normalize(row["address"])
                        or token_similarity(item.address, row["address"]) >= 0.6
                    ):
                        evidence += 2
                if item.dimensions and row["dimensions"] and normalize(item.dimensions) == normalize(row["dimensions"]):
                    evidence += 1
                if item.phone and row["phone"] and normalize(item.phone) == normalize(row["phone"]):
                    evidence += 1
                if item.price and row["price"] and abs(item.price - row["price"]) <= 1000:
                    evidence += 1
                if normalize(item.title) and normalize(item.title) == normalize(row["title"]):
                    evidence += 1
                if evidence >= 2:
                    return row
        return None

    @staticmethod
    def classify(item: Listing, criteria=None, missing_criteria=None) -> str:
        criteria = criteria or {}
        active = any(
            value not in (None, "", [], (), 0, 0.0)
            for value in criteria.values()
        )
        if not active:
            return "Encontrado"
        missing = [str(x) for x in (missing_criteria or []) if x]
        if missing:
            return "Compatível — confirmar " + ", ".join(missing[:3])
        return "Compatível com filtros"

    @staticmethod
    def _merge(old, incoming: Listing) -> Listing:
        old_values = {name: old[name] for name in incoming.__dataclass_fields__}
        merged = {}
        longer_fields = {"title", "neighborhood", "city", "address", "description", "notes"}
        preserve_fields = {
            "dimensions", "topography", "walled", "cab", "cam", "phone",
            "whatsapp", "email", "agency", "broker", "image_url", "contact",
            "listing_code",
        }
        for name in incoming.__dataclass_fields__:
            current, new = old_values.get(name), getattr(incoming, name)
            if name in ("price", "area"):
                merged[name] = new if new is not None else current
            elif name == "photos":
                combined = []
                for value in (current, new):
                    for line in str(value or "").splitlines():
                        if line.strip() and line.strip() not in combined:
                            combined.append(line.strip())
                merged[name] = "\n".join(combined)
            elif name in longer_fields:
                merged[name] = max((str(current or ""), str(new or "")), key=len)
            elif name in preserve_fields:
                merged[name] = current or new or ""
            elif name in ("url", "source"):
                merged[name] = current or new or ""
            else:
                merged[name] = new or current or ""
        return Listing(**merged)

    @staticmethod
    def _register_source(db, listing_id, item: Listing, now):
        if not item.source and not item.url:
            return
        db.execute(
            "INSERT OR IGNORE INTO listing_sources"
            "(listing_id,source,url,listing_code,found_at) VALUES(?,?,?,?,?)",
            (listing_id, item.source or "Fonte não informada", item.url or "",
             item.listing_code or "", now),
        )

    def upsert(self, item: Listing, criteria=None, missing_criteria=None) -> tuple[int, str]:
        now = datetime.now().isoformat(timespec="seconds")
        fp = self.fingerprint(item)
        values = {
            name: getattr(item, name)
            for name in item.__dataclass_fields__
        }
        with self.connect() as db:
            old = self._find_duplicate(db, item)
            if old:
                old = db.execute("SELECT * FROM listings WHERE id=?", (old["id"],)).fetchone()
                if item.price is not None and old["price"] != item.price:
                    db.execute(
                        "INSERT INTO price_history(listing_id,price,recorded_at) VALUES(?,?,?)",
                        (old["id"], item.price, now),
                    )
                merged_item = self._merge(old, item)
                values = {
                    name: getattr(merged_item, name)
                    for name in merged_item.__dataclass_fields__
                }
                assignments = ",".join(f"{key}=?" for key in values)
                db.execute(
                    f"UPDATE listings SET {assignments},classification=?,updated_at=? WHERE id=?",
                    (*values.values(), self.classify(merged_item, criteria, missing_criteria), now, old["id"]),
                )
                self._register_source(db, old["id"], item, now)
                return old["id"], "updated"

            cols = ",".join(values)
            marks = ",".join("?" for _ in values)
            cur = db.execute(
                f"INSERT INTO listings({cols},classification,fingerprint,found_at,updated_at) "
                f"VALUES({marks},?,?,?,?)",
                (*values.values(), self.classify(item, criteria, missing_criteria), fp, now, now),
            )
            if item.price is not None:
                db.execute(
                    "INSERT INTO price_history(listing_id,price,recorded_at) VALUES(?,?,?)",
                    (cur.lastrowid, item.price, now),
                )
            self._register_source(db, cur.lastrowid, item, now)
            return cur.lastrowid, "new"

    def all(self, status: str = "new"):
        with self.connect() as db:
            return db.execute(
                "SELECT * FROM listings WHERE status=? ORDER BY updated_at DESC, found_at DESC",
                (status,),
            ).fetchall()

    def set_status(self, listing_id: int, status: str):
        with self.connect() as db:
            db.execute(
                "UPDATE listings SET status=?, updated_at=? WHERE id=?",
                (status, datetime.now().isoformat(timespec="seconds"), listing_id),
            )

    def get(self, listing_id: int):
        with self.connect() as db:
            return db.execute("SELECT * FROM listings WHERE id=?", (listing_id,)).fetchone()

    def price_history(self, listing_id: int):
        with self.connect() as db:
            return db.execute(
                "SELECT price, recorded_at FROM price_history "
                "WHERE listing_id=? ORDER BY recorded_at DESC",
                (listing_id,),
            ).fetchall()

    def sources(self, listing_id: int):
        with self.connect() as db:
            return db.execute(
                "SELECT source, url, listing_code, found_at FROM listing_sources "
                "WHERE listing_id=? ORDER BY id",
                (listing_id,),
            ).fetchall()

    def set_state(self, key: str, value):
        with self.connect() as db:
            db.execute(
                "INSERT INTO app_state(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, ensure_ascii=False)),
            )

    def get_state(self, key: str, default=None):
        with self.connect() as db:
            row = db.execute("SELECT value FROM app_state WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def backup(self) -> Path:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        target = BACKUP_DIR / f"radar-{datetime.now():%Y%m%d-%H%M%S}.db"
        shutil.copy2(self.path, target)
        backups = sorted(BACKUP_DIR.glob("radar-*.db"), reverse=True)
        for old in backups[10:]:
            old.unlink(missing_ok=True)
        return target
