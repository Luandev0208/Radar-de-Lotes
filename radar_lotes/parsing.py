import re
import unicodedata
from urllib.parse import quote_plus

PRIORITY_NEIGHBORHOODS = (
    "Nacional", "Parque Xangri-lá", "Xangri-lá",
    "Vale das Amendoeiras", "Bom Jesus", "Arvoredo",
)


def plain(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in value if not unicodedata.combining(c)).lower()


def parse_price(value):
    """Converte preços brasileiros ou decimais sem multiplicar centavos por 100."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip().lower()
    multiplier = 1000 if re.search(r"\bmil\b", raw) else 1
    token_match = re.search(r"\d[\d.,\s]*", raw)
    if not token_match:
        return None
    token = token_match.group(0).replace(" ", "")
    if "." in token and "," in token:
        # O separador mais à direita é decimal; o outro é de milhar.
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        tail = token.rsplit(",", 1)[1]
        token = token.replace(",", ".") if len(tail) <= 2 else token.replace(",", "")
    elif "." in token:
        parts = token.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            token = "".join(parts)
    try:
        return float(token) * multiplier
    except ValueError:
        return None


def parse_area(text):
    match = re.search(r"(\d{2,5}(?:[.,]\d+)?)\s*m\s*[²2]", str(text or ""), re.I)
    return float(match.group(1).replace(",", ".")) if match else None


def extract_price(text):
    source = str(text or "")
    match = re.search(r"R\$\s*\d[\d.,\s]*|\b\d+(?:[.,]\d+)?\s*mil\b", source, re.I)
    return parse_price(match.group(0)) if match else None


def extract_dimensions(text):
    match = re.search(r"\b(\d{1,3}(?:[.,]\d+)?)\s*[xX×]\s*(\d{1,3}(?:[.,]\d+)?)\s*(?:m\b)?", str(text or ""))
    return f"{match.group(1)} x {match.group(2)}" if match else ""


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


def find_neighborhood(*texts):
    combined = plain(" ".join(str(x or "") for x in texts))
    for name in PRIORITY_NEIGHBORHOODS:
        if plain(name) in combined:
            return name
    return ""


def maps_query(address="", neighborhood="", city=""):
    parts = []
    for value in (address, neighborhood, city):
        value = str(value or "").strip()
        if value and plain(value) not in {plain(x) for x in parts}:
            parts.append(value)
    if not parts:
        return ""
    return "https://www.google.com/maps/search/?api=1&query=" + quote_plus(", ".join(parts))


def location_is_approximate(address=""):
    return not bool(re.search(r"\b\d{1,6}\b", str(address or "")))
