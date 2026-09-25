import json
import logging
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import Listing
from .parsing import extract_contacts, extract_dimensions, extract_price, find_neighborhood, parse_area, parse_price, plain

LOG = logging.getLogger(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36 RadarDeLotes/1.0"}
PRIORITY_SEARCH_TERMS = (
    "terreno lote Nacional Contagem",
    "terreno lote Xangri-lá Xangri La Contagem",
    "terreno lote Parque Xangri-lá Parque Xangri La Contagem",
    "terreno lote Vale das Amendoeiras Contagem",
    "terreno lote Bom Jesus Contagem",
    "terreno lote Arvoredo Contagem",
)


class Connector(ABC):
    name = "Fonte"
    errors = 0
    @abstractmethod
    def search(self) -> list[Listing]: ...


def _flatten_jsonld(payload):
    queue = payload if isinstance(payload, list) else [payload]
    while queue:
        value = queue.pop(0)
        if not isinstance(value, dict):
            continue
        yield value
        graph = value.get("@graph", [])
        if isinstance(graph, list): queue.extend(graph)
        elements = value.get("itemListElement", [])
        if isinstance(elements, list):
            queue.extend(e.get("item", e) for e in elements if isinstance(e, dict))


def _first_image(image):
    if isinstance(image, list): image = image[0] if image else ""
    if isinstance(image, dict): image = image.get("url") or image.get("contentUrl") or ""
    return str(image or "")


def listing_from_jsonld(candidate, base_url, source):
    name = candidate.get("name") or candidate.get("headline") or ""
    url = candidate.get("url") or candidate.get("mainEntityOfPage") or ""
    if isinstance(url, dict): url = url.get("@id") or url.get("url") or ""
    if not name or not url: return None
    offer = candidate.get("offers", {}) or {}
    if isinstance(offer, list): offer = offer[0] if offer else {}
    description = str(candidate.get("description") or "")
    address_data = candidate.get("address", {}) or {}
    if not isinstance(address_data, dict): address_data = {}
    street = str(address_data.get("streetAddress") or "").strip()
    locality = str(address_data.get("addressLocality") or "").strip()
    region = str(address_data.get("addressRegion") or "").strip()
    postal = str(address_data.get("postalCode") or "").strip()
    combined = " ".join((str(name), description, street, locality, region))
    # Breadcrumbs, menus e páginas institucionais também aparecem em JSON-LD.
    # Exigir indicação textual de lote/terreno e ao menos um dado imobiliário.
    has_land_keyword = bool(re.search(r"\b(terreno|lote|lotes)\b", plain(combined)))
    raw_price = offer.get("price") or candidate.get("price")
    has_property_data = bool(raw_price or parse_area(combined) or street or locality)
    if not has_land_keyword or not has_property_data:
        return None
    city = "Contagem" if "contagem" in plain(combined) else locality
    neighborhood = find_neighborhood(name, description, street)
    if not neighborhood and locality and plain(locality) != "contagem": neighborhood = locality
    contacts = extract_contacts(" ".join((description, str(candidate.get("telephone", "")), str(candidate.get("email", "")))))
    if candidate.get("telephone"): contacts["phone"] = str(candidate["telephone"])
    if candidate.get("email"): contacts["email"] = str(candidate["email"])
    seller = candidate.get("seller") or candidate.get("provider") or {}
    agency = seller.get("name", "") if isinstance(seller, dict) else str(seller or "")
    identifier = candidate.get("sku") or candidate.get("productID") or candidate.get("identifier") or ""
    if isinstance(identifier, dict): identifier = identifier.get("value", "")
    images = candidate.get("image", "")
    image_values = images if isinstance(images, list) else ([images] if images else [])
    photo_urls = [_first_image(photo) for photo in image_values]
    photo_urls = [photo for photo in photo_urls if photo]
    full_address = ", ".join(part for part in (street, neighborhood, city, region, postal) if part)
    topo = next((x.capitalize() for x in ("plano", "aclive", "declive") if re.search(rf"\b{x}\b", plain(combined))), "")
    walled = "Sim" if re.search(r"\bmurad[oa]\b", plain(combined)) else ""
    cab_match = re.search(r"\bCAB\s*[:=-]?\s*([0-9]+(?:[.,][0-9]+)?)", combined, re.I)
    return Listing(
        title=str(name), neighborhood=neighborhood, city=city or "Contagem",
        price=parse_price(raw_price), area=parse_area(combined),
        dimensions=extract_dimensions(combined), topography=topo, walled=walled,
        cab=cab_match.group(1) if cab_match else "", address=full_address,
        url=urljoin(base_url, str(url)), source=source,
        image_url=photo_urls[0] if photo_urls else "", photos="\n".join(photo_urls),
        description=description, listing_code=str(identifier), phone=contacts["phone"],
        whatsapp=contacts["whatsapp"], email=contacts["email"], agency=agency,
    )


class JsonLdSearchConnector(Connector):
    """Lê dados Schema.org públicos; não contorna login, CAPTCHA ou bloqueios."""
    def __init__(self, name: str, urls: list[str]):
        self.name, self.urls, self.errors = name, urls, 0
        self.stats = {"requests": 0, "blocked": 0, "found": 0, "neighborhoods": {}}

    def search(self) -> list[Listing]:
        found = []; self.errors = 0
        self.stats = {"requests": 0, "blocked": 0, "found": 0, "neighborhoods": {}}
        for search_url in self.urls:
            self.stats["requests"] += 1
            try:
                response = requests.get(search_url, headers=HEADERS, timeout=8)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                before = len(found)
                for script in soup.select('script[type="application/ld+json"]'):
                    try: payload = json.loads(script.get_text(strip=True))
                    except (json.JSONDecodeError, TypeError): continue
                    for candidate in _flatten_jsonld(payload):
                        item = listing_from_jsonld(candidate, search_url, self.name)
                        if item:
                            found.append(item)
                            bairro = item.neighborhood or "Não informado"
                            self.stats["neighborhoods"][bairro] = self.stats["neighborhoods"].get(bairro, 0) + 1
                LOG.info("%s: %d anúncios públicos extraídos", self.name, len(found) - before)
            except requests.RequestException as exc:
                self.errors += 1
                if getattr(exc.response, "status_code", None) in (401, 403, 429): self.stats["blocked"] += 1
                LOG.warning("Fonte %s indisponível ou bloqueada: %s", self.name, exc)
        self.stats["found"] = len(found)
        return found


class PublicSearchRssConnector(Connector):
    """Usa resultados públicos indexados; nunca abre ou contorna o portal de destino."""
    name = "Resultados públicos"
    def __init__(self, terms=PRIORITY_SEARCH_TERMS):
        self.terms = terms; self.errors = 0
        self.urls = ["https://www.bing.com/search?format=rss&q=" + quote_plus(term + " venda") for term in terms]
        self.stats = {}

    def search(self) -> list[Listing]:
        found = []; self.errors = 0
        self.stats = {"requests": 0, "blocked": 0, "found": 0, "neighborhoods": {}}
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
                    neighborhood = find_neighborhood(combined)
                    if not neighborhood or not re.search(r"\b(terreno|lote|lotes)\b", plain(combined)) or not link:
                        continue
                    contacts = extract_contacts(description)
                    host = urlparse(link).netloc.removeprefix("www.") or "Resultado público"
                    item = Listing(
                        title=title, neighborhood=neighborhood, city="Contagem",
                        price=extract_price(combined), area=parse_area(combined),
                        dimensions=extract_dimensions(combined), description=description,
                        url=link, source=host, phone=contacts["phone"],
                        whatsapp=contacts["whatsapp"], email=contacts["email"],
                    )
                    if not any(existing.url == item.url for existing in found): found.append(item)
            except (requests.RequestException, ET.ParseError) as exc:
                self.errors += 1
                if isinstance(exc, requests.HTTPError) and getattr(exc.response, "status_code", None) in (401, 403, 429):
                    self.stats["blocked"] += 1
                LOG.warning("Resultados públicos indisponíveis: %s", exc)
        for item in found:
            self.stats["neighborhoods"][item.neighborhood] = self.stats["neighborhoods"].get(item.neighborhood, 0) + 1
        self.stats["found"] = len(found)
        return found


def _query_urls(base, parameter="q"):
    separator = "&" if "?" in base else "?"
    return [base] + [f"{base}{separator}{parameter}={quote_plus(term)}" for term in PRIORITY_SEARCH_TERMS]


def _neighborhood_pages(base, slugs, suffix=""):
    return [base] + [base.rstrip("/") + "/" + slug + suffix for slug in slugs]


def default_connectors() -> list[Connector]:
    neighborhoods = ("nacional", "xangri-la", "parque-xangri-la", "vale-das-amendoeiras", "bom-jesus", "arvoredo")
    return [
        PublicSearchRssConnector(),
        JsonLdSearchConnector("OLX", _query_urls("https://www.olx.com.br/imoveis/terrenos/estado-mg/belo-horizonte-e-regiao/contagem")),
        JsonLdSearchConnector("Viva Real", [
            "https://www.vivareal.com.br/venda/minas-gerais/contagem/lote-terreno_residencial/",
            *[f"https://www.vivareal.com.br/venda/minas-gerais/contagem/bairros/{slug}/lote-terreno_residencial/" for slug in neighborhoods],
        ]),
        JsonLdSearchConnector("Imovelweb", _query_urls("https://www.imovelweb.com.br/terrenos-venda-contagem-mg.html")),
        JsonLdSearchConnector("Chaves na Mão", [
            "https://www.chavesnamao.com.br/terrenos-a-venda/mg-contagem/",
            *[f"https://www.chavesnamao.com.br/terrenos-a-venda/mg-contagem/{slug}/" for slug in neighborhoods],
        ]),
        JsonLdSearchConnector("ZAP Imóveis", [
            "https://www.zapimoveis.com.br/venda/terrenos-lotes-condominios/mg+contagem/",
            *[f"https://www.zapimoveis.com.br/venda/terrenos-lotes-condominios/mg+contagem++{slug}/" for slug in neighborhoods],
        ]),
    ]
