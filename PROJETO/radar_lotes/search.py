import logging
from dataclasses import dataclass
from datetime import datetime

from .connectors import default_connectors
from .database import Database

LOG = logging.getLogger(__name__)


@dataclass
class SearchResult:
    new: int = 0
    updated: int = 0
    rejected: int = 0
    errors: int = 0
    source_stats: dict = None

    def __post_init__(self):
        if self.source_stats is None: self.source_stats = {}


def run_search(db: Database) -> SearchResult:
    result = SearchResult()
    for connector in default_connectors():
        try:
            items = connector.search()
            result.source_stats[connector.name] = getattr(connector, "stats", {"found": len(items)})
            result.errors += getattr(connector, "errors", 0)
            LOG.info("%s: %s anúncios lidos", connector.name, len(items))
            for item in items:
                if item.price is not None and item.price > 420_000:
                    result.rejected += 1
                    continue
                _, action = db.upsert(item)
                setattr(result, action, getattr(result, action) + 1)
        except Exception:
            LOG.exception("Erro na fonte %s", connector.name)
            result.errors += 1
    db.set_state("last_search", datetime.now().isoformat(timespec="minutes"))
    return result
