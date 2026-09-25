import sqlite3

from radar_lotes.database import Database
from radar_lotes.models import Listing


def test_insert_deduplicate_and_price_history(tmp_path):
    db = Database(tmp_path / "test.db")
    item = Listing("Terreno", "Nacional", city="Contagem", price=400000, area=360, url="https://example.com/imovel/123456")
    listing_id, action = db.upsert(item)
    assert action == "new"
    item.price = 390000
    same_id, action = db.upsert(item)
    assert (same_id, action) == (listing_id, "updated")
    with db.connect() as conn:
        prices = conn.execute("SELECT price FROM price_history ORDER BY id").fetchall()
    assert [p[0] for p in prices] == [400000, 390000]


def test_coordinates_are_persisted_and_help_dedup(tmp_path):
    db = Database(tmp_path / "test.db")
    first = Listing("Lote A", "Nacional", city="Contagem", price=395000, area=360, latitude=-19.9000, longitude=-44.0500, source="A", url="https://a.test/imovel/123456")
    second = Listing("Lote B", "Nacional", city="Contagem", price=395000, area=360, latitude=-19.90005, longitude=-44.05005, source="B", url="https://b.test/imovel/987654")
    first_id, _ = db.upsert(first)
    second_id, action = db.upsert(second)
    assert second_id == first_id
    assert action == "updated"
    row = db.get(first_id)
    assert row["latitude"] is not None and row["longitude"] is not None


def test_dynamic_classification_uses_current_filters():
    item = Listing("Terreno", "Nacional", city="Contagem", price=395000, area=360)
    criteria = {"city": "Contagem", "max_price": 420000, "require_price": True}
    assert Database.classify(item, criteria, []) == "Compatível com filtros"
    assert "confirmar" in Database.classify(item, criteria, ["topografia"]).lower()
    assert Database.classify(item) == "Encontrado"


def test_status_change(tmp_path):
    db = Database(tmp_path / "test.db")
    listing_id, _ = db.upsert(Listing("Terreno", "Arvoredo", city="Contagem"))
    db.set_status(listing_id, "interesting")
    assert len(db.all("new")) == 0
    assert db.all("interesting")[0]["id"] == listing_id


def test_migration_adds_coordinates_and_preserves_legacy_data(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
        CREATE TABLE listings (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, neighborhood TEXT NOT NULL,
          city TEXT NOT NULL DEFAULT 'Contagem', price REAL, area REAL,
          dimensions TEXT, topography TEXT, walled TEXT, cab TEXT, cam TEXT,
          address TEXT, url TEXT, source TEXT, image_url TEXT, contact TEXT,
          notes TEXT, status TEXT NOT NULL DEFAULT 'new', classification TEXT,
          fingerprint TEXT NOT NULL UNIQUE, found_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE price_history (id INTEGER PRIMARY KEY, listing_id INTEGER, price REAL, recorded_at TEXT);
        CREATE TABLE app_state (key TEXT PRIMARY KEY, value TEXT);
        INSERT INTO listings(title,neighborhood,fingerprint,found_at,updated_at)
        VALUES('Lote salvo','Nacional','legado','2026-01-01','2026-01-01');
        """)
    db = Database(path)
    assert db.get(1)["title"] == "Lote salvo"
    with db.connect() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(listings)")}
        version = conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
    assert {"latitude", "longitude", "phone", "photos"} <= columns
    assert version == 3
    assert list((tmp_path / "backups").glob("pre-migration-*.db"))
