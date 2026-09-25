import json
import logging
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import Listing
from .parsing import (
    KNOWN_NEIGHBORHOODS, extract_cab_cam, extract_contacts, extract_dimensions,
    extract_price, extract_topography, extract_walled, find_neighborhood,
    parse_area, parse_price, plain,
)

LOG = logging.getLogger(__name__)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/124.0 Safari/537.36 RadarDeLotes/1.5"
}


class Connector(ABC):
    name = "Fonte"
    errors = 0

    @abstractmethod
    def search(self) -> list[Listing]:
        raise NotImplementedError


def _flatten_jsonld(payload):
    queue = payload if isinstance(payload, list) else [payload]
    while queue:
        value = queue.pop(0)
        if not isinstance(value, dict):
            continue
        yield value
        graph = value.get("@graph", [])
        if isinstance(graph, list):
            queue.extend(graph)
        elements = value.get("itemListElement", [])
        if isinstance(elements, list):
            queue.extend(e.get("item", e) for e in elements if isinstance(e, dict))


def _first_image(image):
    if isinstance(image, list):
        image = image[0] if image else ""
    if isinstance(image, dict):
        image = image.get("url") or image.get("contentUrl") or ""
    return str(image or "")


def _clean_address(street="", neighborhood="", city="", region="", postal=""):
    parts = []
    normalized = []
    for value in (street, neighborhood, city, region, postal):
        value = str(value or "").strip(" ,")
        key = plain(value)
        if not key:
            continue
        if any(key == old or key in old or old in key for old in normalized):
            continue
        parts.append(value)
        normalized.append(key)
    return ", ".join(parts)


def listing_from_jsonld(candidate, base_url, source, neighborhoods=()):
    name = candidate.get("name") or candidate.get("headline") or ""
    url = candidate.get("url") or candidate.get("mainEntityOfPage") or ""
    if isinstance(url, dict):
        url = url.get("@id") or url.get("url") or ""
    if not name or not url:
        return None

    offer = candidate.get("offers", {}) or {}
    if isinstance(offer, list):
        offer = offer[0] if offer else {}
    description = str(candidate.get("description") or "")
    address_data = candidate.get("address", {}) or {}
    if not isinstance(address_data, dict):
        address_data = {}
    street = str(address_data.get("streetAddress") or "").strip()
    locality = str(address_data.get("addressLocality") or "").strip()
    region = str(address_data.get("addressRegion") or "").strip()
    postal = str(address_data.get("postalCode") or "").strip()
    combined = " ".join((str(name), description, street, locality, region))

    has_land_keyword = bool(re.search(r"\b(terreno|lote|lotes)\b", plain(combined)))
    raw_price = offer.get("price") or candidate.get("price")
    has_property_data = bool(raw_price or parse_area(combined) or street or locality)
    if not has_land_keyword or not has_property_data:
        return None

    candidates = tuple(dict.fromkeys([*neighborhoods, *KNOWN_NEIGHBORHOODS]))
    neighborhood = find_neighborhood(name, description, street, candidates=candidates)
    if not neighborhood and locality and plain(locality) not in ("contagem", "belo horizonte"):
        neighborhood = locality

    city = locality
    for known_city in ("Contagem", "Belo Horizonte"):
        if plain(known_city) in plain(combined):
            city = known_city
            break

    contacts = extract_contacts(" ".join((
        description, str(candidate.get("telephone", "")), str(candidate.get("email", ""))
    )))
    if candidate.get("telephone"):
        contacts["phone"] = str(candidate["telephone"])
    if candidate.get("email"):
        contacts["email"] = str(candidate["email"])

    seller = candidate.get("seller") or candidate.get("provider") or {}
    agency = seller.get("name", "") if isinstance(seller, dict) else str(seller or "")
    identifier = candidate.get("sku") or candidate.get("productID") or candidate.get("identifier") or ""
    if isinstance(identifier, dict):
        identifier = identifier.get("value", "")

    images = candidate.get("image", "")
    image_values = images if isinstance(images, list) else ([images] if images else [])
    photos = [_first_image(photo) for photo in image_values]
    photos = [photo for photo in photos if photo]

    topo = extract_topography(combined)
    walled = extract_walled(combined)
    cab, cam = extract_cab_cam(combined)
    full_address = _clean_address(street, neighborhood, city, region, postal)

    return Listing(
        title=str(name), neighborhood=neighborhood, city=city or "",
        price=parse_price(raw_price) or extract_price(combined),
        area=parse_area(combined), dimensions=extract_dimensions(combined),
        topography=topo, walled=walled, cab=cab, cam=cam,
        address=full_address, url=urljoin(base_url, str(url)), source=source,
        image_url=photos[0] if photos else "", photos="\n".join(photos),
        description=description, listing_code=str(identifier),
        phone=contacts["phone"], whatsapp=contacts["whatsapp"],
        email=contacts["email"], agency=agency,
    )


