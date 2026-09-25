import re
import unicodedata
from urllib.parse import quote_plus

KNOWN_NEIGHBORHOODS = (
    "Nacional", "Parque Xangri-lá", "Xangri-lá",
    "Vale das Amendoeiras", "Bom Jesus", "Arvoredo",
)

METRO_CITIES = (
    "Belo Horizonte",
    "Contagem",
    "Betim",
    "Ribeirão das Neves",
    "Ibirité",
    "Santa Luzia",
    "Sabará",
    "Nova Lima",
    "Vespasiano",
    "Lagoa Santa",
    "Pedro Leopoldo",
)


def plain(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", value).strip()


def parse_price(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().lower()
    simple = plain(raw)
    multiplier = 1_000_000 if re.search(r"\bmi(?:lha[oõ]es?)?\b", simple) else (1000 if re.search(r"\bmil\b", simple) else 1)
    match = re.search(r"\d[\d.,\s]*", raw)
    if not match:
        return None
    token = match.group(0).replace(" ", "")
    if "." in token and "," in token:
        token = token.replace(".", "").replace(",", ".") if token.rfind(",") > token.rfind(".") else token.replace(",", "")
    elif "," in token:
        tail = token.rsplit(",", 1)[1]
        token = token.replace(",", ".") if len(tail) <= 2 else token.replace(",", "")
    elif "." in token:
        parts = token.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            token = "".join(parts)
    try:
        result = float(token) * multiplier
    except ValueError:
        return None
    return result if result > 0 else None


def parse_area(text):
    source = str(text or "")
    for pattern in (
        r"\b(?:área|area|terreno|lote)\s*(?:total)?\s*[:=-]?\s*(\d{2,6}(?:[.,]\d+)?)\s*m\s*[²2]\b",
        r"\b(\d{2,6}(?:[.,]\d+)?)\s*m\s*[²2]\b",
    ):
        match = re.search(pattern, source, re.I)
        if match:
            return float(match.group(1).replace(",", "."))
    return None


def extract_price(text):
    source = str(text or "")
    match = re.search(
        r"R\$\s*\d[\d.,\s]*|\b\d+(?:[.,]\d+)?\s*(?:mil|mi(?:lh[aã]o|lh[oõ]es)?)\b",
        source,
        re.I,
    )
    return parse_price(match.group(0)) if match else None


def extract_dimensions(text):
    source = str(text or "")
    for pattern in (
        r"\b(\d{1,3}(?:[.,]\d+)?)\s*m?\s*[xX×]\s*(\d{1,3}(?:[.,]\d+)?)\s*m?\b",
        r"\b(?:frente|testada)\s*[:=-]?\s*(\d{1,3}(?:[.,]\d+)?)\s*m\b.{0,80}?\b(?:fundo|fundos|comprimento|profundidade)\s*[:=-]?\s*(\d{1,3}(?:[.,]\d+)?)\s*m\b",
    ):
        match = re.search(pattern, source, re.I | re.S)
        if match:
            return f"{match.group(1).replace(',', '.')} x {match.group(2).replace(',', '.')}"
    return ""


def extract_topography(text):
    value = plain(text)
    if re.search(r"\bterreno\s+plano\b|\btopografia\s*[:=-]?\s*plana?\b", value):
        return "Plano"
    if re.search(r"\baclive\b", value):
        return "Aclive"
    if re.search(r"\bdeclive\b", value):
        return "Declive"
    return ""


def extract_walled(text):
    value = plain(text)
    if re.search(r"\b(?:nao|sem)\s+(?:e\s+)?murad[oa]\b|\bnao\s+possui\s+muro\b", value):
        return "Não"
    if re.search(r"\bmurad[oa]\b", value):
        return "Sim"
    return ""


def extract_cab_cam(text):
    source = str(text or "")
    cab = cam = ""
    for pattern in (
        r"\bCAB\b\s*[:=-]?\s*([0-9]+(?:[.,][0-9]+)?)",
        r"\bcoeficiente\s+de\s+aproveitamento\s+b[aá]sico\b\s*[:=-]?\s*([0-9]+(?:[.,][0-9]+)?)",
    ):
        match = re.search(pattern, source, re.I)
        if match:
            cab = match.group(1).replace(",", ".")
            break
    for pattern in (
        r"\bCAM\b\s*[:=-]?\s*([0-9]+(?:[.,][0-9]+)?)",
        r"\bcoeficiente\s+de\s+aproveitamento\s+m[aá]ximo\b\s*[:=-]?\s*([0-9]+(?:[.,][0-9]+)?)",
    ):
        match = re.search(pattern, source, re.I)
        if match:
            cam = match.group(1).replace(",", ".")
            break
    return cab, cam


def extract_contacts(text):
    source = str(text or "")
    emails = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", source)
    phones = re.findall(r"(?:\+?55\s*)?\(?\d{2}\)?\s*9?\d{4}[-.\s]?\d{4}", source)
    phone = phones[0].strip() if phones else ""
    whatsapp = ""
    wa = re.search(r"(?:whats(?:app)?|wa\.me)[^\d+]*(\+?55\s*)?(\(?\d{2}\)?\s*9?\d{4}[-.\s]?\d{4})", source, re.I)
    if wa:
        whatsapp = wa.group(2).strip()
    return {"phone": phone, "whatsapp": whatsapp, "email": emails[0] if emails else ""}


def find_neighborhood(*texts, candidates=None):
    combined = plain(" ".join(str(x or "") for x in texts))
    for name in tuple(candidates or KNOWN_NEIGHBORHOODS):
        if plain(name) in combined:
            return name
    return ""


def find_city(*texts):
    combined = plain(" ".join(str(x or "") for x in texts))
    for city in METRO_CITIES:
        if plain(city) in combined:
            return city
    return ""


def _valid_coordinate(value, minimum, maximum):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if minimum <= number <= maximum:
        return number
    return None


def maps_query(address="", neighborhood="", city="", state="MG", latitude=None, longitude=None):
    lat = _valid_coordinate(latitude, -90, 90)
    lon = _valid_coordinate(longitude, -180, 180)
    if lat is not None and lon is not None:
        return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{lat:.7f},{lon:.7f}")

    city = str(city or "").strip()
    address = str(address or "").strip()
    neighborhood = str(neighborhood or "").strip()

    if not city:
        city = find_city(address, neighborhood)
    if not city:
        return ""

    values = [x.strip(" ,;-") for x in re.split(r"[,;\n]+", address) if x.strip(" ,;-")]
    values += [neighborhood, city, state, "Brasil"]

    parts = []
    normalized = []
    for value in values:
        value = str(value or "").strip()
        key = plain(value)
        if not key:
            continue
        if any(key == old or key in old or old in key for old in normalized):
            continue
        parts.append(value)
        normalized.append(key)

    if not parts:
        return ""
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(", ".join(parts))


def location_is_approximate(address="", latitude=None, longitude=None):
    if _valid_coordinate(latitude, -90, 90) is not None and _valid_coordinate(longitude, -180, 180) is not None:
        return False
    source = plain(address)
    if not source:
        return True
    street = re.search(r"\b(rua|avenida|av|alameda|travessa|rodovia|estrada|praca)\b", source)
    number = re.search(r"(?:,|\b(?:n|numero|nº)\.?\s*)\s*\d{1,6}\b", source)
    return not bool(street and number)
