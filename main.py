import logging
import sys

from radar_lotes.settings import LOG_DIR, ensure_dirs


def setup_logging():
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(LOG_DIR / "radar.log", encoding="utf-8")],
    )


if __name__ == "__main__":
    setup_logging()
    if "--self-test" in sys.argv:
        from radar_lotes.database import Database
        from radar_lotes.version import __version__
        db = Database()
        print(f"Radar de Lotes {__version__}: OK ({db.path})")
        raise SystemExit(0)
    if "--scheduled" in sys.argv or "--search-only" in sys.argv:
        from radar_lotes.database import Database
        from radar_lotes.search import run_search
        result = run_search(Database())
        if result.new and sys.platform == "win32":
            try:
                from winotify import Notification
                Notification(
                    app_id="Radar de Lotes",
                    title="Novos lotes encontrados",
                    msg=f"{result.new} novo(s) lote(s). Abra o Radar para conferir.",
                ).show()
            except Exception:
                logging.exception("Não foi possível mostrar a notificação")
        raise SystemExit(0 if result.errors == 0 else 2)
    from radar_lotes.ui import run_app
    run_app()
