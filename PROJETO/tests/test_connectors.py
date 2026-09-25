from radar_lotes.connectors import default_connectors, listing_from_jsonld
from radar_lotes.search import SearchFilters


def test_jsonld_extracts_property_fields_without_inventing():
    data = {
        "name": "Lote no Nacional",
        "url": "/imovel/123",
        "description": "Terreno plano, murado, 360 m², 12x30. CAB: 1,0. WhatsApp (31) 99999-9999",
        "offers": {"price": "395000.00"},
        "address": {
            "addressLocality": "Contagem",
            "addressRegion": "MG",
            "streetAddress": "Rua X, 120, Nacional",
        },
        "email": "vendas@imob.com.br",
    }
    item = listing_from_jsonld(data, "https://exemplo.com/busca", "Teste", ("Nacional",))
    assert item.price == 395000
    assert item.city == "Contagem"
    assert item.neighborhood == "Nacional"
    assert item.dimensions == "12 x 30"
    assert item.topography == "Plano"
    assert item.walled == "Sim"
    assert item.cab == "1.0"
    assert item.cam == ""
    assert item.whatsapp
    assert item.email == "vendas@imob.com.br"
    assert item.address.count("Nacional") == 1


def test_non_listing_jsonld_is_rejected():
    menu = {"@type": "WebSite", "name": "Imóveis em Contagem", "url": "/"}
    assert listing_from_jsonld(menu, "https://exemplo.com", "Teste") is None


def test_connectors_follow_filters_instead_of_fixed_neighborhoods():
    filters = SearchFilters(city="Contagem", neighborhoods=("Jardim Riacho",))
    connectors = default_connectors(filters)
    assert any("Jardim+Riacho" in url or "jardim-riacho" in url for connector in connectors for url in connector.urls)
