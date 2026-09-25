import logging
from dataclasses import asdict, dataclass
from datetime import datetime

from .connectors import default_connectors
from .database import Database
from .parsing import plain

LOG = logging.getLogger(__name__)


def _number(value):
    if value in (None, "", 0, 0.0):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class SearchFilters:
    city: str = "Contagem"
    neighborhoods: tuple[str, ...] = ()
    min_price: float | None = None
    max_price: float | None = None
    min_area: float | None = None
    max_area: float | None = None
    dimensions: str = ""
    topography: str = ""
    walled: str = ""

    @classmethod
    def from_dict(cls, data=None):
        data = data or {}
        neighborhoods = data.get("neighborhoods") or ()
        if isinstance(neighborhoods, str):
            neighborhoods = tuple(x.strip() for x in neighborhoods.split(",") if x.strip())
        else:
            neighborhoods = tuple(str(x).strip() for x in neighborhoods if str(x).strip())
        return cls(
            city=str(data.get("city") or "").strip(),
            neighborhoods=neighborhoods,
            min_price=_number(data.get("min_price")),
            max_price=_number(data.get("max_price")),
            min_area=_number(data.get("min_area")),
            max_area=_number(data.get("max_area")),
            dimensions=str(data.get("dimensions") or "").strip(),
            topography=str(data.get("topography") or "").strip(),
            walled=str(data.get("walled") or "").strip(),
        )

    def to_dict(self):
        data = asdict(self)
        data["neighborhoods"] = list(self.neighborhoods)
        return data

    def search_terms(self):
        places = self.neighborhoods or ((self.city,) if self.city else ("",))
        terms = []
        for place in places:
            pieces = ["terreno lote", str(place).strip()]
            if self.city and plain(self.city) not in plain(str(place)):
                pieces.append(self.city)
            term = " ".join(piece for piece in pieces if piece).strip()
            if term and term not in terms:
                terms.append(term)
        return terms or ["terreno lote"]

    def match(self, item):
        missing = []
        if self.city:
            if item.city and plain(item.city) != plain(self.city):
                return False, missing
            if not item.city:
                missing.append("cidade")

        if self.neighborhoods:
            if item.neighborhood:
                current = plain(item.neighborhood)
                wanted = [plain(name) for name in self.neighborhoods]
                if not any(current == name or current in name or name in current for name in wanted):
                    return False, missing
            else:
                missing.append("bairro")

        for field, minimum, maximum, label in (
            ("price", self.min_price, self.max_price, "preço"),
            ("area", self.min_area, self.max_area, "área"),
        ):
            current = getattr(item, field)
            if minimum is not None or maximum is not None:
                if current is None:
                    missing.append(label)
                elif minimum is not None and current < minimum:
                    return False, missing
                elif maximum is not None and current > maximum:
                    return False, missing

        if self.dimensions:
            if item.dimensions:
                wanted = plain(self.dimensions).replace(" ", "")
                current = plain(item.dimensions).replace(" ", "")
                if wanted not in current and current not in wanted:
                    return False, missing
            else:
                missing.append("dimensões")

        if self.topography:
            if item.topography and plain(self.topography) not in plain(item.topography):
                return False, missing
            if not item.topography:
                missing.append("topografia")

        if self.walled:
            if item.walled and plain(self.walled) != plain(item.walled):
                return False, missing
            if not item.walled:
                missing.append("murado")

        return True, missing


@dataclass
class SearchResult:
    new: int = 0
    updated: int = 0
    rejected: int = 0
    errors: int = 0
    source_stats: dict | None = None

    def __post_init__(self):
        if self.source_stats is None:
            self.source_stats = {}


def run_search(db: Database, filters: SearchFilters | None = None):
    filters = filters or SearchFilters()
    result = SearchResult()
    for connector in default_connectors(filters):
        try:
            items = connector.search()
            result.source_stats[connector.name] = getattr(connector, "stats", {"found": len(items)})
            result.errors += getattr(connector, "errors", 0)
            LOG.info("%s: %s anúncios lidos", connector.name, len(items))
            for item in items:
                accepted, missing = filters.match(item)
                if not accepted:
                    result.rejected += 1
                    continue
                _, action = db.upsert(item, criteria=filters.to_dict(), missing_criteria=missing)
                setattr(result, action, getattr(result, action) + 1)
        except Exception:
            LOG.exception("Erro na fonte %s", connector.name)
            result.errors += 1
    db.set_state("last_search", datetime.now().isoformat(timespec="minutes"))
    db.set_state("search_filters", filters.to_dict())
    return result
