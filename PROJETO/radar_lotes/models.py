from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Listing:
    title: str
    neighborhood: str
    city: str = "Contagem"
    price: Optional[float] = None
    area: Optional[float] = None
    dimensions: str = ""
    topography: str = ""
    walled: str = ""
    cab: str = ""
    cam: str = ""
    address: str = ""
    url: str = ""
    source: str = "Manual"
    image_url: str = ""
    contact: str = ""
    notes: str = ""
    description: str = ""
    listing_code: str = ""
    phone: str = ""
    whatsapp: str = ""
    email: str = ""
    agency: str = ""
    broker: str = ""
    photos: str = ""
