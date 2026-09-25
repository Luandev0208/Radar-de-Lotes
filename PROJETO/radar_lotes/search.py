import logging
from dataclasses import asdict, dataclass
from datetime import datetime

from .connectors import default_connectors
from .database import Database
from .parsing import METRO_CITIES, find_city, plain

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
    city: str = ""
    neighborhoods: tuple[str, ...] = ()
    min_price: float | None = None
    max_price: float | None = None
    min_area: float | None = None
    max_area: float | None = None
    dimensions: str = ""
    topography: str = ""
    walled: str = ""
    require_price: bool = True

    @classmethod
    def from_dict(cls, data=None):
        data = data or {}
        neighborhoods = data.get("neighborhoods") or ()
        if isinstance(neighborhoods, str):
            neighborhoods = tuple(x.strip() for x in neighborhoods.split(",") if x.strip())
        else:
            neighborhoods = tuple(str(x).strip() for x in neighborhoods if str(x).strip())
        city = str(data.get("city") or "").strip()
        if city not in METRO_CITIES:
            city = ""
        return cls(
            city=city,
            neighborhoods=neighborhoods,
            min_price=_number(data.get("min_price")),
            max_price=_number(data.get("max_price")),
            min_area=_number(data.get("min_area")),
            max_area=_number(data.get("max_area")),
            dimensions=str(data.get("dimensions") or "").strip(),
            topography=str(data.get("topography") or "").strip(),
            walled=str(data.get("walled") or "").strip(),
            require_price=bool(data.get("require_price", True)),
        )

    def to_dict(self):
        data = asdict(self)
        data["neighborhoods"] = list(self.neighborhoods)
        return data

    def search_terms(self):
        region = self.city or "Belo Horizonte Região Metropolitana MG"
        places = self.neighborhoods or ("",)
        terms = []
        for place in places:
            pieces = ["terreno lote à venda", str(place).strip(), region, "Minas Gerais", "R$"]
            term = " ".join(piece for piece in pieces if piece).strip()
            if term not in terms:
                terms.append(term)
        return terms

    def _item_city(self, item):
        city = str(item.city or "").strip()
        if city in METRO_CITIES:
            return city
        return find_city(item.title, item.description, item.address, item.neighborhood)

    def match(self, item):
        missing = []
        city = self._item_city(item)

        if self.city:
            if not city or plain(city) != plain(self.city):
                return False, missing
        else:
            if city not in METRO_CITIES:
                return False, missing

        if self.require_price and item.price is None:
            return False, ["preço"]

        if self.neighborhoods:
            if item.neighborhood:
                current = plain(item.neighborhood)
                wanted = [plain(name) for name in self.neighborhoods]
                if not any(current == name or current in name or name in current for name in wanted):
                    return False, missing
            else:
                return False, ["bairro"]

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

        if not item.city:
            item.city = city
        return True, missing


@dataclass
class SearchResult:
    new: int = 0
    updated: int = 0
    rejected: int = 0
    missing_price: int = 0
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
            LOG.info("%s: %s anúncios individuais lidos", connector.name, len(items))
            for item in items:
                if filters.require_price and item.price is None:
                    result.missing_price += 1
                    result.rejected += 1
                    continue
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