class JsonLdSearchConnector(Connector):
    """Lê apenas dados públicos Schema.org/JSON-LD; não contorna bloqueios."""

    def __init__(self, name: str, urls: list[str], neighborhoods=()):
        self.name = name
        self.urls = urls
        self.neighborhoods = tuple(neighborhoods)
        self.errors = 0
        self.stats = {}

    def search(self) -> list[Listing]:
        found = []
        self.errors = 0
        self.stats = {"requests": 0, "blocked": 0, "found": 0, "neighborhoods": {}}
        for search_url in self.urls:
            self.stats["requests"] += 1
            try:
                response = requests.get(search_url, headers=HEADERS, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                for script in soup.select('script[type="application/ld+json"]'):
                    try:
                        payload = json.loads(script.get_text(strip=True))
                    except (json.JSONDecodeError, TypeError):
                        continue
                    for candidate in _flatten_jsonld(payload):
                        item = listing_from_jsonld(
                            candidate, search_url, self.name, self.neighborhoods
                        )
                        if item and not any(old.url == item.url for old in found):
                            found.append(item)
                            bairro = item.neighborhood or "Não informado"
                            self.stats["neighborhoods"][bairro] = (
                                self.stats["neighborhoods"].get(bairro, 0) + 1
                            )
            except requests.RequestException as exc:
                self.errors += 1
                if getattr(exc.response, "status_code", None) in (401, 403, 429):
                    self.stats["blocked"] += 1
                LOG.warning("Fonte %s indisponível ou bloqueada: %s", self.name, exc)
        self.stats["found"] = len(found)
        return found


class PublicSearchRssConnector(Connector):
    """Usa resultados públicos indexados; não abre nem contorna o portal de destino."""

    name = "Resultados públicos"

    def __init__(self, terms, neighborhoods=()):
        self.terms = tuple(terms)
        self.neighborhoods = tuple(neighborhoods)
        self.errors = 0
        self.urls = [
            "https://www.bing.com/search?format=rss&q=" + quote_plus(term + " venda")
            for term in self.terms
        ]
        self.stats = {}

    def search(self) -> list[Listing]:
        found = []
        self.errors = 0
        self.stats = {"requests": 0, "blocked": 0, "found": 0, "neighborhoods": {}}
        candidates = tuple(dict.fromkeys([*self.neighborhoods, *KNOWN_NEIGHBORHOODS]))
        for url in self.urls:
            self.stats["requests"] += 1
            try:
                response = requests.get(url, headers=HEADERS, timeout=12)
                response.raise_for_status()
                root = ET.fromstring(response.content)
                for node in root.findall("./channel/item"):
                    title = node.findtext("title", "").strip()
                    link = node.findtext("link", "").strip()
                    description = node.findtext("description", "").strip()
                    combined = f"{title} {description}"
                    if not re.search(r"\b(terreno|lote|lotes)\b", plain(combined)) or not link:
                        continue
                    neighborhood = find_neighborhood(combined, candidates=candidates)
                    contacts = extract_contacts(description)
                    cab, cam = extract_cab_cam(combined)
                    host = urlparse(link).netloc.removeprefix("www.") or "Resultado público"
                    item = Listing(
                        title=title, neighborhood=neighborhood, city="",
                        price=extract_price(combined), area=parse_area(combined),
                        dimensions=extract_dimensions(combined),
                        topography=extract_topography(combined),
                        walled=extract_walled(combined), cab=cab, cam=cam,
                        description=description, url=link, source=host,
                        phone=contacts["phone"], whatsapp=contacts["whatsapp"],
                        email=contacts["email"],
                    )
                    if not any(existing.url == item.url for existing in found):
                        found.append(item)
            except (requests.RequestException, ET.ParseError) as exc:
                self.errors += 1
                if isinstance(exc, requests.HTTPError) and getattr(exc.response, "status_code", None) in (401, 403, 429):
                    self.stats["blocked"] += 1
                LOG.warning("Resultados públicos indisponíveis: %s", exc)
        for item in found:
            key = item.neighborhood or "Não informado"
            self.stats["neighborhoods"][key] = self.stats["neighborhoods"].get(key, 0) + 1
        self.stats["found"] = len(found)
        return found


def _query_urls(base, terms, parameter="q"):
    separator = "&" if "?" in base else "?"
    return [base] + [
        f"{base}{separator}{parameter}={quote_plus(term)}" for term in terms
    ]


def _slug(value):
    return re.sub(r"[^a-z0-9]+", "-", plain(value)).strip("-")


def default_connectors(filters=None) -> list[Connector]:
    neighborhoods = tuple(getattr(filters, "neighborhoods", ()) or ())
    terms = tuple(filters.search_terms()) if filters else ("terreno lote Contagem",)
    city = getattr(filters, "city", "") if filters else "Contagem"
    city_slug = _slug(city or "contagem")
    neighborhood_slugs = [_slug(name) for name in neighborhoods if _slug(name)]

    viva_base = f"https://www.vivareal.com.br/venda/minas-gerais/{city_slug}/lote-terreno_residencial/"
    viva_urls = [viva_base] + [
        f"https://www.vivareal.com.br/venda/minas-gerais/{city_slug}/bairros/{slug}/lote-terreno_residencial/"
        for slug in neighborhood_slugs
    ]

    return [
        PublicSearchRssConnector(terms, neighborhoods),
        JsonLdSearchConnector(
            "OLX",
            _query_urls("https://www.olx.com.br/imoveis/terrenos/estado-mg/belo-horizonte-e-regiao/contagem", terms),
            neighborhoods,
        ),
        JsonLdSearchConnector("Viva Real", viva_urls, neighborhoods),
        JsonLdSearchConnector(
            "Imovelweb",
            _query_urls("https://www.imovelweb.com.br/terrenos-venda-contagem-mg.html", terms),
            neighborhoods,
        ),
        JsonLdSearchConnector(
            "Chaves na Mão",
            _query_urls("https://www.chavesnamao.com.br/terrenos-a-venda/mg-contagem/", terms),
            neighborhoods,
        ),
        JsonLdSearchConnector(
            "ZAP Imóveis",
            _query_urls("https://www.zapimoveis.com.br/venda/terrenos-lotes-condominios/mg+contagem/", terms),
            neighborhoods,
        ),
    ]
