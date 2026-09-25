from pathlib import Path
import sqlite3
from radar_lotes.database import Database
from radar_lotes.models import Listing


def test_insert_deduplicate_and_price_history(tmp_path):
    db = Database(tmp_path / "test.db")
    item = Listing("Terreno", "Nacional", price=400000, area=360, url="https://example.com/1")
    listing_id, action = db.upsert(item)
    assert action == "new"
    item.price = 390000
    same_id, action = db.upsert(item)
    assert (same_id, action) == (listing_id, "updated")
    assert len(db.all("new")) == 1
    with db.connect() as conn:
        prices = conn.execute("SELECT price FROM price_history ORDER BY id").fetchall()
    assert [p[0] for p in prices] == [400000, 390000]


def test_classification_handles_missing_data():
    item = Listing("Terreno", "Nacional")
    assert Database.classify(item) == "Pode ser interessante — precisa confirmar"


def test_status_change(tmp_path):
    db = Database(tmp_path / "test.db")
    listing_id, _ = db.upsert(Listing("Terreno", "Arvoredo"))
    db.set_status(listing_id, "interesting")
    assert len(db.all("new")) == 0
    assert db.all("interesting")[0]["id"] == listing_id


def test_cross_source_duplicate_with_strong_evidence(tmp_path):
    db = Database(tmp_path / "test.db")
    first = Listing("Lote 360m", "Nacional", price=395000, area=360, dimensions="12 x 30", address="Rua X, Nacional", source="A", url="https://a.test/1")
    second = Listing("Outro anúncio", "Nacional", price=395000, area=360, dimensions="12 x 30", address="Rua X, Nacional", source="B", url="https://b.test/9")
    first_id, _ = db.upsert(first)
    second_id, action = db.upsert(second)
    assert second_id == first_id
    assert action == "updated"
    assert len(db.all()) == 1


def test_incomplete_duplicate_preserves_and_combines_data(tmp_path):
    db = Database(tmp_path / "test.db")
    first = Listing(
        "Lote no Nacional", "Nacional", price=395000, area=360, dimensions="12 x 30",
        address="Rua das Flores, 120, Nacional, Contagem", phone="(31) 3333-4444",
        email="vendas@imob-a.com.br", agency="Imobiliária A", photos="https://img/a.jpg",
        source="OLX", url="https://olx.test/a",
    )
    second = Listing(
        "Terreno 360 m²", "Nacional", price=395000, area=360,
        address="Rua das Flores, Nacional", whatsapp="(31) 99999-9999",
        broker="José", photos="https://img/b.jpg", source="Chaves na Mão", url="https://chaves.test/b",
    )
    listing_id, _ = db.upsert(first)
    duplicate_id, action = db.upsert(second)
    row = db.get(listing_id)
    assert duplicate_id == listing_id and action == "updated"
    assert row["phone"] == "(31) 3333-4444"
    assert row["email"] == "vendas@imob-a.com.br"
    assert row["address"] == "Rua das Flores, 120, Nacional, Contagem"
    assert row["whatsapp"] == "(31) 99999-9999"
    assert row["agency"] == "Imobiliária A" and row["broker"] == "José"
    assert "a.jpg" in row["photos"] and "b.jpg" in row["photos"]
    sources = db.sources(listing_id)
    assert {s["source"] for s in sources} == {"OLX", "Chaves na Mão"}
    assert {s["url"] for s in sources} == {"https://olx.test/a", "https://chaves.test/b"}


def test_classification_requires_known_price_and_area():
    assert Database.classify(Listing("Lote", "Nacional", area=360)) == "Pode ser interessante — precisa confirmar"
    assert Database.classify(Listing("Lote", "Nacional", price=395000)) == "Pode ser interessante — precisa confirmar"
    assert Database.classify(Listing("Lote", "Nacional", price=395000, area=360)) == "Muito interessante"
    assert Database.classify(Listing("Lote", "Nacional", price=500000, area=360)) == "Pouco compatível"
    assert Database.classify(Listing("Lote", "Nacional", price=395000, area=700)) == "Pouco compatível"


def test_low_compatibility_does_not_fill_new_tab(tmp_path):
    db = Database(tmp_path / "test.db")
    db.upsert(Listing("Lote fora do perfil", "Nacional", price=395000, area=700))
    assert db.all("new") == []


def test_migration_preserves_legacy_data_and_creates_backup(tmp_path):
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
        assert conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == db.SCHEMA_VERSION
        columns = {row[1] for row in conn.execute("PRAGMA table_info(listings)")}
    assert {"phone", "email", "photos"} <= columns
    assert list((tmp_path / "backups").glob("pre-migration-*.db"))


def test_reopening_database_preserves_status_history_and_settings(tmp_path):
    path = tmp_path / "radar.db"
    db = Database(path)
    listing_id, _ = db.upsert(Listing("Lote salvo", "Nacional", price=395000, area=360))
    db.set_status(listing_id, "interesting")
    db.set_state("github_last_check", "2026-09-25T10:00:00")

    reopened = Database(path)
    row = reopened.get(listing_id)
    assert row["status"] == "interesting"
    assert reopened.get_state("github_last_check") == "2026-09-25T10:00:00"
    with reopened.connect() as conn:
        prices = conn.execute("SELECT price FROM price_history WHERE listing_id=?", (listing_id,)).fetchall()
        assert [price[0] for price in prices] == [395000]
